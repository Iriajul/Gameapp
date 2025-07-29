from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models import Class
from app.schemas import ClassCreate, ClassResponse, ClassUpdate
from app.routers.dependencies import get_current_user
from app.models import User

router = APIRouter()

# Create Class
@router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(class_in: ClassCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    new_class = Class(
        user_id=user.id,
        title=class_in.title,
        description=class_in.description,
        schedule_info=class_in.schedule_info,
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

# Update Class
@router.put("/{class_id}", response_model=ClassResponse)
def update_class(class_id: UUID, class_in: ClassUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    klass = db.query(Class).filter(Class.id == class_id, Class.user_id == user.id).first()
    if not klass:
        raise HTTPException(status_code=404, detail="Class not found")

    for var, value in vars(class_in).items():
        if value is not None:
            setattr(klass, var, value)

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
