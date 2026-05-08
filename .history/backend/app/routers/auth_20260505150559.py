import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User
from app.schemas import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
)
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.services.email import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()

    if len(payload.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters",
        )

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(
        email=email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
    )


@router.post("/request-password-reset")
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    email = payload.email.lower().strip()

    user = db.query(User).filter(User.email == email).first()

    generic_response = {
        "message": "If this email exists, password reset instructions will be sent."
    }

    if not user:
        return generic_response

    reset_token = secrets.token_urlsafe(32)

    user.reset_token_hash = hash_password(reset_token)
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    db.commit()

    query = urlencode(
        {
            "email": email,
            "token": reset_token,
        }
    )

    reset_url = f"{settings.frontend_url}/reset-password?{query}"

    send_password_reset_email(
        to_email=email,
        reset_url=reset_url,
    )

    return generic_response


@router.post("/reset-password")
def reset_password(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    email = payload.email.lower().strip()

    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 8 characters",
        )

    user = db.query(User).filter(User.email == email).first()

    if not user or not user.reset_token_hash or not user.reset_token_expires_at:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    expires_at = user.reset_token_expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        user.reset_token_hash = None
        user.reset_token_expires_at = None
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if not verify_password(payload.reset_token, user.reset_token_hash):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(payload.new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None

    db.commit()

    return {"status": "password_reset"}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 8 characters",
        )

    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(payload.new_password)

    db.commit()

    return {"status": "password_changed"}