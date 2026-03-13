from __future__ import annotations

import frappe

from pharmacy.services.mobile_app_user_service import get_current_mobile_app_user
from pharmacy.services.mobile_service import raise_not_found


def get_current_mobile_app_user_for_checkout():
	return get_current_mobile_app_user(
		fields=[
			"name",
			"full_name",
			"first_name",
			"last_name",
			"mobile_no",
			"customer",
			"default_address",
			"customer_created_on_checkout",
		]
	)


def get_linked_customer_for_checkout(mobile_app_user=None):
	app_user = mobile_app_user or get_current_mobile_app_user_for_checkout()
	if not app_user.customer:
		return None

	customer = frappe.db.get_value(
		"Customer",
		app_user.customer,
		["name", "customer_name", "customer_type", "customer_group", "territory"],
		as_dict=True,
	)
	if not customer:
		raise_not_found(resource_name="Customer", resource_id=app_user.customer)
	return customer


def ensure_customer_for_checkout(mobile_app_user=None) -> frappe._dict:
	app_user = mobile_app_user or get_current_mobile_app_user_for_checkout()
	customer = get_linked_customer_for_checkout(app_user)
	if customer:
		return customer

	customer_doc = frappe.new_doc("Customer")
	customer_doc.customer_name = app_user.full_name or app_user.mobile_no or app_user.name
	customer_doc.customer_type = "Individual"
	customer_doc.customer_group = _get_default_customer_group()
	customer_doc.territory = _get_default_territory()
	customer_doc.flags.ignore_permissions = True
	customer_doc.insert(ignore_permissions=True)

	frappe.db.set_value(
		"Mobile App User",
		app_user.name,
		{
			"customer": customer_doc.name,
			"customer_created_on_checkout": 1,
		},
		update_modified=False,
	)
	return frappe._dict(
		{
			"name": customer_doc.name,
			"customer_name": customer_doc.customer_name,
			"customer_type": customer_doc.customer_type,
			"customer_group": customer_doc.customer_group,
			"territory": customer_doc.territory,
		}
	)


def get_checkout_context() -> dict:
	app_user = get_current_mobile_app_user_for_checkout()
	return {
		"mobile_app_user": app_user,
		"customer": get_linked_customer_for_checkout(app_user),
	}


def _get_default_customer_group() -> str:
	group = frappe.db.get_single_value("Selling Settings", "customer_group")
	return group or frappe.db.get_value("Customer Group", {"is_group": 0}, "name")


def _get_default_territory() -> str:
	territory = frappe.db.get_single_value("Selling Settings", "territory")
	return territory or frappe.db.get_value("Territory", {"is_group": 0}, "name")
