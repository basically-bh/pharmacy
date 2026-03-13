from __future__ import annotations

import frappe
from frappe import _

from pharmacy.pharmacy.doctype.mobile_app_user.mobile_app_user import render_mobile_app_user_address_html
from pharmacy.services.mobile_service import cbool, raise_forbidden, raise_invalid_input, raise_not_found
from pharmacy.utils.mobile_auth import normalize_mobile_no

DEFAULT_COUNTRY_CODE = "+973"
DEFAULT_LANGUAGE = "English"
APP_USER_CONTEXT_FIELDS = [
	"name",
	"full_name",
	"first_name",
	"last_name",
	"country_code",
	"mobile_no",
	"customer",
	"account_status",
	"otp_verification_status",
	"national_id",
	"date_of_birth",
	"gender",
	"default_address",
	"default_payment_method",
	"language",
	"allow_push_notifications",
	"is_mobile_no_verified",
	"customer_created_on_checkout",
	"otp_verified_at",
	"last_login",
	"last_active_at",
	"last_device_name",
	"last_device_platform",
	"app_version",
]


def get_current_mobile_app_user(
	fields: list[str] | tuple[str, ...] | None = None,
	*,
	required: bool = True,
) -> frappe._dict | None:
	from pharmacy.services.auth_service import get_authenticated_mobile_context

	context = get_authenticated_mobile_context(required=False)
	app_user_name = context.mobile_app_user.name if context else _get_request_mobile_app_user_name()
	if not app_user_name:
		if required:
			get_authenticated_mobile_context(required=True)
		return None

	field_list = list(fields or APP_USER_CONTEXT_FIELDS)
	if "name" not in field_list:
		field_list.insert(0, "name")

	app_user = frappe.db.get_value("Mobile App User", app_user_name, field_list, as_dict=True)
	if not app_user:
		if not required:
			return None
		raise_not_found(resource_name="Mobile App User", resource_id=app_user_name)
	return app_user


def get_mobile_app_user_by_mobile(mobile_no: str | None, *, required: bool = True):
	normalized_mobile_no = normalize_mobile_no(mobile_no)
	if not normalized_mobile_no:
		if required:
			raise_invalid_input(
				message=_("A valid mobile_no is required."),
				details={"field": "mobile_no"},
			)
		return None

	app_user = frappe.db.get_value(
		"Mobile App User",
		{"mobile_no": normalized_mobile_no},
		APP_USER_CONTEXT_FIELDS,
		as_dict=True,
	)
	if not app_user:
		if required:
			raise_not_found(resource_name="Mobile App User", resource_id=normalized_mobile_no)
		return None

	return app_user


def get_or_create_mobile_app_user(mobile_no: str | None):
	normalized_mobile_no = normalize_mobile_no(mobile_no)
	if not normalized_mobile_no:
		raise_invalid_input(
			message=_("A valid mobile_no is required."),
			details={"field": "mobile_no"},
		)

	existing = get_mobile_app_user_by_mobile(normalized_mobile_no, required=False)
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Mobile App User",
			"mobile_no": normalized_mobile_no,
			"country_code": DEFAULT_COUNTRY_CODE,
			"account_status": "Active",
			"otp_verification_status": "Not Verified",
			"is_mobile_no_verified": 0,
			"language": DEFAULT_LANGUAGE,
		}
	)
	doc.insert(ignore_permissions=True)
	return frappe._dict(doc.as_dict())


def _get_request_mobile_app_user_name() -> str | None:
	for user in (
		getattr(getattr(frappe.local, "session", None), "user", None),
		getattr(getattr(frappe.local, "login_manager", None), "user", None),
		getattr(getattr(frappe, "session", None), "user", None),
	):
		if not user or user == "Guest":
			continue
		if frappe.db.exists("Mobile App User", user):
			return user
	return None


def ensure_mobile_app_user_is_active(app_user) -> None:
	if (app_user.account_status or "") == "Blocked":
		raise_forbidden(
			message=_("This account is blocked."),
			details={"mobile_app_user": app_user.name},
		)


def touch_mobile_app_user_activity(
	app_user_name: str,
	*,
	device_name: str | None = None,
	platform: str | None = None,
	app_version: str | None = None,
	update_last_login: bool = False,
) -> None:
	now = frappe.utils.now_datetime()
	values = {"last_active_at": now}
	if update_last_login:
		values["last_login"] = now
	if device_name is not None:
		values["last_device_name"] = device_name.strip() or None
	if platform is not None:
		values["last_device_platform"] = platform.strip() or None
	if app_version is not None:
		values["app_version"] = app_version.strip() or None
	frappe.db.set_value("Mobile App User", app_user_name, values, update_modified=False)


def update_mobile_app_user_verification(app_user_name: str) -> None:
	now = frappe.utils.now_datetime()
	frappe.db.set_value(
		"Mobile App User",
		app_user_name,
		{
			"otp_verification_status": "Verified",
			"is_mobile_no_verified": 1,
			"otp_verified_at": now,
			"last_login": now,
			"last_active_at": now,
		},
		update_modified=False,
	)


