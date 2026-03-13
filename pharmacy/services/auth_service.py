from __future__ import annotations

import hmac

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime

from pharmacy.pharmacy.doctype.mobile_otp_request.mobile_otp_request import get_stored_otp_hash
from pharmacy.services.mobile_app_user_service import (
	ensure_mobile_app_user_is_active,
	get_mobile_app_user_by_mobile,
	get_or_create_mobile_app_user,
	serialize_mobile_app_user_profile,
	touch_mobile_app_user_activity,
	update_mobile_app_user_verification,
)
from pharmacy.services.mobile_service import MobileApiError
from pharmacy.utils.mobile_auth import (
	OTP_LENGTH,
	generate_access_token,
	generate_numeric_otp,
	hash_secret,
	mask_mobile_no,
	normalize_mobile_no,
)

OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_SEND_WINDOW_MINUTES = 10
OTP_MAX_SENDS_PER_WINDOW = 3
ACCESS_TOKEN_EXPIRY_DAYS = 30
ACCESS_TOKEN_GENERATION_ATTEMPTS = 5
AUTH_CONTEXT_KEY = "pharmacy_mobile_auth_context"


def send_otp(mobile_no: str | None) -> dict:
	normalized_mobile_no = normalize_mobile_no(mobile_no)
	if not normalized_mobile_no:
		_raise_invalid_input(_("A valid mobile_no is required."), {"field": "mobile_no"})

	_enforce_send_rate_limit(normalized_mobile_no)
	app_user = get_or_create_mobile_app_user(normalized_mobile_no)
	ensure_mobile_app_user_is_active(app_user)
	_expire_pending_otp_requests(normalized_mobile_no)

	otp_code = generate_numeric_otp()
	otp_request = _create_otp_request(app_user, otp_code)
	frappe.db.set_value("Mobile App User", app_user.name, "otp_verification_status", "Pending", update_modified=False)
	_deliver_otp(normalized_mobile_no, otp_code)

	response = {
		"success": True,
		"otp_sent": True,
		"expires_in_seconds": OTP_EXPIRY_MINUTES * 60,
		"masked_mobile_no": mask_mobile_no(normalized_mobile_no),
	}
	if _is_debug_auth_enabled():
		response["debug_otp"] = otp_code
	return response


def verify_otp(mobile_no: str | None, otp: str | None) -> dict:
	app_user, _ = _verify_otp_request(mobile_no=mobile_no, otp=otp)
	return {
		"success": True,
		"verified": True,
		"mobile_app_user": serialize_mobile_app_user_profile(get_current_mobile_app_user_for_name(app_user.name)),
	}


def login_with_otp(
	mobile_no: str | None,
	otp: str | None,
	device_name: str | None = None,
	platform: str | None = None,
	app_version: str | None = None,
) -> dict:
	app_user, _ = _verify_otp_request(mobile_no=mobile_no, otp=otp)
	token_value, token_doc = _issue_access_token(
		app_user,
		device_name=device_name,
		platform=platform,
		app_version=app_version,
	)
	touch_mobile_app_user_activity(
		app_user.name,
		device_name=device_name,
		platform=platform,
		app_version=app_version,
		update_last_login=True,
	)
	context = _build_token_context(
		token_doc,
		token_value=token_value,
		update_last_used=False,
		touch_activity=False,
	)
	return {
		"access_token": token_value,
		"token_type": "Bearer",
		"expires_at": token_doc.expires_at,
		"expires_in_seconds": ACCESS_TOKEN_EXPIRY_DAYS * 24 * 60 * 60,
		"user": _serialize_auth_user(context),
	}


def get_current_mobile_session() -> dict:
	context = get_authenticated_mobile_context(required=False)
	if not context:
		return {"authenticated": False, "guest": True, "user": None}
	return {
		"authenticated": True,
		"guest": False,
		"auth_type": context.auth_type,
		"expires_at": context.get("expires_at"),
		"user": _serialize_auth_user(context),
	}


def logout_mobile_session() -> dict:
	context = get_authenticated_mobile_context(required=False)
	if not context:
		return {"success": True, "logged_out": False}
	if context.auth_type == "bearer" and context.get("token_name"):
		_revoke_access_token(context.token_name, reason="Logged out from mobile app")
	setattr(frappe.local, AUTH_CONTEXT_KEY, False)
	return {"success": True, "logged_out": True}


