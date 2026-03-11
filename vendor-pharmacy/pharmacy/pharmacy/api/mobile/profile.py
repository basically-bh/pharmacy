from __future__ import annotations

import frappe

from pharmacy.pharmacy.services.catalog_service import list_product_data
from pharmacy.pharmacy.services.mobile_service import execute_api
from pharmacy.pharmacy.services.order_service import list_order_data
from pharmacy.pharmacy.services.profile_service import get_profile_data


@frappe.whitelist()
def get_profile() -> dict:
	return execute_api(get_profile_data)


@frappe.whitelist()
def list_products(
	search: str | None = None,
	page: int | str = 1,
	page_size: int | str = 20,
	product_type: str | None = None,
	featured: int | str | None = None,
) -> dict:
	return execute_api(
		list_product_data,
		search=search,
		page=page,
		page_size=page_size,
		product_type=product_type,
		featured=featured,
	)


@frappe.whitelist()
def list_orders(
	page: int | str = 1,
	page_size: int | str = 20,
	status: str | None = None,
) -> dict:
	return execute_api(list_order_data, page=page, page_size=page_size, status=status)
