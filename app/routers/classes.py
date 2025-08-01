from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models import Class, Plan, User
from app.schemas import ClassCreate, ClassResponse, ClassUpdate
from app.routers.dependencies import get_current_user

router = APIRouter()

# Create Class
@router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(class_in: ClassCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan_ids = class_in.plan_ids or []  # fallback to empty list if None
    new_class = Class(
        user_id=user.id,
        title=class_in.title,
        description=class_in.description,
        schedule_info=class_in.schedule_info,
        plan_ids=plan_ids
    )
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    return new_class

# List all classes for user
@router.get("/", response_model=List[ClassResponse])
def get_classes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    classes = db.query(Class).filter(Class.user_id == user.id).all()
    return classes

# Get class details
@router.get("/{class_id}", response_model=ClassResponse)
def get_class(class_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    klass = db.query(Class).filter(Class.id == class_id, Class.user_id == user.id).first()
    if not klass:
        raise HTTPException(status_code=404, detail="Class not found")
    return klass

# Update Class (including updating plan_ids)
@router.put("/{class_id}", response_model=ClassResponse)
def update_class(class_id: UUID, class_in: ClassUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    klass = db.query(Class).filter(Class.id == class_id, Class.user_id == user.id).first()
    if not klass:
        raise HTTPException(status_code=404, detail="Class not found")

    # Update simple fields
    for var, value in vars(class_in).items():
        if var != "plan_ids" and value is not None:
            setattr(klass, var, value)

    # If plan_ids present in update schema, replace or extend it (optional)
    if hasattr(class_in, "plan_ids") and class_in.plan_ids is not None:
        klass.plan_ids = class_in.plan_ids

    klass.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(klass)
    return klass

# Delete Class
@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(class_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    klass = db.query(Class).filter(Class.id == class_id, Class.user_id == user.id).first()
    if not klass:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(klass)
    db.commit()
    return None

# Add a plan to a class
@router.post("/{class_id}/add-plan/{plan_id}", response_model=ClassResponse)
def add_plan_to_class(class_id: UUID, plan_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    klass = db.query(Class).filter(Class.id == class_id, Class.user_id == user.id).first()
    if not klass:
        raise HTTPException(status_code=404, detail="Class not found")

    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.user_id == user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or does not belong to user")

    if plan_id.hex not in klass.plan_ids:
        klass.plan_ids.append(plan_id.hex)  # Store as string if you use ARRAY(String)
        klass.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(klass)
    return klass

# Remove a plan from a class
@router.delete("/{class_id}/remove-plan/{plan_id}", response_model=ClassResponse)
def remove_plan_from_class(class_id: UUID, plan_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    klass = db.query(Class).filter(Class.id == class_id, Class.user_id == user.id).first()
    if not klass:
        raise HTTPException(status_code=404, detail="Class not found")

    if plan_id.hex in klass.plan_ids:
        klass.plan_ids.remove(plan_id.hex)
        klass.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(klass)
    else:
        raise HTTPException(status_code=404, detail="Plan not found in this class")

    return klass
