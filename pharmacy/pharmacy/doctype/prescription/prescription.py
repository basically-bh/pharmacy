# Copyright (c) 2026, Basically and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Prescription(Document):
	def validate(self) -> None:
		if self.issue_date and self.expiry_date and self.expiry_date < self.issue_date:
			frappe.throw(_("Expiry Date cannot be before Issue Date."))
