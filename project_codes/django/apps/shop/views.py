from decimal import Decimal
from datetime import datetime
import re

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin
from django.conf import settings
from django.http import JsonResponse
from django.db.utils import OperationalError, ProgrammingError
from django.db.models import DateField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import DetailView, ListView

from apps.accounts.models import SiteSettings
from apps.catalog.models import Product, ProductCategory
from apps.inventory.models import ExpirationEntry
from .forms import (
    AdminContactMessageForm,
    CheckoutForm,
    ContactCustomerReplyForm,
    ContactMessageForm,
    ContactReplyForm,
)
from .models import (
    ContactMessage,
    ContactMessageEntry,
    Order,
    OrderLine,
    SavedInvoiceProfile,
    SavedShippingAddress,
)

CART_SESSION_KEY = "shop_cart"
User = get_user_model()


def _with_effective_expiration(qs):
    first_exp = ExpirationEntry.objects.filter(
        product_id=OuterRef("pk")
    ).order_by("expiration_date").values("expiration_date")[:1]
    return qs.annotate(
        effective_expiration_value=Coalesce(
            "default_expiration_date",
            Subquery(first_exp, output_field=DateField()),
        )
    )


def _is_staff_or_admin(user):
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name__in=["Admin", "Staff"]).exists()


def _require_customer_user(request):
    """Return redirect response when staff/admin tries to access customer shop screens."""
    if _is_staff_or_admin(getattr(request, "user", None)):
        messages.info(request, "Customer shop pages are disabled for staff/admin accounts.")
        return redirect("pos:session_open")
    return None


def _build_contact_thread(msg):
    """Build a chronological thread including legacy fields and chat entries."""
    thread = []
    chat_entries = None

    try:
        chat_entries = list(msg.chat_entries.select_related("sender").all())
    except (ProgrammingError, OperationalError):
        # Fallback for databases where the new table hasn't been migrated yet.
        chat_entries = None

    if chat_entries is not None and chat_entries:
        for entry in chat_entries:
            sender = entry.sender
            sender_is_staff = _is_staff_or_admin(sender)
            thread.append({
                "author_type": "staff" if sender_is_staff else "customer",
                "is_staff": sender_is_staff,
                "sender_id": getattr(sender, "id", None),
                "sender_label": getattr(sender, "email", "Support Team") if sender else "Support Team",
                "body": entry.body,
                "created_at": entry.created_at,
                "sequence": len(thread),
            })
    else:
        root_sender = msg.sent_by or msg.user
        root_is_staff = _is_staff_or_admin(root_sender)
        thread.append({
            "author_type": "staff" if root_is_staff else "customer",
            "is_staff": root_is_staff,
            "sender_id": getattr(root_sender, "id", None),
            "sender_label": getattr(root_sender, "email", "Support Team") if root_sender else "Support Team",
            "body": msg.body,
            "created_at": msg.created_at,
            "sequence": len(thread),
        })

        if msg.reply:
            thread.append({
                "author_type": "staff",
                "is_staff": True,
                "sender_id": getattr(msg.replied_by, "id", None),
                "sender_label": getattr(msg.replied_by, "email", "Support Team") if msg.replied_by else "Support Team",
                "body": msg.reply,
                "created_at": msg.replied_at or msg.created_at,
                "sequence": len(thread),
            })

        if msg.customer_reply:
            thread.append({
                "author_type": "customer",
                "is_staff": False,
                "sender_id": getattr(msg.customer_replied_by, "id", getattr(msg.user, "id", None)),
                "sender_label": getattr(msg.customer_replied_by, "email", getattr(msg.user, "email", "Customer")),
                "body": msg.customer_reply,
                "created_at": msg.customer_replied_at or msg.created_at,
                "sequence": len(thread),
            })

    thread.sort(key=lambda item: (item["created_at"], item.get("sequence", 0)))
    return thread


_WEEKDAY_INDEX = {
    "Mon": 0,
    "Tue": 1,
    "Wed": 2,
    "Thu": 3,
    "Fri": 4,
    "Sat": 5,
    "Sun": 6,
}


