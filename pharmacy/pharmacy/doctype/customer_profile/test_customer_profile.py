# Copyright (c) 2026, Basically and Contributors
# See license.txt

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestCustomerProfile(IntegrationTestCase):
	"""
	Integration tests for CustomerProfile.
	Use this class for testing interactions between multiple components.
	"""

	def test_user_link_must_be_unique(self) -> None:
		suffix = uuid4().hex[:8]
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": f"customer-profile-{suffix}@example.com",
				"first_name": "Customer",
				"last_name": "Profile",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		customer_one = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": f"Customer Profile Test {suffix} A",
				"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group"),
				"territory": frappe.db.get_single_value("Selling Settings", "territory"),
			}
		).insert(ignore_permissions=True)
		customer_two = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": f"Customer Profile Test {suffix} B",
				"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group"),
				"territory": frappe.db.get_single_value("Selling Settings", "territory"),
			}
		).insert(ignore_permissions=True)

		frappe.get_doc(
			{
				"doctype": "Customer Profile",
				"user": user.name,
				"customer": customer_one.name,
				"account_status": "Active",
			}
			).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Customer Profile",
					"user": user.name,
					"customer": customer_two.name,
					"account_status": "Active",
				}
			).insert(ignore_permissions=True)

	def test_profile_can_exist_before_customer(self) -> None:
		suffix = uuid4().hex[:8]
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": f"customer-profile-no-customer-{suffix}@example.com",
				"first_name": "Profile",
				"last_name": "Only",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

		profile = frappe.get_doc(
			{
				"doctype": "Customer Profile",
				"user": user.name,
				"account_status": "Active",
			}
		).insert(ignore_permissions=True)

		self.assertEqual(profile.user, user.name)
		self.assertFalse(profile.customer)
