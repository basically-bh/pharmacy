from __future__ import annotations

import frappe

from pharmacy.services.mobile_service import execute_api
from pharmacy.services.order_service import get_order_data, list_order_data


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
