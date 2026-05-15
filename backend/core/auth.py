"""Аутентификация пользователей (Offline и Microsoft)."""

import uuid
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

import msal
from loguru import logger

from shared.paths import get_config_dir


@dataclass
class UserProfile:
    """Профиль пользователя."""
    username: str
    uuid: str
    auth_type: str
    access_token: str = ""
    refresh_token: str = ""


class AuthManager:
    """Управление аутентификацией."""

    _profile_file = get_config_dir() / "profile.json"

    @staticmethod
    def offline_login(username: str) -> UserProfile:
        """Офлайн авторизация (генерирует UUID v3 от имени пользователя)."""
        user_uuid = str(uuid.uuid3(uuid.NAMESPACE_OID, username))
        profile = UserProfile(
            username=username,
            uuid=user_uuid,
            auth_type="offline"
        )
        AuthManager._save_profile(profile)
        return profile

    @staticmethod
    def microsoft_login_start(client_id: str) -> dict:
        """Начинает Microsoft OAuth flow (Device Code)."""
        app = msal.PublicClientApplication(client_id)
        flow = app.initiate_device_flow(scopes=["XboxLive.signin"])
        if "user_code" not in flow:
            raise RuntimeError("Failed to create device flow")
        return {
            "url": flow["verification_uri"],
            "state": flow["device_code"],
            "code_verifier": flow["user_code"]
        }

    @staticmethod
    def microsoft_login_complete(client_id: str, auth_code: str, code_verifier: str) -> UserProfile:
        """Завершает Microsoft OAuth через Device Code."""
        app = msal.PublicClientApplication(client_id)
        result = app.acquire_token_by_device_flow(
            {"device_code": auth_code, "user_code": code_verifier}
        )
        if "error" in result:
            raise RuntimeError(result.get("error_description", "Microsoft auth failed"))

        profile = UserProfile(
            username=result.get("account", {}).get("username", "unknown"),
            uuid="",
            auth_type="microsoft",
            access_token=result.get("access_token", ""),
            refresh_token=result.get("refresh_token", "")
        )
        AuthManager._save_profile(profile)
        return profile

    @staticmethod
    def microsoft_refresh(client_id: str, refresh_token: str) -> UserProfile:
        """Обновляет Microsoft токен."""
        app = msal.PublicClientApplication(client_id)
        result = app.acquire_token_by_refresh_token(refresh_token, scopes=["XboxLive.signin"])
        if "error" in result:
            raise RuntimeError(result.get("error_description", "Refresh failed"))

        profile = UserProfile(
            username=result.get("account", {}).get("username", "unknown"),
            uuid="",
            auth_type="microsoft",
            access_token=result.get("access_token", ""),
            refresh_token=result.get("refresh_token", "")
        )
        AuthManager._save_profile(profile)
        return profile

    @staticmethod
    def get_current_profile() -> Optional[UserProfile]:
        """Загружает сохранённый профиль."""
        if not AuthManager._profile_file.exists():
            return None
        try:
            data = json.loads(AuthManager._profile_file.read_text(encoding="utf-8"))
            return UserProfile(**data)
        except Exception as e:
            logger.warning(f"Failed to load profile: {e}")
            return None

    @staticmethod
    def logout() -> None:
        """Удаляет сохранённый профиль."""
        if AuthManager._profile_file.exists():
            AuthManager._profile_file.unlink()

    @staticmethod
    def _save_profile(profile: UserProfile) -> None:
        AuthManager._profile_file.parent.mkdir(parents=True, exist_ok=True)
        AuthManager._profile_file.write_text(
            json.dumps(asdict(profile), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
