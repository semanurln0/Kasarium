"""Phase 2 smoke tests: permissions and basic page access."""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kasarium.settings.test")

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.catalog.models import Product, ProductCategory
from apps.pos.models import ShiftSession, Sale, ReceiptTemplate, POSMessage


def _make_user(username, groups=(), is_superuser=False):
    User = get_user_model()
    email = f"{username}@test.com"
    user = User.objects.create_user(email=email, password="pass")
    user.is_superuser = is_superuser
    user.is_staff = is_superuser
    user.save()
    for g in groups:
        group, _ = Group.objects.get_or_create(name=g)
        user.groups.add(group)
    return user


# ---------------------------------------------------------------------------
# Catalog (Admin / Product Control UI)
# ---------------------------------------------------------------------------

class CatalogPermissionTests(TestCase):
    """Catalog views must be blocked for anonymous and non-admin users."""

    def setUp(self):
        self.client = Client()
        self.anon_client = Client()
        self.staff_user = _make_user("staff1", groups=["Staff"])
        self.admin_user = _make_user("admin1", groups=["Admin"])
        self.superuser = _make_user("super1", is_superuser=True)

    def test_product_list_blocks_anonymous(self):
        resp = self.anon_client.get(reverse("catalog:product_list"))
        self.assertIn(resp.status_code, [302, 403])

    def test_product_list_blocks_staff_role(self):
        self.client.login(username="staff1@test.com", password="pass")
        resp = self.client.get(reverse("catalog:product_list"))
        self.assertIn(resp.status_code, [302, 403])

    def test_product_list_allows_admin_group(self):
        self.client.login(username="admin1@test.com", password="pass")
        resp = self.client.get(reverse("catalog:product_list"))
        self.assertEqual(resp.status_code, 200)

    def test_product_list_allows_superuser(self):
        self.client.login(username="super1@test.com", password="pass")
        resp = self.client.get(reverse("catalog:product_list"))
        self.assertEqual(resp.status_code, 200)

    def test_category_list_blocks_anonymous(self):
        resp = self.anon_client.get(reverse("catalog:category_list"))
        self.assertIn(resp.status_code, [302, 403])

    def test_category_list_allows_admin(self):
        self.client.login(username="admin1@test.com", password="pass")
        resp = self.client.get(reverse("catalog:category_list"))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# Catalog form validations
# ---------------------------------------------------------------------------

