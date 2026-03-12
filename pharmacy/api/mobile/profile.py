from __future__ import annotations

import frappe

from pharmacy.services.mobile_service import execute_api
from pharmacy.services.profile_service import get_profile_data


@frappe.whitelist(allow_guest=True)
def get_profile() -> dict:
	return execute_api(get_profile_data)
