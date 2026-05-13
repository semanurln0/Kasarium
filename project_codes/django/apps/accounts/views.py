from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse_lazy

from .forms import CustomerRegistrationForm, EmailAuthenticationForm, ProfileForm, AdminUserEditForm
from .forms import SiteSettingsForm
from .forms import AdminUserDeleteForm
from .models import SiteSettings

User = get_user_model()


def _is_admin(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Admin").exists()
    )


def _is_pos_staff(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=["Admin", "Staff"]).exists()


@login_required
def site_settings_view(request):
    # Allow admin or pos staff to edit site-wide settings
    if not _is_pos_staff(request.user) and not _is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect("/")

    settings = SiteSettings.get_solo()
    if request.method == "POST":
        form = SiteSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Site settings updated.")
            return redirect("accounts:site_settings")
    else:
        form = SiteSettingsForm(instance=settings)
    return render(request, "accounts/site_settings.html", {"form": form})


class CustomerLoginView(LoginView):
    form_class = EmailAuthenticationForm
    template_name = "accounts/login.html"


def register_view(request):
    if request.user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. Welcome!")
            return redirect("/")
    else:
        form = CustomerRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/accounts/login/")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def delete_account_view(request):
    if request.method == "POST":
        user = request.user
        try:
            # Delete user first; logout only happens on success so that a
            # ProtectedError (e.g. user owns Orders) leaves the user logged in
            # and can be shown a friendly error message instead of a 500.
            user.delete()
        except ProtectedError:
            messages.error(
                request,
                "Your account cannot be deleted because it has associated orders. "
                "Please contact support if you want to close your account.",
            )
            return redirect("accounts:profile")
        # Deletion succeeded — invalidate session, then confirm
        logout(request)
        messages.success(request, "Your account has been deleted.")
        return redirect("accounts:login")
    return render(request, "accounts/delete_account.html")


# ---------------------------------------------------------------------------
# Admin: user management (Admin group or superuser)
# ---------------------------------------------------------------------------

@login_required
def admin_user_list_view(request):
    if not _is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect("/")
    q = request.GET.get("q", "").strip()
    users = User.objects.order_by("email")
    if q:
        users = users.filter(
            Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    return render(request, "accounts/admin_user_list.html", {"users": users, "q": q})


@login_required
def admin_user_edit_view(request, pk):
    if not _is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect("/")
    target = get_object_or_404(User, pk=pk)
    # Prevent non-superusers from editing superusers
    if target.is_superuser and not request.user.is_superuser:
        messages.error(request, "Only a superuser can edit another superuser.")
        return redirect("accounts:admin_user_list")
    if request.method == "POST":
        form = AdminUserEditForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {target.email} updated successfully.")
            return redirect("accounts:admin_user_list")
    else:
        form = AdminUserEditForm(instance=target)
    return render(request, "accounts/admin_user_edit.html", {"form": form, "target": target})


@login_required
def admin_user_delete_view(request, pk):
    if not _is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect("/")
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.error(request, "You cannot delete your own account from the admin user list.")
        return redirect("accounts:admin_user_list")
    if target.is_superuser and not request.user.is_superuser:
        messages.error(request, "Only a superuser can delete another superuser.")
        return redirect("accounts:admin_user_list")
    if request.method == "POST":
        form = AdminUserDeleteForm(request.POST)
        if form.is_valid():
            target.delete()
            messages.success(request, f"User {target.email} deleted.")
            return redirect("accounts:admin_user_list")
    else:
        form = AdminUserDeleteForm()
    return render(request, "accounts/admin_user_delete.html", {"target": target, "form": form})


class AccountPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:profile")


class AccountPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class AccountPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class AccountPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
