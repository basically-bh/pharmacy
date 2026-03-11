from __future__ import annotations

import frappe

from pharmacy.pharmacy.services.cart_service import (
	add_item_to_cart as add_item_to_cart_data,
	create_or_get_cart as create_or_get_cart_data,
	get_cart as get_cart_data,
	remove_item_from_cart as remove_item_from_cart_data,
	update_cart_item_qty as update_cart_item_qty_data,
)
from pharmacy.pharmacy.services.checkout_service import checkout_cart as checkout_cart_data
from pharmacy.pharmacy.services.mobile_service import execute_api
from pharmacy.pharmacy.services.order_service import get_order_data, list_order_data


@frappe.whitelist()
def list_orders(
	page: int | str = 1,
	page_size: int | str = 20,
	status: str | None = None,
) -> dict:
	return execute_api(list_order_data, page=page, page_size=page_size, status=status)


@frappe.whitelist()
def get_order(order_id: str | None = None, id: str | None = None) -> dict:
	return execute_api(get_order_data, order_id=order_id or id)


@frappe.whitelist()
def get_cart() -> dict:
	return execute_api(get_cart_data)


@frappe.whitelist()
def create_or_get_cart() -> dict:
	return execute_api(create_or_get_cart_data)


@frappe.whitelist()
def add_item_to_cart(item_code: str | None = None, qty: int | float | str | None = None) -> dict:
	return execute_api(add_item_to_cart_data, item_code=item_code, qty=qty)


@frappe.whitelist()
def update_cart_item_qty(item_code: str | None = None, qty: int | float | str | None = None) -> dict:
	return execute_api(update_cart_item_qty_data, item_code=item_code, qty=qty)


@frappe.whitelist()
def remove_item_from_cart(item_code: str | None = None) -> dict:
	return execute_api(remove_item_from_cart_data, item_code=item_code)


@frappe.whitelist()
def checkout_cart() -> dict:
	return execute_api(checkout_cart_data)
