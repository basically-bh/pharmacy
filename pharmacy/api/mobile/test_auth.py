# Copyright (c) 2026, Basically and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from pharmacy.services.auth_service import login_with_otp, send_otp, verify_otp
from pharmacy.utils.mobile_auth import hash_secret


class IntegrationTestMobileAuth(IntegrationTestCase):
	def test_send_otp_then_immediate_verify_succeeds(self):
		mobile_no = "+97339000001"

		frappe.db.delete("Mobile OTP Request", {"mobile_no": mobile_no})
		frappe.db.delete("Mobile App User", {"mobile_no": mobile_no})

		send_response = send_otp(mobile_no)
		self.assertTrue(send_response["otp_sent"])

		verify_response = verify_otp(mobile_no, send_response["debug_otp"])
		self.assertTrue(verify_response["verified"])
		self.assertEqual(verify_response["mobile_app_user"]["mobile_no"], mobile_no)

	def test_login_with_otp_creates_access_token_with_deterministic_hash(self):
		mobile_no = "+97339000002"

		frappe.db.delete("Mobile OTP Request", {"mobile_no": mobile_no})
		frappe.db.delete("Mobile App User", {"mobile_no": mobile_no})

		send_response = send_otp(mobile_no)
		login_response = login_with_otp(mobile_no, send_response["debug_otp"])

		self.assertTrue(login_response["access_token"])
		self.assertEqual(login_response["token_type"], "Bearer")

		token_doc = frappe.db.get_value(
			"Mobile Access Token",
			{"token_hash": hash_secret(login_response["access_token"])},
			["name", "token_hash"],
			as_dict=True,
		)
		self.assertIsNotNone(token_doc)
		self.assertEqual(token_doc.token_hash, hash_secret(login_response["access_token"]))
