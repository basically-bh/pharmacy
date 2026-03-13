# Copyright (c) 2026, Basically and contributors
# See license.txt

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from pharmacy.services.auth_service import (
	authenticate_access_token,
	get_current_mobile_session,
	login_with_otp,
	logout_mobile_session,
	send_otp,
	verify_otp,
)
from pharmacy.services.mobile_app_user_service import (
	create_mobile_app_user_address_data,
	get_mobile_app_user_profile_data,
)
from pharmacy.services.mobile_service import MobileApiError
from pharmacy.utils.mobile_auth import mask_mobile_no


class IntegrationTestMobileAuth(IntegrationTestCase):
	def tearDown(self) -> None:
		if hasattr(frappe.local, "pharmacy_mobile_auth_context"):
			delattr(frappe.local, "pharmacy_mobile_auth_context")
		super().tearDown()

	def test_send_and_verify_otp_creates_mobile_app_user_and_returns_bearer_token(self) -> None:
		mobile_no = self._new_mobile_no()

		send_response = send_otp(mobile_no)
		self.assertTrue(send_response["otp_sent"])
		self.assertEqual(send_response["masked_mobile_no"], mask_mobile_no(mobile_no))

		app_user = frappe.db.get_value(
			"Mobile App User",
			{"mobile_no": mobile_no},
			["name", "account_status", "otp_verification_status", "language", "country_code"],
			as_dict=True,
		)
		self.assertIsNotNone(app_user)
		self.assertEqual(app_user.account_status, "Active")
		self.assertEqual(app_user.otp_verification_status, "Pending")
		self.assertEqual(app_user.language, "English")
		self.assertEqual(app_user.country_code, "+973")

		verify_response = login_with_otp(
			mobile_no=mobile_no,
			otp=send_response["debug_otp"],
			device_name="iPhone 17",
			platform="ios",
			app_version="1.0.0",
		)

		self.assertTrue(verify_response["access_token"])
		self.assertEqual(verify_response["token_type"], "Bearer")
		self.assertEqual(verify_response["user"]["mobile_app_user_id"], app_user.name)
		self.assertEqual(verify_response["user"]["mobile_no"], mobile_no)

		context = authenticate_access_token(verify_response["access_token"])
		self.assertEqual(context.mobile_app_user.name, app_user.name)

		reloaded_user = frappe.db.get_value(
			"Mobile App User",
			app_user.name,
			["otp_verification_status", "is_mobile_no_verified", "last_login", "last_active_at"],
			as_dict=True,
		)
		self.assertEqual(reloaded_user.otp_verification_status, "Verified")
		self.assertEqual(reloaded_user.is_mobile_no_verified, 1)
		self.assertIsNotNone(reloaded_user.last_login)
		self.assertIsNotNone(reloaded_user.last_active_at)

	def test_invalid_otp_locks_after_max_attempts(self) -> None:
		app_user = self._create_app_user()
		send_otp(app_user.mobile_no)

		for _ in range(5):
			with self.assertRaises(MobileApiError):
				verify_otp(mobile_no=app_user.mobile_no, otp="000000")

		request_doc = frappe.get_all(
			"Mobile OTP Request",
			fields=["status", "attempt_count"],
			filters={"mobile_no": app_user.mobile_no},
			order_by="creation desc",
			limit_page_length=1,
		)[0]
		self.assertEqual(request_doc.status, "Locked")
		self.assertEqual(request_doc.attempt_count, 5)

	def test_logout_revokes_current_token(self) -> None:
		app_user = self._create_app_user()
		send_response = send_otp(app_user.mobile_no)
		verify_response = login_with_otp(mobile_no=app_user.mobile_no, otp=send_response["debug_otp"])

		context = frappe._dict(
			{
				"auth_type": "bearer",
				"user": app_user.name,
				"mobile_app_user": frappe._dict({"name": app_user.name}),
				"token_name": frappe.db.get_value(
					"Mobile Access Token",
					{"mobile_app_user": app_user.name, "status": "Active"},
					"name",
				),
			}
		)
		setattr(frappe.local, "pharmacy_mobile_auth_context", context)

		logout_response = logout_mobile_session()
		self.assertTrue(logout_response["logged_out"])

		status = frappe.db.get_value("Mobile Access Token", context.token_name, "status")
		self.assertEqual(status, "Revoked")
		self.assertTrue(verify_response["access_token"])

	def test_me_returns_guest_when_not_authenticated(self) -> None:
		self.assertEqual(get_current_mobile_session()["guest"], True)

	def test_profile_and_address_services_use_mobile_app_user_identity(self) -> None:
		app_user = self._create_app_user(first_name="Mobile", last_name="Profile")
		self._set_authenticated_user(app_user.name)

		address_response = create_mobile_app_user_address_data(
			address_line1="Road 101",
			city="Manama",
			country="Bahrain",
			is_default=1,
		)
		profile_response = get_mobile_app_user_profile_data()

		self.assertEqual(address_response["address"]["is_default"], True)
		self.assertEqual(profile_response["mobile_app_user"]["id"], app_user.name)
		self.assertEqual(profile_response["mobile_app_user"]["default_address"]["id"], address_response["address"]["id"])
		self.assertTrue(profile_response["mobile_app_user"]["address_html"])

	def _create_app_user(self, first_name: str | None = None, last_name: str | None = None):
		return frappe.get_doc(
			{
				"doctype": "Mobile App User",
				"first_name": first_name,
				"last_name": last_name,
				"mobile_no": self._new_mobile_no(),
				"account_status": "Active",
				"otp_verification_status": "Not Verified",
				"country_code": "+973",
				"language": "English",
			}
		).insert(ignore_permissions=True)

	def _new_mobile_no(self) -> str:
		digits = f"{uuid4().int % 1000000:06d}"
		return f"+97333{digits}"

	def _set_authenticated_user(self, app_user_name: str) -> None:
		context = frappe._dict(
			{
				"auth_type": "bearer",
				"user": app_user_name,
				"mobile_app_user": frappe._dict({"name": app_user_name}),
				"token_name": None,
				"expires_at": None,
			}
		)
		setattr(frappe.local, "pharmacy_mobile_auth_context", context)
