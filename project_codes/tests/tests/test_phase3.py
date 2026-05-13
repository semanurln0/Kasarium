"""Phase 3 smoke tests: shop, auth, cart, checkout, and order history."""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kasarium.settings.test")

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.catalog.models import Product, ProductCategory
from apps.shop.models import Order, OrderLine

User = get_user_model()


def _make_customer(email, password="testpass123"):
    return User.objects.create_user(email=email, password=password)


def _make_product(name="Widget", price="9.99", barcode="1234560001"):
    cat, _ = ProductCategory.objects.get_or_create(name="Test Category")
    return Product.objects.create(
        barcode=barcode,
        name=name,
        sales_price=price,
        category=cat,
    )


# ---------------------------------------------------------------------------
# A) Anonymous catalog browsing
# ---------------------------------------------------------------------------

class AnonymousCatalogTests(TestCase):
    """Shop catalog is publicly accessible without login."""

    def setUp(self):
        self.client = Client()
        _make_product("Public Widget", "5.00", "9900000001")

    def test_catalog_accessible_anonymous(self):
        resp = self.client.get(reverse("shop:catalog"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Public Widget")

    def test_catalog_search_anonymous(self):
        resp = self.client.get(reverse("shop:catalog") + "?q=Widget")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Public Widget")

    def test_product_detail_accessible_anonymous(self):
        product = Product.objects.first()
        resp = self.client.get(reverse("shop:product_detail", args=[product.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, product.name)

    def test_catalog_filter_by_category(self):
        cat = ProductCategory.objects.get(name="Test Category")
        resp = self.client.get(reverse("shop:catalog") + f"?cat={cat.pk}")
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# B) Cart (session-based, anonymous allowed)
# ---------------------------------------------------------------------------

class CartTests(TestCase):
    """Cart can be used without login."""

    def setUp(self):
        self.client = Client()
        self.product = _make_product("Cart Item", "12.00", "9900000002")

    def test_cart_page_empty_anonymous(self):
        resp = self.client.get(reverse("shop:cart"))
        self.assertEqual(resp.status_code, 200)

    def test_add_to_cart(self):
        resp = self.client.post(
            reverse("shop:add_to_cart", args=[self.product.pk]),
            {"next": "/shop/"},
        )
        # Should redirect after adding
        self.assertIn(resp.status_code, [301, 302])

    def test_cart_shows_added_item(self):
        self.client.post(
            reverse("shop:add_to_cart", args=[self.product.pk]),
            {"next": "/shop/cart/"},
        )
        resp = self.client.get(reverse("shop:cart"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Cart Item")

    def test_remove_from_cart(self):
        self.client.post(
            reverse("shop:add_to_cart", args=[self.product.pk]),
            {"next": "/shop/cart/"},
        )
        self.client.post(reverse("shop:remove_from_cart", args=[self.product.pk]))
        resp = self.client.get(reverse("shop:cart"))
        # Cart should be empty — the empty-cart message should be shown
        self.assertContains(resp, "Your cart is empty")

    def test_update_cart_qty(self):
        self.client.post(
            reverse("shop:add_to_cart", args=[self.product.pk]),
            {"next": "/shop/cart/"},
        )
        self.client.post(
            reverse("shop:update_cart"),
            {f"qty_{self.product.pk}": "3"},
        )
        resp = self.client.get(reverse("shop:cart"))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# C) Checkout redirects to login when anonymous
# ---------------------------------------------------------------------------

class CheckoutAuthTests(TestCase):
    """Checkout requires login."""

    def setUp(self):
        self.client = Client()
        self.product = _make_product("Checkout Item", "15.00", "9900000003")
        # Add item to cart
        self.client.post(
            reverse("shop:add_to_cart", args=[self.product.pk]),
            {"next": "/shop/"},
        )

    def test_checkout_redirects_anonymous_to_login(self):
        resp = self.client.get(reverse("shop:checkout"))
        self.assertIn(resp.status_code, [301, 302])
        self.assertIn("/accounts/login/", resp.url)


# ---------------------------------------------------------------------------
# D) Customer login then place COD order
# ---------------------------------------------------------------------------

class OrderPlacementTests(TestCase):
    """Logged-in customer can place a COD order."""

    def setUp(self):
        self.client = Client()
        self.customer = _make_customer("buyer@example.com")
        self.product = _make_product("Order Product", "20.00", "9900000004")

    def test_login_with_email(self):
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "buyer@example.com", "password": "testpass123"},
        )
        self.assertIn(resp.status_code, [200, 302])

    def test_place_cod_order(self):
        self.client.login(username="buyer@example.com", password="testpass123")
        # Add item to cart
        self.client.post(
            reverse("shop:add_to_cart", args=[self.product.pk]),
            {"next": "/shop/"},
        )
        # Place order
        resp = self.client.post(
            reverse("shop:checkout"),
            {
                "shipping_address": "123 Test Street, Test City",
                "payment_method": "COD",
                "notes": "",
            },
        )
        # Should redirect to order detail
        self.assertIn(resp.status_code, [301, 302])
        self.assertTrue(Order.objects.filter(user=self.customer).exists())
        order = Order.objects.get(user=self.customer)
        self.assertEqual(order.payment_method, "COD")
        self.assertEqual(order.lines.count(), 1)

    def test_order_appears_in_history(self):
        self.client.login(username="buyer@example.com", password="testpass123")
        # Place an order directly
        order = Order.objects.create(
            user=self.customer,
            payment_method="COD",
            shipping_address="123 Street",
        )
        resp = self.client.get(reverse("shop:order_history"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, f"#{order.pk}")

    def test_order_detail_accessible(self):
        self.client.login(username="buyer@example.com", password="testpass123")
        order = Order.objects.create(
            user=self.customer,
            payment_method="COD",
            shipping_address="123 Street",
        )
        resp = self.client.get(reverse("shop:order_detail", args=[order.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_order_history_blocked_anonymous(self):
        resp = self.client.get(reverse("shop:order_history"))
        self.assertIn(resp.status_code, [301, 302])

    def test_other_user_cannot_view_order(self):
        other = _make_customer("other@example.com")
        order = Order.objects.create(
            user=self.customer,
            payment_method="COD",
            shipping_address="123 Street",
        )
        self.client.login(username="other@example.com", password="testpass123")
        resp = self.client.get(reverse("shop:order_detail", args=[order.pk]))
        self.assertEqual(resp.status_code, 404)


# ---------------------------------------------------------------------------
# E) Customer auth: register + login
# ---------------------------------------------------------------------------

class CustomerAuthTests(TestCase):
    """Customer registration and login."""

    def setUp(self):
        self.client = Client()

    def test_register_page_accessible(self):
        resp = self.client.get(reverse("accounts:register"))
        self.assertEqual(resp.status_code, 200)

    def test_login_page_accessible(self):
        resp = self.client.get(reverse("accounts:login"))
        self.assertEqual(resp.status_code, 200)

    def test_register_creates_user(self):
        resp = self.client.post(
            reverse("accounts:register"),
            {
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertIn(resp.status_code, [200, 302])
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_login_with_email(self):
        User.objects.create_user(email="logintest@example.com", password="testpass123")
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "logintest@example.com", "password": "testpass123"},
        )
        self.assertIn(resp.status_code, [200, 302])


# ---------------------------------------------------------------------------
# F) Permissions: customers blocked from admin/POS
# ---------------------------------------------------------------------------

class CustomerRolePermissionTests(TestCase):
    """Customers cannot access admin/POS views."""

    def setUp(self):
        self.client = Client()
        self.customer = _make_customer("cust@example.com")

    def test_customer_blocked_from_pos(self):
        self.client.login(username="cust@example.com", password="testpass123")
        resp = self.client.get(reverse("pos:session_open"))
        self.assertIn(resp.status_code, [302, 403])

    def test_customer_blocked_from_catalog_admin(self):
        self.client.login(username="cust@example.com", password="testpass123")
        resp = self.client.get(reverse("catalog:product_list"))
        self.assertIn(resp.status_code, [302, 403])
