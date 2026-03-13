from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import nowdate

from pharmacy.services.cart_service import get_active_cart_doc_for_mobile_app_user
from pharmacy.services.mobile_service import (
	get_current_mobile_app_user,
	raise_invalid_input,
	raise_not_found,
)
from pharmacy.services.order_service import serialize_order_detail

SALES_ORDER_NAMING_SERIES = "SAL-ORD-.YYYY.-"


def checkout_cart() -> dict:
	app_user = _get_checkout_mobile_app_user()
	cart = get_active_cart_doc_for_mobile_app_user(app_user.name)

	_validate_cart_for_checkout(cart)
	customer_id = _ensure_customer_for_mobile_app_user(app_user)
	default_address_id = _ensure_default_address_link(app_user, customer_id)
	cart.reload()
	sales_order = _create_sales_order_from_cart(
		cart,
		customer_id=customer_id,
		customer_address_id=default_address_id,
	)
	_link_checkout_documents(cart, sales_order)

	cart.order_status = "Pending Review"
	cart.flags.ignore_permissions = True
	cart.flags.ignore_links = True
	cart.submit()
	cart.reload()

	return {
		"order": serialize_order_detail(cart),
		"sales_order": {
			"id": sales_order.name,
			"status": sales_order.status,
			"customer_id": sales_order.customer,
			"transaction_date": sales_order.transaction_date,
			"grand_total": sales_order.grand_total,
			"currency": sales_order.currency,
		},
	}


def prepare_app_order_for_submission(app_order) -> None:
	"""Create the ERP commercial documents required by a submitted App Order.

	App Order is the orchestration document. On first submit we lazily create:
	- Customer, if the linked Mobile App User does not have one yet
	- Customer/address linkage, using the order's chosen delivery address
	- Sales Order, linked back to the App Order
	"""
	if app_order.sales_order and frappe.db.exists("Sales Order", app_order.sales_order):
		if not app_order.customer:
			app_order.customer = frappe.db.get_value("Sales Order", app_order.sales_order, "customer")
		if not app_order.order_status:
			app_order.order_status = "Pending Review"
		return

	app_user = frappe.db.get_value(
		"Mobile App User",
		app_order.mobile_app_user,
		["name", "customer", "full_name", "mobile_no", "default_address"],
		as_dict=True,
	)
	if not app_user:
		raise_not_found(resource_name="Mobile App User", resource_id=app_order.mobile_app_user)

	customer_id = _ensure_customer_for_mobile_app_user(app_user)
	address_id = _ensure_default_address_link(
		app_user,
		customer_id,
		preferred_address_id=app_order.delivery_address,
	)
	sales_order = _create_sales_order_from_cart(
		app_order,
		customer_id=customer_id,
		customer_address_id=address_id,
	)

	sales_order.app_order = app_order.name
	sales_order.flags.ignore_permissions = True
	sales_order.flags.ignore_links = True
	sales_order.save(ignore_permissions=True)

	app_order.customer = customer_id
	app_order.delivery_address = address_id or app_order.delivery_address
	app_order.sales_order = sales_order.name
	app_order.order_status = "Pending Review"


def _get_checkout_mobile_app_user() -> frappe._dict:
	app_user = get_current_mobile_app_user(
		fields=["name", "customer", "full_name", "mobile_no", "default_address"],
		required=False,
	)
	if not app_user:
		raise_not_found(
			resource_name="Mobile App User",
			message=_("Mobile App User not found for the authenticated session."),
		)
	return app_user


def _validate_cart_for_checkout(cart) -> None:
	items = cart.get("items") or []
	if not items:
		raise_invalid_input(
			message=_("Cart is empty."),
			details={"field": "items"},
		)

	for row in items:
		if not row.item_code:
			raise_invalid_input(
				message=_("Cart contains an item without an item_code."),
				details={"field": "item_code"},
			)
		if not row.qty or row.qty <= 0:
			raise_invalid_input(
				message=_("Cart contains an invalid quantity."),
				details={"field": "qty", "item_code": row.item_code},
			)
		if row.requires_prescription and not cart.prescription:
			raise_invalid_input(
				message=_("Prescription is required for one or more cart items."),
				details={"field": "prescription"},
			)


