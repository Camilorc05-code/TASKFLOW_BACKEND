from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import secrets

from app.db.dependencies import get_db
from app.auth.dependencies import get_current_user
from app.auth.hash import verify_password, hash_password
from app.auth.jwt_handler import create_access_token
from app.models.user import User
from app.models.team_member import PasswordResetToken
from app.schemas.user import UserCreate, UserOut, Token, PasswordChange, PasswordResetRequest, PasswordResetConfirm, UserLogin
from app.utils.email_service import send_password_reset_email

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "Username already taken")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(
        username        = data.username,
        email           = data.email,
        hashed_password = hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    data: UserLogin,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}



# ── Cambiar contraseña (usuario logueado) ─────────────────────────────────
@router.post("/change-password", status_code=200)
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(400, "Current password is incorrect")
    if len(data.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


# ── Solicitar reset de contraseña (envía email con Resend) ─────────────────
@router.post("/reset-password/request", status_code=200)
def request_password_reset(
    data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == data.email).first()
    # Siempre 200 para no revelar si el email existe
    if not user:
        return {"message": "If that email exists, a reset link was sent"}

    # Invalidar tokens anteriores
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used    == 0,
    ).update({"used": 1})
    db.commit()

    token = secrets.token_urlsafe(32)
    db.add(PasswordResetToken(user_id=user.id, token=token))
    db.commit()

    # Enviar email con Resend
    email_sent = send_password_reset_email(
        to_email    = user.email,
        reset_token = token,
        username    = user.username,
    )

    return {
        "message":    "If that email exists, a reset link was sent",
        "email_sent": email_sent,
        # En dev sin Resend configurado, devolvemos el token para poder probar
        **({"reset_token": token, "dev_note": "Configure RESEND_API_KEY to send real emails"} if not email_sent else {}),
    }


# ── Confirmar reset de contraseña ─────────────────────────────────────────
@router.post("/reset-password/confirm", status_code=200)
def confirm_password_reset(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == data.token,
        PasswordResetToken.used  == 0,
    ).first()
    if not reset:
        raise HTTPException(400, "Invalid or expired reset token")
    if len(data.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    user = db.query(User).filter(User.id == reset.user_id).first()
    user.hashed_password = hash_password(data.new_password)
    reset.used = 1
    db.commit()
    return {"message": "Password reset successfully. You can now log in."}
