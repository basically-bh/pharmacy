# Copyright (c) 2026, Basically and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MobileAccessToken(Document):
	def validate(self) -> None:
		self.token_hash = (self.token_hash or "").strip()
		self.token_prefix = (self.token_prefix or "").strip() or None
		if not self.token_hash:
			frappe.throw(_("Token hash is required."))
