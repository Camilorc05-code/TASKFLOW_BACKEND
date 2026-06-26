from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserResponse, PasswordChange, PasswordResetRequest, PasswordResetConfirm, UserUpdate
from app.models.user import User
from app.db.dependencies import get_db
from app.auth.dependencies import get_current_user
from app.auth.hash import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.models.team_member import PasswordResetToken
import secrets
from app.utils.email_service import send_password_reset_email


router = APIRouter(tags=["auth"])

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):

    hashed_password = hash_password(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully"
    }

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        user.password,
        db_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    access_token = create_access_token(
        data={
            "sub": db_user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ── Change password (user must be logged in) ────────────────────────────────
@router.post("/change-password", status_code=200)
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


# ── Request password reset (sends token — in production send via email) ─────
@router.post("/reset-password/request", status_code=200)
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    # Always return 200 to avoid email enumeration
    if not user:
        return {"message": "If that email exists, a reset link was sent"}

    # Invalidate old tokens
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == 0
    ).update({"used": 1})
    db.commit()

    token = secrets.token_urlsafe(32)
    reset = PasswordResetToken(user_id=user.id, token=token)
    db.add(reset)
    db.commit()

    # In production: send email with reset link
    # For now: return token in response (dev mode)
    return {
        "message": "Reset token generated",
        "reset_token": token,          # REMOVE in production, use email instead
        "dev_note": "In production this token is sent by email"
    }


# ── Confirm password reset ──────────────────────────────────────────────────
@router.post("/reset-password/confirm", status_code=200)
def confirm_password_reset(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == data.token,
        PasswordResetToken.used == 0
    ).first()

    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = db.query(User).filter(User.id == reset.user_id).first()
    user.hashed_password = hash_password(data.new_password)
    reset.used = 1
    db.commit()
    return {"message": "Password reset successfully. You can now log in."}

# ── Update current user profile ────────────────────────────────────────────
@router.put("/users/me", status_code=200)
def update_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # verificar username duplicado
    if data.username and data.username != current_user.username:
        existing_username = db.query(User).filter(
            User.username == data.username
        ).first()

        if existing_username:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

        current_user.username = data.username

    # verificar email duplicado
    if data.email and data.email != current_user.email:
        existing_email = db.query(User).filter(
            User.email == data.email
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Email already exists"
            )

        current_user.email = data.email

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile updated successfully",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        }
    }
