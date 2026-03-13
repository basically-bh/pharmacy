# Copyright (c) 2026, Basically and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password


class MobileOTPRequest(Document):
	def get_stored_otp_hash(self) -> str | None:
		return get_stored_otp_hash(self.name)


def get_stored_otp_hash(name: str) -> str | None:
	return get_decrypted_password("Mobile OTP Request", name, "otp_hash", raise_exception=False)
