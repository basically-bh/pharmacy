from __future__ import annotations

import hashlib
import secrets
from typing import Final


OTP_LENGTH: Final[int] = 6
ACCESS_TOKEN_BYTES: Final[int] = 32


def normalize_mobile_no(value: str | None) -> str:
	raw_value = (value or "").strip()
	if not raw_value:
		return ""

	characters: list[str] = []
	for index, char in enumerate(raw_value):
		if char.isdigit():
			characters.append(char)
		elif char == "+" and index == 0:
			characters.append(char)

	normalized = "".join(characters)
	if normalized.startswith("00"):
		normalized = f"+{normalized[2:]}"

	if normalized.startswith("+"):
		digit_count = len(normalized) - 1
	else:
		digit_count = len(normalized)

	if digit_count < 8 or digit_count > 15:
		return ""

	return normalized


def mask_mobile_no(value: str | None) -> str | None:
	normalized = normalize_mobile_no(value)
	if not normalized:
		return None

	prefix = "+" if normalized.startswith("+") else ""
	digits = normalized[1:] if prefix else normalized
	if len(digits) <= 4:
		return f"{prefix}{'*' * len(digits)}"
	return f"{prefix}{'*' * (len(digits) - 4)}{digits[-4:]}"


def hash_secret(value: str) -> str:
	return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_numeric_otp() -> str:
	return "".join(secrets.choice("0123456789") for _ in range(OTP_LENGTH))


def generate_access_token() -> str:
	return secrets.token_urlsafe(ACCESS_TOKEN_BYTES)
