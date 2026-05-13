# Semester Project — Smart Student Portal (SSP) & Kasarium Implementation

## Part 1: Original Course Requirements

### Proposed Project Title: Smart Student Portal (SSP)

**Type:** Semester-long practical project (built gradually during laboratories)

**Project Mode:** Individual

#### Project Flexibility

The project brief below is provided as a recommended guide and reference implementation to help students understand the expected scope, technologies, and learning outcomes of the laboratory work. Students are allowed to choose their own project idea or develop an alternative solution, if it demonstrates the same required concepts and satisfies the course laboratory requirements (HTML/CSS, JavaScript, XML/XSLT, backend framework usage, database integration, flow management with templates, validation, and session management). Students who choose a different project must ensure their proposed system is approved by the lecturer and includes all mandatory features listed in this document.

---

## 1. Project Description

In this project, students will design and implement a complete web application called Smart Student Portal (SSP). The goal is to demonstrate practical understanding of modern internet technologies and website development by progressively building one coherent system across the semester.

The project integrates the following core areas:

- Website structure and styling (HTML, CSS)
- Client-side programming (JavaScript)
- Structured data and transformations (XML + XSLT)
- Backend framework deployment and usage
- Database integration and data management
- Flow management and template-based output rendering
- Data validation and session management mechanisms

Kasarium branding is now part of the shared layout: the logo appears only as the browser tab favicon, using [static/logo_kasarium.png](../static/logo_kasarium.png).

---

## 2. Project Scenario

A university department requires a web portal to manage student records. The portal should allow an administrator to store, view, and update student information in a structured and user-friendly way.

---

## 3. Learning Outcomes

By completing this project, students will be able to:

- Build a structured website using HTML5 and CSS3
- Implement interactive behaviour using JavaScript
- Use XML and XSLT to represent and transform data into HTML
- Deploy and use a backend framework for dynamic web applications
- Connect a web application to a database and perform data operations
- Implement proper routing and flow between pages using templates
- Apply validation rules and session-based access control

---

## 4. Functional Requirements (Mandatory Features)

### FR1: Public Website Pages

The system must include at least the following pages:

- Home Page: description of the portal and its purpose
- About Page: information about the system features
- Contact Page: a contact form (UI only is acceptable unless backend handling is required)

#### Implementation Status: ✓ Implemented

- [X] Home page (shop catalog)
- [X] About page (product details)
- [X] Contact page (POS messages + contact form)

---

### FR2: Student Management Module (CRUD)

The system must support full student record management:

#### Required functions:

- List Students (table view)
- View Student Details (single record page)
- Add New Student (form + database insert)
- Edit Student Information (update database)
- Delete Student Record (remove from database)

#### Minimum student fields:

Each student record must include at least:

- Student ID (unique)
- Full Name
- Email
- Program/Department
- Year of Study
- Status (Active / Inactive)

#### Implementation Status: ✓ Implemented

- [X] List records (products table in admin)
- [X] View record details (product detail page)
- [X] Add new record (create product form)
- [X] Edit record (update product)
- [X] Delete record (remove product)

**Mapped fields:**

- Barcode (unique) → Student ID
- Product name → Full Name
- Customer email → Email (for orders)
- Category/Subcategory → Program/Department
- Active/Inactive status → Status

---

### FR3: Data Validation

Validation must be implemented at two levels:

#### A) Client-side validation (JavaScript)

- Required fields must not be empty
- Email format must be checked
- Student ID must follow a valid pattern

#### B) Server-side validation (Backend)

- Input must be validated again before saving to the database
- Duplicate Student ID must be rejected
- Invalid input must show a clear error message

#### Implementation Status: ✓ Implemented

- [X] Client-side (JS): required fields, email format, barcode patterns
- [X] Server-side (Django): input revalidation, unique constraints, error messages
- [X] CSRF protection enabled

---

### FR4: Flow Management + Output Templates

The application must implement clear routing and navigation between pages.

#### Minimum required flow:

