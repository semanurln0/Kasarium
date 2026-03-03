# Semester Project — Progressive Web Application Development
Status: Planning document (UPDATED checklist + mapping to Kasarium). No code will be written until approval.

Legend:
- [x] Planned (to be implemented during the semester)
- [>] Planned for later phase (post-MVP or optional)
- [ ] Not planned / out of scope

Kasarium (Retail POS + Online Shop) will satisfy all mandatory features via analogous modules.

---

## Original Requirements (UPDATED Checklist)

### 1. Project Description
- [x] Design and implement a complete web application; progressive build over the semester

### 2. Project Scenario
- [x] A portal to manage records (admin can store/view/update structured data)

### 3. Learning Outcomes
- [x] Build structured website using HTML5/CSS3
- [x] Implement interactive behaviour using JavaScript (forms validation, POS interactions)
- [x] Use XML + XSLT to represent/transform data (Sales/Orders report)
- [x] Deploy and use a backend framework (Django)
- [x] Connect to a database and perform data operations (PostgreSQL/SQLite)
- [x] Implement routing and template-based output rendering (Django templates)
- [x] Apply validation rules and session-based access control (Auth + role-based)

### 4. Functional Requirements (Mandatory Features)

FR1: Public Website Pages
- [x] Home Page
- [x] About Page
- [x] Contact Page (Formspree + CAPTCHA; backend optional beyond Formspree)

FR2: Management Module (CRUD)
- [x] List records (table)
- [x] View record details (single record page)
- [x] Add new record (form + database insert)
- [x] Edit record (update database)
- [x] Delete record (remove from database)

Minimum student fields (Kasarium mapping):
- [x] Unique ID → Product barcode (unique; nullable for non-barcoded)
- [x] Full Name → Product name
- [x] Email → Customer email (for customer accounts)
- [x] Program/Department → Category/Subcategory
- [x] Year of Study → Not applicable (mapped via product status/created_at)
- [x] Status (Active / Inactive) → Product active/inactive

FR3: Data Validation
Client-side (JavaScript):
- [x] Required fields must not be empty
- [x] Email format must be checked (customer registration)
- [x] ID pattern must be checked (barcode format rules where applicable)
Server-side (Backend):
- [x] Validate input before saving to the database
- [x] Reject duplicate IDs (barcode uniqueness)
- [x] Invalid input must show a clear error message

FR4: Flow Management + Output Templates
- [x] Routing:
  - /home
  - /products (list)
  - /products/new (create)
  - /products/:id (details)
  - /products/:id/edit (edit)
- [x] Templates/views are used to generate output pages (Django templates)

FR5: Session Management
- [x] Login page (admin/dev/staff/customer)
- [x] Restricted access to management/POS pages unless logged in
- [x] Logout function
- [x] Session feedback messages (e.g., “Product added successfully”)

FR6: XML + XSLT Requirement
- [x] Export sales/orders to XML
- [x] Transform XML into an HTML report via XSLT
- [x] Display the report in a browser (“Sales Report” page)

### 5. Non-Functional Requirements (Quality)
- [x] Clean and organized folder structure
- [x] Readable code and consistent naming
- [x] User-friendly navigation and layout
- [x] Proper error handling (invalid IDs, missing record)
- [x] Basic secure coding practices (do not trust user input; CSRF)

### 6. Technologies and Tools
- [x] HTML5
- [x] CSS3
- [x] JavaScript
- [x] XML + XSLT
- [x] Backend framework (Django)
- [x] Database (SQLite dev, PostgreSQL prod)

### 7. Deliverables and Submission Requirements
(a) Complete Source Code
- [x] Full project folder

(b) Database Setup
- [x] Clear instructions for database setup (Django migrations; optional .sql seed)

(c) README File
- [x] Project description
- [x] Instructions on how to run the project
- [x] Required dependencies/tools
- [x] Login credentials for testing (Dev/Staff/Customer demo accounts)
- [x] List of implemented features

(d) Screenshots
- [x] Products list page
- [x] Add/Edit product form page
- [x] XML/XSLT sales report page
- [x] Login/logout and restricted access behaviour
- [x] POS Opening / Sale / Payment / Refund screens (Kasarium equivalents)

### 8. Laboratory Alignment (Project Development Plan)
- [x] HTML/CSS website structure and design
- [x] JavaScript DOM manipulation and validation (forms, POS flows)
- [x] XML and XSLT transformation tasks (sales report)
- [x] Backend routing and template rendering (Django)
- [x] Database integration and CRUD implementation
- [x] Flow management between system pages
- [x] Validation and session mechanisms

### 9. Optional Extensions (Bonus Features)
- [>] Search and filtering (catalog)
- [>] Pagination of product list
- [>] AJAX-based search without reloading
- [x] Role-based access control (Dev/Staff/Customer)
- [>] Export product/order data to JSON
- [x] Improved UI design and responsiveness

---

## Kasarium-Specific Checklist (Added for clarity)

Core POS & Shop
- [x] POS Opening screen with personnel selection (from saved list)
- [x] POS Sale screen: product grid + barcode input (USB HID scanner), non-barcoded items via taps
- [x] POS Payment screen: Cash / Bank/Card (physical terminal)
- [x] POS Refund screen: select order/items, reason codes + “Other” note
- [x] Receipt printing: thermal (adjustable width), editable store info, VAT breakdown (price-included)
- [x] Discount logic:
  - [x] Enter discount amount/% → compute final price, show original vs discounted
  - [x] Enter discounted price → compute discount amount/%
- [x] Tax settings: 21% VAT, price-included, configurable by Dev
- [x] Single register by default; multi-register capability (model support) [>] enable later
- [x] Online shop: catalog, cart, checkout (Cash on Delivery)
- [x] Online payment button with “Coming Soon” placeholder in checkout
- [x] Contact form via Formspree with CAPTCHA (free tier; fallback custom if needed)
- [x] i18n: EN default; LT and others via top-right toggle; machine translation (product descriptions) [>] add later
- [x] XML/XSLT: Sales/Orders export + transform to HTML report

Hardware & Integrations
- [x] USB barcode scanner (Zebra etc.): HID input handling
- [>] Direct ESC/POS network printing (future enhancement)

Security & Admin
- [x] Purchase price visible to Dev only (hidden from Staff/Customer)
- [x] Refund policy default 7 days (configurable)
- [x] Store info editable by Dev: name/address/phone/VAT ID, receipt header/footer