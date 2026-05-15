"""Auth API endpoints."""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional

from loguru import logger
from backend.core.auth import AuthManager

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class OfflineLoginRequest(BaseModel):
    """Запрос офлайн авторизации."""
    username: str = Field(..., min_length=1, max_length=16, description="Имя пользователя")


class UserProfile(BaseModel):
    """Профиль пользователя."""
    username: str
    uuid: str
    auth_type: str  # "offline" | "microsoft"


class MicrosoftLoginStartResponse(BaseModel):
    """Ответ начала MS OAuth."""
    url: str
    state: str
    code_verifier: str


class MicrosoftLoginCompleteRequest(BaseModel):
    """Запрос завершения MS OAuth."""
    client_id: str
    auth_code: str
    code_verifier: str


class MicrosoftRefreshRequest(BaseModel):
    """Запрос обновления токена."""
    client_id: str
    refresh_token: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/auth/offline/login", response_model=UserProfile)
async def offline_login(request: OfflineLoginRequest):
    """Офлайн авторизация (без проверки)."""
    try:
        profile = AuthManager.offline_login(request.username)
        return UserProfile(
            username=profile.username,
            uuid=profile.uuid,
            auth_type=profile.auth_type
        )
    except Exception as e:
        logger.error(f"offline_login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")


@router.post("/auth/microsoft/login/start", response_model=MicrosoftLoginStartResponse)
async def microsoft_login_start(client_id: str = Query(...)):
    """Начать Microsoft OAuth авторизацию."""
    try:
        result = AuthManager.microsoft_login_start(client_id)
        return MicrosoftLoginStartResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/microsoft/login/complete", response_model=UserProfile)
async def microsoft_login_complete(request: MicrosoftLoginCompleteRequest):
    """Завершить Microsoft OAuth авторизацию."""
    try:
        profile = AuthManager.microsoft_login_complete(
            client_id=request.client_id,
            auth_code=request.auth_code,
            code_verifier=request.code_verifier
        )
        return UserProfile(
            username=profile.username,
            uuid=profile.uuid,
            auth_type=profile.auth_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/microsoft/refresh", response_model=UserProfile)
async def microsoft_refresh(request: MicrosoftRefreshRequest):
    """Обновить Microsoft access token."""
    try:
        profile = AuthManager.microsoft_refresh(
            client_id=request.client_id,
            refresh_token=request.refresh_token
        )
        return UserProfile(
            username=profile.username,
            uuid=profile.uuid,
            auth_type=profile.auth_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/auth/profile", response_model=UserProfile)
async def get_current_profile():
    """Получить текущий профиль пользователя."""
    try:
        profile = AuthManager.get_current_profile()
        if profile is None:
            raise HTTPException(
                status_code=404,
                detail="No profile found"
            )
        return UserProfile(
            username=profile.username,
            uuid=profile.uuid,
            auth_type=profile.auth_type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_current_profile error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load profile: {e}")


@router.post("/auth/logout")
async def logout():
    """Выйти из аккаунта."""
    try:
        AuthManager.logout()
        return {"status": "logged_out"}
    except Exception as e:
        logger.error(f"logout error: {e}")
        raise HTTPException(status_code=500, detail=f"Logout failed: {e}")
