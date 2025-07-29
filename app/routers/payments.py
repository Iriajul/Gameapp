# app/routes/payments.py

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.models import User
from app.routers.dependencies import get_current_user, get_db
from app.schemas import PlanRequest
from app.config import (
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    STRIPE_PRICE_MONTHLY,
    STRIPE_PRICE_YEARLY,
    FRONTEND_DOMAIN,
)
from app.database import SessionLocal

router = APIRouter()
stripe.api_key = STRIPE_SECRET_KEY

MONTHLY_PRICE_ID = STRIPE_PRICE_MONTHLY
YEARLY_PRICE_ID = STRIPE_PRICE_YEARLY


@router.post("/create-checkout-session")
async def create_checkout_session(
    plan_request: PlanRequest,
    user: User = Depends(get_current_user),
):
    plan = plan_request.plan

    if plan == "monthly":
        price_id = MONTHLY_PRICE_ID
    elif plan == "yearly":
        price_id = YEARLY_PRICE_ID
    else:
        raise HTTPException(status_code=400, detail="Invalid plan")

    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=f"{FRONTEND_DOMAIN}/subscription-success",
            cancel_url=f"{FRONTEND_DOMAIN}/subscription-cancelled",
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=user.email,
            metadata={"user_id": str(user.id)},
        )
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portal")
def create_customer_portal(user: User = Depends(get_current_user)):
    if not user.subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    try:
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id or user.subscription_id,
            return_url=f"{FRONTEND_DOMAIN}/profile",
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"].get("user_id")
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")

        db: Session = SessionLocal()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                user.is_subscribed = True
                user.subscription_id = subscription_id
                user.stripe_customer_id = customer_id
                db.commit()
        finally:
            db.close()

    return {"status": "success"}
