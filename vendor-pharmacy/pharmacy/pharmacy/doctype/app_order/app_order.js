// Copyright (c) 2026, Basically and contributors
// For license information, please see license.txt

function refreshAppOrderPricing(frm) {
	if (frm.__app_order_syncing) {
		return Promise.resolve();
	}

	frm.__app_order_syncing = true;
	return frm.call("refresh_pricing_for_form")
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
	customer_profile(frm) {
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
