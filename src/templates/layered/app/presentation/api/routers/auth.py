from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.di import get_auth_service, get_user_repository
from app.application.authentication.services.auth_service import AuthService
from app.core.security import get_current_user, require_roles
from app.domain.entities.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", status_code=201)
def register(req: RegisterRequest, svc: AuthService = Depends(get_auth_service)):
    try:
        user = svc.register(req.username, req.password)
        return {"id": user.id, "username": user.username}
    except ValueError as e:  # pragma: no cover - simple branch
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, svc: AuthService = Depends(get_auth_service)):
    if not svc.authenticate(req.username, req.password):
        raise HTTPException(status_code=401, detail="invalid credentials")
    user = get_user_repository().get_by_username(req.username)
    token = svc.create_access_token(user)  # type: ignore[arg-type]
    return TokenResponse(access_token=token)


@router.get("/me")
def me(current: User = Depends(get_current_user)):
    return {"id": current.id, "username": current.username, "roles": current.roles}


@router.get("/admin/ping", dependencies=[Depends(require_roles("admin"))])
def admin_ping():
    return {"message": "admin-ok"}
