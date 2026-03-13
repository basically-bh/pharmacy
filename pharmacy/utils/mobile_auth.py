from __future__ import annotations

import hashlib
import secrets
from typing import Final

OTP_LENGTH: Final[int] = 6
ACCESS_TOKEN_BYTES: Final[int] = 32


def normalize_mobile_no(value: str | None) -> str | None:
	if value is None:
		return None

	raw = str(value).strip()
	if not raw:
		return None

	if raw.startswith("+"):
		digits = "".join(ch for ch in raw[1:] if ch.isdigit())
		return f"+{digits}" if digits else None

	digits = "".join(ch for ch in raw if ch.isdigit())
	if not digits:
		return None
	if digits.startswith("00"):
		digits = digits[2:]
	if len(digits) == 8:
		return f"+973{digits}"
	if digits.startswith("973"):
		return f"+{digits}"
	return f"+{digits}"


def mask_mobile_no(value: str | None) -> str | None:
	normalized = normalize_mobile_no(value)
	if not normalized:
		return None

	digits = normalized[1:]
	if len(digits) <= 4:
		return normalized
	return f"+{'*' * (len(digits) - 4)}{digits[-4:]}"


def hash_secret(value: str) -> str:
	return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_numeric_otp() -> str:
	return "".join(secrets.choice("0123456789") for _ in range(OTP_LENGTH))


def generate_access_token() -> str:
	return secrets.token_urlsafe(ACCESS_TOKEN_BYTES)
