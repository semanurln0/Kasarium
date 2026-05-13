from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.utils import timezone


class SiteTimezoneMiddleware:
    """Activate the timezone configured in SiteSettings for each request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz_name = settings.TIME_ZONE
        try:
            from .models import SiteSettings

            site_settings = SiteSettings.get_solo()
            tz_name = site_settings.timezone or settings.TIME_ZONE
        except Exception:
            tz_name = settings.TIME_ZONE

        try:
            timezone.activate(ZoneInfo(tz_name))
        except ZoneInfoNotFoundError:
            timezone.activate(ZoneInfo(settings.TIME_ZONE))

        response = self.get_response(request)
        timezone.deactivate()
        return response