from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import models, schemas, auth, email_utils, utils
from app.database import get_db

router = APIRouter()

# In-memory store for forgot password codes (replace with Redis/db in production)
forgot_password_codes = {}

# ---------- Sign Up ----------
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user: schemas.SignUpRequest, db: Session = Depends(get_db)):
    if not user.agreed_to_terms:
        raise HTTPException(status_code=400, detail="You must agree to the Terms & Conditions")

    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = auth.hash_password(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_pw,
        agreed_to_terms=user.agreed_to_terms,
        email_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

# ---------- Login ----------
@router.post("/login", response_model=schemas.TokenResponse)
def login(
    user: schemas.LoginRequest,
    request: Request,  # To get user-agent, IP
    db: Session = Depends(get_db),
):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = auth.create_access_token({"user_id": str(db_user.id)})
    refresh_token = auth.create_refresh_token({"user_id": str(db_user.id)})

    # Save refresh token in DB with device info
    user_agent = request.headers.get("user-agent", "unknown")
    ip_address = request.client.host if request.client else None

    # Optionally, delete expired sessions before adding new one (cleanup)
    db.query(models.UserSession).filter(
        models.UserSession.user_id == db_user.id,
        models.UserSession.expires_at < datetime.utcnow()
    ).delete()

    new_session = models.UserSession(
        user_id=db_user.id,
        refresh_token=refresh_token,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(new_session)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# ---------- Forgot Password: Request Code ----------
@router.post("/forgot-password/request-code")
def forgot_password_request(data: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    code = utils.generate_verification_code()
    forgot_password_codes[data.email] = code
    email_utils.send_forgot_password_code(data.email, code)
    return {"message": "Verification code sent to your email"}

# ---------- Forgot Password: Verify Code ----------
@router.post("/forgot-password/verify-code")
def forgot_password_verify(data: schemas.VerifyCodeRequest):
    code = forgot_password_codes.get(data.email)
    if not code or code != data.code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    return {"message": "Verification code validated"}

# ---------- Forgot Password: Reset Password ----------
@router.post("/forgot-password/reset")
def forgot_password_reset(data: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    code = forgot_password_codes.get(data.email)
    if not code or code != data.code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = auth.hash_password(data.new_password)
    db.commit()

    # Remove code after reset
    forgot_password_codes.pop(data.email, None)

    return {"message": "Password reset successful"}

# ---------- Logout ----------
@router.post("/logout")
def logout(
    data: schemas.LogoutRequest = Body(...),
    db: Session = Depends(get_db),
):
    refresh_token = data.refresh_token
    session = db.query(models.UserSession).filter(models.UserSession.refresh_token == refresh_token).first()
    if session:
        db.delete(session)
        db.commit()
        return {"message": "Logged out successfully"}
    else:
        raise HTTPException(status_code=404, detail="Refresh token not found")

# ---------- Refresh Access Token ----------
@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(
    data: schemas.RefreshTokenRequest = Body(...),
    db: Session = Depends(get_db),
):
    refresh_token = data.refresh_token
    payload = auth.verify_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # Check if refresh token exists in DB and is not expired
    session = db.query(models.UserSession).filter(
        models.UserSession.refresh_token == refresh_token,
        models.UserSession.expires_at > datetime.utcnow()
    ).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or invalid")

    # Create new access token
    access_token = auth.create_access_token({"user_id": str(user_id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,  # Optionally rotate tokens here
        "token_type": "bearer"
    }
