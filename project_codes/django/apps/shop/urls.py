from django.urls import path
from . import views

app_name = "shop"

urlpatterns = [
    path("", views.ShopCatalogView.as_view(), name="catalog"),
    path("ajax/catalog/", views.shop_catalog_ajax, name="ajax_catalog"),
    path("product/<int:pk>/", views.ShopProductDetailView.as_view(), name="product_detail"),
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/summary/", views.cart_summary_view, name="cart_summary"),
    path("cart/add/<int:pk>/", views.AddToCartView.as_view(), name="add_to_cart"),
    path("cart/remove/<int:pk>/", views.RemoveFromCartView.as_view(), name="remove_from_cart"),
    path("cart/update/", views.UpdateCartView.as_view(), name="update_cart"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("orders/", views.order_history_view, name="order_history"),
    path("orders/<int:pk>/", views.order_detail_view, name="order_detail"),
    path("orders/<int:pk>/delete/", views.order_delete_view, name="order_delete"),
    # Admin: all customer orders
    path("admin/orders/", views.AdminOrderListView.as_view(), name="admin_order_list"),
    path("admin/orders/<int:pk>/", views.AdminOrderDetailView.as_view(), name="admin_order_detail"),
    # Customer: contact messages
    path("contact/", views.contact_list_view, name="contact_list"),
    path("contact/new/", views.contact_new_view, name="contact_new"),
    path("contact/<int:pk>/", views.contact_detail_view, name="contact_detail"),
    path("contact/<int:pk>/delete/", views.contact_delete_view, name="contact_delete"),
    path("contact/<int:pk>/reply/", views.contact_reply_view, name="contact_reply"),
    # Admin: view customer messages
    path("admin/messages/", views.AdminMessageListView.as_view(), name="admin_message_list"),
    path("admin/messages/new/", views.AdminMessageCreateView.as_view(), name="admin_message_new"),
    path("admin/messages/<int:pk>/", views.AdminMessageDetailView.as_view(), name="admin_message_detail"),
]
