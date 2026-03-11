# Pharmacy

Pharmacy is a Frappe app for pharmacy-specific workflows and data models.

## Structure

This app follows the standard Frappe layout:

- `pharmacy/hooks.py`
- `pharmacy/modules.txt`
- `pharmacy/patches.txt`
- `pharmacy/config/`
- `pharmacy/public/`
- `pharmacy/setup/`
- `pharmacy/templates/`
- `pharmacy/utils/`
- `pharmacy/pharmacy/doctype/`
- `pharmacy/pharmacy/workspace/`

## Notes

- `App Order` is an app-facing orchestration document and does not replace ERPNext `Sales Order` or `Sales Invoice`.
- Mobile API handlers live under `pharmacy/api/mobile/`.
