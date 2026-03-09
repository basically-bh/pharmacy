from __future__ import annotations

import frappe


def execute() -> None:
	if not frappe.db.table_exists("Customer Profile"):
		return

	if frappe.db.has_column("Customer Profile", "status") and frappe.db.has_column(
		"Customer Profile", "account_status"
	):
		frappe.db.sql(
			"""
			update `tabCustomer Profile`
			set account_status = coalesce(nullif(account_status, ''), status)
			where ifnull(status, '') != ''
			"""
		)

	if frappe.db.has_column("Customer Profile", "profile_completion_status"):
		frappe.db.sql(
			"""
			update `tabCustomer Profile`
			set profile_completion_status = 'Incomplete'
			where ifnull(profile_completion_status, '') = ''
			"""
		)
