# Pharmacy

Pharmacy is the ERPNext backend layer for the Basically Pharmacy mobile app.

This app currently provides:

- custom Pharmacy DocTypes and workspace structure
- app-owned `Customer Profile` extension data
- standard ERPNext custom fields managed from app code
- `App Order` orchestration for app-originated order intake ahead of ERP sales documents

## App Order

`App Order` is an app-facing orchestration document. It is not intended to replace ERPNext `Sales Order` or `Sales Invoice`.

Current behavior includes:

- parent defaults for `company`, `currency`, and `price_list`
- customer-context sync from `Customer Profile`
- server-side item pricing refresh
- VAT rate resolution from the item tax setup / item tax template path
- server-side row totals and document totals

### Pricing behavior

Pricing is intentionally aligned with ERPNext sales behavior without turning `App Order` into a fake full sales transaction.

The current pricing flow uses:

- ERPNext `get_price_list_rate(...)` for base selling price lookup from `Item Price`
- ERPNext `get_pricing_rule_for_item(...)` for pricing-rule adjustments

This keeps the pricing path closer to `Sales Order` / `Sales Invoice` behavior while avoiding the heavier full `get_item_details(...)` orchestration path, which expects a more complete sales-document context.

### VAT behavior

VAT on `App Order Item` is resolved from the item's existing ERPNext tax setup.

The app first attempts to derive the effective rate from the item's assigned `Item Tax Template`, using ERPNext's tax-template helpers. If no template-based rate is found, it falls back to the pharmacy app's existing VAT utility behavior.

### Totals

The following values are computed server-side:

- `App Order Item.amount = qty * rate`
- `App Order Item.vat_amount = amount * vat_rate / 100`
- `App Order Item.total_amount = amount + vat_amount`
- `App Order.subtotal = sum(amount)`
- `App Order.tax_amount = sum(vat_amount)`
- `App Order.grand_total = sum(total_amount)`

Client-side form code is limited to triggering recalculation for usability. The source of truth remains the server-side document logic.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the current developer-facing data model and flow boundaries.
