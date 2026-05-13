from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages

from .models import (
    ShiftSession,
    Sale,
    SaleLine,
    Payment,
    Refund,
    RefundLine,
    ReceiptTemplate,
    POSMessage,
)
from .forms import (
    OpenSessionForm, CloseSessionForm, BarcodeEntryForm,
    PaymentForm, RefundForm, ReceiptTemplateForm, POSMessageForm,
)
from apps.catalog.models import Product


def _has_pos_access(user):
    """Return True if the user is superuser, Admin, or Staff."""
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=["Admin", "Staff"]).exists()


def pos_login_required(view_func):
    """Decorator: require login + POS role (Staff/Admin/Superuser)."""
    @login_required
    def wrapped(request, *args, **kwargs):
        if not _has_pos_access(request.user):
            return redirect(settings.LOGIN_URL)
        return view_func(request, *args, **kwargs)
    return wrapped


class POSAccessMixin(AccessMixin):
    """Mixin: require login + POS role (Staff/Admin/Superuser)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not _has_pos_access(request.user):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdminOrSuperuserMixin(AccessMixin):
    """Mixin: require login + Admin role or superuser."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Shift Session
# ---------------------------------------------------------------------------

@pos_login_required
def session_open(request):
    active = ShiftSession.objects.filter(opened_by=request.user, closed_at__isnull=True).first()
    if active:
        return redirect("pos:sale_new", session_id=active.pk)

    if request.method == "POST":
        form = OpenSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.opened_by = request.user
            session.save()
            return redirect("pos:sale_new", session_id=session.pk)
    else:
        form = OpenSessionForm()
    return render(request, "pos/session_open.html", {"form": form})


@pos_login_required
def session_close(request, session_id):
    session = get_object_or_404(ShiftSession, pk=session_id, opened_by=request.user)
    if request.method == "POST":
        form = CloseSessionForm(request.POST, instance=session)
        if form.is_valid():
            s = form.save(commit=False)
            s.closed_at = timezone.now()
            s.save()
            return redirect("pos:session_open")
    else:
        form = CloseSessionForm(instance=session)
    return render(request, "pos/session_close.html", {"form": form, "session": session})


# ---------------------------------------------------------------------------
# Sale
# ---------------------------------------------------------------------------

@pos_login_required
def sale_new(request, session_id):
    session = get_object_or_404(ShiftSession, pk=session_id)
    sale = Sale.objects.create(session=session, status=Sale.STATUS_PENDING)
    return redirect("pos:sale_detail", pk=sale.pk)


@pos_login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    barcode_form = BarcodeEntryForm()
    error = None

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_line":
            barcode_form = BarcodeEntryForm(request.POST)
            if barcode_form.is_valid():
                barcode = barcode_form.cleaned_data["barcode"].strip()
                qty = barcode_form.cleaned_data["qty"]
                try:
                    product = Product.objects.get(barcode=barcode)
                    # Check if line already exists
                    existing = sale.lines.filter(barcode=barcode).first()
                    if existing:
                        existing.qty += qty
                        existing.save()
                    else:
                        SaleLine.objects.create(
                            sale=sale,
                            product=product,
                            barcode=product.barcode,
                            name_snapshot=product.name,
                            unit_price=product.sales_price,
                            qty=qty,
                        )
                    barcode_form = BarcodeEntryForm()
                except Product.DoesNotExist:
                    error = f"Product with barcode '{barcode}' not found."
        elif action == "remove_line":
            line_id = request.POST.get("line_id")
            sale.lines.filter(pk=line_id).delete()

    return render(request, "pos/sale_detail.html", {
        "sale": sale,
        "barcode_form": barcode_form,
        "error": error,
        "lines": sale.lines.all(),
    })


