from django.contrib import admin
from .models import Order, OrderLine, ContactMessage


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    readonly_fields = ("line_total",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "status", "payment_method", "created_at", "total")
    list_filter = ("status", "payment_method")
    search_fields = ("user__email",)
    inlines = [OrderLineInline]
    readonly_fields = ("created_at", "total")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "subject", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("user__email", "subject")
