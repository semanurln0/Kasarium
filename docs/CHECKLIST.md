# Checklist

## Shopping, Cart, and Checkout

- [X] Require login before checkout and support saved profile address and invoice data.
- [X] Cart remove works directly and the cart updates automatically without a manual update button.
- [X] Shop page shows list/table view options and sort controls.
- [X] Shop banners show working hours at the top and company contact details at the bottom.
- [X] Checkout warns when an order is placed outside working hours and lets the customer confirm anyway.
- [X] Customers can cancel only pending orders; preparing orders cannot be cancelled.
- [X] Product detail, cart, and order history keep the key product fields visible: name, sales description, expiration, barcode, quantity, and price.
- [X] The back-to-shop flow keeps the previous search, sort, and page filters.
- [X] Shop and related lists support quick page jumps.
- [X] Staff and customers see the correct navigation for their role.
- [X] Cart visibility is adjusted for staff and admin views so they do not see shop-only cart UI.
- [X] Order history and order detail show the right status-based controls.
- [ ] Refunds system should be improved (no option for choosing only one item from sale? maybe can be shown receipt once again and it can be refunding from seleccting in there)

## Products and Inventory

- [X] Admin and staff can filter orders by status, payment, and date.
- [X] Expiration control supports sorting by name or nearest expiry.
- [X] Expiration dates are color coded so expired and soon-to-expire items stand out.
- [X] Product control supports sorting plus import/export.
- [X] Edit product includes expiration editing, discounts, product image upload and camera support, stock count, and country selection.
- [X] Discount support works in two modes: percentage and explicit discounted price.
- [X] Product image support works for URL, base64, file upload, and camera capture.
- [X] Expiration data is consistent between expiry control and the shop and product control views.
- [X] Product images, discounts, and expiration values are preserved in the main shop views.

## Messages and Notifications

- [X] Popup notifications for pending orders and unread messages are implemented, and badge counts remain visible in the navigation.
- [X] Customers can reply to incoming messages from the message list.
- [X] Messages are hidden per side instead of being deleted globally, so customer deletes do not remove staff or admin history and vice versa.
- [X] Admin and staff can send new messages to customers.
- [X] Customer replies and admin replies both stay visible in the same message thread.
- [X] Dark-mode success and notification text stays readable.
- [X] Message delete actions only hide items for the current side.
- [ ] Email notifications for password reset, order updates, and messaging updates.
- [ ] Dedicated contact page with external form provider integration.

## Accounts and Access

- [X] Admin can delete users.
- [X] New registrations default to the Customer role.
- [X] All users can change their password in their profile.
- [X] Forgot-password entry point exists on the login screen.
- [X] Address forms are detailed, with separate fields for street, city, postal code, and related data.
- [X] Settings page is accessible and editable by admin and staff.
- [X] Admin, staff, and customer navigation visibility is role based.
- [X] Staff and admin users are blocked from customer-only shop flows.
- [X] User-facing profile and access flows work with the restored local dev setup.

## User-Reported Fixes Already Applied

- [X] Dark mode contrast was improved and logout text is readable.
- [X] Flying cart shows the actual cart contents instead of only a count.
- [X] Expiration dates are visible in the shop, cart, and order views.
- [X] Returning from product detail preserves the previous shop filters.
- [X] The top-level launcher and local dev workflow are working.
- [X] Clickable footer and banner contact links launch phone and map targets.
- [X] The checkout invoice and saved shipping flows are wired up.

## Planned or Optional

- [ ] Maybe add a courier page.

> ## Release and Pre-Deployment

- [X] All tests pass: `pytest` -> 115 passed.
- [X] Django system check passes: `python project_codes/django/manage.py check --settings=kasarium.settings.dev`.
- [X] HOMEWORK.md was updated when roadmap items changed.
- [X] P2_main_project.py --check passes in local dev.
- [X] run.py --check passes in local dev.
- [X] Local SQLite dev database starts cleanly with seeded roles, demo users, and imported phase-1 products.
- [ ] `project_codes/frontend/staticfiles/` exists or `STATICFILES_DIRS` is configured.
- [ ] Render environment variables are set correctly.
- [ ] Database migrations are applied on deployment.
- [ ] A production superuser account is created.
- [ ] SSL certificate is active in production.
- [ ] Tag the release commit.
- [ ] Create GitHub release notes.
- [ ] Notify the team and customers of availability.
