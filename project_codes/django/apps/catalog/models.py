from decimal import Decimal

from django.db import models


class ProductCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "product categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    DISCOUNT_KIND_PERCENT = "percent"
    DISCOUNT_KIND_PRICE = "price"
    DISCOUNT_KIND_CHOICES = [
        (DISCOUNT_KIND_PERCENT, "Percentage"),
        (DISCOUNT_KIND_PRICE, "Discounted price"),
    ]

    barcode = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    sales_price = models.DecimalField(max_digits=10, decimal_places=2)
    sales_description = models.TextField(blank=True)
    website_description = models.TextField(blank=True)
    origin = models.CharField(max_length=100, blank=True)
    default_expiration_date = models.DateField(null=True, blank=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_kind = models.CharField(max_length=20, choices=DISCOUNT_KIND_CHOICES, default=DISCOUNT_KIND_PERCENT)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_on_hand = models.PositiveIntegerField(default=0)
    image_url = models.URLField(blank=True)
    image_data = models.TextField(blank=True)
    wholesaler = models.CharField(max_length=255, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(
        ProductCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.barcode} — {self.name}"

    @property
    def discounted_price(self):
        if self.discount_kind == self.DISCOUNT_KIND_PRICE and self.discount_value is not None:
            return self.discount_value
        if not self.discount_percent:
            return self.sales_price
        return self.sales_price * (Decimal("100") - Decimal(str(self.discount_percent))) / Decimal("100")

    @property
    def has_discount(self):
        return bool(self.discount_percent and self.discount_percent > 0)

    def save(self, *args, **kwargs):
        if self.discount_kind == self.DISCOUNT_KIND_PRICE and self.discount_value is not None and self.sales_price:
            final_price = Decimal(str(self.discount_value))
            if final_price < 0:
                final_price = Decimal("0.00")
            if final_price > self.sales_price:
                final_price = self.sales_price
            percent = (self.sales_price - final_price) * Decimal("100") / self.sales_price if self.sales_price else Decimal("0")
            self.discount_percent = percent.quantize(Decimal("0.01"))
            self.discount_value = final_price
        elif self.discount_kind == self.DISCOUNT_KIND_PERCENT and self.discount_value is not None:
            percent = Decimal(str(self.discount_value))
            if percent < 0:
                percent = Decimal("0")
            if percent > 100:
                percent = Decimal("100")
            self.discount_percent = percent.quantize(Decimal("0.01"))
            self.discount_value = percent.quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

    @property
    def effective_expiration_date(self):
        if self.default_expiration_date:
            return self.default_expiration_date
        first = self.expiration_entries.order_by("expiration_date").first()
        if first:
            return first.expiration_date
        return None