def _is_within_work_hours(site_settings, moment=None):
    if not getattr(settings, "WORK_HOURS_ENFORCEMENT", True):
        return True
    text = (site_settings.work_hours or "").strip()
    match = re.match(
        r"^(?P<days>[A-Za-z]{3}(?:-[A-Za-z]{3})?)\s+(?P<start>\d{2}:\d{2})-(?P<end>\d{2}:\d{2})$",
        text,
    )
    if not match:
        return True

    moment = moment or datetime.now()
    day_part = match.group("days")
    if "-" in day_part:
        start_day, end_day = day_part.split("-", 1)
    else:
        start_day = end_day = day_part

    start_idx = _WEEKDAY_INDEX.get(start_day[:3].title())
    end_idx = _WEEKDAY_INDEX.get(end_day[:3].title())
    if start_idx is None or end_idx is None:
        return True

    weekday = moment.weekday()
    in_day_range = start_idx <= weekday <= end_idx if start_idx <= end_idx else weekday >= start_idx or weekday <= end_idx
    if not in_day_range:
        return False

    start_time = datetime.strptime(match.group("start"), "%H:%M").time()
    end_time = datetime.strptime(match.group("end"), "%H:%M").time()
    current_time = moment.time()
    return start_time <= current_time <= end_time


# ---------------------------------------------------------------------------
# Helper: cart from session
# ---------------------------------------------------------------------------

def _get_cart(request):
    """Return a copy of the cart dict from session."""
    return dict(request.session.get(CART_SESSION_KEY, {}))


def _save_cart(request, cart):
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def _cart_payload(request):
    cart = _get_cart(request)
    items = []
    total = Decimal("0.00")
    for pid, data in cart.items():
        subtotal = Decimal(str(data["price"])) * data["qty"]
        items.append({
            "id": pid,
            "name": data["name"],
            "barcode": data.get("barcode", ""),
            "sales_description": data.get("sales_description", ""),
            "expiration_date": data.get("expiration_date", ""),
            "price": f'{Decimal(str(data["price"])):.2f}',
            "qty": data["qty"],
            "subtotal": f"{subtotal:.2f}",
        })
        total += subtotal
    return {"items": items, "total": f"{total:.2f}"}


# ---------------------------------------------------------------------------
# Public: Shop catalog (anonymous-accessible)
# ---------------------------------------------------------------------------

class ShopCatalogView(ListView):
    model = Product
    template_name = "shop/catalog.html"
    context_object_name = "products"
    paginate_by = 24

    def dispatch(self, request, *args, **kwargs):
        blocked = _require_customer_user(request)
        if blocked:
            return blocked
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = _with_effective_expiration(
            Product.objects.select_related("category").prefetch_related("expiration_entries")
        )
        q = self.request.GET.get("q", "").strip()
        cat = self.request.GET.get("cat", "").strip()
        sort = self.request.GET.get("sort", "name_asc")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(barcode__icontains=q))
        if cat:
            qs = qs.filter(category__pk=cat)
        sort_map = {
            "name_asc": "name",
            "name_desc": "-name",
            "price_asc": "sales_price",
            "price_desc": "-sales_price",
        }
        qs = qs.order_by(sort_map.get(sort, "name"))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["categories"] = ProductCategory.objects.all()
        ctx["selected_cat"] = self.request.GET.get("cat", "")
        ctx["sort"] = self.request.GET.get("sort", "name_asc")
        ctx["view_mode"] = self.request.GET.get("view", "grid")
        return ctx


def shop_catalog_ajax(request):
    """AJAX endpoint returning rendered HTML for the product grid and pagination."""
    from django.core.paginator import Paginator
    from django.http import JsonResponse
    from django.template.loader import render_to_string

    blocked = _require_customer_user(request)
    if blocked:
        return redirect("pos:session_open")

    qs = _with_effective_expiration(
        Product.objects.select_related("category").prefetch_related("expiration_entries").all()
    )
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("cat", "").strip()
    sort = request.GET.get("sort", "name_asc")
    view_mode = request.GET.get("view", "grid")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(barcode__icontains=q))
    if cat:
        qs = qs.filter(category__pk=cat)
    sort_map = {
        "name_asc": "name",
        "name_desc": "-name",
        "price_asc": "sales_price",
        "price_desc": "-sales_price",
    }
    qs = qs.order_by(sort_map.get(sort, "name"))

    # paginate (match ShopCatalogView.paginate_by)
    page_num = request.GET.get("page", "1")
    paginator = Paginator(qs, 24)
    page = paginator.get_page(page_num)

    html = render_to_string("shop/_product_grid.html", {
        "products": page.object_list,
        "is_paginated": page.has_other_pages(),
        "page_obj": page,
        "paginator": paginator,
        "q": q,
        "selected_cat": cat,
        "sort": sort,
        "view_mode": view_mode,
        "request": request,
    })
    return JsonResponse({"html": html})