def get_authenticated_mobile_context(*, required: bool = True):
	cached_context = getattr(frappe.local, AUTH_CONTEXT_KEY, None)
	if cached_context is not None:
		if required and not cached_context:
			_raise_authentication_required()
		return cached_context or None

	access_token = _extract_bearer_token()
	context = None
	if access_token:
		context = authenticate_access_token(access_token, required=required)
	elif required:
		_raise_authentication_required()

	setattr(frappe.local, AUTH_CONTEXT_KEY, context or False)
	return context


def authenticate_access_token(access_token: str, *, required: bool = True):
	token_hash = hash_secret(access_token)
	token_doc = frappe.db.get_value(
		"Mobile Access Token",
		{"token_hash": token_hash},
		["name", "mobile_app_user", "status", "expires_at", "platform", "device_name", "app_version"],
		as_dict=True,
	)
	if not token_doc:
		if required:
			_raise_authentication_required()
		return None

	now = now_datetime()
	if token_doc.status != "Active":
		if required:
			_raise_authentication_required()
		return None

	if get_datetime(token_doc.expires_at) <= now:
		frappe.db.set_value(
			"Mobile Access Token",
			token_doc.name,
			{
				"status": "Expired",
				"revoked_on": now,
				"revocation_reason": "Expired",
			},
			update_modified=False,
		)
		if required:
			raise MobileApiError(
				code="token_expired",
				message=_("The access token has expired. Please log in again."),
				http_status_code=401,
			)
		return None

	context = _build_token_context(
		token_doc,
		token_value=access_token,
		update_last_used=True,
		touch_activity=True,
	)
	setattr(frappe.local, AUTH_CONTEXT_KEY, context)
	return context


def get_current_mobile_app_user_for_name(name: str):
	app_user = frappe.db.get_value("Mobile App User", name, "*", as_dict=True)
	if not app_user:
		raise_not_found_mobile_user(name)
	return frappe._dict(app_user)


def _verify_otp_request(*, mobile_no: str | None, otp: str | None):
	normalized_mobile_no = normalize_mobile_no(mobile_no)
	if not normalized_mobile_no:
		_raise_invalid_input(_("A valid mobile_no is required."), {"field": "mobile_no"})

	otp_code = (otp or "").strip()
	if len(otp_code) != OTP_LENGTH or not otp_code.isdigit():
		_raise_invalid_input(_("A valid OTP is required."), {"field": "otp"})

	otp_request = _get_latest_pending_otp_request(normalized_mobile_no)
	if not otp_request:
		raise MobileApiError(
			code="invalid_otp",
			message=_("The OTP is invalid or has expired."),
			http_status_code=422,
		)

	now = now_datetime()
	if get_datetime(otp_request.expires_at) <= now:
		_mark_otp_request_status(otp_request.name, "Expired")
		raise MobileApiError(
			code="otp_expired",
			message=_("The OTP has expired. Please request a new code."),
			http_status_code=422,
		)

	if (otp_request.attempt_count or 0) >= (otp_request.max_attempts or OTP_MAX_ATTEMPTS):
		_lock_otp_request(otp_request.name)
		raise MobileApiError(
			code="otp_locked",
			message=_("Too many invalid OTP attempts. Please request a new code."),
			http_status_code=429,
		)

	stored_otp_hash = get_stored_otp_hash(otp_request.name)
	if not stored_otp_hash or not hmac.compare_digest(hash_secret(otp_code), stored_otp_hash):
		attempt_count = (otp_request.attempt_count or 0) + 1
		values = {"attempt_count": attempt_count}
		if attempt_count >= (otp_request.max_attempts or OTP_MAX_ATTEMPTS):
			values["status"] = "Locked"
			values["locked_on"] = now
		frappe.db.set_value("Mobile OTP Request", otp_request.name, values, update_modified=False)
		raise MobileApiError(
			code="invalid_otp",
			message=_("The OTP is invalid or has expired."),
			http_status_code=422,
			details={"remaining_attempts": max((otp_request.max_attempts or OTP_MAX_ATTEMPTS) - attempt_count, 0)},
		)

	app_user = get_mobile_app_user_by_mobile(normalized_mobile_no)
	ensure_mobile_app_user_is_active(app_user)
	update_mobile_app_user_verification(app_user.name)
	frappe.db.set_value(
		"Mobile OTP Request",
		otp_request.name,
		{
			"status": "Consumed",
			"verified_on": now,
			"consumed_on": now,
			"attempt_count": (otp_request.attempt_count or 0) + 1,
		},
		update_modified=False,
	)
	return get_current_mobile_app_user_for_name(app_user.name), otp_request


