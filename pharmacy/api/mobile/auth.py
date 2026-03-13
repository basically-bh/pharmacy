from __future__ import annotations

import frappe

from pharmacy.services.auth_service import (
	get_current_mobile_session,
	login_with_otp as login_with_otp_data,
	logout_mobile_session,
	send_otp as send_otp_data,
)
from pharmacy.services.mobile_service import execute_api, get_request_value


@frappe.whitelist(allow_guest=True)
def send_otp(mobile_no: str | None = None) -> dict:
	return execute_api(send_otp_data, mobile_no=mobile_no or get_request_value("mobile_no"))


@frappe.whitelist(allow_guest=True)
def verify_otp(
	mobile_no: str | None = None,
	otp: str | None = None,
	device_name: str | None = None,
	platform: str | None = None,
	app_version: str | None = None,
) -> dict:
	return execute_api(
		login_with_otp_data,
		mobile_no=mobile_no or get_request_value("mobile_no"),
		otp=otp or get_request_value("otp"),
		device_name=device_name or get_request_value("device_name"),
		platform=platform or get_request_value("platform"),
		app_version=app_version or get_request_value("app_version"),
	)


@frappe.whitelist(allow_guest=True)
def me() -> dict:
	return execute_api(get_current_mobile_session)


@frappe.whitelist(allow_guest=True)
def logout() -> dict:
	return execute_api(logout_mobile_session)
