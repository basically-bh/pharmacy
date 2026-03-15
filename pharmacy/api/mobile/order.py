from __future__ import annotations

import frappe

from pharmacy.services.cart_service import (
	add_item_to_cart as add_item_to_cart_data,
	get_cart as get_cart_data,
	remove_item_from_cart as remove_item_from_cart_data,
	update_cart_item_qty as update_cart_item_qty_data,
)
from pharmacy.services.checkout_service import checkout_cart as checkout_cart_data
from pharmacy.services.mobile_service import execute_api, get_request_value
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
	return execute_api(get_order_data, order_id=order_id or id)


@frappe.whitelist(allow_guest=True)
def get_cart() -> dict:
	return execute_api(get_cart_data)


@frappe.whitelist(allow_guest=True)
def add_item_to_cart(item_code: str | None = None, qty: int | float | str | None = None) -> dict:
	return execute_api(
		add_item_to_cart_data,
		item_code=item_code or get_request_value("item_code", aliases=("product_id", "id")),
		qty=qty if qty is not None else get_request_value("qty", aliases=("quantity",)),
	)


@frappe.whitelist(allow_guest=True)
def update_cart_item_qty(item_code: str | None = None, qty: int | float | str | None = None) -> dict:
	return execute_api(update_cart_item_qty_data, item_code=item_code, qty=qty)


@frappe.whitelist(allow_guest=True)
def remove_item_from_cart(item_code: str | None = None) -> dict:
	return execute_api(remove_item_from_cart_data, item_code=item_code)


@frappe.whitelist(allow_guest=True)
def checkout_cart() -> dict:
	return execute_api(checkout_cart_data)
