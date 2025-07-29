from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models import Plan
from app.schemas import PlanCreate, PlanResponse, PlanUpdate
from app.routers.dependencies import get_current_user
from app.models import User

router = APIRouter()

# Create Plan
@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(plan_in: PlanCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = Plan(
        user_id=user.id,
        title=plan_in.title,
        description=plan_in.description,
        start_date=plan_in.start_date,
        end_date=plan_in.end_date
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

# Get all plans for user
@router.get("/", response_model=List[PlanResponse])
def get_plans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plans = db.query(Plan).filter(Plan.user_id == user.id).all()
    return plans

# Get recent plans (last 5)
@router.get("/recent", response_model=List[PlanResponse])
def get_recent_plans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plans = db.query(Plan).filter(Plan.user_id == user.id).order_by(Plan.created_at.desc()).limit(5).all()
    return plans

# Get last plan (most recent)
@router.get("/last", response_model=PlanResponse)
def get_last_plan(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = db.query(Plan).filter(Plan.user_id == user.id).order_by(Plan.created_at.desc()).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No plans found")
    return plan

# Update Plan
@router.put("/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: UUID, plan_in: PlanUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.user_id == user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    for var, value in vars(plan_in).items():
        if value is not None:
            setattr(plan, var, value)

    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return plan

# Delete Plan
@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.user_id == user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return None
