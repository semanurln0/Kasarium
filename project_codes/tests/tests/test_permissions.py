"""Minimal tests for role permissions and import idempotency."""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kasarium.settings.test")

import django
django.setup()

import csv
import tempfile
from pathlib import Path

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.catalog.models import Product, ProductCategory
from apps.inventory.models import ExpirationEntry
from apps.shop.models import ContactMessage


def _make_user(tag, groups=(), is_superuser=False):
    User = get_user_model()
    email = f"{tag}@test.com"
    user = User.objects.create_user(email=email, password="pass")
    user.is_superuser = is_superuser
    user.is_staff = is_superuser
    user.save()
    for g in groups:
        grp, _ = Group.objects.get_or_create(name=g)
        user.groups.add(grp)
    return user


class SeedRolesTest(TestCase):
    def test_seed_roles_creates_groups(self):
        from django.core.management import call_command
        call_command("seed_roles", verbosity=0)
        self.assertTrue(Group.objects.filter(name="Admin").exists())
        self.assertTrue(Group.objects.filter(name="Staff").exists())
        self.assertTrue(Group.objects.filter(name="Customer").exists())

    def test_seed_roles_idempotent(self):
        from django.core.management import call_command
        call_command("seed_roles", verbosity=0)
        call_command("seed_roles", verbosity=0)
        self.assertEqual(Group.objects.filter(name="Admin").count(), 1)


