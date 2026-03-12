from __future__ import annotations


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
		"depends_on": "eval:doc.show_in_mobile_app==1",
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
		_section_break("mobile_app_classification_section", "Classification", "mobile_app_tab"),
		_app_item_field(
			"show_in_mobile_app",
			"Show in Mobile App",
			"Check",
			"mobile_app_classification_section",
			default="0",
			depends_on="",
		),
		_app_item_field(
			"product_type",
			"Product Type",
			"Select",
			"show_in_mobile_app",
			options="\nMedicine\nSupplement\nMedical Device\nPersonal Care",
		),
		_app_item_field(
			"requires_prescription",
			"Requires Prescription",
			"Check",
			"product_type",
			default="0",
		),
		_app_item_field(
			"requires_pharmacist_review",
			"Requires Pharmacist Review",
			"Check",
			"requires_prescription",
			default="0",
		),
		_column_break("mobile_app_classification_column", "requires_pharmacist_review"),
		_app_item_field(
			"nhra_registration_no",
			"NHRA Registration No",
			"Data",
			"mobile_app_classification_column",
		),
		_app_item_field(
			"regulated_price",
			"Regulated Price",
			"Currency",
			"nhra_registration_no",
		),
		_section_break("mobile_app_product_section", "Product Details", "regulated_price"),
		_app_item_field(
			"active_ingredient",
			"Active Ingredient",
			"Data",
			"mobile_app_product_section",
		),
		_app_item_field("strength", "Strength", "Data", "active_ingredient"),
		_app_item_field("form", "Form", "Data", "strength"),
		_app_item_field("pack_size", "Pack Size", "Data", "form"),
		_column_break("mobile_app_product_column", "pack_size"),
		_app_item_field(
			"refill_eligible",
			"Refill Eligible",
			"Check",
			"mobile_app_product_column",
			default="0",
		),
		_app_item_field(
			"subscription_eligible",
			"Subscription Eligible",
			"Check",
			"refill_eligible",
			default="0",
		),
		_app_item_field("min_patient_age", "Min Patient Age", "Int", "subscription_eligible"),
		_app_item_field("max_patient_age", "Max Patient Age", "Int", "min_patient_age"),
		_section_break("mobile_app_section", "App Experience", "max_patient_age"),
		_app_item_field(
			"is_hidden_in_app",
			"Is Hidden in App",
			"Check",
			"mobile_app_section",
			default="0",
		),
		_app_item_field("featured", "Featured", "Check", "is_hidden_in_app", default="0"),
		_app_item_field(
			"app_short_description",
			"App Short Description",
			"Small Text",
			"featured",
		),
		_app_item_field(
			"app_long_description",
			"App Long Description",
			"Text Editor",
			"app_short_description",
		),
		_app_item_field(
			"search_keywords",
			"Search Keywords",
			"Small Text",
			"app_long_description",
			description="Comma-separated keywords used by the mobile app catalog search.",
		),
		_app_item_field(
			"symptom_tags",
			"Symptom Tags",
			"Small Text",
			"search_keywords",
			description="Comma-separated symptom tags for app discovery and recommendations.",
		),
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
		},
		{
			"fieldname": "mobile_app_sort_order",
			"label": "Mobile App Sort Order",
			"fieldtype": "Int",
			"insert_after": "mobile_app_sf_symbol",
			"default": "0",
		},
	],
	"Mode of Payment": [
		{
			"fieldname": "is_app_payment_method",
			"label": "Is App Payment Method",
			"fieldtype": "Check",
			"insert_after": "enabled",
			"default": "0",
		},
	],
	"Sales Order": _orchestration_link_fields("mobile_app_section", "total_commission"),
	"Sales Invoice": _orchestration_link_fields("mobile_app_section", "total_commission"),
	"Delivery Note": _orchestration_link_fields("mobile_app_section", "total_commission"),
}
