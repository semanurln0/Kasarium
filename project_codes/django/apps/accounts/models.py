from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager where email is the unique identifier for authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom user model using email as the primary login identifier."""

    username = None  # Remove username field; email is used instead
    email = models.EmailField(unique=True)

    # Customer profile fields
    phone = models.CharField(max_length=30, blank=True, verbose_name="Phone number")
    address = models.TextField(blank=True, verbose_name="Address")
    street_address = models.CharField(max_length=255, blank=True, verbose_name="Street address")
    house_number = models.CharField(max_length=30, blank=True, verbose_name="House number")
    apartment_number = models.CharField(max_length=30, blank=True, verbose_name="Apartment / unit")
    district = models.CharField(max_length=100, blank=True, verbose_name="District / area")
    city = models.CharField(max_length=100, blank=True, verbose_name="City")
    state_region = models.CharField(max_length=100, blank=True, verbose_name="State / region")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="Postal code")
    country = models.CharField(max_length=100, blank=True, verbose_name="Country")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password are sufficient

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class SiteSettings(models.Model):
    """Singleton model to hold site-wide settings editable by admin/staff.

    Use `SiteSettings.objects.first()` or `SiteSettings.get_solo()` to access.
    """

    work_hours = models.CharField(max_length=200, default="Mon-Sat 08:00-20:00", help_text="Human readable work hours")
    contact_phone = models.CharField(max_length=50, blank=True, default="+370 600 00000")
    contact_email = models.EmailField(blank=True, default="contact@kasarium.local")
    contact_address = models.CharField(max_length=255, blank=True, default="Main Street 10, Vilnius, Lithuania")
    shipment_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="Default shipment/courier price")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
