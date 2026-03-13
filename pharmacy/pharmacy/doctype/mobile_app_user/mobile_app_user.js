// Copyright (c) 2026, Basically and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mobile App User", {
	refresh(frm) {
		set_full_name(frm);
		render_default_address(frm);
	},

	first_name(frm) {
		set_full_name(frm);
	},

	last_name(frm) {
		set_full_name(frm);
	},

	default_address(frm) {
		render_default_address(frm);
	},
});

function set_full_name(frm) {
	const parts = [frm.doc.first_name, frm.doc.last_name]
		.map((value) => (value || "").trim())
		.filter(Boolean);

	frm.set_value("full_name", parts.join(" "));
}

function render_default_address(frm) {
	const field = frm.get_field("address_html");
	if (!field || !field.$wrapper) {
		return;
	}

	if (!frm.doc.default_address) {
		field.$wrapper.empty();
		return;
	}

	frm.call({
		method: "frappe.contacts.doctype.address.address.get_address_display",
		args: {
			address_dict: frm.doc.default_address,
		},
		callback(r) {
			field.$wrapper.html(r.message || "");
		},
	});
}
