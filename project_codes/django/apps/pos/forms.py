from django import forms
from .models import ShiftSession, Sale, SaleLine, Payment, Refund, ReceiptTemplate, POSMessage
from apps.catalog.models import Product


class OpenSessionForm(forms.ModelForm):
    class Meta:
        model = ShiftSession
        fields = ["opening_cash"]


class CloseSessionForm(forms.ModelForm):
    class Meta:
        model = ShiftSession
        fields = ["closing_cash"]


class BarcodeEntryForm(forms.Form):
    barcode = forms.CharField(max_length=50, label="Barcode")
    qty = forms.IntegerField(min_value=1, initial=1, label="Qty")


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["method", "amount"]


class RefundForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ["amount", "reason"]


class ReceiptTemplateForm(forms.ModelForm):
    class Meta:
        model = ReceiptTemplate
        fields = ["name", "paper_width", "header", "footer", "show_barcode", "show_datetime", "show_cashier"]


class POSMessageForm(forms.ModelForm):
    class Meta:
        model = POSMessage
        fields = ["title", "body", "is_active"]
