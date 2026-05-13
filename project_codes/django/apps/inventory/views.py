from datetime import datetime

from django.contrib.auth.mixins import AccessMixin
from django.db.models import DateField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.views.generic import ListView

from apps.catalog.models import Product
from .models import ExpirationEntry


class AdminOrSuperuserMixin(AccessMixin):
    """Allow access only to superusers or users in the 'Admin' or 'Staff' group."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (
            request.user.is_superuser
            or request.user.groups.filter(name__in=["Admin", "Staff"]).exists()
        ):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ExpirationListView(AdminOrSuperuserMixin, ListView):
    model = Product
    template_name = "inventory/expiration_list.html"
    context_object_name = "products"
    paginate_by = 50

    def get_queryset(self):
        first_expiration = ExpirationEntry.objects.filter(
            product_id=OuterRef("pk")
        ).order_by("expiration_date").values("expiration_date")[:1]
        first_raw = ExpirationEntry.objects.filter(
            product_id=OuterRef("pk")
        ).order_by("expiration_date").values("raw_value")[:1]
        first_source = ExpirationEntry.objects.filter(
            product_id=OuterRef("pk")
        ).order_by("expiration_date").values("source")[:1]

        qs = Product.objects.annotate(
            effective_expiration_value=Coalesce(
                "default_expiration_date",
                Subquery(first_expiration, output_field=DateField()),
            ),
            effective_raw_value=Subquery(first_raw),
            effective_source=Subquery(first_source),
        )
        q = self.request.GET.get("q", "").strip()
        sort = self.request.GET.get("sort", "nearest")
        if q:
            qs = qs.filter(Q(barcode__icontains=q) | Q(name__icontains=q))
        if sort == "alpha":
            qs = qs.order_by("name", "effective_expiration_value")
        elif sort == "latest":
            qs = qs.order_by("-effective_expiration_value", "name")
        else:
            qs = qs.order_by("effective_expiration_value", "name")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["sort"] = self.request.GET.get("sort", "nearest")
        for product in ctx.get("products", []):
            expiration = getattr(product, "effective_expiration_value", None)
            if not expiration:
                product.expiration_tone = "neutral"
                continue
            days_left = (expiration - datetime.now().date()).days
            if days_left < 0:
                product.expiration_tone = "expired"
            elif days_left <= 90:
                product.expiration_tone = "warning"
            else:
                product.expiration_tone = "normal"
        return ctx
