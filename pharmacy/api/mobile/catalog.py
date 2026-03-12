from __future__ import annotations

import frappe

from pharmacy.services.catalog_service import get_product_data, list_product_data
from pharmacy.services.mobile_service import execute_api


@frappe.whitelist(allow_guest=True)
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


@frappe.whitelist(allow_guest=True)
def get_product(product_id: str | None = None, id: str | None = None) -> dict:
	return execute_api(get_product_data, product_id=product_id or id)
