from django.conf import settings
from django.db import models


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PREPARING = "preparing"
    STATUS_ON_COURIER = "on_courier"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PREPARING, "Preparing"),
        (STATUS_ON_COURIER, "On courier"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    PAYMENT_COD = "COD"
    PAYMENT_ONLINE = "online"
    PAYMENT_CHOICES = [
        (PAYMENT_COD, "Cash on Delivery"),
        (PAYMENT_ONLINE, "Online Payment"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_CHOICES, default=PAYMENT_COD
    )
    shipping_address = models.TextField(blank=True)
    shipping_phone = models.CharField(max_length=50, blank=True)
    shipping_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    # Invoice fields
    need_invoice = models.BooleanField(default=False, help_text="Customer requested an invoice")
    invoice_company_name = models.CharField(max_length=255, blank=True)
    invoice_tax_id = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.user}"

    @property
    def total(self):
        return sum(line.line_total for line in self.lines.all())

    @property
    def grand_total(self):
        return self.total + self.shipping_price

    @property
    def can_cancel(self):
        return self.status == self.STATUS_PENDING


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        "catalog.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    name_snapshot = models.CharField(max_length=255)
    barcode_snapshot = models.CharField(max_length=50, blank=True)
    sales_description_snapshot = models.CharField(max_length=255, blank=True)
    expiration_date_snapshot = models.DateField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField(default=1)

    @property
    def line_total(self):
        return self.unit_price * self.qty

    def __str__(self):
        return f"{self.name_snapshot} x{self.qty}"


class ContactMessage(models.Model):
    """Customer-to-admin contact/support message."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contact_messages",
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_contact_messages",
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    reply = models.TextField(blank=True)
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replied_contact_messages",
    )
    replied_at = models.DateTimeField(null=True, blank=True)
    customer_reply = models.TextField(blank=True)
    customer_replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_replied_messages",
    )
    customer_replied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_by_customer = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    deleted_for_customer = models.BooleanField(default=False)
    deleted_for_staff = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Message from {self.user} — {self.subject}"


class ContactMessageEntry(models.Model):
    """Single chat entry attached to a contact message thread."""

    message = models.ForeignKey(
        ContactMessage,
        on_delete=models.CASCADE,
        related_name="chat_entries",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_message_entries",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"Entry #{self.pk} for Message #{self.message_id}"


class SavedShippingAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_shipping_addresses",
    )
    title = models.CharField(max_length=100)
    phone = models.CharField(max_length=50, blank=True)
    street_address = models.CharField(max_length=255, blank=True)
    district = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title", "-created_at"]

    def __str__(self):
        return f"{self.user} — {self.title}"

    @property
    def full_address(self):
        parts = [
            self.street_address,
            self.district,
            self.city,
            self.state_region,
            self.postal_code,
            self.country,
        ]
        return ", ".join(p for p in parts if p)


class SavedInvoiceProfile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_invoice_profiles",
    )
    title = models.CharField(max_length=100)
    company_name = models.CharField(max_length=255)
    vat_number = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    street_address = models.CharField(max_length=255, blank=True)
    district = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default="Lithuania")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title", "-created_at"]

    def __str__(self):
        return f"{self.user} — {self.title}"

    @property
    def full_address(self):
        parts = [
            self.street_address,
            self.district,
            self.city,
            self.state_region,
            self.postal_code,
            self.country,
        ]
        return ", ".join(p for p in parts if p)