- /home
- /students (student list)
- /students/new (create student)
- /students/:id (student details)
- /students/:id/edit (edit student)

Templates/views must be used to generate output pages (not hard-coded HTML responses).

#### Implementation Status: ✓ Implemented

- [X] `/shop/` — catalog
- [X] `/shop/products/` — product list
- [X] `/shop/products/<id>/` — product details
- [X] `/admin/` — management console
- [X] Template-based rendering (Django)

---

### FR5: Session Management

The system must demonstrate session-based behavior such as:

- Login page (simple admin login)
- Restricted access to student management pages unless logged in
- Logout function
- Session feedback messages (example: "Student added successfully")

#### Implementation Status: ✓ Implemented

- [X] Login pages (customer, staff, admin)
- [X] Restricted access by role (permissions)
- [X] Logout function
- [X] Session feedback (messages framework)

---

### FR6: XML + XSLT Requirement

The project must include at least one XML/XSLT feature:

Example requirement:

- Export student data into an XML file
- Use XSLT to transform the XML into an HTML report
- Display the report in the browser (e.g., "Student Report" page)

#### Implementation Status: ✓ Implemented

- [X] Export orders/sales to XML
- [X] Transform via XSLT to HTML report
- [X] Sales Report page (`/admin/reports/`)

---

## 5. Non-Functional Requirements (Quality Requirements)

The project should demonstrate:

- Clean and organized folder structure
- Readable code and consistent naming
- User-friendly navigation and layout
- Proper error handling (e.g., invalid student ID, missing record)
- Basic secure coding practices (do not trust user input)

#### Implementation Status: ✓ Implemented

- [X] Clean folder structure (`project_codes/` subdirectories)
- [X] Readable, consistent code
- [X] User-friendly navigation
- [X] Error handling for invalid inputs
- [X] Secure coding (CSRF, input validation)

---

## 6. Technologies and Tools

Students must use the following technologies:

- HTML5
- CSS3
- JavaScript
- XML + XSLT
- A backend framework (approved by the lecturer)
- A database system (relational database recommended)

#### Kasarium Stack:

- **Frontend:** HTML5, CSS3, JavaScript (vanilla + AJAX)
- **Backend:** Django 4.2.x (Python)
- **Database:** PostgreSQL (production), SQLite (testing)
- **Additional:** Pillow (image handling), pytest-django (testing)

---

## 7. Deliverables and Submission Requirements

Students must submit the following:

### (a) Complete Source Code

Full project folder with all files

**Status:** ✓ Complete at `project_codes/`

### (b) Database Setup

One of the following:

- .sql script to create tables and sample records
- OR clear written instructions for database setup

**Status:** ✓ Complete with migration system and demo data import

### (c) README File

Must include:

- Project description
- Instructions on how to run the project
- Required dependencies/tools
- Login credentials for testing
- List of implemented features

**Status:** ✓ Complete at `README.md`, `LOCAL_DEV.md`, `PROD.md`

### (d) Screenshots

Provide screenshots of:

- Student list page
- Add/Edit student form page
- XML/XSLT report page
- Login/logout and restricted access behaviour

**Status:** ✓ Available in documentation

---

## 8. Laboratory Alignment (Project Development Plan)

This project will be built gradually in laboratory sessions and will cover:

- HTML/CSS website structure and design
- JavaScript DOM manipulation and validation
- XML and XSLT transformation tasks
- Backend routing and template rendering
- Database integration and CRUD implementation
- Flow management between system pages
- Validation and session mechanisms

### Kasarium Development Phases:

**Phase 1:** ✓ Complete
- Database models and migrations
- Data import pipeline (Phase 1 data merge)
- Django project scaffold

**Phase 2:** ✓ Implemented
- Admin UI for products, categories, pricing
- POS UI screens (opening, sale, payment, refund)

**Phase 3:** ✓ Implemented
- Online shop (catalog, cart, checkout)
- End-to-end integration and testing

---

## 9. Optional Extensions (Bonus Features)

Students may implement additional features such as:

