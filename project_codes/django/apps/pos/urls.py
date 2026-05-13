from django.urls import path
from . import views

app_name = "pos"

urlpatterns = [
    path("session/", views.session_open, name="session_open"),
    path("session/<int:session_id>/close/", views.session_close, name="session_close"),
    path("session/<int:session_id>/sale/new/", views.sale_new, name="sale_new"),
    path("sale/<int:pk>/", views.sale_detail, name="sale_detail"),
    path("sale/<int:pk>/payment/", views.sale_payment, name="sale_payment"),
    path("sale/<int:pk>/receipt/", views.sale_receipt, name="sale_receipt"),
    path("refund/", views.refund_create, name="refund_create"),
    path("sales/", views.SaleHistoryView.as_view(), name="sale_history"),
    path("receipts/", views.ReceiptTemplateListView.as_view(), name="receipt_list"),
    path("receipts/new/", views.ReceiptTemplateCreateView.as_view(), name="receipt_create"),
    path("receipts/<int:pk>/edit/", views.ReceiptTemplateUpdateView.as_view(), name="receipt_update"),
    path("receipts/<int:pk>/delete/", views.ReceiptTemplateDeleteView.as_view(), name="receipt_delete"),
    path("receipts/<int:pk>/preview/", views.receipt_preview, name="receipt_preview"),
]
