from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from lexima_dms.api.deps import get_current_user, get_db
from lexima_dms.api.schemas import Token, UserOut
from lexima_dms.app_core.config import get_settings
from lexima_dms.app_core.security import create_access_token, verify_password
from lexima_dms.db.models import User, UserRole
from lexima_dms.services.ldap_auth import authenticate_ldap

router = APIRouter(prefix="/auth", tags=["auth"])


def _authenticate_user(db: Session, username: str, password: str) -> User | None:
    settings = get_settings()
    user = db.query(User).filter(User.username == username).one_or_none()

    if settings.ldap_enabled:
        if authenticate_ldap(username, password):
            if not user:
                # Auto-create user from AD on first login
                role = UserRole(settings.ldap_default_role)
                user = User(
                    username=username,
                    password_hash="",  # AD user, no local password
                    role=role,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            return user
        # LDAP failed: AD-only users (empty password_hash) can't fall back to local
        if user and not user.password_hash:
            return None

    if user and user.password_hash and verify_password(password, user.password_hash):
        return user
    return None


@router.post("/token", response_model=Token)
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = _authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")

    access_token = create_access_token(subject=user.username, extra={"uid": user.id, "role": user.role.value})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.get("/info")
def auth_info() -> dict:
    """Информация о режиме аутентификации (для отображения на форме входа)."""
    settings = get_settings()
    return {"ldap_enabled": settings.ldap_enabled}

