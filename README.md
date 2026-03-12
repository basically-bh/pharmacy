# Pharmacy

Pharmacy is a Frappe app for pharmacy-specific workflows and data models.

## Structure

This app follows the standard Frappe layout:

- `pyproject.toml`
- `README.md`
- `setup.py`
- `requirements.txt`
- `pharmacy/hooks.py`
- `pharmacy/modules.txt`
- `pharmacy/config/`
- `pharmacy/public/`
- `pharmacy/setup/`
- `pharmacy/templates/`
- `pharmacy/utils/`
- `pharmacy/api/`
- `pharmacy/services/`
- `pharmacy/pharmacy/doctype/`
- `pharmacy/pharmacy/workspace/`

## Notes

- `App Order` is an app-facing orchestration document and does not replace ERPNext `Sales Order` or `Sales Invoice`.
- Mobile API implementation lives under `pharmacy/api/mobile/`.
