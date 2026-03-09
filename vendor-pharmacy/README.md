# Pharmacy

Pharmacy is the ERPNext backend layer for the Basically Pharmacy mobile app.

This repository currently focuses on the application foundation:

- custom Pharmacy DocTypes and workspace structure
- app-owned `Customer Profile` extension data
- standard ERPNext custom fields managed from app code

Business logic such as pricing, totals, and checkout orchestration is intentionally deferred until after the model foundation is stabilized.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the current developer-facing data model and flow boundaries.
