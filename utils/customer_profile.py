from __future__ import annotations

import frappe
from frappe import _


def validate_customer_matches_profile(
	doc,
	*,
	profile_field: str = "customer_profile",
	customer_field: str = "customer",
) -> None:
	"""Prevent transactional docs from pointing at a mismatched Customer.

	The app anchors on Customer Profile first. Once a lazy-created ERPNext
	Customer exists, it must stay consistent with the linked profile.
	"""
	customer_profile = doc.get(profile_field)
	customer = doc.get(customer_field)
	if not customer_profile or not customer:
		return

	expected_customer = frappe.db.get_value("Customer Profile", customer_profile, "customer")
	if not expected_customer or expected_customer == customer:
		return

	frappe.throw(
		_("Customer {0} does not match Customer Profile {1}.").format(
			frappe.bold(customer),
			frappe.bold(customer_profile),
		)
	)