def _build_token_context(token_doc, *, token_value: str, update_last_used: bool, touch_activity: bool):
	app_user = get_current_mobile_app_user_for_name(token_doc.mobile_app_user)
	ensure_mobile_app_user_is_active(app_user)

	if update_last_used:
		frappe.db.set_value(
			"Mobile Access Token",
			token_doc.name,
			{
				"last_used_on": now_datetime(),
				"last_ip": _get_request_ip(),
			},
			update_modified=False,
		)

	if touch_activity:
		touch_mobile_app_user_activity(
			app_user.name,
			device_name=token_doc.device_name,
			platform=token_doc.platform,
			app_version=token_doc.app_version,
			update_last_login=False,
		)

	return frappe._dict(
		{
			"auth_type": "bearer",
			"user": app_user.name,
			"mobile_app_user": app_user,
			"token_name": token_doc.name,
			"expires_at": token_doc.expires_at,
			"token_prefix": token_value[:8],
		}
	)


def _serialize_auth_user(context) -> dict:
	app_user = context.mobile_app_user
	return {
		"user_id": app_user.name,
		"mobile_app_user_id": app_user.name,
		"customer_id": app_user.customer or None,
		"mobile_no": app_user.mobile_no or None,
		"full_name": app_user.full_name or None,
		"is_mobile_no_verified": bool(app_user.is_mobile_no_verified),
	}


