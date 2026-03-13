from __future__ import annotations

import frappe

from pharmacy.services.mobile_app_user_service import get_current_mobile_app_user


def get_mobile_checkout_context() -> dict:
	app_user = get_current_mobile_app_user(fields=["name", "customer", "default_address"], required=False)
	if not app_user:
		return {"mobile_app_user": None, "customer_id": None, "default_address": None}
	return {
		"mobile_app_user": frappe._dict(app_user),
		"customer_id": app_user.customer or None,
		"default_address": app_user.default_address or None,
	}