@pos_login_required
def sale_payment(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.sale = sale
            payment.save()
            sale.status = Sale.STATUS_PAID
            sale.save()
            messages.success(request, "Payment recorded. Sale complete.")
            return redirect("pos:sale_receipt", pk=sale.pk)
    else:
        form = PaymentForm(initial={"amount": sale.total})
    return render(request, "pos/sale_payment.html", {"sale": sale, "form": form})


@pos_login_required
def sale_receipt(request, pk):
    sale = get_object_or_404(Sale.objects.prefetch_related("lines", "refunds__lines", "refunds__lines__sale_line"), pk=pk)
    return render(request, "pos/sale_receipt.html", {
        "sale": sale,
        "refunds": sale.refunds.prefetch_related("lines", "lines__sale_line").all(),
        "refund_page_url": reverse("pos:refund_create") + f"?sale_id={sale.pk}",
    })


def _get_refunded_qty_map(sale):
    refunded = {}
    for refund in sale.refunds.prefetch_related("lines").all():
        for refund_line in refund.lines.all():
            refunded[refund_line.sale_line_id] = refunded.get(refund_line.sale_line_id, 0) + refund_line.qty
    return refunded


def _update_sale_refund_status(sale):
    refunded_map = _get_refunded_qty_map(sale)
    total_original = 0
    total_remaining = 0
    total_refunded = 0
    for line in sale.lines.all():
        refunded_qty = refunded_map.get(line.pk, 0)
        total_original += line.qty
        total_refunded += refunded_qty
        total_remaining += max(line.qty - refunded_qty, 0)

    if total_refunded <= 0:
        return
    if total_remaining <= 0:
        sale.status = Sale.STATUS_REFUNDED
    else:
        sale.status = Sale.STATUS_PARTIALLY_REFUNDED
    sale.save(update_fields=["status"])


@pos_login_required
def refund_create(request):
    sale = None
    sale_lines = []
    refund_history = []
    recent_sales = (
        Sale.objects.prefetch_related("payments", "lines")
        .order_by("-created_at")[:30]
    )

    sale_id = request.GET.get("sale_id") or request.POST.get("sale_id")
    if sale_id:
        sale = get_object_or_404(
            Sale.objects.prefetch_related("lines", "refunds__lines"),
            pk=sale_id,
        )
        refunded_map = _get_refunded_qty_map(sale)
        for line in sale.lines.all():
            refunded_qty = refunded_map.get(line.pk, 0)
            sale_lines.append({
                "line": line,
                "refunded_qty": refunded_qty,
                "available_qty": max(line.qty - refunded_qty, 0),
            })
        refund_history = sale.refunds.prefetch_related("lines", "lines__sale_line").all()

    if request.method == "POST":
        action = request.POST.get("action")
        if action in {"find", "select_sale"}:
            sale_id = request.POST.get("sale_id")
            if Sale.objects.filter(pk=sale_id).exists():
                return redirect(f"{reverse('pos:refund_create')}?sale_id={sale_id}")
            messages.error(request, f"Sale #{sale_id} not found.")
        elif action == "refund_lines":
            sale = get_object_or_404(
                Sale.objects.prefetch_related("lines", "refunds__lines"),
                pk=request.POST.get("sale_id"),
            )
            refunded_map = _get_refunded_qty_map(sale)
            selected = []
            total_amount = 0
            reason = (request.POST.get("reason") or "").strip()

            for line in sale.lines.all():
                qty_raw = (request.POST.get(f"refund_qty_{line.pk}") or "").strip()
                if not qty_raw:
                    continue
                try:
                    qty = int(qty_raw)
                except ValueError:
                    messages.error(request, f"Invalid quantity for {line.name_snapshot}.")
                    break
                if qty <= 0:
                    continue
                available_qty = max(line.qty - refunded_map.get(line.pk, 0), 0)
                if qty > available_qty:
                    messages.error(request, f"Refund quantity for {line.name_snapshot} exceeds available quantity ({available_qty}).")
                    break
                selected.append((line, qty))
                total_amount += line.unit_price * qty
            else:
                if not selected:
                    messages.error(request, "Select at least one line item to refund.")
                else:
                    refund = Refund.objects.create(
                        sale=sale,
                        amount=total_amount,
                        reason=reason,
                    )
                    for line, qty in selected:
                        RefundLine.objects.create(
                            refund=refund,
                            sale_line=line,
                            qty=qty,
                            unit_price=line.unit_price,
                        )
                    _update_sale_refund_status(sale)
                    messages.success(request, f"Refund registered for {len(selected)} item line(s).")
                    return redirect("pos:sale_receipt", pk=sale.pk)
    return render(
        request,
        "pos/refund.html",
        {
            "sale": sale,
            "sale_lines": sale_lines,
            "refund_history": refund_history,
            "recent_sales": recent_sales,
        },
    )


# ---------------------------------------------------------------------------
# Receipt Template
# ---------------------------------------------------------------------------

class ReceiptTemplateListView(POSAccessMixin, ListView):
    model = ReceiptTemplate
    template_name = "pos/receipt_list.html"
    context_object_name = "templates"


class ReceiptTemplateCreateView(AdminOrSuperuserMixin, CreateView):
    model = ReceiptTemplate
    form_class = ReceiptTemplateForm
    template_name = "pos/receipt_form.html"
    success_url = reverse_lazy("pos:receipt_list")


class ReceiptTemplateUpdateView(AdminOrSuperuserMixin, UpdateView):
    model = ReceiptTemplate
    form_class = ReceiptTemplateForm
    template_name = "pos/receipt_form.html"
    success_url = reverse_lazy("pos:receipt_list")


class ReceiptTemplateDeleteView(AdminOrSuperuserMixin, DeleteView):
    model = ReceiptTemplate
    template_name = "pos/receipt_confirm_delete.html"
    success_url = reverse_lazy("pos:receipt_list")


@pos_login_required
def receipt_preview(request, pk):
    template = get_object_or_404(ReceiptTemplate, pk=pk)
    return render(request, "pos/receipt_preview.html", {"tmpl": template})


# ---------------------------------------------------------------------------
# POS Messages
# ---------------------------------------------------------------------------

class POSMessageListView(POSAccessMixin, ListView):
    model = POSMessage
    template_name = "pos/message_list.html"
    context_object_name = "pos_messages"


class POSMessageCreateView(AdminOrSuperuserMixin, CreateView):
    model = POSMessage
    form_class = POSMessageForm
    template_name = "pos/message_form.html"
    success_url = reverse_lazy("pos_messages:message_list")


class POSMessageUpdateView(AdminOrSuperuserMixin, UpdateView):
    model = POSMessage
    form_class = POSMessageForm
    template_name = "pos/message_form.html"
    success_url = reverse_lazy("pos_messages:message_list")


class POSMessageDeleteView(AdminOrSuperuserMixin, DeleteView):
    model = POSMessage
    template_name = "pos/message_confirm_delete.html"
    success_url = reverse_lazy("pos_messages:message_list")


# ---------------------------------------------------------------------------
# Sale History
# ---------------------------------------------------------------------------

class SaleHistoryView(POSAccessMixin, ListView):
    """View all completed sales with filtering and summary statistics."""
    model = Sale
    template_name = "pos/sale_history.html"
    context_object_name = "sales"
    paginate_by = 20

    def get_queryset(self):
        qs = Sale.objects.prefetch_related('lines').order_by('-created_at')
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            try:
                from datetime import datetime
                qs = qs.filter(created_at__date__gte=datetime.strptime(date_from, "%Y-%m-%d").date())
            except:
                pass
        
        if date_to:
            try:
                from datetime import datetime
                qs = qs.filter(created_at__date__lte=datetime.strptime(date_to, "%Y-%m-%d").date())
            except:
                pass
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # Summary statistics
        today = timezone.now().date()
        ctx['sales_today'] = Sale.objects.filter(created_at__date=today).count()
        ctx['total_sales_today'] = sum(
            s.total for s in Sale.objects.filter(created_at__date=today)
        )
        ctx['status_choices'] = Sale.STATUS_CHOICES
        
        return ctx

