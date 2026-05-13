from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CustomerLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/password/", views.AccountPasswordChangeView.as_view(), name="password_change"),
    path("profile/delete/", views.delete_account_view, name="delete_account"),
    path("admin/users/", views.admin_user_list_view, name="admin_user_list"),
    path("admin/users/<int:pk>/edit/", views.admin_user_edit_view, name="admin_user_edit"),
    path("admin/users/<int:pk>/delete/", views.admin_user_delete_view, name="admin_user_delete"),
    path("settings/", views.site_settings_view, name="site_settings"),
    path("password-reset/", views.AccountPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.AccountPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.AccountPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", views.AccountPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
