from __future__ import annotations

from datetime import timedelta
from typing import Sequence

from passlib.context import CryptContext

from app.core.config import get_settings
from app.domain.entities.user import User
from app.infrastructure.repositories.user_repository import UserRepositoryProtocol
from app.core.security import JWTService

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service using repository + JWT service."""

    def __init__(self, repo: UserRepositoryProtocol, jwt_service: JWTService) -> None:
        self._repo = repo
        self._jwt = jwt_service

    def register(self, username: str, password: str, roles: Sequence[str] | None = None) -> User:
        if self._repo.get_by_username(username):  # type: ignore[arg-type]
            raise ValueError("User already exists")
        hashed = PWD_CONTEXT.hash(password)
        return self._repo.create(username=username, password_hash=hashed, roles=list(roles or ["user"]))

    def authenticate(self, username: str, password: str) -> bool:
        user = self._repo.get_by_username(username)
        if not user:
            return False
        return PWD_CONTEXT.verify(password, user.password_hash)

    def create_access_token(self, user: User) -> str:
        settings = get_settings()
        return self._jwt.encode(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.access_token_exp_minutes),
            roles=user.roles,
            username=user.username,
        )
