from pharmacy.pharmacy.services.catalog_service import (
	PRODUCT_FIELDS,
	get_product_data,
	list_product_data,
	serialize_product_detail,
	serialize_product_summary,
)


def _get_price_map(item_codes: list[str], price_list: str | None) -> dict[str, frappe._dict]:
	if not item_codes or not price_list:
		return {}

	rows = frappe.get_all(
		"Item Price",
		fields=["item_code", "price_list_rate", "currency", "valid_from", "modified"],
		filters={
			"item_code": ["in", item_codes],
			"price_list": price_list,
		},
		order_by="valid_from desc, modified desc",
	)
	price_map: dict[str, frappe._dict] = {}
	for row in rows:
		price_map.setdefault(row.item_code, row)
	return price_map


def _split_csv(value: str | None) -> list[str]:
	if not value:
		return []
	return [part.strip() for part in value.split(",") if part.strip()]
