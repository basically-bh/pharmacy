from __future__ import annotations

import frappe

from pharmacy.services.auth_service import authenticate_access_token


def validate_mobile_bearer_auth() -> None:
	authorization_header = frappe.get_request_header("Authorization", "")
	if not authorization_header:
		return

	try:
		auth_type, access_token = authorization_header.split(" ", 1)
	except ValueError:
		return

	if auth_type.lower() != "bearer" or not access_token.strip():
		return

	context = authenticate_access_token(access_token.strip(), required=False)
	if not context:
		return

	# Frappe raises AuthenticationError for any Authorization header unless the
	# request is marked as authenticated before routing reaches /api/method.
	form_dict = frappe.local.form_dict
	frappe.set_user(context.user)
	frappe.local.form_dict = form_dict
	if getattr(frappe.local, "login_manager", None):
		frappe.local.login_manager.user = context.user
