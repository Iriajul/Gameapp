from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from app.database import get_db
from app import models, auth
from app.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    FACEBOOK_CLIENT_ID,
    FACEBOOK_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    FACEBOOK_REDIRECT_URI,
)

router = APIRouter()
oauth = OAuth()

# Register Google OAuth client
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "email"},
)

# Register Facebook OAuth client
oauth.register(
    name="facebook",
    client_id=FACEBOOK_CLIENT_ID,
    client_secret=FACEBOOK_CLIENT_SECRET,
    authorize_url="https://www.facebook.com/dialog/oauth",
    access_token_url="https://graph.facebook.com/oauth/access_token",
    client_kwargs={"scope": "email"},
)

# --- Google Login ---
@router.get("/auth/google")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)

@router.get("/auth/google/callback")
async def google_auth_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    resp = await oauth.google.get("https://www.googleapis.com/oauth2/v1/userinfo", token=token)
    user_info = resp.json()

    email = user_info.get("email")
    if email is None:
        raise HTTPException(status_code=400, detail="Failed to get user email from Google")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            username=user_info.get("name", "Google User"),
            email=email,
            password_hash=auth.hash_password("oauth_dummy_password"),
            agreed_to_terms=True,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = auth.create_access_token({"user_id": str(user.id)})
    refresh_token = auth.create_refresh_token({"user_id": str(user.id)})

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# --- Facebook Login ---
@router.get("/auth/facebook")
async def facebook_login(request: Request):
    return await oauth.facebook.authorize_redirect(request, FACEBOOK_REDIRECT_URI)

@router.get("/auth/facebook/callback")
async def facebook_auth_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.facebook.authorize_access_token(request)
    resp = await oauth.facebook.get("https://graph.facebook.com/me?fields=id,name,email", token=token)
    user_info = resp.json()

    email = user_info.get("email")
    if email is None:
        raise HTTPException(status_code=400, detail="Failed to get user email from Facebook")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            username=user_info.get("name", "Facebook User"),
            email=email,
            password_hash=auth.hash_password("oauth_dummy_password"),
            agreed_to_terms=True,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = auth.create_access_token({"user_id": str(user.id)})
    refresh_token = auth.create_refresh_token({"user_id": str(user.id)})

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
