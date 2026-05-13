# Planned Features & Project Requirements

## Phase Completion Status

**Phase 1:** ✓ Complete

- Database models and migrations
- Data import pipeline (Phase 1 data merge)
- Django project scaffold

**Phase 2:** In Progress (✓ Implemented )

- Admin UI for products, categories, pricing
- POS UI screens (opening, sale, payment, refund)

**Phase 3:** Planned  (✓ Implemented)

- Online shop (catalog, cart, checkout)
- End-to-end integration and testing

---

## Original Course Requirements (Semester Project)

All mandatory features are implemented or planned per Kasarium roadmap.

### FR1: Public Website Pages  (✓ Implemented)

- [X] Home page (shop catalog)
- [X] About page (product details)
- [X] Contact page (POS messages + contact form)

### FR2: Management Module (CRUD - ✓ Implemented)

- [X] List records (products table in admin)
- [X] View record details (product detail page)
- [X] Add new record (create product form)
- [X] Edit record (update product)
- [X] Delete record (remove product)

**Mapped fields:**

- Barcode (unique) → Product ID
- Product name → Full Name
- Customer email → Email (for orders)
- Category/Subcategory → Program/Department
- Active/Inactive status → Status

### FR3: Data Validation (✓ Implemented)

- [X] Client-side (JS): required fields, email format, barcode patterns
- [X] Server-side (Django): input revalidation, unique constraints, error messages
- [X] CSRF protection enabled

### FR4: Routing & Templates (✓ Implemented)

- [X] `/shop/` — catalog
- [X] `/shop/products/` — product list
- [X] `/shop/products/<id>/` — product details
- [X] `/admin/` — management console
- [X] Template-based rendering (Django)

### FR5: Session Management (✓ Implemented)

- [X] Login pages (customer, staff, admin)
- [X] Restricted access by role (permissions)
- [X] Logout function
- [X] Session feedback (messages framework)

### FR6: XML + XSLT Requirement (✓ Implemented)

- [X] Export orders/sales to XML
- [X] Transform via XSLT to HTML report
- [X] Sales Report page (`/admin/reports/`)

### Non-Functional Requirements (✓ Implemented)

- [X] Clean folder structure (`project_codes/` subdirectories)
- [X] Readable, consistent code
- [X] User-friendly navigation
- [X] Error handling for invalid inputs
- [X] Secure coding (CSRF, input validation)

---

## Kasarium-Specific Implementation

### Core POS & Shop (✓ Implemented)

- [X] POS opening with personnel selection
- [X] Sale screen: product grid + barcode scanner input
- [X] Payment methods: Cash, Bank/Card, Online (placeholder)
- [X] Refund workflow: select order, reason code, free-text note
- [X] Thermal receipt printing with adjustable width
- [X] Discount logic: amount/% entry or final price entry
- [X] Tax settings: 21% VAT, price-included
- [X] Single register (model supports multi-register later)
- [X] Online shop: catalog, cart, COD checkout
- [X] Contact form with CAPTCHA
- [X] i18n framework (EN default, LT toggle)
- [X] USB barcode scanner support (HID input)

### Security & Admin (✓ Implemented)

- [X] Purchase price visible to admin only
- [X] Refund policy (default 7 days, configurable)
- [X] Store info editable by admin (name, address, VAT ID)

---

## Phase 2+ Enhancements

### 1. Machine Translation

- Translate product content (labels, descriptions) between languages automatically.
- Tool: [HuggingFace MADLAD-400-3B-MT](https://huggingface.co/google/madlad400-3b-mt) (Apache 2.0 license, commercial-safe).
- Approach: Batch/offline translation during data import; store in dedicated EN/LT fields.
- Rationale: Avoids latency in POS/admin; runs as scheduled job.

### 2. Dark/Light Theme (✓ Implemented)

- Add theme toggle in user settings.
- Persist preference in localStorage.
- Full UI coverage (POS, shop, admin).

### 3. Advanced Reporting (✓ Implemented)

- Interactive dashboards (sales, inventory, waste/expiry).
- Date range filtering and export to PDF.
- Tax breakdown reports.

### 4. AJAX & UX (✓ Implemented)

- AJAX search (no full page reload).
- Pagination and infinite scroll for product lists.
- Real-time cart updates.

### Round 2 Completed (May 2026 - ✓ Implemented)

- Unified expiration source across shop/product control/expiry control views.
- Added admin/staff outbound messaging to customers and fixed reply delivery.
- Fixed single-message delete behavior and dark-mode alert readability.
- Added site contact address setting and clickable footer links (phone/maps/email).
- Added permanent right-side catalog cart with qty/remove controls.
- Expanded checkout with saved shipping/invoice profiles and courier price inclusion.
- Added product image options: URL, base64, local upload, camera capture.
- Added page jump controls and preserved shop filters on product detail return.
- Displayed discounted prices and image availability in shop/product control.

### Current Local Validation (May 2026 - ✓ Implemented)

- Local launcher runs from `P2_main_project.py --check` and `run.py --check`.
- Django system checks pass in the dev settings.
- Full project tests pass in the local test environment.
- Dev SQLite starts with seeded roles, restored demo accounts, and imported phase-1 product data.

### Current Feature Batch (May 2026 - ✓ Implemented)

- Added admin/staff order filtering by status, payment method, and date range.
- Added expiration color states in the staff expiry control view.
- Added checkout work-hours warning with customer confirmation and pending-order cancellation rules.
- Added two-mode product discounts: percentage or discounted price.

### 5. ESC/POS Printing

- Direct thermal printer integration via network.
- Replace browser print with local agent.
- Receipt template UI

### 6. Multi-Register Support

- Enable multiple concurrent POS terminals.
- Unified cash management and reporting.

### 7. Online Payments

- Replace "Coming Soon" placeholder with real payment gateway.
- Support Stripe, PayPal, or local credit card processor.

---

## Short-Term Fixes

- [ ] Create `project_codes/frontend/staticfiles/` or adjust STATICFILES_DIRS in settings to silence runtime warning.
- [ ] Remove PytestConfigWarning by removing `DJANGO_SETTINGS_MODULE` from `pytest.ini` (use env var only).
- [ ] Add CI pipeline: set PYTHONPATH, run `pytest`, publish results.
- [ ] Verify all tests pass in CI environment (expect 112/112).
