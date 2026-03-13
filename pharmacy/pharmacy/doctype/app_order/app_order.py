# Copyright (c) 2026, Basically and contributors
# For license information, please see license.txt

from __future__ import annotations

import erpnext
import frappe
from frappe.model.document import Document
from frappe.utils import flt

from erpnext.accounts.doctype.pricing_rule.pricing_rule import get_pricing_rule_for_item
from erpnext.stock.get_item_details import get_price_list_rate
from pharmacy.services.checkout_service import prepare_app_order_for_submission
from pharmacy.utils.customer_profile import validate_customer_matches_profile
from pharmacy.utils.vat import calculate_vat_amount, get_applicable_item_vat_rate


class AppOrder(Document):
	def validate(self) -> None:
		validate_customer_matches_profile(self)
		self.set_parent_defaults()
		self.sync_customer_profile_details()
		self.apply_item_pricing()
		self.calculate_totals()

	def before_submit(self) -> None:
		prepare_app_order_for_submission(self)

	@frappe.whitelist()
	def refresh_pricing_for_form(self) -> dict:
		self.set_parent_defaults()
		self.sync_customer_profile_details()
		self.apply_item_pricing()
		self.calculate_totals()
		return self.get_pricing_refresh_payload()

	def get_pricing_refresh_payload(self) -> dict:
		return {
			"customer": self.customer,
			"contact_mobile": self.contact_mobile,
			"delivery_address": self.delivery_address,
			"company": self.company,
			"currency": self.currency,
			"price_list": self.price_list,
			"subtotal": self.subtotal,
			"tax_amount": self.tax_amount,
			"grand_total": self.grand_total,
			"items": [
				{
					"name": row.name,
					"item_code": row.item_code,
					"item_name": row.item_name,
					"uom": row.uom,
					"qty": row.qty,
					"rate": row.rate,
					"amount": row.amount,
					"vat_rate": row.vat_rate,
					"vat_amount": row.vat_amount,
					"total_amount": row.total_amount,
				}
				for row in (self.get("items") or [])
			],
		}

	def set_parent_defaults(self) -> None:
		if not self.price_list:
			self.price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")

		if not self.company:
			self.company = erpnext.get_default_company()

		if self.company and not self.currency:
			self.currency = erpnext.get_company_currency(self.company)

	def sync_customer_profile_details(self) -> None:
		if not self.customer_profile:
			return

		profile = frappe.db.get_value(
			"Customer Profile",
			self.customer_profile,
			["customer", "default_address", "user", "mobile_no"],
			as_dict=True,
		)
		if not profile:
			return

		# Customer Profile provides defaults for the order, but it should not
		# erase values the user selected directly on the App Order form.
		if profile.customer:
			self.customer = profile.customer

		if profile.default_address and not self.delivery_address:
			self.delivery_address = profile.default_address

		if profile.mobile_no and not self.contact_mobile:
			self.contact_mobile = profile.mobile_no

	def apply_item_pricing(self) -> None:
		for row in self.get("items") or []:
			self.apply_item_defaults(row)

	def apply_item_defaults(self, row) -> None:
		if not row.item_code:
			self.reset_item_amounts(row)
			return

		item_meta = frappe.get_cached_value(
			"Item",
			row.item_code,
			["stock_uom", "item_name"],
			as_dict=True,
		) or {}
		row.uom = row.uom or item_meta.get("stock_uom")
		row.item_name = item_meta.get("item_name")

		if self.price_list and self.company and self.currency:
			row.rate = self.get_item_price_rate(row, item_meta)
		else:
			row.rate = 0.0

		row.amount = flt(row.qty) * flt(row.rate)
		row.vat_rate = get_applicable_item_vat_rate(
			row.item_code,
			company=self.company,
			transaction_date=self.transaction_date,
			base_net_rate=row.amount,
		)
		row.vat_amount = calculate_vat_amount(row.amount, row.vat_rate)
		row.total_amount = flt(row.amount) + flt(row.vat_amount)

	def get_item_price_rate(self, row, item_meta: frappe._dict | None = None) -> float:
		"""Resolve rate with ERPNext's price-list lookup plus pricing-rule engine."""
		if not self.price_list:
			return 0.0

		item_meta = item_meta or frappe.get_cached_value(
			"Item",
			row.item_code,
			["name", "stock_uom", "item_group", "brand"],
			as_dict=True,
		) or {}
		stock_uom = item_meta.get("stock_uom") or row.uom
		args = frappe._dict(
			{
				"doctype": "Sales Order",
				"parenttype": "Sales Order",
				"name": row.name,
				"parent": self.name,
				"child_docname": row.name,
				"item_code": row.item_code,
				"item_group": item_meta.get("item_group"),
				"brand": item_meta.get("brand"),
				"customer": self.customer,
				"company": self.company,
				"currency": self.currency,
				"conversion_rate": 1.0,
				"price_list": self.price_list,
				"selling_price_list": self.price_list,
				"price_list_currency": self.currency,
				"plc_conversion_rate": 1.0,
				"transaction_date": self.transaction_date,
				"qty": flt(row.qty) or 1.0,
				"uom": row.uom or stock_uom,
				"stock_uom": stock_uom,
				"conversion_factor": 1.0,
				"ignore_pricing_rule": 0,
				"ignore_party": False,
			}
		)
		item_doc = frappe.get_cached_doc("Item", row.item_code)
		price_data = frappe._dict()
		price_data.update(get_price_list_rate(args, item_doc))

		args.price_list_rate = flt(price_data.get("price_list_rate"))
		args.rate = args.price_list_rate
		args.base_net_rate = args.price_list_rate
		args.stock_qty = flt(args.qty)
		pricing_doc = frappe._dict(
			{
				"doctype": "Sales Order",
				"company": self.company,
				"customer": self.customer,
				"currency": self.currency,
				"conversion_rate": 1.0,
				"selling_price_list": self.price_list,
				"price_list_currency": self.currency,
				"plc_conversion_rate": 1.0,
				"transaction_date": self.transaction_date,
				"taxes": [],
				"items": [],
				"ignore_pricing_rule": 0,
			}
		)
		pricing_rule_data = frappe._dict(get_pricing_rule_for_item(args, doc=pricing_doc))
		return flt(
			pricing_rule_data.get("rate")
			or pricing_rule_data.get("price_list_rate")
			or price_data.get("price_list_rate")
		)

	def calculate_totals(self) -> None:
		self.subtotal = 0.0
		self.tax_amount = 0.0
		self.grand_total = 0.0

		for row in self.get("items") or []:
			self.subtotal += flt(row.amount)
			self.tax_amount += flt(row.vat_amount)
			self.grand_total += flt(row.total_amount)

	def reset_item_amounts(self, row) -> None:
		row.rate = 0.0
		row.amount = 0.0
		row.vat_rate = 0.0
		row.vat_amount = 0.0
		row.total_amount = 0.0


@frappe.whitelist()
def refresh_app_order_pricing(doc: dict | str) -> dict:
	if isinstance(doc, str):
		doc = frappe.parse_json(doc)

	app_order = frappe.get_doc(doc)
	app_order.set_parent_defaults()
	app_order.sync_customer_profile_details()
	app_order.apply_item_pricing()
	app_order.calculate_totals()
	return app_order.get_pricing_refresh_payload()
