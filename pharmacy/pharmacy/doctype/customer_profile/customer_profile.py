# Copyright (c) 2026, Basically and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from pharmacy.utils.mobile_auth import normalize_mobile_no


class CustomerProfile(Document):
	"""Pharmacy-specific extension layer for customer state.

	Lifecycle and architecture boundary:
	- User: created first and remains the native identity/authentication record.
	- Customer Profile: created second as the pharmacy-owned extension layer.
	- Customer: created lazily only when the user first transacts.
	- Contact: remains the native ERPNext communication/person record.
	"""

	def validate(self) -> None:
		self._ensure_unique_link("user", _("User"))
		self._sync_mobile_no()

	def _ensure_unique_link(self, fieldname: str, label: str) -> None:
		value = self.get(fieldname)
		if not value:
			return

		existing_profile = frappe.db.get_value(
			"Customer Profile",
			{
				fieldname: value,
				"name": ["!=", self.name or ""],
			},
			"name",
		)
		if existing_profile:
			frappe.throw(
				_("Customer Profile {0} is already linked to {1} {2}.").format(
					frappe.bold(existing_profile),
					label,
					frappe.bold(value),
				)
			)

	def _sync_mobile_no(self) -> None:
		user_mobile_no = frappe.db.get_value("User", self.user, "mobile_no") if self.user else None
		candidate_mobile_no = self.mobile_no or user_mobile_no
		normalized_mobile_no = normalize_mobile_no(candidate_mobile_no)
		self.mobile_no = normalized_mobile_no or ""
