from django.urls import path
from . import views

app_name = "pos_messages"

urlpatterns = [
    path("", views.POSMessageListView.as_view(), name="message_list"),
    path("new/", views.POSMessageCreateView.as_view(), name="message_create"),
    path("<int:pk>/edit/", views.POSMessageUpdateView.as_view(), name="message_update"),
    path("<int:pk>/delete/", views.POSMessageDeleteView.as_view(), name="message_delete"),
]
