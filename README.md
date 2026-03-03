# Kasarium — Retail POS + Online Shop (Initial Plan)

Status: Planning phase only (no code will be written until approval)

Repo name: Kasarium

This document captures decisions, architecture, data model, flows, UI wireframes, and deployment plan for Kasarium. It reflects your constraints and screenshots (Image 1–4) shared from current Odoo usage.

---

## 1) Decisions and Constraints

- USB barcode scanner: Yes (e.g., Zebra; acts as HID keyboard input)
- Online payment: Placeholder only (“Online Payment — Coming Soon”); active method: Cash on Delivery (COD)
- Tax: 21% VAT; prices displayed are tax-included; configurable by Developer (Dev)
- Receipt: Printable after each sale on thermal printer; receipt template must be adjustable (paper width differs per device)
- Registers: Default single register; multi-register support is optional for later
- Quantities: 
  - Piece-based items: integer
  - Weighted items (kg/l): decimal
- Refund policy: Default 7 days; configurable by Dev
- Refund reasons: Selectable list + “Other” with free text
- Purchase price: Visible to Dev only
- Store info (name/address/VAT ID): Editable by Dev; appears on receipts
- Language: Default EN; toggle for LT and others
- i18n: Machine translation will be added after Phase 3
- Contact form: POS Messages + custom CAPTCHA (no Formspree)

---

## 2) High-Level Architecture

- Framework: Django (server-rendered templates) + Django REST Framework (for selective endpoints)
- Apps:
  - users: Custom User with `user_type = dev | staff | customer`; register/login/logout; role-based access
  - products: Catalog, categories, stock, pricing, expiry dates
  - pos: Cash session, sale, payment, refund, receipt printing
  - shop: Online catalog, cart, checkout (COD), Online Payment button (disabled/placeholder)
  - orders: Orders and order items; status transitions; refund records
  - settings: Store, tax, receipt, language configuration
  - contact: Contact -> POS Messages (Custom form + CAPTCHA)
  - i18n: UI strings translations (EN default; LT toggle); optional machine translation after Phase 3
- Database:
  - Dev: SQLite
  - Prod: Postgres (Render PostgreSQL)
- Deployment: Render.com Web Service (gunicorn); environment variables for secrets and settings

---

## 3) Roles and Access

- Dev (you)
  - Full admin and configuration access (tax, store info, language toggles, etc.)
  - Create staff accounts (personnel)
  - View/edit purchase price and sensitive fields
- Staff (personnel)
  - POS usage: open/close session, sale, refund
  - Edit allowed product fields: `retail_price`, `on_hand_quantity`, `expiry_date` (purchase price hidden)
- Customer
  - Self-register
  - Browse products (see retail prices and tax-included total)
  - Cart + checkout (COD); see “Online Payment — Coming Soon” button

---

## 4) Data Model (Concept)

- Category: `name`, `slug`
- SubCategory: `category_fk`, `name`, `slug`
- Product:
  - `category/subcategory`, `name`, `ingredients`, `origin`
  - `unit` = piece | kg | liter
  - `on_hand_quantity` (decimal; integer constraints applied in UI for piece)
  - `retail_price` (tax-included)
  - `purchase_price` (Dev-only visibility)
  - `barcode` (unique; nullable for non-barcoded items)
  - `is_active`, timestamps
- ExpirationDate: `product_fk`, `expiration_date`, timestamps
- StockMovement: `product_fk`, `delta`, `reason`, timestamps
- TaxSetting (store scope):
  - `rate` default 21 (%)
  - `price_includes_tax` = true
- StoreSetting:
  - Store name, address, phone, VAT ID/company ID (editable by Dev); receipt header/footer text; paper width presets
- Order:
  - `customer_fk` (or POS anonymous customer)
  - `status` = pending | paid | cancelled | refunded
  - `payment_method` = cod | online (placeholder)
  - `total_price` (tax-included), timestamps
  - `register_fk`, `cash_session_fk` (for POS)
- OrderItem:
  - `order_fk`, `product_fk`, `quantity (decimal)`, `unit_price (tax-included)`
- Refund:
  - `order_fk`, `items with quantities`, `reason_code`, `reason_note`
  - `policy_days` default 7 (configurable by Dev)
- Register:
  - `name/identifier`, `is_active`
