from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

from app.core.config import get_settings
from app.domain.entities.user import User


class JWTService:
    def __init__(self, secret: str, algorithm: str) -> None:
        self.secret = secret
        self.algorithm = algorithm

    def encode(
        self,
        subject: str,
        expires_delta: timedelta,
        roles: Sequence[str],
        username: str,
    ) -> str:
        to_encode = {
            "sub": subject,
            "username": username,
            "roles": list(r.lower() for r in roles),
            "exp": datetime.now(timezone.utc) + expires_delta,
        }
        return jwt.encode(to_encode, self.secret, algorithm=self.algorithm)

    def decode(self, token: str) -> dict:
        return jwt.decode(token, self.secret, algorithms=[self.algorithm])


bearer = HTTPBearer(auto_error=True)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> User:
    settings = get_settings()
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:  # pragma: no cover - error path
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Late import to avoid circular dependency at module import time
    from app.core.di import get_user_repository  # noqa: WPS433,F401
    repo = get_user_repository()
    user = repo.get_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user  # type: ignore[return-value]


def require_roles(*roles: str):
    role_set = set(r.lower() for r in roles)

    def dependency(user: User = Depends(get_current_user)) -> User:
        if not role_set.intersection(r.lower() for r in user.roles):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return dependency
