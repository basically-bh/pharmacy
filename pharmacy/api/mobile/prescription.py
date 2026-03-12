from __future__ import annotations

import frappe

from pharmacy.services.mobile_service import execute_api
from pharmacy.services.prescription_service import (
	get_prescription_data,
	list_prescription_data,
)


@frappe.whitelist(allow_guest=True)
def list_prescriptions(
	page: int | str = 1,
	page_size: int | str = 20,
	status: str | None = None,
) -> dict:
	return execute_api(list_prescription_data, page=page, page_size=page_size, status=status)


@frappe.whitelist(allow_guest=True)
def get_prescription(prescription_id: str | None = None, id: str | None = None) -> dict:
	return execute_api(get_prescription_data, prescription_id=prescription_id or id)