- CashSession:
  - `register_fk`, `staff_fk`, `opening_cash`, `opening_note`, `closed_at`, `closing_cash`, `difference`

---

## 5) Discount Logic (POS and Shop Admin)

Discount must support both inputs:

- Input A: Discount amount (absolute or percentage) applied on base price
  - Show original price and discounted price
  - Example:
    - Base price: €10.00
    - Discount: €2.00 → Final: €8.00
    - Discount: 10% → Final: €9.00
- Input B: Discounted price → compute discount amount
  - Example:
    - Base price: €10.00
    - Discounted price entered: €8.50 → Discount amount = €1.50 (15%)

Validation and permissions:
- Staff can apply discounts (no limits default)
- Dev can set max discount thresholds (optional future feature)

---

## 6) POS Screens and Flow (referencing your images)

- Opening screen (Image 1)
  - Select personnel from saved list
  - Enter “Opening cash” + optional note
  - Open session for the selected register (default single register)
- Sale screen (Image 2)
  - Product grid on the right; personnel selects items (supports non-barcoded fruits/vegetables by tapping)
  - Barcode input (HID scanner): focus maintained; on scan, product auto-added
  - Cart shows line items; quantities (integer for piece, decimal for kg/l); discount UI (both modes)
  - Totals: subtotal, VAT (computed from price-included model), grand total
- Payment (Image 3)
  - Methods: Cash, Bank/Card (physical POS terminal), Customer Account (optional)
  - “Online Payment — Coming Soon” appears on the shop checkout, not POS
  - After confirmation: print receipt
- Refund (Image 4)
  - List prior orders; select order; pick items and quantities to refund
  - Choose reason code; “Other” → free text
  - Stock adjustments and optional refund receipt

---

## 7) Receipt Printing (Thermal; adjustable layout)

- HTML/CSS thermal template with adjustable width presets (58mm, 80mm)
- Store info from `StoreSetting` (editable by Dev)
- Content:
  - Header: store name, address, phone, VAT/company ID, date/time, cashier, register, order/receipt number
  - Line items: name, qty, unit price, line total
  - Summary:
    - VAT 21% (included): `VAT = total - total / (1 + 0.21)`
    - Total payment
    - Payment method
  - Footer: thank you, refund policy (default 7 days)
- Printing approach:
  - Browser print to local thermal printer (initial)
  - Future: Direct ESC/POS network printing via local agent

---

## 8) Online Shop (Minimal viable)

- Catalog list, search/filter, product details
- Cart → Checkout:
  - Active method: Cash on Delivery (COD)
  - Online Payment button: disabled with tooltip “Coming Soon”
- Order confirmation + customer order history
- Contact page is implemented as POS Messages + custom CAPTCHA

---

## 9) USB Barcode Scanner Integration

- Treats scanner as keyboard; input focused at barcode field
- On scan + Enter: lookup by barcode; add to cart
- Debounce/timing guard to avoid mixed keystrokes
- Non-barcoded items via grid selection + manual qty entry (kg/l decimals)

---

## 10) Internationalization and Machine Translation

- Default language: English
- Toggle in top-right: LT and other languages
- Server-side i18n (Django translations) for UI strings
- Machine translation (product descriptions) will be added after Phase 3

---

## 11) Contact Form (POS Messages + CAPTCHA)

- Replace “Contact” with POS Messages module.
- Messages are stored in the main database and visible to Dev/Admin.
- Implement custom CAPTCHA (simple challenge or Turnstile/hCaptcha later).

---

## 12) Deployment (Render.com)

- Service: Web Service (gunicorn)
- Dev DB: SQLite; Prod DB: Render PostgreSQL
- Env variables:
  - `SECRET_KEY`, `ALLOWED_HOSTS`
  - `DATABASE_URL` (prod)
  - `STORE_NAME`, `STORE_ADDRESS`, `STORE_PHONE`, `STORE_VAT_ID`
  - `TAX_RATE=21`, `PRICE_INCLUDES_TAX=true`
  - `DEFAULT_REFUND_DAYS=7`
- Static assets: Whitenoise
- SSL: Managed by Render
- Logging: Application + access logs

---

## 13) Security, Validation, Sessions (to match course needs)

- Client-side validation: forms (required fields, email format, numeric ranges)
- Server-side validation: all inputs revalidated before DB writes
- CSRF protection (Django)
- Session management:
  - Login required for restricted pages (POS, admin)
  - Customer self-register and login
  - Staff accounts created by Dev
