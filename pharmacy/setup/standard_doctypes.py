from __future__ import annotations

SHOW_IN_APP_DEPENDS_ON = "eval:doc.show_in_mobile_app==1"
DETAILS_SECTION_DEPENDS_ON = "eval:['Medicine', 'Supplement'].includes(doc.mobile_app_product_type)"
MEDICINE_ONLY_DEPENDS_ON = "eval:doc.mobile_app_product_type=='Medicine'"


def _section_break(fieldname: str, label: str | None = None, insert_after: str | None = None) -> dict:
	field = {
		"fieldname": fieldname,
		"fieldtype": "Section Break",
	}
	if label:
		field["label"] = label
	if insert_after:
		field["insert_after"] = insert_after
	return field


def _column_break(fieldname: str, insert_after: str) -> dict:
	return {
		"fieldname": fieldname,
		"fieldtype": "Column Break",
		"insert_after": insert_after,
	}


def _app_item_field(
	fieldname: str,
	label: str,
	fieldtype: str,
	insert_after: str,
	**extra: str | int,
) -> dict:
	field = {
		"fieldname": fieldname,
		"label": label,
		"fieldtype": fieldtype,
		"insert_after": insert_after,
		"depends_on": SHOW_IN_APP_DEPENDS_ON,
	}
	field.update(extra)
	return field


def _orchestration_link_fields(section_fieldname: str, insert_after: str) -> list[dict]:
	return [
		{
			**_section_break(section_fieldname, "Mobile App", insert_after),
			"collapsible": 1,
		},
		{
			"fieldname": "app_order",
			"label": "App Order",
			"fieldtype": "Link",
			"options": "App Order",
			"insert_after": section_fieldname,
			"read_only": 1,
		},
		_column_break("mobile_app_column", "app_order"),
		{
			"fieldname": "prescription",
			"label": "Prescription",
			"fieldtype": "Link",
			"options": "Prescription",
			"insert_after": "mobile_app_column",
		},
	]


# Single source of truth for all code-managed custom fields added to standard
# ERPNext DocTypes by the Pharmacy app.
STANDARD_CUSTOM_FIELDS: dict[str, list[dict]] = {
	"Item": [
		{
			"fieldname": "mobile_app_tab",
			"label": "Mobile App",
			"fieldtype": "Tab Break",
			"insert_after": "default_item_manufacturer",
		},
		_section_break("mobile_app_visibility_section", "Visibility", "mobile_app_tab"),
		_app_item_field(
			"show_in_mobile_app",
			"Show in Mobile App",
			"Check",
			"mobile_app_visibility_section",
			default="0",
			depends_on="",
		),
		_app_item_field(
			"mobile_app_product_type",
			"Product Type",
			"Select",
			"show_in_mobile_app",
			options="\nMedicine\nSupplement\nMedical Device\nPersonal Care",
		),
		_app_item_field(
			"mobile_app_featured",
			"Featured",
			"Check",
			"mobile_app_product_type",
			default="0",
		),
		_section_break("mobile_app_section", "App Experience", "mobile_app_featured"),
		_app_item_field(
			"mobile_app_short_description",
			"Short Description",
			"Small Text",
			"mobile_app_section",
		),
		_app_item_field(
			"mobile_app_long_description",
			"Long Description",
			"Text Editor",
			"mobile_app_short_description",
		),
		_app_item_field(
			"mobile_app_search_keywords",
			"Search Keywords",
			"Small Text",
			"mobile_app_long_description",
			description="Comma-separated keywords used by the mobile app catalog search.",
		),
		_app_item_field(
			"mobile_app_symptom_tags",
			"Symptom Tags",
			"Small Text",
			"mobile_app_search_keywords",
			description="Comma-separated symptom tags for app discovery and recommendations.",
			depends_on=DETAILS_SECTION_DEPENDS_ON,
		),
		{
			**_section_break("mobile_app_product_section", "Details", "mobile_app_product_type"),
			"depends_on": DETAILS_SECTION_DEPENDS_ON,
		},
		_app_item_field(
			"requires_prescription",
			"Requires Prescription",
			"Check",
			"mobile_app_product_section",
			default="0",
			depends_on=MEDICINE_ONLY_DEPENDS_ON,
		),
		_app_item_field(
			"requires_pharmacist_review",
			"Requires Pharmacist Review",
			"Check",
			"requires_prescription",
			default="0",
			depends_on=MEDICINE_ONLY_DEPENDS_ON,
		),
		_app_item_field(
			"nhra_registration_no",
			"NHRA Registration No",
			"Data",
			"requires_pharmacist_review",
			depends_on=DETAILS_SECTION_DEPENDS_ON,
		),
		_app_item_field(
			"regulated_price",
			"Regulated Price",
			"Currency",
			"nhra_registration_no",
			depends_on=DETAILS_SECTION_DEPENDS_ON,
		),
		_app_item_field(
			"active_ingredients",
			"Active Ingredients",
			"Data",
			"regulated_price",
			depends_on=DETAILS_SECTION_DEPENDS_ON,
		),
		_app_item_field("strength", "Strength", "Data", "active_ingredients", depends_on=DETAILS_SECTION_DEPENDS_ON),
		_app_item_field("form", "Form", "Data", "strength", depends_on=DETAILS_SECTION_DEPENDS_ON),
		_app_item_field("pack_size", "Pack Size", "Data", "form", depends_on=DETAILS_SECTION_DEPENDS_ON),
		_app_item_field("manufacturer", "Manufacturer", "Data", "pack_size", depends_on=DETAILS_SECTION_DEPENDS_ON),
		_column_break("mobile_app_details_column", "manufacturer"),
		_app_item_field(
			"min_patient_age",
			"Min Patient Age",
			"Int",
			"mobile_app_details_column",
			depends_on=DETAILS_SECTION_DEPENDS_ON,
		),
		_app_item_field("max_patient_age", "Max Patient Age", "Int", "min_patient_age", depends_on=DETAILS_SECTION_DEPENDS_ON),
	],
	"Item Group": [
		{
			"fieldname": "mobile_app_section",
			"label": "Mobile App",
			"fieldtype": "Section Break",
			"insert_after": "image",
		},
		{
			"fieldname": "show_in_mobile_app",
			"label": "Show in Mobile App",
			"fieldtype": "Check",
			"insert_after": "mobile_app_section",
			"default": "0",
		},
		{
			"fieldname": "mobile_app_sf_symbol",
			"label": "Mobile App Icon",
			"fieldtype": "Data",
			"insert_after": "show_in_mobile_app",
			"depends_on": SHOW_IN_APP_DEPENDS_ON,
		},
		{
			"fieldname": "mobile_app_sort_order",
			"label": "Mobile App Sort Order",
			"fieldtype": "Int",
			"insert_after": "mobile_app_sf_symbol",
			"default": "0",
			"depends_on": SHOW_IN_APP_DEPENDS_ON,
		},
	],
	"Mode of Payment": [
		{
			"fieldname": "show_in_mobile_app",
			"label": "Show in Mobile App",
			"fieldtype": "Check",
			"insert_after": "enabled",
			"default": "0",
		},
	],
	"Sales Order": _orchestration_link_fields("mobile_app_section", "total_commission"),
	"Sales Invoice": _orchestration_link_fields("mobile_app_section", "total_commission"),
	"Delivery Note": _orchestration_link_fields("mobile_app_section", "total_commission"),
}
