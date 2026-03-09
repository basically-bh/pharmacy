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


def _pharmacy_item_field(
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
		"depends_on": "eval:doc.is_pharmacy_item==1",
	}
	field.update(extra)
	return field


def _orchestration_link_fields(section_fieldname: str, insert_after: str) -> list[dict]:
	return [
		_section_break(section_fieldname, "Pharmacy", insert_after),
		{
			"fieldname": "app_order",
			"label": "App Order",
			"fieldtype": "Link",
			"options": "App Order",
			"insert_after": section_fieldname,
		},
		{
			"fieldname": "prescription",
			"label": "Prescription",
			"fieldtype": "Link",
			"options": "Prescription",
			"insert_after": "app_order",
		},
	]


# Single source of truth for all code-managed custom fields added to standard
# ERPNext DocTypes by the Pharmacy app.
STANDARD_CUSTOM_FIELDS: dict[str, list[dict]] = {
	"Item": [
		{
			"fieldname": "basically_tab",
			"label": "Basically",
			"fieldtype": "Tab Break",
			"insert_after": "default_item_manufacturer",
		},
		_section_break("basically_classification_section", "Classification", "basically_tab"),
		_pharmacy_item_field(
			"is_pharmacy_item",
			"Is Pharmacy Item",
			"Check",
			"basically_classification_section",
			default="0",
			depends_on="",
		),
		_pharmacy_item_field(
			"product_type",
			"Product Type",
			"Select",
			"is_pharmacy_item",
			options="\nMedicine\nSupplement\nMedical Device\nPersonal Care",
		),
		_pharmacy_item_field(
			"requires_prescription",
			"Requires Prescription",
			"Check",
			"product_type",
			default="0",
		),
		_pharmacy_item_field(
			"requires_pharmacist_review",
			"Requires Pharmacist Review",
			"Check",
			"requires_prescription",
			default="0",
		),
		_column_break("basically_classification_column", "requires_pharmacist_review"),
		_pharmacy_item_field(
			"nhra_registration_no",
			"NHRA Registration No",
			"Data",
			"basically_classification_column",
		),
		_pharmacy_item_field(
			"regulated_price",
			"Regulated Price",
			"Currency",
			"nhra_registration_no",
		),
		_section_break("basically_product_section", "Product Details", "regulated_price"),
		_pharmacy_item_field(
			"active_ingredient",
			"Active Ingredient",
			"Data",
			"basically_product_section",
		),
		_pharmacy_item_field("strength", "Strength", "Data", "active_ingredient"),
		_pharmacy_item_field("form", "Form", "Data", "strength"),
		_pharmacy_item_field("pack_size", "Pack Size", "Data", "form"),
		_column_break("basically_product_column", "pack_size"),
		_pharmacy_item_field(
			"refill_eligible",
			"Refill Eligible",
			"Check",
			"basically_product_column",
			default="0",
		),
		_pharmacy_item_field(
			"subscription_eligible",
			"Subscription Eligible",
			"Check",
			"refill_eligible",
			default="0",
		),
		_pharmacy_item_field("min_patient_age", "Min Patient Age", "Int", "subscription_eligible"),
		_pharmacy_item_field("max_patient_age", "Max Patient Age", "Int", "min_patient_age"),
		_section_break("basically_app_section", "App Experience", "max_patient_age"),
		_pharmacy_item_field(
			"is_hidden_in_app",
			"Is Hidden in App",
			"Check",
			"basically_app_section",
			default="0",
		),
		_pharmacy_item_field("featured", "Featured", "Check", "is_hidden_in_app", default="0"),
		_pharmacy_item_field("sort_order", "Sort Order", "Int", "featured", default="0"),
		_column_break("basically_app_column", "sort_order"),
		_pharmacy_item_field(
			"app_short_description",
			"App Short Description",
			"Small Text",
			"basically_app_column",
		),
		_pharmacy_item_field(
			"app_long_description",
			"App Long Description",
			"Text Editor",
			"app_short_description",
		),
		_pharmacy_item_field(
			"search_keywords",
			"Search Keywords",
			"Small Text",
			"app_long_description",
			description="Comma-separated keywords used by the mobile app catalog search.",
		),
		_pharmacy_item_field(
			"symptom_tags",
			"Symptom Tags",
			"Small Text",
			"search_keywords",
			description="Comma-separated symptom tags for app discovery and recommendations.",
		),
	],
	"Sales Order": _orchestration_link_fields("pharmacy_section", "additional_info_section"),
	"Sales Invoice": _orchestration_link_fields("pharmacy_section", "more_information"),
	"Delivery Note": _orchestration_link_fields("pharmacy_section", "more_info"),
}
