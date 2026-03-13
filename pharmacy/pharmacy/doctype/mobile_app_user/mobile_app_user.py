# Copyright (c) 2026, Basically and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from pharmacy.utils.mobile_auth import normalize_mobile_no


class MobileAppUser(Document):
	def validate(self) -> None:
		self._set_defaults()
		self._set_full_name()
		self._normalize_mobile_no()
		self._ensure_unique_mobile_no()
		self._reset_verification_state_if_mobile_changed()
		self._render_default_address_html()

	def onload(self) -> None:
		self._render_default_address_html()

	def _set_defaults(self) -> None:
		self.account_status = self.account_status or "Active"
		self.otp_verification_status = self.otp_verification_status or "Not Verified"
		self.country_code = self.country_code or "+973"
		self.language = self.language or "English"

	def _set_full_name(self) -> None:
		parts = [part.strip() for part in [self.first_name, self.last_name] if part and part.strip()]
		self.full_name = " ".join(parts)

	def _normalize_mobile_no(self) -> None:
		normalized_mobile_no = normalize_mobile_no(self.mobile_no)
		if not normalized_mobile_no:
			frappe.throw(_("A valid mobile number is required."))
		self.mobile_no = normalized_mobile_no

	def _ensure_unique_mobile_no(self) -> None:
		existing_name = frappe.db.get_value(
			"Mobile App User",
			{
				"mobile_no": self.mobile_no,
				"name": ["!=", self.name or ""],
			},
			"name",
		)
		if existing_name:
			frappe.throw(
				_("Mobile number {0} is already linked to Mobile App User {1}.").format(
					frappe.bold(self.mobile_no),
					frappe.bold(existing_name),
				)
			)

	def _reset_verification_state_if_mobile_changed(self) -> None:
		previous_doc = self.get_doc_before_save()
		if previous_doc and previous_doc.mobile_no == self.mobile_no:
			return

		self.otp_verification_status = "Not Verified"
		self.is_mobile_no_verified = 0
		self.otp_verified_at = None

	def _render_default_address_html(self) -> None:
		self.address_html = render_mobile_app_user_address_html(self.default_address)


def render_mobile_app_user_address_html(address_name: str | None) -> str:
	if not address_name:
		return ""

	if not frappe.db.exists("Address", address_name):
		return ""

	from frappe.contacts.doctype.address.address import get_address_display

	address_doc = frappe.get_cached_doc("Address", address_name)
	return get_address_display(address_doc.as_dict()) or ""