class ProductFormValidationTests(TestCase):
    """Barcode must be digits-only; sales_price must be >= 0."""

    def setUp(self):
        self.client = Client()
        self.admin_user = _make_user("admin2", groups=["Admin"])
        self.client.login(username="admin2@test.com", password="pass")

    def test_barcode_non_digits_rejected(self):
        resp = self.client.post(reverse("catalog:product_create"), {
            "barcode": "ABC123",
            "name": "Test",
            "sales_price": "5.00",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp.context["form"], "barcode", "Barcode must contain digits only.")

    def test_negative_price_rejected(self):
        resp = self.client.post(reverse("catalog:product_create"), {
            "barcode": "1234567890",
            "name": "Test",
            "sales_price": "-1.00",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp.context["form"], "sales_price", "Sales price must be 0 or greater.")

    def test_valid_product_creates(self):
        resp = self.client.post(reverse("catalog:product_create"), {
            "barcode": "9876543210",
            "name": "Valid Product",
            "sales_price": "10.00",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Product.objects.filter(barcode="9876543210").exists())

    def test_duplicate_barcode_rejected(self):
        Product.objects.create(barcode="1111111111", name="Existing", sales_price="1.00")
        resp = self.client.post(reverse("catalog:product_create"), {
            "barcode": "1111111111",
            "name": "Duplicate",
            "sales_price": "2.00",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp.context["form"], "barcode", "A product with this barcode already exists.")


# ---------------------------------------------------------------------------
# POS screens
# ---------------------------------------------------------------------------

class POSPermissionTests(TestCase):
    """POS screens must be blocked for anonymous users and customer role."""

    def setUp(self):
        self.client = Client()
        self.anon_client = Client()
        self.customer = _make_user("customer1", groups=["Customer"])
        self.staff_user = _make_user("staff2", groups=["Staff"])
        self.admin_user = _make_user("admin3", groups=["Admin"])

    def test_pos_session_blocks_anonymous(self):
        resp = self.anon_client.get(reverse("pos:session_open"))
        self.assertIn(resp.status_code, [302, 403])

    def test_pos_session_blocks_customer(self):
        self.client.login(username="customer1@test.com", password="pass")
        resp = self.client.get(reverse("pos:session_open"))
        self.assertIn(resp.status_code, [302, 403])

    def test_pos_session_allows_staff(self):
        self.client.login(username="staff2@test.com", password="pass")
        resp = self.client.get(reverse("pos:session_open"))
        self.assertEqual(resp.status_code, 200)

    def test_pos_session_allows_admin(self):
        self.client.login(username="admin3@test.com", password="pass")
        resp = self.client.get(reverse("pos:session_open"))
        self.assertEqual(resp.status_code, 200)

    def test_pos_refund_blocks_anonymous(self):
        resp = self.anon_client.get(reverse("pos:refund_create"))
        self.assertIn(resp.status_code, [302, 403])

    def test_pos_refund_allows_staff(self):
        self.client.login(username="staff2@test.com", password="pass")
        resp = self.client.get(reverse("pos:refund_create"))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# Receipt Template UI
# ---------------------------------------------------------------------------

class ReceiptTemplateTests(TestCase):
    """Receipt template CRUD pages return 200 for allowed roles."""

    def setUp(self):
        self.client = Client()
        self.staff_user = _make_user("staff3", groups=["Staff"])
        self.admin_user = _make_user("admin4", groups=["Admin"])

    def test_receipt_list_allows_staff(self):
        self.client.login(username="staff3@test.com", password="pass")
        resp = self.client.get(reverse("pos:receipt_list"))
        self.assertEqual(resp.status_code, 200)

    def test_receipt_create_blocks_staff(self):
        self.client.login(username="staff3@test.com", password="pass")
        resp = self.client.get(reverse("pos:receipt_create"))
        self.assertIn(resp.status_code, [302, 403])

    def test_receipt_create_allows_admin(self):
        self.client.login(username="admin4@test.com", password="pass")
        resp = self.client.get(reverse("pos:receipt_create"))
        self.assertEqual(resp.status_code, 200)

    def test_receipt_preview_returns_200(self):
        tmpl = ReceiptTemplate.objects.create(name="T1", paper_width=58)
        self.client.login(username="staff3@test.com", password="pass")
        resp = self.client.get(reverse("pos:receipt_preview", args=[tmpl.pk]))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# POS Messages UI
# ---------------------------------------------------------------------------

class POSMessageTests(TestCase):
    """POS message list returns 200 for staff; create blocked for non-admin."""

    def setUp(self):
        self.client = Client()
        self.staff_user = _make_user("staff4", groups=["Staff"])
        self.admin_user = _make_user("admin5", groups=["Admin"])
        self.anon_client = Client()

    def test_message_list_blocks_anonymous(self):
        resp = self.anon_client.get(reverse("pos_messages:message_list"))
        self.assertIn(resp.status_code, [302, 403])

    def test_message_list_allows_staff(self):
        self.client.login(username="staff4@test.com", password="pass")
        resp = self.client.get(reverse("pos_messages:message_list"))
        self.assertEqual(resp.status_code, 200)

    def test_message_create_blocks_staff(self):
        self.client.login(username="staff4@test.com", password="pass")
        resp = self.client.get(reverse("pos_messages:message_create"))
        self.assertIn(resp.status_code, [302, 403])

    def test_message_create_allows_admin(self):
        self.client.login(username="admin5@test.com", password="pass")
        resp = self.client.get(reverse("pos_messages:message_create"))
        self.assertEqual(resp.status_code, 200)