def _create_otp_request(app_user, otp_code: str):
	now = now_datetime()
	doc = frappe.get_doc(
		{
			"doctype": "Mobile OTP Request",
			"mobile_no": app_user.mobile_no,
			"mobile_app_user": app_user.name,
			"status": "Pending",
			"otp_hash": hash_secret(otp_code),
			"attempt_count": 0,
			"max_attempts": OTP_MAX_ATTEMPTS,
			"expires_at": add_to_date(now, minutes=OTP_EXPIRY_MINUTES, as_datetime=True),
			"sent_on": now,
			"request_ip": _get_request_ip(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def _deliver_otp(mobile_no: str, otp_code: str) -> None:
	message = _("Your Basically verification code is {0}. It expires in {1} minutes.").format(
		otp_code, OTP_EXPIRY_MINUTES
	)
	for hook_path in frappe.get_hooks("mobile_otp_delivery"):
		dispatcher = frappe.get_attr(hook_path)
		dispatcher(mobile_no=mobile_no, message=message, otp_code=otp_code)
		return

	try:
		from frappe.core.doctype.sms_settings.sms_settings import send_sms
	except (ImportError, TypeError):
		send_sms = None

	if callable(send_sms):
		try:
			send_sms(receiver_list=[mobile_no], msg=message)
			return
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Pharmacy Mobile OTP Delivery Error")
			raise MobileApiError(
				code="otp_delivery_failed",
				message=_("Failed to deliver OTP."),
				http_status_code=500,
			)

	if _is_debug_auth_enabled():
		frappe.logger("pharmacy.mobile_auth").info("OTP for %s: %s", mobile_no, otp_code)
		return

	raise MobileApiError(
		code="otp_delivery_unavailable",
		message=_("OTP delivery is not configured."),
		http_status_code=500,
	)


def _get_latest_pending_otp_request(mobile_no: str):
	otp_requests = frappe.get_all(
		"Mobile OTP Request",
		filters={"mobile_no": mobile_no, "status": "Pending"},
		fields=["name", "mobile_no", "mobile_app_user", "status", "attempt_count", "max_attempts", "expires_at", "sent_on"],
		order_by="sent_on desc, creation desc",
		limit_page_length=5,
	)
	now = now_datetime()
	for otp_request in otp_requests:
		if otp_request.expires_at and get_datetime(otp_request.expires_at) <= now:
			_mark_otp_request_status(otp_request.name, "Expired")
			continue
		return otp_request
	return None


def _expire_pending_otp_requests(mobile_no: str) -> None:
	pending_names = frappe.get_all(
		"Mobile OTP Request",
		pluck="name",
		filters={"mobile_no": mobile_no, "status": "Pending"},
	)
	for name in pending_names:
		frappe.db.set_value("Mobile OTP Request", name, "status", "Expired", update_modified=False)


def _mark_otp_request_status(name: str, status: str) -> None:
	frappe.db.set_value("Mobile OTP Request", name, "status", status, update_modified=False)


def _lock_otp_request(name: str) -> None:
	frappe.db.set_value(
		"Mobile OTP Request",
		name,
		{"status": "Locked", "locked_on": now_datetime()},
		update_modified=False,
	)


def _issue_access_token(
	app_user,
	*,
	device_name: str | None = None,
	platform: str | None = None,
	app_version: str | None = None,
):
	now = now_datetime()
	for _ in range(ACCESS_TOKEN_GENERATION_ATTEMPTS):
		token_value = generate_access_token()
		token_hash = hash_secret(token_value)
		if frappe.db.exists("Mobile Access Token", {"token_hash": token_hash}):
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Mobile Access Token",
				"mobile_app_user": app_user.name,
				"status": "Active",
				"token_prefix": token_value[:8],
				"token_hash": token_hash,
				"issued_on": now,
				"expires_at": add_to_date(now, days=ACCESS_TOKEN_EXPIRY_DAYS, as_datetime=True),
				"platform": (platform or "").strip() or None,
				"device_name": (device_name or "").strip() or None,
				"app_version": (app_version or "").strip() or None,
				"last_ip": _get_request_ip(),
			}
		)
		doc.insert(ignore_permissions=True)
		return token_value, doc

	raise MobileApiError(
		code="token_generation_failed",
		message=_("Failed to create an access token. Please try again."),
		http_status_code=500,
	)


def _revoke_access_token(token_name: str, *, reason: str) -> None:
	frappe.db.set_value(
		"Mobile Access Token",
		token_name,
		{
			"status": "Revoked",
			"revoked_on": now_datetime(),
			"revocation_reason": reason,
		},
		update_modified=False,
	)


def _enforce_send_rate_limit(mobile_no: str) -> None:
	window_start = add_to_date(now_datetime(), minutes=-OTP_SEND_WINDOW_MINUTES, as_datetime=True)
	send_count = frappe.db.count(
		"Mobile OTP Request",
		filters={"mobile_no": mobile_no, "sent_on": (">=", window_start)},
	)
	if send_count >= OTP_MAX_SENDS_PER_WINDOW:
		raise MobileApiError(
			code="too_many_requests",
			message=_("Too many OTP requests. Please try again later."),
			http_status_code=429,
		)


def _extract_bearer_token() -> str | None:
	header_value = _get_request_header("Authorization")
	if not header_value:
		return None
	try:
		auth_type, token = header_value.split(" ", 1)
	except ValueError:
		return None
	if auth_type.lower() != "bearer":
		return None
	return token.strip() or None


def _get_request_header(name: str) -> str | None:
	header_getter = getattr(frappe, "get_request_header", None)
	if callable(header_getter):
		value = header_getter(name)
		if value:
			return value

	request = getattr(frappe.local, "request", None)
	if not request:
		return None

	headers = getattr(request, "headers", None)
	if headers:
		value = headers.get(name)
		if value:
			return value

	environ = getattr(request, "environ", None) or {}
	return environ.get(f"HTTP_{name.upper().replace('-', '_')}")


def _get_request_ip() -> str | None:
	request = getattr(frappe.local, "request", None)
	if not request:
		return None
	headers = getattr(request, "headers", None) or {}
	return headers.get("X-Forwarded-For") or getattr(request, "remote_addr", None)


def _is_debug_auth_enabled() -> bool:
	return bool(getattr(frappe.conf, "developer_mode", 0) or getattr(frappe.flags, "in_test", False))


def _raise_authentication_required() -> None:
	raise MobileApiError(
		code="forbidden",
		message=_("Authentication is required."),
		http_status_code=403,
	)


def _raise_invalid_input(message: str, details: dict | None = None) -> None:
	raise MobileApiError(
		code="invalid_input",
		message=message,
		http_status_code=422,
		details=details or {},
	)


def raise_not_found_mobile_user(name: str) -> None:
	raise MobileApiError(
		code="not_found",
		message=_("Mobile App User {0} was not found.").format(name),
		http_status_code=404,
		details={"resource": "Mobile App User", "resource_id": name},
	)