def serialize_mobile_app_user_profile(app_user) -> dict:
	address = _get_address_data(app_user.default_address)
	default_payment_method = _get_mode_of_payment(app_user.default_payment_method)
	address_html = render_mobile_app_user_address_html(app_user.default_address)
	return {
		"id": app_user.name,
		"full_name": app_user.full_name or None,
		"first_name": app_user.first_name or None,
		"last_name": app_user.last_name or None,
		"country_code": app_user.country_code or None,
		"mobile_no": app_user.mobile_no or None,
		"customer_id": app_user.customer or None,
		"account_status": app_user.account_status or None,
		"otp_verification_status": app_user.otp_verification_status or None,
		"is_mobile_no_verified": cbool(app_user.is_mobile_no_verified),
		"personal_info": {
			"national_id": app_user.national_id or None,
			"date_of_birth": app_user.date_of_birth,
			"gender": app_user.gender or None,
		},
		"preferences": {
			"language": app_user.language or None,
			"allow_push_notifications": cbool(app_user.allow_push_notifications),
			"default_payment_method": default_payment_method,
		},
		"default_address": address,
		"address_html": address_html,
		"device": {
			"last_device_name": app_user.last_device_name or None,
			"last_device_platform": app_user.last_device_platform or None,
			"app_version": app_user.app_version or None,
		},
		"activity": {
			"otp_verified_at": app_user.otp_verified_at,
			"last_login": app_user.last_login,
			"last_active_at": app_user.last_active_at,
		},
	}


def get_mobile_app_user_profile_data() -> dict:
	app_user_name = get_current_mobile_app_user(fields=["name"]).name
	app_user = frappe.get_doc("Mobile App User", app_user_name)
	touch_mobile_app_user_activity(app_user.name)
	app_user.reload()
	return {"mobile_app_user": serialize_mobile_app_user_profile(frappe._dict(app_user.as_dict()))}


def update_mobile_app_user_profile_data(**payload) -> dict:
	app_user = frappe.get_doc("Mobile App User", get_current_mobile_app_user(fields=["name"]).name)

	updatable_fields = (
		"first_name",
		"last_name",
		"country_code",
		"mobile_no",
		"national_id",
		"date_of_birth",
		"gender",
		"language",
		"allow_push_notifications",
		"default_payment_method",
	)
	for fieldname in updatable_fields:
		if fieldname not in payload or payload[fieldname] is None:
			continue
		value = payload[fieldname]
		if fieldname == "allow_push_notifications":
			value = 1 if cbool(value) else 0
		elif isinstance(value, str):
			value = value.strip()
		app_user.set(fieldname, value or None)

	_validate_default_payment_method(app_user.default_payment_method)
	app_user.flags.ignore_permissions = True
	app_user.save(ignore_permissions=True)
	touch_mobile_app_user_activity(app_user.name)
	app_user.reload()
	return {"mobile_app_user": serialize_mobile_app_user_profile(frappe._dict(app_user.as_dict()))}


def get_mobile_app_user_addresses_data() -> dict:
	app_user = get_current_mobile_app_user(fields=["name", "default_address"])
	addresses = [_serialize_address(address_name, default_address=app_user.default_address) for address_name in _get_address_names_for_user(app_user.name)]
	touch_mobile_app_user_activity(app_user.name)
	return {"addresses": addresses}


def create_mobile_app_user_address_data(
	*,
	address_title: str | None = None,
	address_type: str | None = None,
	address_line1: str | None = None,
	address_line2: str | None = None,
	city: str | None = None,
	state: str | None = None,
	country: str | None = None,
	pincode: str | None = None,
	email_id: str | None = None,
	phone: str | None = None,
	is_default: int | str | bool | None = None,
) -> dict:
	app_user = get_current_mobile_app_user(fields=["name", "full_name", "mobile_no", "customer", "default_address"])
	if not address_line1 or not str(address_line1).strip():
		raise_invalid_input(message=_("address_line1 is required."), details={"field": "address_line1"})
	if not city or not str(city).strip():
		raise_invalid_input(message=_("city is required."), details={"field": "city"})
	if not country or not str(country).strip():
		raise_invalid_input(message=_("country is required."), details={"field": "country"})

	address = frappe.get_doc(
		{
			"doctype": "Address",
			"address_title": (address_title or app_user.full_name or app_user.mobile_no or app_user.name).strip(),
			"address_type": (address_type or "Shipping").strip(),
			"address_line1": address_line1.strip(),
			"address_line2": (address_line2 or "").strip() or None,
			"city": city.strip(),
			"state": (state or "").strip() or None,
			"country": country.strip(),
			"pincode": (pincode or "").strip() or None,
			"email_id": (email_id or "").strip() or None,
			"phone": normalize_mobile_no(phone) or ((phone or "").strip() or None),
			"links": [
				{
					"link_doctype": "Mobile App User",
					"link_name": app_user.name,
				}
			],
		}
	)
	if app_user.customer:
		address.append(
			"links",
			{
				"link_doctype": "Customer",
				"link_name": app_user.customer,
			},
		)

	address.insert(ignore_permissions=True)

	if cbool(is_default) or not app_user.default_address:
		_set_default_address(app_user.name, address.name)

	touch_mobile_app_user_activity(app_user.name)
	current_default = frappe.db.get_value("Mobile App User", app_user.name, "default_address")
	return {"address": _serialize_address(address.name, default_address=current_default)}


