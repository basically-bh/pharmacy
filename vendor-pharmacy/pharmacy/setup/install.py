from __future__ import annotations

from pharmacy.setup.custom_fields import apply_custom_fields
from pharmacy.setup.standard_doctypes import STANDARD_CUSTOM_FIELDS


def setup() -> None:
	"""Install/migrate entry point for Pharmacy-managed metadata."""
	apply_custom_fields(get_custom_fields())


def get_custom_fields() -> dict[str, list[dict]]:
	"""Return all standard DocType custom fields managed by this app."""
	return STANDARD_CUSTOM_FIELDS
