from __future__ import annotations

import frappe

from pharmacy.pharmacy.services.mobile_service import cbool, get_current_customer_profile, raise_not_found


def get_profile_data() -> dict:
	profile = get_current_customer_profile(
		fields=[
			"name",
			"user",
			"customer",
			"customer_name",
			"national_id",
			"account_status",
			"profile_completion_status",
			"marketing_opt_in",
			"push_notifications_enabled",
			"default_address",
			"default_payment_method",
		],
		required=False,
	)
	if not profile:
		raise_not_found(
			resource_name="Customer Profile",
			message="Customer Profile not found for the authenticated user.",
		)

	user = (
		frappe.db.get_value(
			"User",
			profile.user,
			["full_name", "email", "mobile_no"],
			as_dict=True,
		)
		if profile.user
		else {}
	) or {}

	return {
		"profile": {
			"id": profile.name,
			"user_id": profile.user,
			"customer_id": profile.customer or None,
			"customer_name": profile.customer_name or None,
			"national_id": profile.national_id or None,
			"account": {
				"status": profile.account_status or None,
				"completion_status": profile.profile_completion_status or None,
			},
			"contact": {
				"full_name": user.get("full_name") or None,
				"email": user.get("email") or None,
				"mobile_no": user.get("mobile_no") or None,
			},
			"preferences": {
				"marketing_opt_in": cbool(profile.marketing_opt_in),
				"push_notifications_enabled": cbool(profile.push_notifications_enabled),
			},
			"defaults": {
				"address_id": profile.default_address or None,
				"payment_method_id": profile.default_payment_method or None,
			},
		}
	}
