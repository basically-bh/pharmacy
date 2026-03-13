from __future__ import annotations

import frappe

from pharmacy.services.mobile_service import execute_api
from pharmacy.services.mobile_app_user_service import (
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