class ShopProductDetailView(DetailView):
    model = Product
    template_name = "shop/product_detail.html"
    context_object_name = "product"

    def dispatch(self, request, *args, **kwargs):
        blocked = _require_customer_user(request)
        if blocked:
            return blocked
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return _with_effective_expiration(
            Product.objects.select_related("category").prefetch_related("expiration_entries")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["next_url"] = self.request.GET.get("next") or reverse("shop:catalog")
        return ctx


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------

class CartView(View):
    template_name = "shop/cart.html"

    def get(self, request):
        blocked = _require_customer_user(request)
        if blocked:
            return blocked
        payload = _cart_payload(request)
        return render(request, self.template_name, {
            "items": payload["items"],
            "total": payload["total"],
        })


def cart_summary_view(request):
    blocked = _require_customer_user(request)
    if blocked:
        return blocked
    return JsonResponse(_cart_payload(request))


class AddToCartView(View):
    def post(self, request, pk):
        blocked = _require_customer_user(request)
        if blocked:
            return blocked
        product = get_object_or_404(
            _with_effective_expiration(Product.objects.prefetch_related("expiration_entries")),
            pk=pk,
        )
        cart = _get_cart(request)
        pid = str(pk)
        expiration_date = str(
            getattr(product, "effective_expiration_value", None)
            or product.effective_expiration_date
            or ""
        )
        if pid in cart:
            cart[pid]["qty"] += 1
        else:
            cart[pid] = {
                "name": product.name,
                "barcode": product.barcode,
                "sales_description": product.sales_description,
                "expiration_date": expiration_date,
                "price": str(product.sales_price),
                "qty": 1,
            }
        _save_cart(request, cart)
        messages.success(request, f'"{product.name}" added to cart.')
        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("shop:cart")
        return redirect(next_url)


class RemoveFromCartView(View):
    def post(self, request, pk):
        blocked = _require_customer_user(request)
        if blocked:
            return blocked
        cart = _get_cart(request)
        pid = str(pk)
        cart.pop(pid, None)
        _save_cart(request, cart)
        return redirect("shop:cart")


class UpdateCartView(View):
    def post(self, request):
        blocked = _require_customer_user(request)
        if blocked:
            return blocked
        cart = _get_cart(request)
        for pid in list(cart.keys()):
            qty_str = request.POST.get(f"qty_{pid}", "")
            if qty_str.isdigit() and int(qty_str) > 0:
                cart[pid]["qty"] = int(qty_str)
            elif qty_str == "0" or qty_str == "":
                cart.pop(pid, None)
        _save_cart(request, cart)
        return redirect("shop:cart")


# ---------------------------------------------------------------------------
# Checkout (login required)
# ---------------------------------------------------------------------------

@login_required
def checkout_view(request):
    blocked = _require_customer_user(request)
    if blocked:
        return blocked

    cart = _get_cart(request)
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect("shop:catalog")

    items = []
    total = Decimal("0.00")
    site_settings = SiteSettings.get_solo()
    shipping_price = Decimal(site_settings.shipment_price or 0)
    outside_work_hours = not _is_within_work_hours(site_settings)
    for pid, data in cart.items():
        subtotal = Decimal(str(data["price"])) * data["qty"]
        items.append({
            "id": pid,
            "name": data["name"],
            "price": Decimal(str(data["price"])),
            "qty": data["qty"],
            "subtotal": subtotal,
        })
        total += subtotal

    grand_total = total + shipping_price

    saved_addresses = SavedShippingAddress.objects.filter(user=request.user)
    saved_invoices = SavedInvoiceProfile.objects.filter(user=request.user)

    shipping_choices = [("", "-- Enter a new shipping address --")] + [
        (str(a.pk), f"{a.title} - {a.full_address}") for a in saved_addresses
    ]
    invoice_choices = [("", "-- Enter a new invoice profile --")] + [
        (str(i.pk), f"{i.title} - {i.company_name}") for i in saved_invoices
    ]

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        form.fields["saved_shipping_address"].choices = shipping_choices
        form.fields["saved_invoice_profile"].choices = invoice_choices
        if form.is_valid():
            if outside_work_hours and not form.cleaned_data.get("confirm_out_of_hours_order"):
                form.add_error(
                    "confirm_out_of_hours_order",
                    "Please confirm that you still want to place this order for the next working hours.",
                )
                messages.warning(
                    request,
                    "This order will be processed during the next available working hours.",
                )
                return render(request, "shop/checkout.html", {
                    "form": form,
                    "items": items,
                    "total": total,
                    "shipping_price": shipping_price,
                    "grand_total": grand_total,
                    "outside_work_hours": outside_work_hours,
                })
            payment_method = form.cleaned_data["payment_method"]
            if payment_method == "online":
                messages.info(request, "Online payment is coming soon. Please choose Cash on Delivery.")
                return render(request, "shop/checkout.html", {
                    "form": form,
                    "items": items,
                    "total": total,
                    "shipping_price": shipping_price,
                    "grand_total": grand_total,
                    "outside_work_hours": outside_work_hours,
                })

            selected_shipping = None
            if form.cleaned_data.get("saved_shipping_address"):
                selected_shipping = saved_addresses.filter(pk=form.cleaned_data["saved_shipping_address"]).first()

            if selected_shipping:
                shipping_phone = selected_shipping.phone
                shipping_parts = [
                    selected_shipping.street_address,
                    selected_shipping.district,
                    selected_shipping.city,
                    selected_shipping.state_region,
                    selected_shipping.postal_code,
                    selected_shipping.country,
                ]
            else:
                shipping_phone = form.cleaned_data.get("shipping_phone", "")
                shipping_parts = [
                    form.cleaned_data.get("shipping_street_address", ""),
                    form.cleaned_data.get("shipping_district", ""),
                    form.cleaned_data.get("shipping_city", ""),
                    form.cleaned_data.get("shipping_state_region", ""),
                    form.cleaned_data.get("shipping_postal_code", ""),
                    form.cleaned_data.get("shipping_country", ""),
                ]
            shipping_address = ", ".join([p for p in shipping_parts if p])
            if not shipping_address:
                shipping_address = form.cleaned_data.get("shipping_address", "")

            selected_invoice = None
            if form.cleaned_data.get("saved_invoice_profile"):
                selected_invoice = saved_invoices.filter(pk=form.cleaned_data["saved_invoice_profile"]).first()

            need_invoice = form.cleaned_data.get("need_invoice", False)
            invoice_company_name = ""
            invoice_tax_id = ""
            invoice_note = ""
            if need_invoice:
                if selected_invoice:
                    invoice_company_name = selected_invoice.company_name
                    invoice_tax_id = selected_invoice.vat_number
                    invoice_note = (
                        f"Invoice email: {selected_invoice.email}; "
                        f"Invoice phone: {selected_invoice.phone}; "
                        f"Invoice address: {selected_invoice.full_address}"
                    )
                else:
                    invoice_company_name = form.cleaned_data.get("invoice_company_name", "")
                    invoice_tax_id = form.cleaned_data.get("invoice_tax_id", "")
                    invoice_parts = [
                        form.cleaned_data.get("invoice_street_address", ""),
                        form.cleaned_data.get("invoice_district", ""),
                        form.cleaned_data.get("invoice_city", ""),
                        form.cleaned_data.get("invoice_state_region", ""),
                        form.cleaned_data.get("invoice_postal_code", ""),
                        form.cleaned_data.get("invoice_country", ""),
                    ]
                    invoice_note = (
                        f"Invoice email: {form.cleaned_data.get('invoice_email', '')}; "
                        f"Invoice phone: {form.cleaned_data.get('invoice_phone', '')}; "
                        f"Invoice address: {', '.join([p for p in invoice_parts if p])}"
                    )

            notes = form.cleaned_data.get("notes", "")
            if need_invoice and invoice_note:
                notes = (notes + "\n\n" + invoice_note).strip()

            order = Order.objects.create(
                user=request.user,
                payment_method=payment_method,
                shipping_address=shipping_address,
                shipping_phone=shipping_phone,
                shipping_price=shipping_price,
                notes=notes,
                need_invoice=need_invoice,
                invoice_company_name=invoice_company_name,
                invoice_tax_id=invoice_tax_id,
            )

            if not selected_shipping and form.cleaned_data.get("save_shipping_address"):
                SavedShippingAddress.objects.create(
                    user=request.user,
                    title=form.cleaned_data.get("shipping_address_title", "Address"),
                    phone=shipping_phone,
                    street_address=form.cleaned_data.get("shipping_street_address", ""),
                    district=form.cleaned_data.get("shipping_district", ""),
                    city=form.cleaned_data.get("shipping_city", ""),
                    state_region=form.cleaned_data.get("shipping_state_region", ""),
                    postal_code=form.cleaned_data.get("shipping_postal_code", ""),
                    country=form.cleaned_data.get("shipping_country", ""),
                )

            if need_invoice and not selected_invoice and form.cleaned_data.get("save_invoice_profile"):
                SavedInvoiceProfile.objects.create(
                    user=request.user,
                    title=form.cleaned_data.get("invoice_profile_title", "Invoice"),
                    company_name=form.cleaned_data.get("invoice_company_name", ""),
                    vat_number=form.cleaned_data.get("invoice_tax_id", ""),
                    email=form.cleaned_data.get("invoice_email", ""),
                    phone=form.cleaned_data.get("invoice_phone", ""),
                    street_address=form.cleaned_data.get("invoice_street_address", ""),
                    district=form.cleaned_data.get("invoice_district", ""),
                    city=form.cleaned_data.get("invoice_city", ""),
                    state_region=form.cleaned_data.get("invoice_state_region", ""),
                    postal_code=form.cleaned_data.get("invoice_postal_code", ""),
                    country=form.cleaned_data.get("invoice_country", "Lithuania"),
                )

            for item in items:
                product = Product.objects.filter(pk=item["id"]).first()
                OrderLine.objects.create(
                    order=order,
                    product=product,
                    name_snapshot=item["name"],
                    barcode_snapshot=item.get("barcode", ""),
                    sales_description_snapshot=item.get("sales_description", "")[:255],
                    expiration_date_snapshot=parse_date(item.get("expiration_date", "") or ""),
                    unit_price=item["price"],
                    qty=item["qty"],
                )
            # Clear cart
            request.session.pop(CART_SESSION_KEY, None)
            request.session.modified = True
            messages.success(request, f"Order #{order.pk} placed successfully!")
            return redirect("shop:order_detail", pk=order.pk)
    else:
        user = request.user
        form = CheckoutForm(initial={
            "shipping_phone": user.phone,
            "shipping_street_address": user.street_address,
            "shipping_district": user.district,
            "shipping_city": user.city,
            "shipping_state_region": user.state_region,
            "shipping_postal_code": user.postal_code,
            "shipping_country": user.country or "Lithuania",
            "invoice_email": user.email,
            "invoice_phone": user.phone,
            "invoice_country": user.country or "Lithuania",
        })

    form.fields["saved_shipping_address"].choices = shipping_choices
    form.fields["saved_invoice_profile"].choices = invoice_choices

    return render(request, "shop/checkout.html", {
        "form": form,
        "items": items,
        "total": total,
        "shipping_price": shipping_price,
        "grand_total": grand_total,
        "outside_work_hours": outside_work_hours,
    })


# ---------------------------------------------------------------------------
# Order history (login required)
# ---------------------------------------------------------------------------

@login_required
def order_history_view(request):
    blocked = _require_customer_user(request)
    if blocked:
        return blocked
    orders = Order.objects.filter(user=request.user).prefetch_related("lines")
    return render(request, "shop/order_history.html", {"orders": orders})


@login_required
def order_detail_view(request, pk):
    blocked = _require_customer_user(request)
    if blocked:
        return blocked
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "shop/order_detail.html", {"order": order})


