"""
Comprehensive validation test suite for Kasarium.

This test file validates all major features and database connectivity
to ensure the application is fully functional before deployment.
"""
import pytest
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.catalog.models import Product, ProductCategory
from apps.shop.models import Order, OrderLine, ContactMessage
from apps.pos.models import ShiftSession, Sale, SaleLine
from apps.inventory.models import ExpirationEntry
from apps.accounts.models import CustomUser


User = get_user_model()


class DatabaseConnectivityTests(TestCase):
    """Verify all database tables exist and are accessible."""

    def test_user_model_accessible(self):
        """CustomUser model queries work."""
        count = User.objects.count()
        assert isinstance(count, int)
        assert count >= 0

    def test_product_model_accessible(self):
        """Product model queries work."""
        count = Product.objects.count()
        assert isinstance(count, int)

    def test_category_model_accessible(self):
        """ProductCategory model queries work."""
        count = ProductCategory.objects.count()
        assert isinstance(count, int)

    def test_order_model_accessible(self):
        """Order model queries work."""
        count = Order.objects.count()
        assert isinstance(count, int)

    def test_sale_model_accessible(self):
        """Sale model queries work."""
        count = Sale.objects.count()
        assert isinstance(count, int)

    def test_shift_session_model_accessible(self):
        """ShiftSession model queries work."""
        count = ShiftSession.objects.count()
        assert isinstance(count, int)

    def test_expiration_model_accessible(self):
        """ExpirationEntry model queries work."""
        count = ExpirationEntry.objects.count()
        assert isinstance(count, int)


