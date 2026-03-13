from __future__ import annotations

import frappe

from pharmacy.services.mobile_app_user_service import get_app_payment_methods_data
from pharmacy.services.mobile_service import execute_api


@frappe.whitelist(allow_guest=True)
def get_app_payment_methods() -> dict:
	return execute_api(get_app_payment_methods_data)
