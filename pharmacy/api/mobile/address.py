from __future__ import annotations

import frappe

from pharmacy.services.mobile_app_user_service import (
	create_mobile_app_user_address_data,
	get_mobile_app_user_addresses_data,
	set_default_address_data,
)
from pharmacy.services.mobile_service import cbool, execute_api, get_request_value


@frappe.whitelist(allow_guest=True)
def get_mobile_app_user_addresses() -> dict:
	return execute_api(get_mobile_app_user_addresses_data)


@frappe.whitelist(allow_guest=True)
def create_mobile_app_user_address(
	address_title: str | None = None,
	address_type: str | None = None,
	address_line1: str | None = None,
	address_line2: str | None = None,
	city: str | None = None,
	state: str | None = None,
	country: str | None = None,
	pincode: str | None = None,
	email_id: str | None = None,
	phone: str | None = None,
	is_default: int | str | bool | None = None,
) -> dict:
	return execute_api(
		create_mobile_app_user_address_data,
		address_title=address_title or get_request_value("address_title"),
		address_type=address_type or get_request_value("address_type"),
		address_line1=address_line1 or get_request_value("address_line1"),
		address_line2=address_line2 or get_request_value("address_line2"),
		city=city or get_request_value("city"),
		state=state or get_request_value("state"),
		country=country or get_request_value("country"),
		pincode=pincode or get_request_value("pincode"),
		email_id=email_id or get_request_value("email_id"),
		phone=phone or get_request_value("phone"),
		is_default=is_default if is_default is not None else cbool(get_request_value("is_default")),
	)


@frappe.whitelist(allow_guest=True)
def set_default_address(address_id: str | None = None, id: str | None = None) -> dict:
	return execute_api(set_default_address_data, address_id=address_id or id or get_request_value("address_id", aliases=("id",)))
