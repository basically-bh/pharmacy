## v0.6.0
Mobile API foundation for the Basically mobile app.

This release introduces the **mobile API layer for the Basically platform** built on top of ERPNext.

The pharmacy app now exposes a structured mobile API supporting authentication, customer profile management, product catalog access, cart management, checkout, and order retrieval. This release establishes the backend foundation for the Basically iOS application.

---

## Mobile Authentication

Implemented a secure OTP-based mobile authentication system.

Features:
- OTP request endpoint
- OTP verification endpoint
- bearer access token issuance
- token expiration handling
- logout endpoint

### Authentication Endpoints

- `send_otp`
- `verify_otp`
- `me`
- `logout`

Mobile access tokens are stored in the `Mobile Access Token` doctype and validated through a bearer authentication hook.

---

## Mobile User System

Introduced a dedicated mobile user model separate from ERPNext website users.

### New Doctypes

- `Mobile App User`
- `Mobile OTP Request`
- `Mobile Access Token`

Features:
- mobile number identity
- OTP verification status
- token lifecycle management
- link to ERPNext Customer created during checkout

---

## Customer Profile API

Mobile users can retrieve and update their profile information.

### Endpoints

- `get_mobile_app_user_profile`
- `update_mobile_app_user_profile`

Supported fields include:

- first name
- last name
- national ID
- date of birth
- mobile number

---

## Address Management API

Mobile users can manage delivery addresses.

### Endpoints

- `create_address`
- `get_addresses`
- `set_default_address`

Addresses are stored using ERPNext's native `Address` doctype.

---

## Product Catalog API

Introduced a mobile-friendly catalog API.

### Endpoints

- `get_products`
- `get_product`

Product detail response includes:

- item code
- product name
- item group
- image URL
- pricing information
- prescription requirement flags

Medical product data:

- active ingredients
- strength
- dosage form
- pack size
- NHRA registration number

Additional product metadata:

- brand
- manufacturer
- country of origin

This API replaces reliance on ERPNext Website Item for mobile catalog use.

---

## Cart API

Implemented a mobile cart system backed by ERPNext.

### Endpoints

- `get_cart`
- `add_item_to_cart`
- `update_cart_item_qty`
- `remove_item_from_cart`

Features:

- draft cart creation
- item quantity updates
- backend-driven cart totals

---

## Checkout API

Implemented checkout flow integrated with ERPNext sales workflow.

### Endpoint

- `checkout_cart`

Checkout behavior:

- creates a Sales Order
- links Mobile App User to Customer
- creates Customer automatically if none exists
- assigns delivery address
- transfers cart items into order lines

---

## Orders API

Mobile users can retrieve order history and order details.

### Endpoints

- `list_orders`
- `get_order`

Features:

- order summaries
- order line items
- pricing breakdown
- order timestamps
- consistent order reference numbers

---

## Architecture Improvements

### Mobile API Structure

Introduced a dedicated mobile API module:
pharmacy.api.mobileModules include:

- auth
- profile
- address
- catalog
- order

### Service Layer

Business logic moved into service modules:
Examples:

- `auth_service.py`
- `cart_service.py`
- `order_service.py`
- `mobile_app_user_service.py`

This separation keeps API controllers lightweight and isolates domain logic.

---

## Stability Fixes

Resolved several integration issues discovered during mobile app development:

- bearer token authentication context resolution
- OTP hash validation with Frappe password fields
- token hash uniqueness conflicts
- mobile user context resolution across services
- cart ownership resolution
- product detail API shape consistency

---

## Notes

This release establishes the **backend foundation for the Basically mobile commerce platform**.

Future backend work will focus on:

- delivery fee calculation
- inventory availability APIs
- prescription upload workflow
- pharmacist review workflow
- order status lifecycle
- notification system