from django.urls import path
from .views import ExpirationListView

app_name = "inventory"

urlpatterns = [
    path(
        "",
        ExpirationListView.as_view(),
        name="expiration_list",
    ),
]