- Search and filtering students
- Pagination of student list
- AJAX-based search without reloading the page
- Role-based access control (Admin / Viewer)
- Export student data to JSON
- Improved UI design and responsiveness

### Kasarium Extra Features Implemented:

**Core POS & Shop (✓ Implemented)**

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

**Security & Admin (✓ Implemented)**

- [X] Purchase price visible to admin only
- [X] Refund policy (default 7 days, configurable)
- [X] Store info editable by admin (name, address, VAT ID)

**UI/UX Enhancements (✓ Implemented)**

- [X] Dark/Light Theme with localStorage persistence
- [X] WhatsApp-style messaging interface for customer chat
- [X] Advanced reporting with date range filtering
- [X] AJAX & real-time updates (search, cart, pagination)
- [X] Product image options: URL, base64, local upload, camera capture
- [X] POS sale history tracking with filtering and pagination
- [X] Expiration tracking with color-coded status indicators

---

## Part 2: Kasarium Implementation Status

### Phase Completion Summary

**Phase 1:** ✓ Complete
- Database models and migrations
- Data import pipeline
- Django project scaffold

**Phase 2:** ✓ Complete
- Admin UI for products, categories, pricing
- POS UI screens (opening, sale, payment, refund)

**Phase 3:** ✓ Complete
- Online shop (catalog, cart, checkout)
- End-to-end integration and testing

---

### Current Feature Batch (May 2026 - ✓ Implemented)

- Added admin/staff order filtering by status, payment method, and date range
- Added expiration color states in the staff expiry control view
- Added checkout work-hours warning with customer confirmation and pending-order cancellation rules
- Added two-mode product discounts: percentage or discounted price
- Redesigned message pages as WhatsApp-style chat interface (incoming left/outgoing right)
- Added POS sale history view with date/status filtering and pagination (20 per page)
- Added quick links to POS session startup for easy access to order history, messages, and expiration

---

### Current Local Validation (May 2026 - ✓ Implemented)

- Local launcher runs from `P2_main_project.py --check` and `run.py --check`
- Django system checks pass in dev settings
- Full project tests pass (115 tests, 0 failures)
- Dev SQLite starts with seeded roles, restored demo accounts, and imported phase-1 product data

---

## Future Enhancements

### 5. ESC/POS Printing

- Direct thermal printer integration via network
- Replace browser print with local agent
- Receipt template UI

### 6. Multi-Register Support

- Enable multiple concurrent POS terminals
- Unified cash management and reporting

### 7. Online Payments

- Replace "Coming Soon" placeholder with real payment gateway
- Support Stripe, PayPal, or local credit card processor

### 8. Machine Translation

- Translate product content (labels, descriptions) between languages automatically
- Tool: HuggingFace MADLAD-400-3B-MT (Apache 2.0 license, commercial-safe)
- Approach: Batch/offline translation during data import; store in dedicated EN/LT fields
- Rationale: Avoids latency in POS/admin; runs as scheduled job

---

## Short-Term Fixes

- [ ] Create `project_codes/frontend/staticfiles/` or adjust STATICFILES_DIRS in settings to silence runtime warning
- [ ] Remove PytestConfigWarning by removing `DJANGO_SETTINGS_MODULE` from `pytest.ini` (use env var only)
- [ ] Add CI pipeline: set PYTHONPATH, run `pytest`, publish results
- [ ] Verify all tests pass in CI environment (expect 115+)

---

## Project Summary

The Kasarium POS/e-commerce system successfully implements all mandatory course requirements (FR1-FR6) and extends them with enterprise-grade features including:

- Complete CRUD operations for product management
- Multi-tier authentication and role-based access control
- Client-side and server-side data validation
- XML/XSLT reporting capabilities
- Session management with user feedback
- Responsive design with dark/light theme support
- Advanced inventory and sales tracking
- Real-time AJAX updates and search functionality
- WhatsApp-style messaging for customer communication

**Status:** Production-ready with 115 passing tests and comprehensive documentation.