def set_default_address_data(address_id: str | None = None) -> dict:
	app_user = get_current_mobile_app_user(fields=["name"])
	address_name = _get_owned_address_name(app_user.name, address_id)
	_set_default_address(app_user.name, address_name)
	touch_mobile_app_user_activity(app_user.name)
	return {
		"success": True,
		"default_address": _serialize_address(address_name, default_address=address_name),
	}


def get_app_payment_methods_data() -> dict:
	payment_methods = frappe.get_all(
		"Mode of Payment",
		filters={"is_app_payment_method": 1},
		fields=["name", "type"],
		order_by="name asc",
	)
	return {
		"payment_methods": [
			{
				"id": row.name,
				"name": row.name,
				"type": row.type or None,
			}
			for row in payment_methods
		]
	}


def _set_default_address(app_user_name: str, address_name: str | None) -> None:
	if address_name and not _has_mobile_app_user_link(address_name, app_user_name):
		raise_forbidden(
			message=_("You do not have access to this address."),
			details={"resource": "Address", "resource_id": address_name},
		)

	frappe.db.set_value(
		"Mobile App User",
		app_user_name,
		"default_address",
		address_name,
		update_modified=False,
	)


def _serialize_address(address_name: str, *, default_address: str | None) -> dict:
	address = _get_address_data(address_name)
	if not address:
		raise_not_found(resource_name="Address", resource_id=address_name)

	address["is_default"] = address_name == default_address
	return address


def _get_address_data(address_name: str | None) -> dict | None:
	if not address_name:
		return None

	address = frappe.db.get_value(
		"Address",
		address_name,
		[
			"name",
			"address_title",
			"address_type",
			"address_line1",
			"address_line2",
			"city",
			"state",
			"country",
			"pincode",
			"email_id",
			"phone",
		],
		as_dict=True,
	)
	if not address:
		return None

	address_doc = frappe.get_cached_doc("Address", address_name)
	return {
		"id": address.name,
		"title": address.address_title or None,
		"address_type": address.address_type or None,
		"address_line1": address.address_line1 or None,
		"address_line2": address.address_line2 or None,
		"city": address.city or None,
		"state": address.state or None,
		"country": address.country or None,
		"pincode": address.pincode or None,
		"email_id": address.email_id or None,
		"phone": address.phone or None,
		"display_html": render_mobile_app_user_address_html(address_doc.name),
	}


def _get_mode_of_payment(mode_of_payment: str | None) -> dict | None:
	if not mode_of_payment:
		return None
	row = frappe.db.get_value(
		"Mode of Payment",
		mode_of_payment,
		["name", "type", "is_app_payment_method"],
		as_dict=True,
	)
	if not row:
		return None
	return {
		"id": row.name,
		"name": row.name,
		"type": row.type or None,
		"is_app_payment_method": cbool(row.is_app_payment_method),
	}


def _validate_default_payment_method(mode_of_payment: str | None) -> None:
	if not mode_of_payment:
		return

	is_app_payment_method = frappe.db.get_value("Mode of Payment", mode_of_payment, "is_app_payment_method")
	if not is_app_payment_method:
		raise_invalid_input(
			message=_("Selected payment method is not available in the mobile app."),
			details={"field": "default_payment_method", "value": mode_of_payment},
		)


def _get_address_names_for_user(app_user_name: str) -> list[str]:
	rows = frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Address",
			"link_doctype": "Mobile App User",
			"link_name": app_user_name,
		},
		pluck="parent",
		order_by="parent asc",
	)
	return list(dict.fromkeys(rows))


def _get_owned_address_name(app_user_name: str, address_name: str | None) -> str:
	address_name = (address_name or "").strip()
	if not address_name:
		raise_invalid_input(message=_("address_id is required."), details={"field": "address_id"})
	if not frappe.db.exists("Address", address_name):
		raise_not_found(resource_name="Address", resource_id=address_name)
	if not _has_mobile_app_user_link(address_name, app_user_name):
		raise_forbidden(
			message=_("You do not have access to this address."),
			details={"resource": "Address", "resource_id": address_name},
		)
	return address_name


def _has_mobile_app_user_link(address_name: str, app_user_name: str) -> bool:
	return bool(
		frappe.db.exists(
			"Dynamic Link",
			{
				"parenttype": "Address",
				"parent": address_name,
				"link_doctype": "Mobile App User",
				"link_name": app_user_name,
			},
		)
	)
