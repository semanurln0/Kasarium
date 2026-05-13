from django.contrib import admin
from .models import ShiftSession, Sale, SaleLine, Payment, Refund, ReceiptTemplate, POSMessage

admin.site.register(ShiftSession)
admin.site.register(Sale)
admin.site.register(SaleLine)
admin.site.register(Payment)
admin.site.register(Refund)
admin.site.register(ReceiptTemplate)
admin.site.register(POSMessage)