@login_required
def order_delete_view(request, pk):
    blocked = _require_customer_user(request)
    if blocked:
        return blocked
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == "POST":
        if order.can_cancel:
            order.status = Order.STATUS_CANCELLED
            order.save(update_fields=["status"])
            messages.success(request, f"Order #{pk} cancelled.")
        else:
            messages.error(request, "This order can no longer be cancelled.")
    return redirect("shop:order_history")


# ---------------------------------------------------------------------------
# Admin: all orders (Admin group or superuser)
# ---------------------------------------------------------------------------

class AdminRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not _is_staff_or_admin(request.user):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdminOrderListView(AdminRequiredMixin, ListView):
    model = Order
    template_name = "shop/order_admin_list.html"
    context_object_name = "orders"
    paginate_by = 30

    def get_queryset(self):
        qs = Order.objects.select_related("user").prefetch_related("lines").order_by("-created_at")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        payment = self.request.GET.get("payment", "").strip()
        created_from = self.request.GET.get("created_from", "").strip()
        created_to = self.request.GET.get("created_to", "").strip()
        if q:
            qs = qs.filter(Q(user__email__icontains=q) | Q(pk__icontains=q))
        if status in dict(Order.STATUS_CHOICES):
            qs = qs.filter(status=status)
        if payment in dict(Order.PAYMENT_CHOICES):
            qs = qs.filter(payment_method=payment)
        if created_from:
            parsed_from = parse_date(created_from)
            if parsed_from:
                qs = qs.filter(created_at__date__gte=parsed_from)
        if created_to:
            parsed_to = parse_date(created_to)
            if parsed_to:
                qs = qs.filter(created_at__date__lte=parsed_to)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        ctx["payment"] = self.request.GET.get("payment", "")
        ctx["created_from"] = self.request.GET.get("created_from", "")
        ctx["created_to"] = self.request.GET.get("created_to", "")
        ctx["status_choices"] = Order.STATUS_CHOICES
        ctx["payment_choices"] = Order.PAYMENT_CHOICES
        return ctx


