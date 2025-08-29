"""Dependency injection container (very light-weight)."""
from __future__ import annotations

from app.core.config import get_settings
from app.application.authentication.services.auth_service import AuthService
from app.infrastructure.repositories.user_repository import InMemoryUserRepository, UserRepositoryProtocol
from app.core.security import JWTService

_USER_REPO: UserRepositoryProtocol | None = None
_AUTH_SERVICE: AuthService | None = None
_JWT_SERVICE: JWTService | None = None


def get_user_repository() -> UserRepositoryProtocol:
    global _USER_REPO  # noqa: PLW0603
    if _USER_REPO is None:
        _USER_REPO = InMemoryUserRepository()
    return _USER_REPO


def get_jwt_service() -> JWTService:
    global _JWT_SERVICE  # noqa: PLW0603
    if _JWT_SERVICE is None:
        settings = get_settings()
        _JWT_SERVICE = JWTService(settings.secret_key, settings.jwt_algorithm)
    return _JWT_SERVICE


def get_auth_service() -> AuthService:
    global _AUTH_SERVICE  # noqa: PLW0603
    if _AUTH_SERVICE is None:
        _AUTH_SERVICE = AuthService(get_user_repository(), get_jwt_service())
    return _AUTH_SERVICE


def get_secret_key() -> str:
    return get_settings().secret_key
