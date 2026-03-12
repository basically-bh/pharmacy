# Copyright (c) 2026, Basically and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from pharmacy.utils.customer_profile import validate_customer_matches_profile


class Prescription(Document):
	"""Prescription intake record linked to an app-level customer identity."""

	def validate(self) -> None:
		validate_customer_matches_profile(self)
		if self.issue_date and self.expiry_date and self.expiry_date < self.issue_date:
			frappe.throw(_("Expiry Date cannot be before Issue Date."))
