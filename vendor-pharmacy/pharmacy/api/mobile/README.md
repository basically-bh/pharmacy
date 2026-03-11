# Mobile API Test Guide

Use these read-only calls to smoke-test the mobile API layer locally before wiring the app.

## Bench execute

Replace `<site>` with your Frappe site name and update IDs to records owned by the logged-in user.

```bash
bench --site <site> execute pharmacy.api.mobile.profile.get_profile
bench --site <site> execute pharmacy.api.mobile.catalog.list_products --kwargs '{"page": 1, "page_size": 5}'
bench --site <site> execute pharmacy.api.mobile.catalog.get_product --kwargs '{"product_id": "ITEM-0001"}'
bench --site <site> execute pharmacy.api.mobile.prescription.list_prescriptions --kwargs '{"page": 1, "page_size": 5}'
bench --site <site> execute pharmacy.api.mobile.prescription.get_prescription --kwargs '{"prescription_id": "RX-2026-0001"}'
bench --site <site> execute pharmacy.api.mobile.order.list_orders --kwargs '{"page": 1, "page_size": 5}'
bench --site <site> execute pharmacy.api.mobile.order.get_order --kwargs '{"order_id": "APP-ORD-0001"}'
```

## HTTP examples

Use an authenticated session or API key/token pair.

```bash
curl -X GET "https://<host>/api/method/pharmacy.api.mobile.profile.get_profile" \
  -H "Authorization: token <api_key>:<api_secret>"

curl -X GET "https://<host>/api/method/pharmacy.api.mobile.catalog.list_products?page=1&page_size=5&featured=1" \
  -H "Authorization: token <api_key>:<api_secret>"

curl -X GET "https://<host>/api/method/pharmacy.api.mobile.catalog.get_product?product_id=ITEM-0001" \
  -H "Authorization: token <api_key>:<api_secret>"

curl -X GET "https://<host>/api/method/pharmacy.api.mobile.prescription.list_prescriptions?page=1&page_size=5&status=Validated" \
  -H "Authorization: token <api_key>:<api_secret>"

curl -X GET "https://<host>/api/method/pharmacy.api.mobile.prescription.get_prescription?prescription_id=RX-2026-0001" \
  -H "Authorization: token <api_key>:<api_secret>"

curl -X GET "https://<host>/api/method/pharmacy.api.mobile.order.list_orders?page=1&page_size=5&status=Pending%20Fulfillment" \
  -H "Authorization: token <api_key>:<api_secret>"

curl -X GET "https://<host>/api/method/pharmacy.api.mobile.order.get_order?order_id=APP-ORD-0001" \
  -H "Authorization: token <api_key>:<api_secret>"
```

## Expected error shape

All hardened read endpoints now return the same error envelope:

```json
{
  "error": {
    "code": "invalid_input",
    "message": "page_size cannot be greater than 100.",
    "details": {
      "field": "page_size",
      "max_value": 100
    }
  }
}
```