class AdminOrderDetailView(AdminRequiredMixin, DetailView):
    model = Order
    template_name = "shop/order_admin_detail.html"
    context_object_name = "order"

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if request.POST.get("action") == "delete":
            order.delete()
            messages.success(request, f"Order #{pk} deleted.")
            return redirect("shop:admin_order_list")
        new_status = request.POST.get("status")
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.pk} status updated to {order.get_status_display()}.")
        return redirect("shop:admin_order_detail", pk=pk)


# ---------------------------------------------------------------------------
# Customer: contact messages
# ---------------------------------------------------------------------------

@login_required
def contact_list_view(request):
    blocked = _require_customer_user(request)
    if blocked:
        return blocked
    ContactMessage.objects.filter(
        user=request.user,
        sent_by__isnull=False,
        read_by_customer=False,
        deleted_for_customer=False,
    ).update(read_by_customer=True)
    msgs = ContactMessage.objects.filter(
        user=request.user,
        deleted_for_customer=False,
    ).select_related("sent_by", "replied_by", "customer_replied_by")
    return render(request, "shop/contact_list.html", {"contact_messages": msgs})


@login_required
def contact_new_view(request):
    blocked = _require_customer_user(request)
    if blocked:
        return blocked
    if request.method == "POST":
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.user = request.user
            msg.sent_by = request.user
            msg.read_by_customer = True
            msg.save()
            messages.success(request, "Your message has been sent.")
            return redirect("shop:contact_list")
    else:
        form = ContactMessageForm()
    return render(request, "shop/contact_form.html", {"form": form})


