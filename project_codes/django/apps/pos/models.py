from django.conf import settings
from django.db import models


class ShiftSession(models.Model):
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="shift_sessions",
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Session #{self.pk} — {self.opened_by}"

    @property
    def is_open(self):
        return self.closed_at is None


class Sale(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_REFUNDED = "refunded"
    STATUS_PARTIALLY_REFUNDED = "partially_refunded"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_REFUNDED, "Refunded"),
        (STATUS_PARTIALLY_REFUNDED, "Partially refunded"),
    ]

    session = models.ForeignKey(ShiftSession, on_delete=models.PROTECT, related_name="sales")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    def __str__(self):
        return f"Sale #{self.pk} [{self.status}]"

    @property
    def total(self):
        return sum(line.line_total for line in self.lines.all())


class SaleLine(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        "catalog.Product", null=True, blank=True, on_delete=models.SET_NULL
    )
    barcode = models.CharField(max_length=50)
    name_snapshot = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField(default=1)

    @property
    def line_total(self):
        return self.unit_price * self.qty

    def __str__(self):
        return f"{self.barcode} x{self.qty}"


class Payment(models.Model):
    METHOD_CASH = "cash"
    METHOD_CARD = "card"
    METHOD_CHOICES = [
        (METHOD_CASH, "Cash"),
        (METHOD_CARD, "Card"),
    ]

    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="payments")
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Payment #{self.pk} [{self.method}] {self.amount}"


class Refund(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="refunds")
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"Refund #{self.pk} for Sale #{self.sale_id}"


class RefundLine(models.Model):
    refund = models.ForeignKey(Refund, on_delete=models.CASCADE, related_name="lines")
    sale_line = models.ForeignKey(SaleLine, on_delete=models.PROTECT, related_name="refund_lines")
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self):
        return self.unit_price * self.qty

    def __str__(self):
        return f"Refund line #{self.pk} for SaleLine #{self.sale_line_id} x{self.qty}"


class ReceiptTemplate(models.Model):
    WIDTH_58 = 58
    WIDTH_80 = 80
    WIDTH_CHOICES = [(WIDTH_58, "58mm"), (WIDTH_80, "80mm")]

    name = models.CharField(max_length=100)
    paper_width = models.IntegerField(choices=WIDTH_CHOICES, default=WIDTH_58)
    header = models.TextField(blank=True)
    footer = models.TextField(blank=True)
    show_barcode = models.BooleanField(default=True)
    show_datetime = models.BooleanField(default=True)
    show_cashier = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.paper_width}mm)"


class POSMessage(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
