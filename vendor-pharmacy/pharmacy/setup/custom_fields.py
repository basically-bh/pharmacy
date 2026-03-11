from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

PHARMACY_MODULE = "Pharmacy"


def apply_custom_fields(custom_fields: dict[str, list[dict]]) -> None:
	"""Create or update the app-managed custom fields for standard DocTypes.

	This wrapper keeps field definitions in code and makes repeated runs safe.
	`create_custom_fields(..., update=True)` handles the primary idempotent sync,
	and we then enforce `module = "Pharmacy"` explicitly for every managed field.
	"""
	normalized_fields = _normalize_custom_fields(custom_fields)

	create_custom_fields(normalized_fields, ignore_validate=True, update=True)
	_sync_managed_field_metadata(normalized_fields)
	_migrate_legacy_custom_fields()

	frappe.clear_cache()
	frappe.db.commit()


def _normalize_custom_fields(custom_fields: dict[str, list[dict]]) -> dict[str, list[dict]]:
	"""Apply app defaults and validate the managed field definitions."""
	normalized_fields: dict[str, list[dict]] = {}

	for doctype, field_definitions in custom_fields.items():
		normalized_fields[doctype] = []

		for field_definition in field_definitions:
			_validate_field_definition(doctype, field_definition)

			normalized_definition = {"module": PHARMACY_MODULE, **field_definition}
			normalized_fields[doctype].append(normalized_definition)

	return normalized_fields


def _validate_field_definition(doctype: str, field_definition: dict) -> None:
	"""Guard rails for code-managed fields we want to keep consistent."""
	fieldname = field_definition.get("fieldname")
	if not fieldname:
		raise ValueError(f"Missing fieldname in custom field definition for {doctype}.")

	if fieldname.startswith("custom_"):
		raise ValueError(
			f"Custom field {doctype}.{fieldname} uses the reserved 'custom_' prefix. "
			"Pharmacy-managed fields must use stable code-defined fieldnames."
		)


def _sync_managed_field_metadata(custom_fields: dict[str, list[dict]]) -> None:
	"""Update managed properties on existing Custom Field records in place.

	This is intentionally limited to the keys defined in code so reruns stay safe
	and user-managed properties outside the installer contract are left alone.
	"""
	for doctype, field_definitions in custom_fields.items():
		for field_definition in field_definitions:
			custom_field_name = f"{doctype}-{field_definition['fieldname']}"
			if not frappe.db.exists("Custom Field", custom_field_name):
				continue

			custom_field = frappe.get_doc("Custom Field", custom_field_name)
			has_changes = False

			for key, value in field_definition.items():
				if custom_field.get(key) != value:
					custom_field.set(key, value)
					has_changes = True

			if not has_changes:
				continue

			custom_field.flags.ignore_validate = True
			custom_field.flags.ignore_permissions = True
			custom_field.save()


def _migrate_legacy_custom_fields() -> None:
	"""Handle one-time renames/removals for app-managed custom fields."""
	_migrate_item_app_flag()
	_remove_legacy_item_layout_fields()
	_remove_legacy_selling_layout_fields()


def _migrate_item_app_flag() -> None:
	"""Rename the Item mobile toggle into the current add_to_mobile_app field."""
	legacy_field = "Item-is_pharmacy_item"
	previous_field = "Item-is_app_item"
	current_field = "Item-add_to_mobile_app"

	if frappe.db.exists("Custom Field", current_field):
		if frappe.db.exists("Custom Field", legacy_field):
			frappe.db.sql(
				"""
				update `tabItem`
				set add_to_mobile_app = is_pharmacy_item
				where ifnull(is_pharmacy_item, 0) != 0
				  and ifnull(add_to_mobile_app, 0) = 0
				"""
			)

		if frappe.db.exists("Custom Field", previous_field):
			frappe.db.sql(
				"""
				update `tabItem`
				set add_to_mobile_app = is_app_item
				where ifnull(is_app_item, 0) != 0
				  and ifnull(add_to_mobile_app, 0) = 0
				"""
			)

	for field_name in (legacy_field, previous_field):
		if not frappe.db.exists("Custom Field", field_name):
			continue

		frappe.delete_doc("Custom Field", field_name, force=1, ignore_missing=True)


def _remove_legacy_item_layout_fields() -> None:
	legacy_fieldnames = [
		"basically_tab",
		"basically_classification_section",
		"basically_classification_column",
		"basically_product_section",
		"basically_product_column",
		"basically_app_section",
		"basically_app_column",
	]
	for fieldname in legacy_fieldnames:
		custom_field_name = f"Item-{fieldname}"
		if not frappe.db.exists("Custom Field", custom_field_name):
			continue

		frappe.delete_doc("Custom Field", custom_field_name, force=1, ignore_missing=True)


def _remove_legacy_selling_layout_fields() -> None:
	for doctype in ("Sales Order", "Sales Invoice", "Delivery Note"):
		for fieldname in ("pharmacy_section", "pharmacy_order"):
			custom_field_name = f"{doctype}-{fieldname}"
			if not frappe.db.exists("Custom Field", custom_field_name):
				continue

			frappe.delete_doc("Custom Field", custom_field_name, force=1, ignore_missing=True)
