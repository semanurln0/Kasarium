from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import ContactMessage

User = get_user_model()


class CheckoutForm(forms.Form):
    PAYMENT_COD = "COD"
    PAYMENT_ONLINE = "online"
    PAYMENT_CHOICES = [
        (PAYMENT_COD, "Cash on Delivery (COD)"),
        (PAYMENT_ONLINE, "Online Payment (coming soon)"),
    ]

    saved_shipping_address = forms.ChoiceField(required=False, label="Use saved shipping address")
    shipping_phone = forms.CharField(required=False, max_length=50, label="Shipping phone")
    shipping_street_address = forms.CharField(required=False, max_length=255, label="Street address")
    shipping_district = forms.CharField(required=False, max_length=100, label="District")
    shipping_city = forms.CharField(required=False, max_length=100, label="City")
    shipping_state_region = forms.CharField(required=False, max_length=100, label="State / region")
    shipping_postal_code = forms.CharField(required=False, max_length=20, label="Postal code")
    shipping_country = forms.CharField(required=False, max_length=100, initial="Lithuania", label="Country")
    save_shipping_address = forms.BooleanField(required=False, label="Save this shipping address")
    shipping_address_title = forms.CharField(required=False, max_length=100, label="Shipping address title")

    shipping_address = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect,
        initial=PAYMENT_COD,
        label="Payment method",
    )
    confirm_out_of_hours_order = forms.BooleanField(
        required=False,
        label="I understand this order will be delivered during the next working hours",
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Order notes (optional)",
        required=False,
    )
    
    # Invoice fields
    saved_invoice_profile = forms.ChoiceField(required=False, label="Use saved invoice profile")
    need_invoice = forms.BooleanField(
        required=False,
        label="I need an invoice for this order",
    )
    invoice_company_name = forms.CharField(
        max_length=255,
        required=False,
        label="Company name (for invoice)",
    )
    invoice_tax_id = forms.CharField(
        max_length=50,
        required=False,
        label="VAT / Tax number",
    )
    invoice_email = forms.EmailField(required=False, label="Invoice email")
    invoice_phone = forms.CharField(required=False, max_length=50, label="Invoice phone")
    invoice_street_address = forms.CharField(required=False, max_length=255, label="Invoice street address")
    invoice_district = forms.CharField(required=False, max_length=100, label="Invoice district")
    invoice_city = forms.CharField(required=False, max_length=100, label="Invoice city")
    invoice_state_region = forms.CharField(required=False, max_length=100, label="Invoice state / region")
    invoice_postal_code = forms.CharField(required=False, max_length=20, label="Invoice postal code")
    invoice_country = forms.CharField(required=False, max_length=100, initial="Lithuania", label="Invoice country")
    save_invoice_profile = forms.BooleanField(required=False, label="Save this invoice profile")
    invoice_profile_title = forms.CharField(required=False, max_length=100, label="Invoice profile title")

    def clean(self):
        cleaned = super().clean()
        legacy_shipping_address = (cleaned.get("shipping_address") or "").strip()
        required_shipping = [
            "shipping_phone",
            "shipping_street_address",
            "shipping_city",
            "shipping_postal_code",
            "shipping_country",
        ]
        if not cleaned.get("saved_shipping_address") and not legacy_shipping_address:
            for field_name in required_shipping:
                if not cleaned.get(field_name):
                    self.add_error(field_name, "This field is required.")

        if cleaned.get("save_shipping_address") and not cleaned.get("shipping_address_title"):
            self.add_error("shipping_address_title", "Provide a title to save this address.")

        if cleaned.get("need_invoice"):
            if not cleaned.get("saved_invoice_profile"):
                required_invoice = [
                    "invoice_company_name",
                    "invoice_tax_id",
                    "invoice_street_address",
                    "invoice_city",
                    "invoice_postal_code",
                    "invoice_country",
                    "invoice_email",
                ]
                for field_name in required_invoice:
                    if not cleaned.get(field_name):
                        self.add_error(field_name, "This field is required.")

            if cleaned.get("save_invoice_profile") and not cleaned.get("invoice_profile_title"):
                self.add_error("invoice_profile_title", "Provide a title to save this invoice profile.")

        return cleaned


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["subject", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 5}),
        }


class ContactReplyForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["reply"]
        widgets = {
            "reply": forms.Textarea(attrs={"rows": 5, "placeholder": "Write your reply here..."}),
        }


class ContactCustomerReplyForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["customer_reply"]
        widgets = {
            "customer_reply": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Reply to this message..."}
            ),
        }


class AdminContactMessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Recipient customer",
    )

    class Meta:
        model = ContactMessage
        fields = ["recipient", "subject", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recipient"].queryset = User.objects.filter(
            is_superuser=False,
            is_staff=False,
        ).exclude(
            Q(groups__name="Admin") | Q(groups__name="Staff")
        ).distinct().order_by("email")
