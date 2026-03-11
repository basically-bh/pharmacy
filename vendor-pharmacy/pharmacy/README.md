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
- `pharmacy/api/` as stable public whitelisted entrypoints
- `pharmacy/services/` as compatibility imports for existing runtime paths
- `pharmacy/pharmacy/doctype/`
- `pharmacy/pharmacy/api/`
- `pharmacy/pharmacy/services/`
- `pharmacy/pharmacy/workspace/`

## Notes

- `App Order` is an app-facing orchestration document and does not replace ERPNext `Sales Order` or `Sales Invoice`.
- Mobile API implementation lives under `pharmacy/pharmacy/api/mobile/`.
- Legacy method paths under `pharmacy/api/mobile/` are preserved as compatibility exports.
