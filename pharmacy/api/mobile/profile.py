from __future__ import annotations

import frappe

from pharmacy.services.mobile_service import execute_api, get_request_value
from pharmacy.services.profile_service import (
	get_mobile_app_user_profile_data,
	update_mobile_app_user_profile_data,
)


@frappe.whitelist(allow_guest=True)
def get_mobile_app_user_profile() -> dict:
	return execute_api(get_mobile_app_user_profile_data)


@frappe.whitelist(allow_guest=True)
def update_mobile_app_user_profile() -> dict:
	return execute_api(update_mobile_app_user_profile_data, dict(frappe.form_dict))


@frappe.whitelist(allow_guest=True)
def get_profile() -> dict:
	return get_mobile_app_user_profile()


@frappe.whitelist(allow_guest=True)
def update_mobile_app_user_profile(
	first_name: str | None = None,
	last_name: str | None = None,
	country_code: str | None = None,
	mobile_no: str | None = None,
	national_id: str | None = None,
	date_of_birth: str | None = None,
	gender: str | None = None,
	language: str | None = None,
	allow_push_notifications: int | str | bool | None = None,
	default_payment_method: str | None = None,
) -> dict:
	return execute_api(
		update_mobile_app_user_profile_data,
		first_name=first_name or get_request_value("first_name"),
		last_name=last_name or get_request_value("last_name"),
		country_code=country_code or get_request_value("country_code"),
		mobile_no=mobile_no or get_request_value("mobile_no"),
		national_id=national_id or get_request_value("national_id"),
		date_of_birth=date_of_birth or get_request_value("date_of_birth"),
		gender=gender or get_request_value("gender"),
		language=language or get_request_value("language"),
		allow_push_notifications=allow_push_notifications
		if allow_push_notifications is not None
		else get_request_value("allow_push_notifications"),
		default_payment_method=default_payment_method or get_request_value("default_payment_method"),
	)
