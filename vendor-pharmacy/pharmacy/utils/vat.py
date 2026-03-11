from __future__ import annotations

import frappe
from frappe.utils import cint, flt

from erpnext.stock.get_item_details import get_item_tax_map, get_item_tax_template


DEFAULT_VAT_RATE = 10.0
ZERO_RATED_TAX_CODES = {"ZR", "EX"}


def get_default_vat_rate() -> float:
	"""Return the default VAT rate for pharmacy retail transactions."""
	return DEFAULT_VAT_RATE


def get_item_vat_rate(item_code: str) -> float:
	"""Determine VAT rate using Item tax flags, falling back to the standard rate."""
	return get_applicable_item_vat_rate(item_code)


def get_applicable_item_vat_rate(
	item_code: str,
	*,
	company: str | None = None,
	transaction_date: str | None = None,
	base_net_rate: float | None = None,
	tax_category: str | None = None,
) -> float:
	"""Resolve the effective VAT rate from item tax templates before using the legacy fallback."""
	if not item_code:
		return 0.0

	if company:
		ctx = frappe._dict(
			{
				"item_code": item_code,
				"company": company,
				"transaction_date": transaction_date,
				"tax_category": tax_category,
				"base_net_rate": flt(base_net_rate),
			}
		)
		out = frappe._dict()
		tax_template = get_item_tax_template(ctx, out=out)
		if tax_template:
			item_tax_map = get_item_tax_map(
				doc={"company": company, "taxes": []},
				tax_template=tax_template,
				as_json=False,
			)
			if item_tax_map:
				return flt(max((flt(rate) for rate in item_tax_map.values()), default=0.0))

	item_meta = frappe.get_meta("Item")
	if item_meta.has_field("is_zero_rated") and cint(
		frappe.db.get_value("Item", item_code, "is_zero_rated")
	):
		return 0.0

	if item_meta.has_field("is_exempt") and cint(
		frappe.db.get_value("Item", item_code, "is_exempt")
	):
		return 0.0

	if item_meta.has_field("tax_code"):
		tax_code = (frappe.db.get_value("Item", item_code, "tax_code") or "").upper().strip()
		if tax_code in ZERO_RATED_TAX_CODES:
			return 0.0

	return get_default_vat_rate()


def calculate_vat_amount(amount: float, vat_rate: float, precision: int | None = None) -> float:
	"""Return VAT amount for the provided net amount."""
	return flt((flt(amount) * flt(vat_rate)) / 100, precision)
