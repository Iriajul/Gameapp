# app/routes/users.py

from fastapi import APIRouter, Depends
from app.models import User
from app.routers.dependencies import get_current_user

router = APIRouter()

@router.get("/profile")
def get_user_profile(user: User = Depends(get_current_user)):
    return {
        "username": user.username,
        "email": user.email,
        "is_subscribed": user.is_subscribed,
        "subscription_id": user.subscription_id,
        "trial_ends_at": user.trial_ends_at,
        "email_verified": user.email_verified,
    }
