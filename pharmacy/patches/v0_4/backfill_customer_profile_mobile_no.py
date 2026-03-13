from __future__ import annotations

import frappe

from pharmacy.utils.mobile_auth import normalize_mobile_no


def execute() -> None:
	profiles = frappe.get_all("Customer Profile", fields=["name", "user", "mobile_no"])
	for profile in profiles:
		current_mobile_no = normalize_mobile_no(profile.mobile_no)
		if current_mobile_no:
			if current_mobile_no != profile.mobile_no:
				frappe.db.set_value(
					"Customer Profile",
					profile.name,
					"mobile_no",
					current_mobile_no,
					update_modified=False,
				)
			continue

		if not profile.user:
			continue

		user_mobile_no = normalize_mobile_no(frappe.db.get_value("User", profile.user, "mobile_no"))
		if not user_mobile_no:
			continue

		existing_profile = frappe.db.get_value(
			"Customer Profile",
			{"mobile_no": user_mobile_no, "name": ["!=", profile.name]},
			"name",
		)
		if existing_profile:
			frappe.log_error(
				title="Customer Profile Mobile Backfill Skipped",
				message=(
					f"Skipping mobile number backfill for {profile.name}. "
					f"Normalized mobile number {user_mobile_no} already belongs to {existing_profile}."
				),
			)
			continue

		frappe.db.set_value(
			"Customer Profile",
			profile.name,
			"mobile_no",
			user_mobile_no,
			update_modified=False,
		)
