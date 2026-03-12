from __future__ import annotations

import frappe
from frappe import _

from pharmacy.services.mobile_service import (
	build_list_response,
	cbool,
	get_request_value,
	parse_pagination,
	raise_invalid_input,
	raise_not_found,
)

PRODUCT_FIELDS = [
	"name",
	"item_name",
	"item_group",
	"image",
	"description",
	"stock_uom",
	"disabled",
	"show_in_mobile_app",
	"product_type",
	"requires_prescription",
	"requires_pharmacist_review",
	"nhra_registration_no",
	"regulated_price",
	"active_ingredient",
	"strength",
	"form",
	"pack_size",
	"refill_eligible",
	"subscription_eligible",
	"min_patient_age",
	"max_patient_age",
	"featured",
	"sort_order",
	"app_short_description",
	"app_long_description",
	"search_keywords",
	"symptom_tags",
]


def list_product_data(
	*,
	search: str | None = None,
	page: int | str = 1,
	page_size: int | str = 20,
	product_type: str | None = None,
	featured: int | str | None = None,
) -> dict:
	page_number, size, offset = parse_pagination(page, page_size)
	filters = {
		"show_in_mobile_app": 1,
		"disabled": 0,
		"is_hidden_in_app": 0,
	}
	if product_type:
		filters["product_type"] = product_type
	if featured is not None and str(featured) != "":
		if str(featured).strip().lower() not in {"0", "1", "true", "false", "yes", "no", "on", "off"}:
			raise_invalid_input(
				message=_("featured must be a boolean-like value."),
				details={"field": "featured", "value": featured},
			)
		filters["featured"] = 1 if cbool(featured) else 0

	search_value = (search or "").strip()
	or_filters = None
	if search_value:
		like_value = f"%{search_value}%"
		or_filters = [
			["Item", "name", "like", like_value],
			["Item", "item_name", "like", like_value],
			["Item", "app_short_description", "like", like_value],
			["Item", "search_keywords", "like", like_value],
			["Item", "symptom_tags", "like", like_value],
		]

	products = frappe.get_all(
		"Item",
		fields=PRODUCT_FIELDS,
		filters=filters,
		or_filters=or_filters,
		order_by="featured desc, sort_order asc, item_name asc",
		limit_start=offset,
		limit_page_length=size,
	)
	total_count = _get_product_count(filters=filters, or_filters=or_filters)
	price_context = _get_price_context()
	price_map = _get_price_map([row.name for row in products], price_context.price_list)
	item_groups = _get_mobile_item_groups()

	items = [
		serialize_product_summary(row, price_context=price_context, price_map=price_map)
		for row in products
	]
	response = build_list_response(
		items=items,
		page=page_number,
		page_size=size,
		total_count=total_count,
	)
	# Mobile app navigation now sources categories from Item Group metadata,
	# while product_type remains in the payload for backward compatibility.
	response["item_groups"] = item_groups
	return response


def get_product_data(product_id: str | None = None) -> dict:
	product_name = (product_id or get_request_value("product_id", aliases=("id",)) or "").strip()
	if not product_name:
		raise_invalid_input(
			message=_("product_id is required."),
			details={"field": "product_id"},
		)

	product = frappe.db.get_value(
		"Item",
		{
			"name": product_name,
			"show_in_mobile_app": 1,
			"disabled": 0,
			"is_hidden_in_app": 0,
		},
		PRODUCT_FIELDS,
		as_dict=True,
	)
	if not product:
		raise_not_found(resource_name="Product", resource_id=product_name)

	price_context = _get_price_context()
	price_map = _get_price_map([product.name], price_context.price_list)
	return {
		"product": serialize_product_detail(
			product,
			price_context=price_context,
			price_map=price_map,
		)
	}


def serialize_product_summary(
	product: frappe._dict,
	*,
	price_context: frappe._dict,
	price_map: dict[str, frappe._dict],
) -> dict:
	price = price_map.get(product.name)
	return {
		"id": product.name,
		"name": product.item_name or product.name,
		"item_group": product.item_group or None,
		"short_description": product.app_short_description or product.description or None,
		"image_url": product.image or None,
		"product_type": product.product_type or None,
		"requires_prescription": cbool(product.requires_prescription),
		"requires_pharmacist_review": cbool(product.requires_pharmacist_review),
		"featured": cbool(product.featured),
		"price": {
			"price_list": price_context.price_list or None,
			"currency": (price or {}).get("currency") or price_context.currency or None,
			"amount": (price or {}).get("price_list_rate") or product.regulated_price or 0,
		},
	}


def serialize_product_detail(
	product: frappe._dict,
	*,
	price_context: frappe._dict,
	price_map: dict[str, frappe._dict],
) -> dict:
	data = serialize_product_summary(
		product,
		price_context=price_context,
		price_map=price_map,
	)
	data.update(
		{
			"description": {
				"short": product.app_short_description or product.description or None,
				"long": product.app_long_description or None,
			},
			"medical": {
				"active_ingredient": product.active_ingredient or None,
				"strength": product.strength or None,
				"form": product.form or None,
				"pack_size": product.pack_size or None,
				"nhra_registration_no": product.nhra_registration_no or None,
				"min_patient_age": product.min_patient_age,
				"max_patient_age": product.max_patient_age,
			},
			"fulfillment": {
				"uom": product.stock_uom or None,
				"refill_eligible": cbool(product.refill_eligible),
				"subscription_eligible": cbool(product.subscription_eligible),
			},
			"discovery": {
				"keywords": _split_csv(product.search_keywords),
				"symptom_tags": _split_csv(product.symptom_tags),
				"sort_order": product.sort_order or 0,
			},
		}
	)
	return data


def _get_product_count(*, filters: dict, or_filters: list[list[str]] | None) -> int:
	return len(
		frappe.get_all(
			"Item",
			fields=["name"],
			filters=filters,
			or_filters=or_filters,
			order_by=None,
		)
	)


def _get_price_context() -> frappe._dict:
	price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
	currency = frappe.db.get_value("Price List", price_list, "currency") if price_list else None
	return frappe._dict({"price_list": price_list, "currency": currency})


def _get_price_map(item_codes: list[str], price_list: str | None) -> dict[str, frappe._dict]:
	if not item_codes or not price_list:
		return {}

	rows = frappe.get_all(
		"Item Price",
		fields=["item_code", "price_list_rate", "currency"],
		filters={"item_code": ["in", item_codes], "price_list": price_list},
	)
	return {row.item_code: row for row in rows}


def _get_mobile_item_groups() -> list[dict]:
	rows = frappe.get_all(
		"Item Group",
		fields=[
			"name",
			"show_in_mobile_app",
			"mobile_app_sf_symbol",
			"mobile_app_sort_order",
			"image",
		],
		filters={"show_in_mobile_app": 1},
		order_by="mobile_app_sort_order asc, name asc",
	)
	return [
		{
			"name": row.name,
			"show_in_mobile_app": cbool(row.show_in_mobile_app),
			"mobile_app_sf_symbol": row.mobile_app_sf_symbol or None,
			"mobile_app_sort_order": row.mobile_app_sort_order or 0,
			"image": row.image or None,
		}
		for row in rows
	]


def _split_csv(value: str | None) -> list[str]:
	return [part.strip() for part in (value or "").split(",") if part.strip()]
