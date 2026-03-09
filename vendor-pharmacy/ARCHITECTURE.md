# Pharmacy Architecture

## Core entities

- `User`: native ERPNext identity and authentication record.
- `Customer Profile`: Pharmacy app-specific extension layer linked to `User`.
- `Customer`: native ERPNext commercial entity used when transactions enter ERP flows.
- `Contact`: native ERPNext communication/person record; the Pharmacy app does not create a parallel custom contact layer.

## Lifecycle

1. `User` is created first during signup or onboarding.
2. `Customer Profile` can be created next and may exist before any transaction.
3. `Customer` is created lazily when the user first transacts.

Because of that lifecycle:

- `Customer Profile.user` is required.
- `Customer Profile.customer` is optional until the first transaction.
- transactional documents should primarily anchor on `customer_profile`, then carry `customer` only when it exists.

## App Order role

`App Order` is an orchestration document for the mobile app and Pharmacy workflow. It is not the final ERP accounting or fulfillment document.

Current downstream target flow:

`App Order -> Sales Order -> Sales Invoice -> Delivery Note`

Pricing, totals, and ERP document creation logic are intentionally deferred until after the model foundation is stable.
