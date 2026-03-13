from __future__ import annotations

import frappe

from pharmacy.services.cart_service import (
	add_item_to_cart as add_item_to_cart_data,
	create_or_get_cart as create_or_get_cart_data,
	get_cart as get_cart_data,
	remove_item_from_cart as remove_item_from_cart_data,
	resolve_cart_item_code,
	resolve_cart_qty,
	update_cart_item_qty as update_cart_item_qty_data,
)
from pharmacy.services.checkout_service import checkout_cart as checkout_cart_data
from pharmacy.services.mobile_service import execute_api, get_request_value, log_mobile_request_debug
from pharmacy.services.order_service import get_order_data, list_order_data


@frappe.whitelist(allow_guest=True)
def list_orders(
	page: int | str = 1,
	page_size: int | str = 20,
	status: str | None = None,
) -> dict:
	return execute_api(list_order_data, page=page, page_size=page_size, status=status)


@frappe.whitelist(allow_guest=True)
def get_order(order_id: str | None = None, id: str | None = None) -> dict:
	resolved_order_id = order_id or id or get_request_value("order_id", aliases=("id",))
	log_mobile_request_debug(
		"pharmacy.api.mobile.order.get_order",
		resolved={"order_id": resolved_order_id},
	)
	return execute_api(get_order_data, order_id=resolved_order_id)


@frappe.whitelist(allow_guest=True)
def get_cart() -> dict:
	return execute_api(get_cart_data)


@frappe.whitelist(allow_guest=True)
def create_or_get_cart() -> dict:
	return execute_api(create_or_get_cart_data)


@frappe.whitelist(allow_guest=True)
def add_item_to_cart(item_code: str | None = None, qty: int | float | str | None = None) -> dict:
	resolved_item_code = item_code or get_request_value("item_code")
	resolved_qty = qty if qty is not None else get_request_value("qty")
	log_mobile_request_debug(
		"pharmacy.api.mobile.order.add_item_to_cart",
		resolved={"item_code": resolved_item_code, "qty": resolved_qty},
	)
	return execute_api(add_item_to_cart_data, item_code=resolved_item_code, qty=resolved_qty)


@frappe.whitelist(allow_guest=True)
def update_cart_item_qty(item_code: str | None = None, qty: int | float | str | None = None) -> dict:
	resolved_item_code = resolve_cart_item_code(item_code)
	resolved_qty = resolve_cart_qty(qty)
	log_mobile_request_debug(
		"pharmacy.api.mobile.order.update_cart_item_qty",
		resolved={"item_code": resolved_item_code, "qty": resolved_qty},
	)
	return execute_api(update_cart_item_qty_data, item_code=resolved_item_code, qty=resolved_qty)


@frappe.whitelist(allow_guest=True)
def remove_item_from_cart(item_code: str | None = None) -> dict:
	resolved_item_code = resolve_cart_item_code(item_code)
	log_mobile_request_debug(
		"pharmacy.api.mobile.order.remove_item_from_cart",
		resolved={"item_code": resolved_item_code},
	)
	return execute_api(remove_item_from_cart_data, item_code=resolved_item_code)


@frappe.whitelist(allow_guest=True)
def update_cart_item(item_code: str | None = None, qty: int | float | str | None = None) -> dict:
	return update_cart_item_qty(item_code=item_code, qty=qty)


@frappe.whitelist(allow_guest=True)
def remove_cart_item(item_code: str | None = None) -> dict:
	return remove_item_from_cart(item_code=item_code)


@frappe.whitelist(allow_guest=True)
def checkout_cart() -> dict:
	return execute_api(checkout_cart_data)
