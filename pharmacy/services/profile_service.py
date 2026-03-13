from __future__ import annotations

from pharmacy.services import mobile_app_user_service

__all__ = [
	"get_mobile_app_user_profile_data",
	"update_mobile_app_user_profile_data",
]


def get_mobile_app_user_profile_data() -> dict:
	return mobile_app_user_service.get_mobile_app_user_profile_data()


def update_mobile_app_user_profile_data(**payload) -> dict:
	return mobile_app_user_service.update_mobile_app_user_profile_data(**payload)
