from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import nowdate, nowtime

from pharmacy.services.mobile_service import (
	get_current_customer,
	get_current_mobile_app_user,
	raise_invalid_input,
	raise_not_found,
)
from pharmacy.services.order_service import serialize_order_detail

APP_ORDER_NAMING_SERIES = "AO-.YY."


def get_cart() -> dict:
	app_user = get_current_mobile_app_user(fields=["name"])
	cart = get_active_cart_doc_for_mobile_app_user(app_user.name, allow_missing=True)
	return {"cart": serialize_cart(cart) if cart else None}


def create_or_get_cart() -> dict:
	app_user = get_current_mobile_app_user(fields=["name"])
	cart = get_active_cart_doc_for_mobile_app_user(app_user.name, allow_missing=True)
	if not cart:
		cart = _create_cart(app_user.name)
	return {"cart": serialize_cart(cart)}


def add_item_to_cart(item_code: str | None, qty: int | float | str | None) -> dict:
	app_user = get_current_mobile_app_user(fields=["name"])
	cart = get_active_cart_doc_for_mobile_app_user(app_user.name, allow_missing=True)
	if not cart:
		cart = _create_cart(app_user.name)

	item_code = _normalize_item_code(item_code)
	qty_value = _parse_qty(qty, fieldname="qty")
	_validate_cart_item(item_code)

	row = _get_cart_item(cart, item_code)
	if row:
		row.qty = (row.qty or 0) + qty_value
	else:
		cart.append(
			"items",
			{
				"item_code": item_code,
				"qty": qty_value,
				"line_status": "Pending",
			},
		)

	_save_cart(cart)
	return {"cart": serialize_cart(cart)}


def update_cart_item_qty(item_code: str | None, qty: int | float | str | None) -> dict:
	app_user = get_current_mobile_app_user(fields=["name"])
	cart = get_active_cart_doc_for_mobile_app_user(app_user.name)
	item_code = _normalize_item_code(item_code)
	qty_value = _parse_qty(qty, fieldname="qty")

	row = _get_cart_item(cart, item_code)
	if not row:
		raise_not_found(resource_name="Cart Item", resource_id=item_code)

	row.qty = qty_value
	_save_cart(cart)
	return {"cart": serialize_cart(cart)}


def remove_item_from_cart(item_code: str | None) -> dict:
	app_user = get_current_mobile_app_user(fields=["name"])
	cart = get_active_cart_doc_for_mobile_app_user(app_user.name)
	item_code = _normalize_item_code(item_code)

	row = _get_cart_item(cart, item_code)
	if not row:
		raise_not_found(resource_name="Cart Item", resource_id=item_code)

	cart.remove(row)
	_save_cart(cart)
	return {"cart": serialize_cart(cart)}


def serialize_cart(doc) -> dict:
	data = serialize_order_detail(doc)
	data["item_count"] = len(doc.get("items") or [])
	data["is_active_cart"] = doc.docstatus == 0
	return data


def get_active_cart_doc_for_mobile_app_user(
	mobile_app_user: str,
	*,
	allow_missing: bool = False,
):
	active_carts = frappe.get_all(
		"App Order",
		fields=["name"],
		filters={
			"mobile_app_user": mobile_app_user,
			"docstatus": 0,
		},
		order_by="modified desc, creation desc",
	)
	if not active_carts:
		if allow_missing:
			return None
		raise_not_found(resource_name="Cart", resource_id=mobile_app_user)
	if len(active_carts) > 1:
		raise_invalid_input(
			message=_("Multiple active carts found for this mobile app user."),
			details={
				"mobile_app_user": mobile_app_user,
				"cart_ids": [row.name for row in active_carts],
			},
		)
	return frappe.get_doc("App Order", active_carts[0].name)


def _create_cart(mobile_app_user: str):
	doc = frappe.new_doc("App Order")
	doc.naming_series = APP_ORDER_NAMING_SERIES
	doc.mobile_app_user = mobile_app_user
	doc.customer = get_current_customer(required=False)
	doc.transaction_date = nowdate()
	doc.transaction_time = nowtime()
	doc.source = "App"
	doc.order_status = "Draft"
	doc.insert(ignore_permissions=True)
	return doc


def _save_cart(doc) -> None:
	doc.order_status = "Draft"
	doc.save(ignore_permissions=True)


def _normalize_item_code(item_code: str | None) -> str:
	value = (item_code or "").strip()
	if not value:
		raise_invalid_input(
			message=_("item_code is required."),
			details={"field": "item_code"},
		)
	return value


def _parse_qty(value: int | float | str | None, *, fieldname: str) -> float:
	try:
		qty_value = float(value)
	except (TypeError, ValueError):
		raise_invalid_input(
			message=_("{0} must be a positive number.").format(fieldname),
			details={"field": fieldname, "value": value},
		)
	if qty_value <= 0:
		raise_invalid_input(
			message=_("{0} must be greater than 0.").format(fieldname),
			details={"field": fieldname, "value": value},
		)
	return qty_value


def _validate_cart_item(item_code: str) -> None:
	item = frappe.db.get_value(
		"Item",
		item_code,
		["name", "show_in_mobile_app", "disabled", "is_hidden_in_app"],
		as_dict=True,
	)
	if not item:
		raise_not_found(resource_name="Item", resource_id=item_code)
	if not item.show_in_mobile_app or item.disabled or item.is_hidden_in_app:
		raise_invalid_input(
			message=_("Item {0} is not available for the mobile cart.").format(item_code),
			details={"item_code": item_code},
		)


def _get_cart_item(doc, item_code: str):
	for row in doc.get("items") or []:
		if row.item_code == item_code:
			return row
	return None


def resolve_cart_item_code(item_code: str | None) -> str | None:
	return item_code


def resolve_cart_qty(qty: int | float | str | None) -> int | float | str | bool | None:
	return qty
