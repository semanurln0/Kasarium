from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path("admin/", admin.site.urls),
    # Custom accounts URLs (register, login, logout) take precedence
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    # Django auth URLs for password reset etc.
    path("accounts/", include("django.contrib.auth.urls")),
    path("shop/", include("apps.shop.urls", namespace="shop")),
    path("catalog/", include("apps.catalog.urls", namespace="catalog")),
    path("inventory/", include("apps.inventory.urls", namespace="inventory")),
    path("pos/", include("apps.pos.urls", namespace="pos")),
    path("messages/", include("apps.pos.message_urls", namespace="pos_messages")),
    path("", lambda request: redirect("shop:catalog"), name="home"),
]
