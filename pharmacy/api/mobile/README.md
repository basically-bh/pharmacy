# Pharmacy Mobile API

## Bench execute examples

```bash
bench --site <site> execute pharmacy.api.mobile.auth.send_otp --kwargs '{"mobile_no": "+97312345678"}'
bench --site <site> execute pharmacy.api.mobile.auth.verify_otp --kwargs '{"mobile_no": "+97312345678", "otp": "123456"}'
bench --site <site> execute pharmacy.api.mobile.auth.me
bench --site <site> execute pharmacy.api.mobile.auth.logout
bench --site <site> execute pharmacy.api.mobile.profile.get_profile
bench --site <site> execute pharmacy.api.mobile.catalog.list_products --kwargs '{"page": 1, "page_size": 5}'
bench --site <site> execute pharmacy.api.mobile.catalog.get_product --kwargs '{"product_id": "ITEM-0001"}'
bench --site <site> execute pharmacy.api.mobile.prescription.list_prescriptions --kwargs '{"page": 1, "page_size": 5}'
bench --site <site> execute pharmacy.api.mobile.prescription.get_prescription --kwargs '{"prescription_id": "RX-2026-0001"}'
bench --site <site> execute pharmacy.api.mobile.order.list_orders --kwargs '{"page": 1, "page_size": 5}'
bench --site <site> execute pharmacy.api.mobile.order.get_order --kwargs '{"order_id": "APP-ORD-0001"}'
bench --site <site> execute pharmacy.api.mobile.order.get_cart
bench --site <site> execute pharmacy.api.mobile.order.add_item_to_cart --kwargs '{"item_code": "100103", "qty": 1}'
bench --site <site> execute pharmacy.api.mobile.order.update_cart_item_qty --kwargs '{"item_code": "100103", "qty": 2}'
bench --site <site> execute pharmacy.api.mobile.order.remove_item_from_cart --kwargs '{"item_code": "100103"}'
bench --site <site> execute pharmacy.api.mobile.order.checkout_cart
```

## Authentication payloads

`send_otp`

```json
{
  "mobile_no": "+97312345678"
}
```

```json
{
  "success": true,
  "otp_sent": true,
  "expires_in_seconds": 600,
  "masked_mobile_no": "*******5678"
}
```

`verify_otp`

```json
{
  "mobile_no": "+97312345678",
  "otp": "123456",
  "platform": "ios",
  "device_name": "iPhone 17",
  "app_version": "1.0.0"
}
```

```json
{
  "access_token": "<token>",
  "token_type": "Bearer",
  "expires_at": "2026-04-11 17:15:00",
  "expires_in_seconds": 2592000,
  "user": {
    "user_id": "mobile@example.com",
    "profile_id": "mobile@example.com",
    "customer_id": "CUST-0001",
    "customer_name": "Mobile Auth",
    "national_id": "1234567890",
    "mobile_no": "+97312345678",
    "full_name": "Mobile Auth",
    "email": "mobile@example.com"
  }
}
```