@login_required
def contact_delete_view(request, pk):
    blocked = _require_customer_user(request)
    if blocked:
        return blocked
    msg = get_object_or_404(ContactMessage, pk=pk, user=request.user)
    if request.method == "POST":
        msg.deleted_for_customer = True
        msg.save(update_fields=["deleted_for_customer"])
        messages.success(request, "Message deleted.")
    return redirect("shop:contact_list")


@login_required
def contact_reply_view(request, pk):
    blocked = _require_customer_user(request)
    if blocked:
        return blocked
    msg = get_object_or_404(ContactMessage, pk=pk, user=request.user, deleted_for_customer=False)
    if request.method != "POST":
        return redirect("shop:contact_detail", pk=msg.pk)

    customer_text = (request.POST.get("customer_reply") or "").strip()
    if customer_text:
        ContactMessageEntry.objects.create(
            message=msg,
            sender=request.user,
            body=customer_text,
        )
        msg.customer_reply = customer_text
        msg.customer_replied_by = request.user
        msg.customer_replied_at = timezone.now()
        msg.read_by_customer = True
        msg.is_read = False
        msg.save(update_fields=["customer_reply", "customer_replied_by", "customer_replied_at", "read_by_customer", "is_read"])
        messages.success(request, "Reply sent.")
    else:
        messages.error(request, "Please write a reply before sending.")
    return redirect("shop:contact_detail", pk=msg.pk)


