from __future__ import annotations

from math import ceil

import frappe
from frappe import _

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class MobileApiError(Exception):
	def __init__(
		self,
		*,
		code: str,
		message: str,
		http_status_code: int,
		details: dict | None = None,
	) -> None:
		super().__init__(message)
		self.code = code
		self.message = message
		self.http_status_code = http_status_code
		self.details = details or {}


def execute_api(method, /, *args, **kwargs) -> dict:
	try:
		return method(*args, **kwargs)
	except MobileApiError as exc:
		frappe.local.response["http_status_code"] = exc.http_status_code
		return {
			"error": {
				"code": exc.code,
				"message": exc.message,
				"details": exc.details,
			}
		}
	except frappe.PermissionError:
		return build_error_response(
			code="forbidden",
			message=_("You do not have access to this resource."),
			http_status_code=403,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Pharmacy Mobile API Error")
		return build_error_response(
			code="internal_error",
			message=_("An unexpected error occurred."),
			http_status_code=500,
		)


def require_authenticated_user() -> str:
	user = frappe.session.user
	if not user or user == "Guest":
		raise MobileApiError(
			code="forbidden",
			message=_("Authentication is required."),
			http_status_code=403,
		)
	return user


def get_current_mobile_app_user(
	fields: list[str] | tuple[str, ...] | None = None,
	*,
	required: bool = True,
) -> frappe._dict | None:
	require_authenticated_user()
	from pharmacy.services.auth_service import get_authenticated_mobile_context

	context = frappe._dict(get_authenticated_mobile_context())
	app_user_name = context.get("mobile_app_user_id")
	if not app_user_name:
		if not required:
			return None
		raise_not_found(
			resource_name="Mobile App User",
			message=_("Mobile App User not found for the authenticated session."),
		)

	field_list = list(fields or ["name", "customer", "full_name", "mobile_no", "default_address"])
	if "name" not in field_list:
		field_list.insert(0, "name")

	app_user = frappe.db.get_value(
		"Mobile App User",
		app_user_name,
		field_list,
		as_dict=True,
	)
	if not app_user:
		if not required:
			return None
		raise_not_found(
			resource_name="Mobile App User",
			resource_id=app_user_name,
			message=_("Mobile App User not found for the authenticated session."),
		)
	return app_user


def get_current_customer(*, required: bool = False) -> str | None:
	require_authenticated_user()
	from pharmacy.services.auth_service import get_authenticated_mobile_context

	context = frappe._dict(get_authenticated_mobile_context())
	customer_id = context.get("customer_id")
	if customer_id or not required:
		return customer_id

	raise_not_found(
		resource_name="Customer",
		message=_("Customer not found for the authenticated mobile user."),
	)


def parse_pagination(page: int | str = 1, page_size: int | str = DEFAULT_PAGE_SIZE) -> tuple[int, int, int]:
	page_number = parse_positive_int(page, fieldname="page")
	size = parse_positive_int(page_size, fieldname="page_size")
	if size > MAX_PAGE_SIZE:
		raise_invalid_input(
			message=_("page_size cannot be greater than {0}.").format(MAX_PAGE_SIZE),
			details={"field": "page_size", "max_value": MAX_PAGE_SIZE},
		)
	offset = (page_number - 1) * size
	return page_number, size, offset


def build_list_response(
	*,
	items: list[dict],
	page: int,
	page_size: int,
	total_count: int,
) -> dict:
	total_pages = ceil(total_count / page_size) if total_count else 0
	return {
		"items": items,
		"pagination": {
			"page": page,
			"page_size": page_size,
			"total_count": total_count,
			"total_pages": total_pages,
			"has_next": page < total_pages,
			"has_previous": page > 1,
		},
	}


def parse_positive_int(value: int | str | None, *, fieldname: str) -> int:
	try:
		parsed = int(value)
	except (TypeError, ValueError):
		raise_invalid_input(
			message=_("{0} must be a positive integer.").format(fieldname),
			details={"field": fieldname, "value": value},
		)
	if parsed < 1:
		raise_invalid_input(
			message=_("{0} must be greater than or equal to 1.").format(fieldname),
			details={"field": fieldname, "value": value},
		)
	return parsed


def cbool(value: int | str | bool | None) -> bool:
	if isinstance(value, bool):
		return value
	if value is None:
		return False
	return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_request_value(key: str, aliases: tuple[str, ...] = ()) -> str | None:
	for candidate in (key, *aliases):
		value = frappe.form_dict.get(candidate)
		if value is None:
			continue
		return value.strip() if isinstance(value, str) else value
	return None


def raise_invalid_input(message: str, details: dict | None = None) -> None:
	raise MobileApiError(
		code="invalid_input",
		message=message,
		http_status_code=422,
		details=details,
	)


def raise_not_found(
	*,
	resource_name: str,
	resource_id: str | None = None,
	message: str | None = None,
	details: dict | None = None,
) -> None:
	resource_label = resource_name if resource_id is None else f"{resource_name} {resource_id}"
	raise MobileApiError(
		code="not_found",
		message=message or _("{0} was not found.").format(resource_label),
		http_status_code=404,
		details=details or {"resource": resource_name, "resource_id": resource_id},
	)


def raise_forbidden(message: str, details: dict | None = None) -> None:
	raise MobileApiError(
		code="forbidden",
		message=message,
		http_status_code=403,
		details=details,
	)


def build_error_response(*, code: str, message: str, http_status_code: int, details: dict | None = None) -> dict:
	frappe.local.response["http_status_code"] = http_status_code
	return {
		"error": {
			"code": code,
			"message": message,
			"details": details or {},
		}
	}


def get_owned_resource_name(
	*,
	doctype: str,
	resource_id: str,
	owner_name: str,
	owner_field: str = "mobile_app_user",
	resource_label: str | None = None,
) -> str:
	resource = frappe.db.get_value(
		doctype,
		resource_id,
		["name", owner_field],
		as_dict=True,
	)
	label = resource_label or doctype
	if not resource:
		raise_not_found(resource_name=label, resource_id=resource_id)
	if resource.get(owner_field) != owner_name:
		raise_forbidden(
			message=_("You do not have access to this {0}.").format(label.lower()),
			details={"resource": label, "resource_id": resource_id},
		)
	return resource.name
