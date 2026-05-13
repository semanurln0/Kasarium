from django.contrib.auth.mixins import AccessMixin
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView,
)
import csv
from .models import ProductCategory, Product
from .forms import ProductCategoryForm, ProductForm


class AdminOrSuperuserMixin(AccessMixin):
    """Allow access only to superusers or users in the 'Admin' group."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ProductCategoryListView(AdminOrSuperuserMixin, ListView):
    model = ProductCategory
    template_name = "catalog/category_list.html"
    context_object_name = "categories"


class ProductCategoryCreateView(AdminOrSuperuserMixin, CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")


class ProductCategoryUpdateView(AdminOrSuperuserMixin, UpdateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")


class ProductCategoryDeleteView(AdminOrSuperuserMixin, DeleteView):
    model = ProductCategory
    template_name = "catalog/category_confirm_delete.html"
    success_url = reverse_lazy("catalog:category_list")


class ProductListView(AdminOrSuperuserMixin, ListView):
    model = Product
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related("category").prefetch_related("expiration_entries")
        q = self.request.GET.get("q", "").strip()
        sort = self.request.GET.get("sort", "name_asc")
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(barcode__icontains=q) | Q(name__icontains=q))
        sort_map = {
            "name_asc": "name",
            "name_desc": "-name",
            "price_asc": "sales_price",
            "price_desc": "-sales_price",
            "stock_desc": "-stock_on_hand",
            "stock_asc": "stock_on_hand",
        }
        qs = qs.order_by(sort_map.get(sort, "name"))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["sort"] = self.request.GET.get("sort", "name_asc")
        return ctx


class ProductDetailView(AdminOrSuperuserMixin, DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"


class ProductCreateView(AdminOrSuperuserMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ProductUpdateView(AdminOrSuperuserMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ProductDeleteView(AdminOrSuperuserMixin, DeleteView):
    model = Product
    template_name = "catalog/product_confirm_delete.html"
    success_url = reverse_lazy("catalog:product_list")


class ProductExportCsvView(AdminOrSuperuserMixin, ListView):
    model = Product

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="products_export.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "barcode", "name", "sales_price", "sales_description", "website_description",
            "origin", "default_expiration_date", "discount_percent", "discount_kind", "discount_value", "stock_on_hand",
            "image_url", "image_data", "category", "wholesaler", "cost_price",
        ])
        for p in Product.objects.select_related("category").all().order_by("name"):
            writer.writerow([
                p.barcode, p.name, p.sales_price, p.sales_description, p.website_description,
                p.origin, p.default_expiration_date or "", p.discount_percent, p.discount_kind, p.discount_value or "", p.stock_on_hand,
                p.image_url, p.image_data, p.category.name if p.category else "", p.wholesaler, p.cost_price or "",
            ])
        return response


class ProductImportCsvView(AdminOrSuperuserMixin, CreateView):
    model = Product
    fields = []
    template_name = "catalog/product_import.html"
    success_url = reverse_lazy("catalog:product_list")

    def post(self, request, *args, **kwargs):
        upload = request.FILES.get("csv_file")
        if not upload:
            messages.error(request, "Please choose a CSV file.")
            return self.get(request, *args, **kwargs)

        decoded = upload.read().decode("utf-8-sig").splitlines()
        reader = csv.DictReader(decoded)
        created = 0
        updated = 0
        for row in reader:
            barcode = (row.get("barcode") or "").strip()
            if not barcode:
                continue
            defaults = {
                "name": (row.get("name") or "").strip()[:255],
                "sales_price": row.get("sales_price") or 0,
                "sales_description": row.get("sales_description") or "",
                "website_description": row.get("website_description") or "",
                "origin": row.get("origin") or "",
                "image_url": row.get("image_url") or "",
                "image_data": row.get("image_data") or "",
                "discount_percent": row.get("discount_percent") or 0,
                "discount_kind": row.get("discount_kind") or "percent",
                "discount_value": row.get("discount_value") or None,
                "stock_on_hand": row.get("stock_on_hand") or 0,
                "wholesaler": row.get("wholesaler") or "",
                "cost_price": row.get("cost_price") or None,
            }
            obj, was_created = Product.objects.update_or_create(barcode=barcode, defaults=defaults)
            cat_name = (row.get("category") or "").strip()
            if cat_name:
                cat, _ = ProductCategory.objects.get_or_create(name=cat_name)
                if obj.category_id != cat.id:
                    obj.category = cat
                    obj.save(update_fields=["category"])
            if was_created:
                created += 1
            else:
                updated += 1

        messages.success(request, f"Import finished: {created} created, {updated} updated.")
        return redirect(self.success_url)

