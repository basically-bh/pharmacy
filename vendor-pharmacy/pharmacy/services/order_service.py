from __future__ import annotations

import frappe
from frappe import _

from pharmacy.services.mobile_service import (
	build_list_response,
	cbool,
	get_current_customer_profile,
	get_owned_resource_name,
	get_request_value,
	parse_pagination,
	raise_invalid_input,
)

ORDER_LIST_FIELDS = [
	"name",
	"customer",
	"customer_profile",
	"prescription",
	"transaction_date",
	"transaction_time",
	"source",
	"order_status",
	"currency",
	"subtotal",
	"tax_amount",
	"grand_total",
	"docstatus",
]
VALID_ORDER_STATUSES = {
	"Draft",
	"Pending Review",
	"Pending Payment",
	"Pending Fulfillment",
	"Completed",
	"Cancelled",
}


def list_order_data(
	*,
	page: int | str = 1,
	page_size: int | str = 20,
	status: str | None = None,
) -> dict:
	profile = get_current_customer_profile(fields=["name"])
	page_number, size, offset = parse_pagination(page, page_size)
	filters = {"customer_profile": profile.name}
	if status:
		if status not in VALID_ORDER_STATUSES:
			raise_invalid_input(
				message=_("Invalid order status."),
				details={"field": "status", "value": status, "allowed_values": sorted(VALID_ORDER_STATUSES)},
			)
		filters["order_status"] = status

	rows = frappe.get_all(
		"App Order",
		fields=ORDER_LIST_FIELDS,
		filters=filters,
		order_by="creation desc",
		limit_start=offset,
		limit_page_length=size,
	)
	total_count = frappe.db.count("App Order", filters=filters)
	item_counts = _get_item_counts([row.name for row in rows])
	items = [serialize_order_summary(row, item_count=item_counts.get(row.name, 0)) for row in rows]
	return build_list_response(
		items=items,
		page=page_number,
		page_size=size,
		total_count=total_count,
	)


def get_order_data(order_id: str | None = None) -> dict:
	profile = get_current_customer_profile(fields=["name"])
	name = (order_id or get_request_value("order_id", aliases=("id",)) or "").strip()
	if not name:
		raise_invalid_input(
			message=_("order_id is required."),
			details={"field": "order_id"},
		)

	order_name = get_owned_resource_name(
		doctype="App Order",
		resource_id=name,
		profile_name=profile.name,
		resource_label="Order",
	)

	doc = frappe.get_doc("App Order", order_name)
	return {"order": serialize_order_detail(doc)}


def serialize_order_summary(row: frappe._dict, *, item_count: int) -> dict:
	return {
		"id": row.name,
		"status": row.order_status or None,
		"source": row.source or None,
		"prescription_id": row.prescription or None,
		"transaction_date": row.transaction_date,
		"transaction_time": row.transaction_time,
		"item_count": item_count,
		"totals": {
			"currency": row.currency or None,
			"subtotal": row.subtotal or 0,
			"tax_amount": row.tax_amount or 0,
			"grand_total": row.grand_total or 0,
		},
		"submitted": row.docstatus == 1,
	}


def serialize_order_detail(doc) -> dict:
	return {
		"id": doc.name,
		"customer_id": doc.customer or None,
		"customer_profile_id": doc.customer_profile or None,
		"customer_name": doc.customer_name or None,
		"contact_mobile": doc.contact_mobile or None,
		"delivery_address_id": doc.delivery_address or None,
		"prescription_id": doc.prescription or None,
		"status": doc.order_status or None,
		"source": doc.source or None,
		"submitted": doc.docstatus == 1,
		"transaction": {
			"date": doc.transaction_date,
			"time": doc.transaction_time,
		},
		"totals": {
			"currency": doc.currency or None,
			"subtotal": doc.subtotal or 0,
			"tax_amount": doc.tax_amount or 0,
			"grand_total": doc.grand_total or 0,
		},
		"items": [
			{
				"item_code": row.item_code or None,
				"item_name": row.item_name or None,
				"uom": row.uom or None,
				"qty": row.qty or 0,
				"requires_prescription": cbool(row.requires_prescription),
				"line_status": row.line_status or None,
				"pricing": {
					"rate": row.rate or 0,
					"amount": row.amount or 0,
					"vat_rate": row.vat_rate or 0,
					"vat_amount": row.vat_amount or 0,
					"total_amount": row.total_amount or 0,
				},
			}
			for row in doc.get("items") or []
		],
	}


def _get_item_counts(parent_names: list[str]) -> dict[str, int]:
	if not parent_names:
		return {}

	return {
		parent_name: frappe.db.count(
			"App Order Item",
			filters={"parent": parent_name},
		)
		for parent_name in parent_names
	}
