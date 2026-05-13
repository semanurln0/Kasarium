from django.contrib import admin
from .models import ExpirationEntry

@admin.register(ExpirationEntry)
class ExpirationEntryAdmin(admin.ModelAdmin):
    list_display = ["product", "expiration_date", "source", "created_at"]
    list_filter = ["source"]
    search_fields = ["product__barcode", "product__name"]
