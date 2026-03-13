// Copyright (c) 2026, Basically and contributors
// For license information, please see license.txt

function refreshAppOrderPricing(frm) {
	if (frm.__app_order_syncing) {
		return Promise.resolve();
	}

	frm.__app_order_syncing = true;
	return frappe.call({
		method: "pharmacy.pharmacy.doctype.app_order.app_order.refresh_app_order_pricing",
		args: { doc: frm.doc }
	})
		.then((r) => {
			const data = r.message || {};
			const itemRowsByName = new Map((frm.doc.items || []).map((row) => [row.name, row]));
			const parentUpdates = {};

			["customer", "contact_mobile", "company", "currency", "price_list", "subtotal", "tax_amount", "grand_total"].forEach((fieldname) => {
				if (data[fieldname] !== undefined && frm.doc[fieldname] !== data[fieldname]) {
					parentUpdates[fieldname] = data[fieldname];
				}
			});

			if (!frm.doc.delivery_address && data.delivery_address) {
				parentUpdates.delivery_address = data.delivery_address;
			}

			const parentUpdatePromise = Object.keys(parentUpdates).length
				? frm.set_value(parentUpdates)
				: Promise.resolve();

			return parentUpdatePromise.then(() => {
				(data.items || []).forEach((itemData) => {
					const row = itemRowsByName.get(itemData.name);
					if (!row) {
						return;
					}

					[
						"item_name",
						"uom",
						"rate",
						"amount",
						"vat_rate",
						"vat_amount",
						"total_amount",
					].forEach((fieldname) => {
						if (row[fieldname] !== itemData[fieldname]) {
							frappe.model.set_value(row.doctype, row.name, fieldname, itemData[fieldname]);
						}
					});
				});
			});
		})
		.then(() => {
			frm.refresh_fields(["company", "currency", "price_list", "contact_mobile", "delivery_address", "items", "subtotal", "tax_amount", "grand_total"]);
		})
		.finally(() => {
			frm.__app_order_syncing = false;
		});
}

frappe.ui.form.on("App Order", {
	refresh(frm) {
		if (frm.is_new()) {
			refreshAppOrderPricing(frm);
		}
	},
	mobile_app_user(frm) {
		refreshAppOrderPricing(frm);
	},
	price_list(frm) {
		refreshAppOrderPricing(frm);
	},
	company(frm) {
		refreshAppOrderPricing(frm);
	},
	transaction_date(frm) {
		refreshAppOrderPricing(frm);
	}
});

frappe.ui.form.on("App Order Item", {
	item_code(frm) {
		refreshAppOrderPricing(frm);
	},
	qty(frm) {
		refreshAppOrderPricing(frm);
	}
});
