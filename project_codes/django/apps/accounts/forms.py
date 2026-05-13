from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group

User = get_user_model()


class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email address")
    first_name = forms.CharField(max_length=150, required=False, label="First name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            customer_group, _ = Group.objects.get_or_create(name="Customer")
            user.groups.add(customer_group)
        return user


class EmailAuthenticationForm(AuthenticationForm):
    """Login form that labels the username field as 'Email address'."""

    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"autofocus": True}),
    )


class ProfileForm(forms.ModelForm):
    """Allow customers to edit their public profile and saved address."""

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone",
            "street_address",
            "house_number",
            "apartment_number",
            "district",
            "city",
            "state_region",
            "postal_code",
            "country",
            "address",
        )
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "street_address": forms.TextInput(attrs={"placeholder": "Street name"}),
            "house_number": forms.TextInput(attrs={"placeholder": "12A"}),
            "apartment_number": forms.TextInput(attrs={"placeholder": "4B"}),
            "district": forms.TextInput(attrs={"placeholder": "District / neighborhood"}),
            "state_region": forms.TextInput(attrs={"placeholder": "State / region"}),
            "country": forms.TextInput(attrs={"placeholder": "Country"}),
        }
        labels = {
            "first_name": "First name",
            "last_name": "Last name",
            "phone": "Phone number",
            "street_address": "Street address",
            "house_number": "House number",
            "apartment_number": "Apartment / unit",
            "district": "District / area",
            "address": "Address",
            "city": "City",
            "state_region": "State / region",
            "postal_code": "Postal code",
            "country": "Country",
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        legacy_address = (self.cleaned_data.get("address") or "").strip()
        parts = [
            user.street_address,
            user.house_number,
            user.apartment_number,
            user.district,
            user.city,
            user.state_region,
            user.postal_code,
            user.country,
        ]
        detailed_address = ", ".join(part for part in parts if part)
        user.address = detailed_address or legacy_address
        if commit:
            user.save()
        return user


class AdminUserEditForm(forms.ModelForm):
    """Form for admin/superuser to edit any user account."""

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Groups",
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone",
            "street_address",
            "house_number",
            "apartment_number",
            "district",
            "address",
            "city",
            "state_region",
            "postal_code",
            "country",
            "is_active",
            "is_staff",
            "groups",
        )
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }


class AdminUserDeleteForm(forms.Form):
    confirm = forms.BooleanField(required=True, label="Confirm deletion")


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        from .models import SiteSettings

        model = SiteSettings
        fields = ("work_hours", "contact_phone", "contact_email", "contact_address", "shipment_price")
        widgets = {
            "work_hours": forms.TextInput(),
            "contact_phone": forms.TextInput(),
            "contact_email": forms.EmailInput(),
            "contact_address": forms.TextInput(),
            "shipment_price": forms.NumberInput(attrs={"step": "0.01"}),
        }