class ImportPhase1DataIdempotencyTest(TestCase):
    def _make_csv(self, path, rows=None):
        """Write a products_with_expiration CSV for testing."""
        fieldnames = [
            "Barcode", "barcode_norm", "Name", "Sales Price", "Sales Description",
            "Description for the website", "Origin",
            "Website Product Category", "expiration_date",
        ]
        if rows is None:
            rows = [
                {
                    "Barcode": "001234567890",
                    "barcode_norm": "1234567890",
                    "Name": "Test Product",
                    "Sales Price": "9.99",
                    "Sales Description": "A test product",
                    "Description for the website": "",
                    "Origin": "TR",
                    "Website Product Category": "Test Category",
                    "expiration_date": "2025-12-31",
                },
                # Discount row — blank barcode, must be skipped
                {
                    "Barcode": "",
                    "barcode_norm": "",
                    "Name": "Discount 0",
                    "Sales Price": "0",
                    "Sales Description": "",
                    "Description for the website": "",
                    "Origin": "",
                    "Website Product Category": "",
                    "expiration_date": "",
                },
                # Row with missing expiration — raw_value should become ""
                {
                    "Barcode": "9876543210",
                    "barcode_norm": "9876543210",
                    "Name": "No Expiry Product",
                    "Sales Price": "5.00",
                    "Sales Description": "",
                    "Description for the website": "",
                    "Origin": "",
                    "Website Product Category": "",
                    "expiration_date": "",
                },
            ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_import_is_idempotent(self):
        from django.core.management import call_command
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "products_with_expiration.csv"
            self._make_csv(str(csv_path))

            call_command("import_phase1_data", csv=str(csv_path), verbosity=0)
            call_command("import_phase1_data", csv=str(csv_path), verbosity=0)

        # Only 2 real products (Discount row skipped)
        self.assertEqual(Product.objects.count(), 2)
        product = Product.objects.get(barcode="001234567890")
        self.assertEqual(
            ExpirationEntry.objects.filter(product=product).count(), 1
        )

    def test_discount_row_skipped(self):
        from django.core.management import call_command
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "products_with_expiration.csv"
            self._make_csv(str(csv_path))
            call_command("import_phase1_data", csv=str(csv_path), verbosity=0)
        # Blank-barcode Discount row must not create a Product
        self.assertFalse(Product.objects.filter(name="Discount 0").exists())

    def test_raw_value_never_null(self):
        from django.core.management import call_command
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "products_with_expiration.csv"
            self._make_csv(str(csv_path))
            call_command("import_phase1_data", csv=str(csv_path), verbosity=0)
        # The row with no expiration_date should have raw_value="" (not NULL)
        product = Product.objects.get(barcode="9876543210")
        entry = ExpirationEntry.objects.get(product=product)
        self.assertIsNotNone(entry.raw_value)
        self.assertEqual(entry.raw_value, "")

    def test_barcode_fallback_to_Barcode_column(self):
        """If barcode_norm is empty, the Barcode column is used directly."""
        from django.core.management import call_command
        rows = [{
            "Barcode": "0011223344",
            "barcode_norm": "",          # ignored — Barcode column is used
            "Name": "Fallback Product",
            "Sales Price": "1.00",
            "Sales Description": "",
            "Description for the website": "",
            "Origin": "",
            "Website Product Category": "",
            "expiration_date": "",
        }]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "products_with_expiration.csv"
            self._make_csv(str(csv_path), rows=rows)
            call_command("import_phase1_data", csv=str(csv_path), verbosity=0)
        self.assertTrue(Product.objects.filter(barcode="0011223344").exists())

    def test_barcode_excel_float_suffix(self):
        """Barcodes written by pandas as '4032489019859.0' must import correctly."""
        from django.core.management import call_command
        rows = [
            {
                "Barcode": "4032489019859.0",   # pandas dtype=str artefact
                "barcode_norm": "4032489019859",
                "Name": "Float Suffix Product",
                "Sales Price": "3.50",
                "Sales Description": "",
                "Description for the website": "",
                "Origin": "",
                "Website Product Category": "",
                "expiration_date": "",
            },
            {
                "Barcode": "4.032489019859e+12",   # scientific notation artefact
                "barcode_norm": "4032489019859",
                "Name": "Scientific Notation Product",
                "Sales Price": "3.50",
                "Sales Description": "",
                "Description for the website": "",
                "Origin": "",
                "Website Product Category": "",
                "expiration_date": "",
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "products_with_expiration.csv"
            self._make_csv(str(csv_path), rows=rows)
            call_command("import_phase1_data", csv=str(csv_path), verbosity=0)
        # Both rows normalize to the same barcode; only 1 product should exist
        self.assertEqual(Product.objects.filter(barcode="4032489019859").count(), 1)

    def test_deposit_row_skipped(self):
        """Deposit rows with empty barcodes must be skipped, same as Discount rows."""
        from django.core.management import call_command
        rows = [
            {
                "Barcode": "999000111222",
                "barcode_norm": "999000111222",
                "Name": "Real Product",
                "Sales Price": "5.00",
                "Sales Description": "",
                "Description for the website": "",
                "Origin": "",
                "Website Product Category": "",
                "expiration_date": "",
            },
            # Deposit row — blank barcode, must be skipped
            {
                "Barcode": "",
                "barcode_norm": "",
                "Name": "Deposit 0.25",
                "Sales Price": "0.25",
                "Sales Description": "",
                "Description for the website": "",
                "Origin": "",
                "Website Product Category": "",
                "expiration_date": "",
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "products_with_expiration.csv"
            self._make_csv(str(csv_path), rows=rows)
            call_command("import_phase1_data", csv=str(csv_path), verbosity=0)
        # Deposit row must not be imported as a product
        self.assertFalse(Product.objects.filter(name="Deposit 0.25").exists())
        # Real product must be imported
        self.assertTrue(Product.objects.filter(barcode="999000111222").exists())

    def test_import_utf8_bom_csv(self):
        """CSV files with a UTF-8 BOM (e.g. exported from Excel) must import
        correctly; a BOM must not corrupt the first column header."""
        from django.core.management import call_command
        rows = [{
            "Barcode": "8000000000001",
            "barcode_norm": "8000000000001",
            "Name": "BOM Product",
            "Sales Price": "3.00",
            "Sales Description": "",
            "Description for the website": "",
            "Origin": "",
            "Website Product Category": "",
            "expiration_date": "",
        }]
        fieldnames = [
            "Barcode", "barcode_norm", "Name", "Sales Price", "Sales Description",
            "Description for the website", "Origin",
            "Website Product Category", "expiration_date",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "products_bom.csv"
            # Write with UTF-8 BOM (utf-8-sig) to simulate an Excel export
            with open(str(csv_path), "w", newline="", encoding="utf-8-sig") as f:
                import csv as _csv
                writer = _csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            call_command("import_phase1_data", csv=str(csv_path), verbosity=0)
        # Product must be imported despite the BOM
        self.assertTrue(Product.objects.filter(barcode="8000000000001").exists())


# ---------------------------------------------------------------------------
# End-to-end: import → shop catalog visibility
# ---------------------------------------------------------------------------

class ImportToShopCatalogTest(TestCase):
    """Verify that products imported via import_phase1_data appear on the
    public shop catalog page.  This is the end-to-end guarantee that 'all
    data will be shown on the website after import'."""

    def _make_csv(self, path, rows):
        fieldnames = [
            "Barcode", "barcode_norm", "Name", "Sales Price", "Sales Description",
            "Description for the website", "Origin",
            "Website Product Category", "expiration_date",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_imported_products_visible_in_shop_catalog(self):
        """After import all real products must be accessible via GET /shop/."""
        from django.core.management import call_command
        rows = [
            {"Barcode": "1111111111111", "barcode_norm": "1111111111111",
             "Name": "Apple Juice", "Sales Price": "1.99",
             "Sales Description": "", "Description for the website": "",
             "Origin": "DE", "Website Product Category": "Beverages",
             "expiration_date": "2025-12-01"},
            {"Barcode": "2222222222222", "barcode_norm": "2222222222222",
             "Name": "Whole Milk", "Sales Price": "0.99",
             "Sales Description": "", "Description for the website": "",
             "Origin": "FR", "Website Product Category": "Dairy",
             "expiration_date": ""},
            # Discount row — must be skipped
            {"Barcode": "", "barcode_norm": "",
             "Name": "Discount 0", "Sales Price": "0",
             "Sales Description": "", "Description for the website": "",
             "Origin": "", "Website Product Category": "",
             "expiration_date": ""},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "products_with_expiration.csv"
            self._make_csv(str(csv_path), rows)
            call_command("import_phase1_data", csv=str(csv_path), verbosity=0)

        # Both real products must be in the DB
        self.assertEqual(Product.objects.count(), 2)

        # Both must be visible via the shop catalog endpoint (no login needed)
        client = Client()
        resp = client.get(reverse("shop:catalog"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Apple Juice")
        self.assertContains(resp, "Whole Milk")
        # Discount row must NOT appear
        self.assertNotContains(resp, "Discount 0")


# ---------------------------------------------------------------------------
# Inventory expiration page access
# ---------------------------------------------------------------------------

class ExpirationListAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = _make_user("exp_customer", groups=["Customer"])
        self.staff = _make_user("exp_staff", groups=["Staff"])
        self.admin = _make_user("exp_admin", groups=["Admin"])
        self.superuser = _make_user("exp_super", is_superuser=True)

    def test_anonymous_redirected(self):
        resp = self.client.get(reverse("inventory:expiration_list"))
        self.assertIn(resp.status_code, [302, 403])

    def test_customer_blocked(self):
        self.client.login(username="exp_customer@test.com", password="pass")
        resp = self.client.get(reverse("inventory:expiration_list"))
        self.assertIn(resp.status_code, [302, 403])

    def test_staff_allowed(self):
        self.client.login(username="exp_staff@test.com", password="pass")
        resp = self.client.get(reverse("inventory:expiration_list"))
        self.assertEqual(resp.status_code, 200)

    def test_admin_allowed(self):
        self.client.login(username="exp_admin@test.com", password="pass")
        resp = self.client.get(reverse("inventory:expiration_list"))
        self.assertEqual(resp.status_code, 200)

    def test_superuser_allowed(self):
        self.client.login(username="exp_super@test.com", password="pass")
        resp = self.client.get(reverse("inventory:expiration_list"))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# Admin order management
# ---------------------------------------------------------------------------

class AdminOrderViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = _make_user("ord_customer", groups=["Customer"])
        self.admin = _make_user("ord_admin", groups=["Admin"])

    def test_admin_order_list_blocked_for_customer(self):
        self.client.login(username="ord_customer@test.com", password="pass")
        resp = self.client.get(reverse("shop:admin_order_list"))
        self.assertIn(resp.status_code, [302, 403])

    def test_admin_order_list_allowed_for_admin(self):
        self.client.login(username="ord_admin@test.com", password="pass")
        resp = self.client.get(reverse("shop:admin_order_list"))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# Customer contact messages
# ---------------------------------------------------------------------------

class ContactMessageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = _make_user("msg_customer", groups=["Customer"])
        self.admin = _make_user("msg_admin", groups=["Admin"])

    def test_contact_list_requires_login(self):
        resp = self.client.get(reverse("shop:contact_list"))
        self.assertIn(resp.status_code, [302, 403])

    def test_customer_can_view_message_list(self):
        self.client.login(username="msg_customer@test.com", password="pass")
        resp = self.client.get(reverse("shop:contact_list"))
        self.assertEqual(resp.status_code, 200)

    def test_customer_can_send_message(self):
        self.client.login(username="msg_customer@test.com", password="pass")
        resp = self.client.post(reverse("shop:contact_new"), {
            "subject": "Test subject",
            "body": "Hello, I need help.",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(ContactMessage.objects.filter(user=self.customer).count(), 1)

    def test_customer_can_reply_to_incoming_message(self):
        msg = ContactMessage.objects.create(
            user=self.customer,
            sent_by=self.admin,
            subject="Support",
            body="Please send more details.",
        )
        self.client.login(username="msg_customer@test.com", password="pass")
        resp = self.client.post(reverse("shop:contact_reply", args=[msg.pk]), {
            "customer_reply": "Here are the details you asked for.",
        })
        self.assertEqual(resp.status_code, 302)
        msg.refresh_from_db()
        self.assertEqual(msg.customer_reply, "Here are the details you asked for.")
        self.assertTrue(msg.customer_replied_at is not None)

    def test_customer_delete_hides_only_customer_side(self):
        msg = ContactMessage.objects.create(
            user=self.customer,
            subject="Hide me",
            body="Body",
        )
        self.client.login(username="msg_customer@test.com", password="pass")
        resp = self.client.post(reverse("shop:contact_delete", args=[msg.pk]))
        self.assertEqual(resp.status_code, 302)
        msg.refresh_from_db()
        self.assertTrue(msg.deleted_for_customer)
        self.assertFalse(msg.deleted_for_staff)

    def test_admin_delete_hides_only_staff_side(self):
        msg = ContactMessage.objects.create(
            user=self.customer,
            subject="Admin hide",
            body="Body",
        )
        self.client.login(username="msg_admin@test.com", password="pass")
        resp = self.client.post(reverse("shop:admin_message_detail", args=[msg.pk]), {
            "action": "delete",
        })
        self.assertEqual(resp.status_code, 302)
        msg.refresh_from_db()
        self.assertTrue(msg.deleted_for_staff)
        self.assertFalse(msg.deleted_for_customer)

    def test_admin_can_view_all_messages(self):
        ContactMessage.objects.create(user=self.customer, subject="Hi", body="Body")
        self.client.login(username="msg_admin@test.com", password="pass")
        resp = self.client.get(reverse("shop:admin_message_list"))
        self.assertEqual(resp.status_code, 200)

    def test_message_marked_read_on_admin_view(self):
        msg = ContactMessage.objects.create(user=self.customer, subject="Hi", body="Body")
        self.assertFalse(msg.is_read)
        self.client.login(username="msg_admin@test.com", password="pass")
        self.client.get(reverse("shop:admin_message_detail", args=[msg.pk]))
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)


# ---------------------------------------------------------------------------
# Customer profile editing
# ---------------------------------------------------------------------------

class ProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = _make_user("profile_user", groups=["Customer"])

    def test_profile_requires_login(self):
        resp = self.client.get(reverse("accounts:profile"))
        self.assertIn(resp.status_code, [302, 403])

    def test_profile_get_returns_200(self):
        self.client.login(username="profile_user@test.com", password="pass")
        resp = self.client.get(reverse("accounts:profile"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"My Profile", resp.content)

    def test_profile_saves_fields(self):
        self.client.login(username="profile_user@test.com", password="pass")
        resp = self.client.post(reverse("accounts:profile"), {
            "first_name": "Alice",
            "last_name": "Smith",
            "phone": "+905551234567",
            "address": "123 Main St",
            "city": "Istanbul",
            "postal_code": "34000",
        })
        self.assertEqual(resp.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alice")
        self.assertEqual(self.user.phone, "+905551234567")
        self.assertEqual(self.user.city, "Istanbul")
        self.assertEqual(self.user.postal_code, "34000")

    def test_profile_partial_update(self):
        """Submitting only some fields still saves correctly."""
        self.client.login(username="profile_user@test.com", password="pass")
        self.client.post(reverse("accounts:profile"), {
            "first_name": "Bob",
            "last_name": "",
            "phone": "",
            "address": "456 Other St",
            "city": "",
            "postal_code": "",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Bob")
        self.assertEqual(self.user.address, "456 Other St")


# ---------------------------------------------------------------------------
# Account deletion
# ---------------------------------------------------------------------------

class DeleteAccountTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = _make_user("delete_me")

    def test_delete_requires_login(self):
        resp = self.client.get(reverse("accounts:delete_account"))
        self.assertIn(resp.status_code, [302, 403])

    def test_delete_get_shows_confirm_page(self):
        self.client.login(username="delete_me@test.com", password="pass")
        resp = self.client.get(reverse("accounts:delete_account"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Delete Account", resp.content)

    def test_delete_post_removes_account(self):
        User = get_user_model()
        uid = self.user.pk
        self.client.login(username="delete_me@test.com", password="pass")
        resp = self.client.post(reverse("accounts:delete_account"))
        self.assertIn(resp.status_code, [301, 302])
        self.assertFalse(User.objects.filter(pk=uid).exists())

    def test_delete_user_with_orders_shows_error(self):
        """Deleting a user who owns Orders must not return 500; user stays."""
        from apps.shop.models import Order
        # Create an order for the user — this places a PROTECT constraint on deletion
        Order.objects.create(user=self.user, shipping_address="123 Test St")
        uid = self.user.pk
        self.client.login(username="delete_me@test.com", password="pass")
        resp = self.client.post(reverse("accounts:delete_account"))
        # Must NOT be a 500 — should redirect with an error message
        self.assertNotEqual(resp.status_code, 500)
        self.assertIn(resp.status_code, [301, 302])
        # User must still exist (deletion was blocked)
        User = get_user_model()
        self.assertTrue(User.objects.filter(pk=uid).exists())


# ---------------------------------------------------------------------------
# Admin user management
# ---------------------------------------------------------------------------

class AdminUserManagementTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = _make_user("admin_mgr", groups=["Admin"])
        self.regular = _make_user("regular_joe")

    def test_user_list_requires_admin(self):
        self.client.login(username="regular_joe@test.com", password="pass")
        resp = self.client.get(reverse("accounts:admin_user_list"))
        # Should redirect or show error, not 200
        self.assertNotEqual(resp.status_code, 200)

    def test_admin_can_list_users(self):
        self.client.login(username="admin_mgr@test.com", password="pass")
        resp = self.client.get(reverse("accounts:admin_user_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"User Management", resp.content)

    def test_admin_can_search_users(self):
        self.client.login(username="admin_mgr@test.com", password="pass")
        resp = self.client.get(reverse("accounts:admin_user_list") + "?q=regular_joe")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"regular_joe", resp.content)

    def test_admin_can_edit_user(self):
        self.client.login(username="admin_mgr@test.com", password="pass")
        resp = self.client.get(
            reverse("accounts:admin_user_edit", args=[self.regular.pk])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Edit User", resp.content)

    def test_admin_edit_saves_fields(self):
        self.client.login(username="admin_mgr@test.com", password="pass")
        resp = self.client.post(
            reverse("accounts:admin_user_edit", args=[self.regular.pk]),
            {
                "email": "regular_joe@test.com",
                "first_name": "Joe",
                "last_name": "Regular",
                "phone": "",
                "address": "",
                "city": "Berlin",
                "postal_code": "",
                "is_active": "on",
                "groups": [],
            },
        )
        self.assertIn(resp.status_code, [301, 302])
        self.regular.refresh_from_db()
        self.assertEqual(self.regular.first_name, "Joe")
        self.assertEqual(self.regular.city, "Berlin")

    def test_non_superuser_cannot_edit_superuser(self):
        User = get_user_model()
        su = _make_user("supertest", is_superuser=True)
        self.client.login(username="admin_mgr@test.com", password="pass")
        resp = self.client.post(
            reverse("accounts:admin_user_edit", args=[su.pk]),
            {
                "email": su.email,
                "first_name": "Hacked",
                "last_name": "",
                "phone": "",
                "address": "",
                "city": "",
                "postal_code": "",
                "is_active": "on",
                "groups": [],
            },
        )
        # Should redirect with error, not save
        self.assertIn(resp.status_code, [301, 302])
        su.refresh_from_db()
        self.assertNotEqual(su.first_name, "Hacked")
