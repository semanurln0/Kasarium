"""Management command to seed Groups and Permissions."""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


ROLE_PERMISSIONS = {
    "Admin": {
        "apps.catalog": ["add", "change", "delete", "view"],
        "apps.inventory": ["add", "change", "delete", "view"],
        "apps.pos": ["add", "change", "delete", "view"],
    },
    "Staff": {
        "apps.pos": ["add", "change", "view"],
        "apps.catalog": ["view"],
        "apps.inventory": ["view"],
    },
    "Customer": {},
}


class Command(BaseCommand):
    help = "Seed Groups: Admin, Staff, Customer with permissions."

    def handle(self, *args, **options):
        for group_name, app_perms in ROLE_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            perms = []
            for app_label, actions in app_perms.items():
                cts = ContentType.objects.filter(app_label=app_label.split(".")[1])
                for ct in cts:
                    for action in actions:
                        codename = f"{action}_{ct.model}"
                        try:
                            perm = Permission.objects.get(content_type=ct, codename=codename)
                            perms.append(perm)
                        except Permission.DoesNotExist:
                            pass
            group.permissions.set(perms)
            status = "created" if created else "updated"
            self.stdout.write(self.style.SUCCESS(f"Group '{group_name}' {status}."))