- Flow/templating: Django routing + templates; consistent navigation

---

## 14) XML + XSLT Feature (Course Requirement)

- Export monthly sales/orders to XML
- Transform XML into HTML report via XSLT
- Publish “Sales Report” page to render the transformed output
- Include totals, tax breakdown, top products

---

## 15) UI Wireframes (ASCII)

Opening (Image 1 inspired):
```
+------------------------------------------------------------+
| Kasarium POS — Open Session                                |
|                                                            |
| Personnel: [ Select from list v ]                          |
| Register:  [ Default Register v ]                          |
| Opening Cash: [ 21.96 ]   [💵]                             |
| Opening Note: [ Add a note...                         ]    |
|                                                            |
| [ Open Session ]                                           |
+------------------------------------------------------------+
```

Sale screen (Image 2 inspired):
```
+------------------------------------------------------------+
| [Home] [Search...]                      Cart: 3 items €45  |
|------------------------------------------------------------|
| Products Grid (tap to add)    | Cart                       |
| [Fruit] [Veg] [Bakery] ...    | 1) Apples      1.250 kg    |
| [Item tiles...]               |    @€2.00/kg  → €2.50      |
|                               | 2) Milk 1L       x2        |
|                               |    @€1.50      → €3.00     |
|                               | 3) Cookies       x1        |
|                               |    @€2.20      → €2.20     |
|                               |----------------------------|
| Barcode: [___________] [Scan] | Discount: [ € / % ]        |
|                               |   Mode A: Amount or %      |
|                               |   Mode B: Enter final price|
|                               |----------------------------|
|                               | Subtotal: €7.70            |
|                               | VAT(inc): €1.34            |
|                               | TOTAL:  €9.04              |
|                               | [ Checkout ]               |
+------------------------------------------------------------+
```

Payment (Image 3 inspired):
```
+----------------------------------------------+
| Payment — Total: €4.00                       |
|                                              |
| Select method:                               |
|  [ Cash ]  [ Bank/Card ]  [ Customer Acc ]   |
|                                              |
| [ Confirm & Print Receipt ]                  |
+----------------------------------------------+
```

Refund (Image 4 inspired):
```
+-----------------------------------------------------------+
| Refunds — Orders                                          |
|-----------------------------------------------------------|
| List: [#310 €3.00 Paid] [#311 €0.38 Paid] ...             |
|-----------------------------------------------------------|
| Selected Order: #401                                      |
| Items to refund:                                          |
|  [x] Juniper Syrup   qty: [1.00]  line: €4.00             |
| Reason: [Damaged v] [Other note: __________ ]             |
|-----------------------------------------------------------|
| [ Process Refund ]   [ Print Refund Receipt ]             |
+-----------------------------------------------------------+
```

---

## 16) Milestones (no coding until approval)

- M0: Approval of name (Kasarium) and spec (DONE)
- M1: Repo scaffold + settings + users/products models
- M2: Shop catalog + cart + checkout (COD), “Online Payment — Coming Soon”
- M3: POS opening/sale/payment/refund flows; receipt template adjustable
- M4: i18n (EN default, LT toggle)
- M5: XML/XSLT Sales Report
- M6: Render deploy + test

---

## Phase Plan

### Phase 1 — Backend + Database
- Django backend scaffold + settings
- Core database models + migrations
- Role-based access (Dev / Staff / Customer) and permissions
- Data preparation + merge pipeline (products + expiration merge, import to DB)

### Phase 2 — Frontend (excluding Online Shop)
- Admin / Product Control UI (CRUD + validations)
- POS UI screens (opening / sale / payment / refund) — UI implementation
- Receipt template UI (thermal width presets)
- POS Messages UI (replaces Contact page)

### Phase 3 — Frontend + Wrap-up (Online Shop + Integration)
- Online shop (catalog / cart / checkout COD + “Online Payment coming soon”)
- Integrate all modules and finalize flows
- End-to-end testing + deployment readiness

---

## Fixes (Later)
- Dark/Light theme settings (toggle + persistence)
- Machine translation (languages / product descriptions)
- AJAX search (no full page reload)
- Pagination / infinite scroll
- Direct ESC/POS printing integration
- Multi-register UI enablement
- Better reporting/dashboard screens
- Performance optimizations (indexes/caching)