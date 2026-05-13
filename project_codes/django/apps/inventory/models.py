from django.db import models
from apps.catalog.models import Product


class ExpirationEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="expiration_entries")
    expiration_date = models.DateField(null=True, blank=True)
    raw_value = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "expiration entries"
        ordering = ["expiration_date"]

    def __str__(self):
        return f"{self.product.barcode} — {self.expiration_date}"