def _ensure_customer_for_mobile_app_user(app_user: frappe._dict) -> str:
	if app_user.customer:
		return app_user.customer

	customer = frappe.new_doc("Customer")
	customer.customer_name = app_user.full_name or app_user.mobile_no or app_user.name
	customer.customer_type = "Individual"
	customer.customer_group = _get_default_customer_group()
	customer.territory = _get_default_territory()
	customer.flags.ignore_permissions = True
	customer.insert(ignore_permissions=True)

	frappe.db.set_value("Mobile App User", app_user.name, "customer", customer.name, update_modified=False)
	if frappe.db.has_column("Mobile App User", "customer_created_on_checkout"):
		frappe.db.set_value(
			"Mobile App User",
			app_user.name,
			"customer_created_on_checkout",
			1,
			update_modified=False,
		)
	frappe.db.commit()
	return customer.name


def _ensure_default_address_link(
	app_user: frappe._dict,
	customer_id: str,
	*,
	preferred_address_id: str | None = None,
) -> str | None:
	address_id = preferred_address_id or app_user.default_address or None
	if not address_id:
		return None

	if not frappe.db.exists("Address", address_id):
		raise_not_found(resource_name="Address", resource_id=address_id)

	address = frappe.get_doc("Address", address_id)
	links = address.get("links") or []
	has_customer_link = any(
		row.link_doctype == "Customer" and row.link_name == customer_id
		for row in links
	)
	if not has_customer_link:
		address.append(
			"links",
			{
				"link_doctype": "Customer",
				"link_name": customer_id,
			},
		)
		address.flags.ignore_permissions = True
		address.save(ignore_permissions=True)

	if not app_user.default_address:
		frappe.db.set_value("Mobile App User", app_user.name, "default_address", address_id, update_modified=False)
		app_user.default_address = address_id

	return address_id


def _create_sales_order_from_cart(
	cart,
	*,
	customer_id: str,
	customer_address_id: str | None = None,
):
	sales_order = frappe.new_doc("Sales Order")
	sales_order.flags.ignore_permissions = True
	sales_order.flags.ignore_links = True
	sales_order.naming_series = _get_sales_order_naming_series()
	sales_order.customer = customer_id
	sales_order.customer_address = customer_address_id
	sales_order.shipping_address_name = customer_address_id
	sales_order.company = cart.company
	sales_order.order_type = "Sales"
	sales_order.transaction_date = cart.transaction_date or nowdate()
	sales_order.delivery_date = cart.transaction_date or nowdate()
	sales_order.currency = cart.currency
	sales_order.conversion_rate = 1.0
	sales_order.selling_price_list = cart.price_list
	sales_order.price_list_currency = cart.currency
	sales_order.plc_conversion_rate = 1.0
	sales_order.prescription = cart.prescription

	for row in cart.get("items") or []:
		sales_order.append(
			"items",
			{
				"item_code": row.item_code,
				"item_name": row.item_name,
				"qty": row.qty,
				"uom": row.uom,
				"stock_uom": row.uom,
				"conversion_factor": 1.0,
				"rate": row.rate,
				"price_list_rate": row.rate,
			},
		)

	sales_order.set_missing_values()
	sales_order.customer_address = customer_address_id
	sales_order.shipping_address_name = customer_address_id
	sales_order.total = cart.subtotal or 0
	sales_order.net_total = cart.subtotal or 0
	sales_order.base_total = cart.subtotal or 0
	sales_order.base_net_total = cart.subtotal or 0
	sales_order.grand_total = cart.grand_total or 0
	sales_order.rounded_total = cart.grand_total or 0
	sales_order.base_grand_total = cart.grand_total or 0
	sales_order.base_rounded_total = cart.grand_total or 0
	sales_order.total_taxes_and_charges = cart.tax_amount or 0
	sales_order.base_total_taxes_and_charges = cart.tax_amount or 0
	sales_order.insert(ignore_permissions=True, ignore_links=True)
	return sales_order


def _link_checkout_documents(cart, sales_order) -> None:
	sales_order.app_order = cart.name
	sales_order.flags.ignore_permissions = True
	sales_order.flags.ignore_links = True
	sales_order.save(ignore_permissions=True)

	cart.sales_order = sales_order.name
	cart.flags.ignore_permissions = True
	cart.flags.ignore_links = True
	cart.save(ignore_permissions=True)


def _get_default_customer_group() -> str:
	group = frappe.db.get_single_value("Selling Settings", "customer_group")
	return group or frappe.db.get_value("Customer Group", {"is_group": 0}, "name")


def _get_default_territory() -> str:
	territory = frappe.db.get_single_value("Selling Settings", "territory")
	return territory or frappe.db.get_value("Territory", {"is_group": 0}, "name")


def _get_sales_order_naming_series() -> str:
	return (
		frappe.db.get_value("Property Setter", {"doc_type": "Sales Order", "field_name": "naming_series", "property": "default"}, "value")
		or SALES_ORDER_NAMING_SERIES
	)
