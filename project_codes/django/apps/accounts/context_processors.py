"""Context processors for the accounts app."""


def user_roles(request):
    """Inject role booleans into every template context."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"is_pos_staff": False, "is_admin_group": False}

    if user.is_superuser:
        return {"is_pos_staff": True, "is_admin_group": True}

    groups = set(user.groups.values_list("name", flat=True))
    return {
        "is_pos_staff": bool(groups & {"Admin", "Staff"}),
        "is_admin_group": "Admin" in groups,
    }


def site_settings(request):
    """Inject site settings (work hours, timezone, contact info, shipment price) into templates."""
    from .models import SiteSettings

    try:
        s = SiteSettings.get_solo()
    except Exception:
        return {}
    return {
        "site_work_hours": s.work_hours,
        "site_timezone": s.timezone,
        "site_contact_phone": s.contact_phone,
        "site_contact_email": s.contact_email,
        "site_contact_address": s.contact_address,
        "site_shipment_price": s.shipment_price,
    }
