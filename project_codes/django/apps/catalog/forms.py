from django import forms
import base64
from .models import ProductCategory, Product


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ["name"]


class ProductForm(forms.ModelForm):
    image_upload = forms.ImageField(required=False, label="Upload image file")

    class Meta:
        model = Product
        fields = [
            "barcode", "name", "sales_price", "sales_description",
            "website_description", "origin", "default_expiration_date",
            "discount_kind", "discount_value", "stock_on_hand", "image_url", "image_data", "category",
            "wholesaler", "cost_price",
        ]
        widgets = {
            "default_expiration_date": forms.DateInput(attrs={"type": "date"}),
            "origin": forms.TextInput(attrs={"list": "country-list", "placeholder": "Type country"}),
            "image_data": forms.Textarea(attrs={"rows": 3, "placeholder": "Paste base64 data URI here or use camera capture"}),
            "discount_kind": forms.Select(),
            "discount_value": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    ADMIN_ONLY_FIELDS = {"wholesaler", "cost_price"}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        is_admin = bool(user and (user.is_superuser or user.groups.filter(name="Admin").exists()))
        for field_name in [
            "sales_description",
            "website_description",
            "origin",
            "default_expiration_date",
            "discount_kind",
            "discount_value",
            "stock_on_hand",
            "image_url",
            "image_data",
            "category",
        ]:
            if field_name in self.fields:
                self.fields[field_name].required = False
        if "discount_kind" in self.fields:
            self.fields["discount_kind"].choices = Product.DISCOUNT_KIND_CHOICES
        if "discount_value" in self.fields:
            self.fields["discount_value"].label = "Discount amount"
        if not is_admin:
            for field_name in self.ADMIN_ONLY_FIELDS:
                self.fields.pop(field_name, None)
        if self.instance and self.instance.pk and not self.instance.discount_value and self.instance.discount_percent:
            self.initial.setdefault("discount_kind", Product.DISCOUNT_KIND_PERCENT)
            self.initial.setdefault("discount_value", self.instance.discount_percent)

    def clean_barcode(self):
        barcode = self.cleaned_data.get("barcode", "").strip()
        if not barcode.isdigit():
            raise forms.ValidationError("Barcode must contain digits only.")
        qs = Product.objects.filter(barcode=barcode)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A product with this barcode already exists.")
        return barcode

    def clean_sales_price(self):
        price = self.cleaned_data.get("sales_price")
        if price is not None and price < 0:
            raise forms.ValidationError("Sales price must be 0 or greater.")
        return price

    def clean_discount_percent(self):
        return self.cleaned_data.get("discount_percent")

    def clean(self):
        cleaned = super().clean()
        discount_kind = cleaned.get("discount_kind") or Product.DISCOUNT_KIND_PERCENT
        discount_value = cleaned.get("discount_value")
        if discount_value in (None, ""):
            return cleaned

        if discount_kind == Product.DISCOUNT_KIND_PERCENT:
            if discount_value != int(discount_value):
                self.add_error("discount_value", "Discount percent must be a whole number.")
            elif discount_value < 0 or discount_value > 100:
                self.add_error("discount_value", "Discount percent must be between 0 and 100.")
        elif discount_kind == Product.DISCOUNT_KIND_PRICE:
            price = cleaned.get("sales_price")
            if price is not None and discount_value > price:
                self.add_error("discount_value", "Discounted price cannot be greater than the sales price.")
            elif discount_value < 0:
                self.add_error("discount_value", "Discounted price must be 0 or greater.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded = self.cleaned_data.get("image_upload")
        if uploaded:
            raw = uploaded.read()
            mime = uploaded.content_type or "image/png"
            encoded = base64.b64encode(raw).decode("ascii")
            instance.image_data = f"data:{mime};base64,{encoded}"
        discount_kind = self.cleaned_data.get("discount_kind") or Product.DISCOUNT_KIND_PERCENT
        discount_value = self.cleaned_data.get("discount_value")
        if discount_value in (None, ""):
            instance.discount_kind = Product.DISCOUNT_KIND_PERCENT
            instance.discount_value = None
        else:
            instance.discount_kind = discount_kind
            instance.discount_value = discount_value
        if commit:
            instance.save()
        return instance
