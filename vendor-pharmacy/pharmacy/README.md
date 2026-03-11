# Pharmacy

Pharmacy is a Frappe app for pharmacy-specific workflows and data models.

## Structure

This repository contains the app root only:

- `config`
- `hooks.py`
- `modules.txt`
- `patches`
- `pharmacy`
- `public`
- `setup`
- `templates`
- `utils`

## Current App Order Scope

The current `App Order` implementation is an app-facing orchestration document. It is not intended to replace ERPNext `Sales Order` or `Sales Invoice`.

Implemented behavior includes:

- parent defaults for company, currency, price list, contact mobile, and delivery address
- item price lookup using ERPNext selling price logic with pricing rule evaluation
- VAT rate resolution from existing item tax setup
- row and document total calculations

## Notes

- Exchange-rate handling is intentionally kept out of the current `App Order` flow.
- Additional workflow and API behavior can be added incrementally on top of this baseline.
