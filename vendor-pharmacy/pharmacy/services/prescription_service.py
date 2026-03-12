from __future__ import annotations

import frappe
from frappe import _

from pharmacy.services.mobile_service import (
	build_list_response,
	get_current_customer_profile,
	get_owned_resource_name,
	get_request_value,
	parse_pagination,
	raise_invalid_input,
)

PRESCRIPTION_LIST_FIELDS = [
	"name",
	"customer",
	"customer_profile",
	"customer_name",
	"prescription_status",
	"uploaded_on",
	"uploaded_by",
	"doctor_name",
	"doctor_license_number",
	"issue_date",
	"expiry_date",
]
VALID_PRESCRIPTION_STATUSES = {
	"Draft",
	"Submitted",
	"Under Review",
	"Validated",
	"Rejected",
	"Expired",
	"Fulfilled",
}


def list_prescription_data(
	*,
	page: int | str = 1,
	page_size: int | str = 20,
	status: str | None = None,
) -> dict:
	profile = get_current_customer_profile(fields=["name"])
	page_number, size, offset = parse_pagination(page, page_size)
	filters = {"customer_profile": profile.name}
	if status:
		if status not in VALID_PRESCRIPTION_STATUSES:
			raise_invalid_input(
				message=_("Invalid prescription status."),
				details={"field": "status", "value": status, "allowed_values": sorted(VALID_PRESCRIPTION_STATUSES)},
			)
		filters["prescription_status"] = status

	rows = frappe.get_all(
		"Prescription",
		fields=PRESCRIPTION_LIST_FIELDS,
		filters=filters,
		order_by="uploaded_on desc, modified desc",
		limit_start=offset,
		limit_page_length=size,
	)
	total_count = frappe.db.count("Prescription", filters=filters)
	item_counts = _get_item_counts([row.name for row in rows], child_doctype="Prescription Item")
	items = [serialize_prescription_summary(row, item_count=item_counts.get(row.name, 0)) for row in rows]
	return build_list_response(
		items=items,
		page=page_number,
		page_size=size,
		total_count=total_count,
	)


def get_prescription_data(prescription_id: str | None = None) -> dict:
	profile = get_current_customer_profile(fields=["name"])
	name = (prescription_id or get_request_value("prescription_id", aliases=("id",)) or "").strip()
	if not name:
		raise_invalid_input(
			message=_("prescription_id is required."),
			details={"field": "prescription_id"},
		)

	prescription_name = get_owned_resource_name(
		doctype="Prescription",
		resource_id=name,
		profile_name=profile.name,
		resource_label="Prescription",
	)

	doc = frappe.get_doc("Prescription", prescription_name)
	return {"prescription": serialize_prescription_detail(doc)}


def serialize_prescription_summary(row: frappe._dict, *, item_count: int) -> dict:
	return {
		"id": row.name,
		"status": row.prescription_status or None,
		"uploaded_on": row.uploaded_on,
		"doctor_name": row.doctor_name or None,
		"issue_date": row.issue_date,
		"expiry_date": row.expiry_date,
		"item_count": item_count,
	}


def serialize_prescription_detail(doc) -> dict:
	return {
		"id": doc.name,
		"customer_id": doc.customer or None,
		"customer_profile_id": doc.customer_profile or None,
		"status": doc.prescription_status or None,
		"uploaded_on": doc.uploaded_on,
		"uploaded_by": doc.uploaded_by or None,
		"file_url": doc.prescription_file or None,
		"doctor": {
			"name": doc.doctor_name or None,
			"license_number": doc.doctor_license_number or None,
		},
		"dates": {
			"issue_date": doc.issue_date,
			"expiry_date": doc.expiry_date,
		},
		"review_notes": doc.review_notes or None,
		"items": [
			{
				"prescribed_item_name": row.prescribed_item_name or None,
				"approved_item": row.approved_item or None,
				"line_status": row.line_status or None,
				"prescribed_qty": row.prescribed_qty or 0,
				"approved_qty": row.approved_qty or 0,
				"dosage": row.dosage or None,
				"frequency": row.frequency or None,
				"duration_days": row.duration_days or 0,
				"instructions": row.instructions or None,
			}
			for row in doc.get("items") or []
		],
	}


def _get_item_counts(parent_names: list[str], *, child_doctype: str) -> dict[str, int]:
	if not parent_names:
		return {}

	return {
		parent_name: frappe.db.count(
			child_doctype,
			filters={"parent": parent_name},
		)
		for parent_name in parent_names
	}