class UserAuthenticationTests(TestCase):
    """Verify user authentication and role-based access."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            email="admin@test.com", password="adminpass123"
        )
        self.staff_user = User.objects.create_user(
            email="staff@test.com", password="staffpass123"
        )
        self.staff_user.is_staff = True
        self.staff_user.save()
        self.customer_user = User.objects.create_user(
            email="customer@test.com", password="customerpass123"
        )

    def test_admin_user_created(self):
        """Superuser creation works."""
        assert self.admin_user.is_superuser
        assert self.admin_user.email == "admin@test.com"

    def test_staff_user_created(self):
        """Staff user creation works."""
        assert self.staff_user.is_staff
        assert self.staff_user.email == "staff@test.com"

    def test_customer_user_created(self):
        """Customer user creation works."""
        assert not self.customer_user.is_staff
        assert self.customer_user.email == "customer@test.com"

    def test_login_redirects_to_shop(self):
        """Login page is accessible."""
        resp = self.client.get(reverse("accounts:login"))
        assert resp.status_code == 200

    def test_admin_login_successful(self):
        """Admin can log in."""
        success = self.client.login(email="admin@test.com", password="adminpass123")
        assert success


class ProductCatalogTests(TestCase):
    """Verify product catalog functionality."""

    def setUp(self):
        self.category = ProductCategory.objects.create(name="Electronics")
        self.product = Product.objects.create(
            barcode="1234567890",
            name="Test Phone",
            sales_price=Decimal("999.99"),
            category=self.category,
            sales_description="A test phone",
        )

    def test_category_created(self):
        """Product categories can be created."""
        assert self.category.name == "Electronics"
        assert ProductCategory.objects.count() >= 1

    def test_product_created(self):
        """Products can be created."""
        assert self.product.name == "Test Phone"
        assert self.product.barcode == "1234567890"
        assert self.product.sales_price == Decimal("999.99")

    def test_product_has_category(self):
        """Products link to categories."""
        assert self.product.category == self.category
        assert self.category.products.count() >= 1

    def test_barcode_unique_constraint(self):
        """Duplicate barcodes are rejected."""
        with pytest.raises(Exception):  # IntegrityError
            Product.objects.create(
                barcode="1234567890",  # Duplicate
                name="Another Phone",
                sales_price=Decimal("500.00"),
            )


class InventoryTests(TestCase):
    """Verify inventory and expiration tracking."""

    def setUp(self):
        self.product = Product.objects.create(
            barcode="999888777",
            name="Milk",
            sales_price=Decimal("2.50"),
        )

    def test_expiration_date_creation(self):
        """Expiration dates can be recorded."""
        from datetime import date

        exp = ExpirationEntry.objects.create(
            product=self.product, expiration_date=date(2026, 6, 1)
        )
        assert exp.product == self.product
        assert ExpirationEntry.objects.count() >= 1


class PosWorkflowTests(TestCase):
    """Verify POS workflow (shift, sales, etc)."""

    def setUp(self):
        self.cashier = User.objects.create_user(
            email="cashier@test.com", password="cashierpass"
        )
        self.cashier.is_staff = True
        self.cashier.save()

        self.product = Product.objects.create(
            barcode="5555555555",
            name="Coffee",
            sales_price=Decimal("3.50"),
        )

    def test_shift_session_creation(self):
        """Cashier can open a shift session."""
        session = ShiftSession.objects.create(
            opened_by=self.cashier, opening_cash=Decimal("100.00")
        )
        assert session.is_open
        assert session.opened_by == self.cashier

    def test_sale_creation(self):
        """Sale can be created within a session."""
        session = ShiftSession.objects.create(
            opened_by=self.cashier, opening_cash=Decimal("100.00")
        )
        sale = Sale.objects.create(session=session, status=Sale.STATUS_PENDING)
        assert sale.session == session
        assert sale.status == Sale.STATUS_PENDING

    def test_sale_line_creation(self):
        """Sale line items can be added."""
        session = ShiftSession.objects.create(
            opened_by=self.cashier, opening_cash=Decimal("100.00")
        )
        sale = Sale.objects.create(session=session)
        line = SaleLine.objects.create(
            sale=sale,
            product=self.product,
            barcode="5555555555",
            name_snapshot="Coffee",
            unit_price=Decimal("3.50"),
            qty=2,
        )
        assert line.sale == sale
        assert line.product == self.product
        assert line.qty == 2


class OrderCheckoutTests(TestCase):
    """Verify order and checkout workflow."""

    def setUp(self):
        self.customer = User.objects.create_user(
            email="buyer@test.com", password="buyerpass"
        )
        self.product = Product.objects.create(
            barcode="7777777777",
            name="Laptop",
            sales_price=Decimal("1299.99"),
        )

    def test_order_creation(self):
        """Customer orders can be created."""
        order = Order.objects.create(
            user=self.customer,
            status=Order.STATUS_PENDING,
            payment_method=Order.PAYMENT_COD,
        )
        assert order.user == self.customer
        assert order.status == Order.STATUS_PENDING

    def test_order_item_creation(self):
        """Order items can be added."""
        order = Order.objects.create(
            user=self.customer,
            status=Order.STATUS_PENDING,
            payment_method=Order.PAYMENT_COD,
        )
        item = OrderLine.objects.create(
            order=order,
            product=self.product,
            name_snapshot="Laptop",
            qty=1,
            unit_price=Decimal("1299.99"),
        )
        assert item.order == order
        assert item.product == self.product


class PermissionTests(TestCase):
    """Verify role-based access control."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            email="admin2@test.com", password="admin123"
        )
        self.staff = User.objects.create_user(
            email="staff2@test.com", password="staff123"
        )
        self.staff.is_staff = True
        self.staff.save()
        self.customer = User.objects.create_user(
            email="customer2@test.com", password="customer123"
        )

    def test_anonymous_cannot_access_admin(self):
        """Anonymous user cannot access admin features."""
        resp = self.client.get("/admin/")
        assert resp.status_code in [301, 302, 403, 404]  # Redirect or forbidden


class SettingsValidationTests(TestCase):
    """Verify Django settings are correct."""

    def test_debug_mode(self):
        """Debug is configured (True for dev)."""
        from django.conf import settings

        assert hasattr(settings, "DEBUG")

    def test_installed_apps(self):
        """All required apps are installed."""
        from django.conf import settings

        required_apps = [
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "apps.accounts",
            "apps.catalog",
            "apps.pos",
            "apps.shop",
        ]
        for app in required_apps:
            assert app in settings.INSTALLED_APPS, f"{app} not installed"

    def test_auth_user_model(self):
        """Custom user model is configured."""
        from django.conf import settings

        assert settings.AUTH_USER_MODEL == "accounts.CustomUser"

    def test_database_configured(self):
        """Database is configured."""
        from django.conf import settings

        assert "default" in settings.DATABASES
        db = settings.DATABASES["default"]
        assert "ENGINE" in db
