# Pharmacy Mobile API

## Bench execute examples

```bash
bench --site <site> execute pharmacy.api.mobile.profile.get_profile
bench --site <site> execute pharmacy.api.mobile.catalog.list_products --kwargs '{"page": 1, "page_size": 5}'
bench --site <site> execute pharmacy.api.mobile.catalog.get_product --kwargs '{"product_id": "ITEM-0001"}'
bench --site <site> execute pharmacy.api.mobile.prescription.list_prescriptions --kwargs '{"page": 1, "page_size": 5}'
bench --site <site> execute pharmacy.api.mobile.prescription.get_prescription --kwargs '{"prescription_id": "RX-2026-0001"}'
bench --site <site> execute pharmacy.api.mobile.order.list_orders --kwargs '{"page": 1, "page_size": 5}'
bench --site <site> execute pharmacy.api.mobile.order.get_order --kwargs '{"order_id": "APP-ORD-0001"}'
bench --site <site> execute pharmacy.api.mobile.order.get_cart
bench --site <site> execute pharmacy.api.mobile.order.create_or_get_cart
bench --site <site> execute pharmacy.api.mobile.order.add_item_to_cart --kwargs '{"item_code": "100103", "qty": 1}'
bench --site <site> execute pharmacy.api.mobile.order.update_cart_item_qty --kwargs '{"item_code": "100103", "qty": 2}'
bench --site <site> execute pharmacy.api.mobile.order.remove_item_from_cart --kwargs '{"item_code": "100103"}'
bench --site <site> execute pharmacy.api.mobile.order.checkout_cart
```