@login_required
def contact_detail_view(request, pk):
    blocked = _require_customer_user(request)
    if blocked:
        return blocked
    msg = get_object_or_404(ContactMessage, pk=pk, user=request.user, deleted_for_customer=False)
    if not msg.read_by_customer:
        msg.read_by_customer = True
        msg.save(update_fields=["read_by_customer"])
    thread_messages = []
    for item in _build_contact_thread(msg):
        item["direction"] = "outgoing" if item.get("sender_id") == request.user.id else "incoming"
        thread_messages.append(item)
    return render(request, "shop/contact_detail.html", {"msg": msg, "thread_messages": thread_messages})


# ---------------------------------------------------------------------------
# Admin: view customer contact messages
# ---------------------------------------------------------------------------

class AdminMessageListView(AdminRequiredMixin, ListView):
    model = ContactMessage
    template_name = "shop/contact_admin_list.html"
    context_object_name = "contact_messages"
    paginate_by = 30

    def get_queryset(self):
        return ContactMessage.objects.filter(deleted_for_staff=False).select_related(
            "user", "sent_by", "replied_by", "customer_replied_by"
        ).order_by("-created_at")


class AdminMessageCreateView(AdminRequiredMixin, View):
    template_name = "shop/contact_admin_new.html"

    def get(self, request):
        form = AdminContactMessageForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = AdminContactMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.user = form.cleaned_data["recipient"]
            msg.sent_by = request.user
            msg.is_read = True
            msg.read_by_customer = False
            msg.save()
            messages.success(request, f"Message sent to {msg.user.email}.")
            return redirect("shop:admin_message_list")
        return render(request, self.template_name, {"form": form})


class AdminMessageDetailView(AdminRequiredMixin, DetailView):
    model = ContactMessage
    template_name = "shop/contact_admin_detail.html"
    context_object_name = "msg"

    def get_queryset(self):
        return ContactMessage.objects.filter(deleted_for_staff=False).select_related(
            "user", "sent_by", "replied_by", "customer_replied_by"
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.POST.get("action") == "delete":
            obj.deleted_for_staff = True
            obj.save(update_fields=["deleted_for_staff"])
            messages.success(request, "Message deleted.")
            return redirect("shop:admin_message_list")

        reply_text = (request.POST.get("reply") or "").strip()
        if reply_text:
            ContactMessageEntry.objects.create(
                message=obj,
                sender=request.user,
                body=reply_text,
            )
            obj.reply = reply_text
            obj.replied_by = request.user
            obj.replied_at = timezone.now()
            obj.is_read = True
            obj.read_by_customer = False
            obj.save(update_fields=["reply", "replied_by", "replied_at", "is_read", "read_by_customer"])
            messages.success(request, "Reply sent.")
            return redirect("shop:admin_message_detail", pk=obj.pk)
        messages.error(request, "Please write a reply before sending.")
        return render(request, self.template_name, {"msg": obj, "form": ContactReplyForm(instance=obj)})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ContactReplyForm(instance=self.object)
        thread_messages = []
        for item in _build_contact_thread(self.object):
            item["direction"] = "outgoing" if item.get("is_staff") else "incoming"
            thread_messages.append(item)
        context["thread_messages"] = thread_messages
        return context

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.is_read:
            obj.is_read = True
            obj.save()
        return super().get(request, *args, **kwargs)
