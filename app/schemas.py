from pydantic import BaseModel, EmailStr, Field, model_validator
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# --------------------
# User Signup Schema
# --------------------
class SignUpRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    agreed_to_terms: bool = Field(..., description="User must agree to terms")

    @model_validator(mode='before')
    def passwords_match(cls, values):
        pw = values.get('password')
        cpw = values.get('confirm_password')
        if pw != cpw:
            raise ValueError('Password and Confirm Password do not match')
        return values

# --------------------
# Login Schema
# --------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --------------------
# Token Response
# --------------------
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# --------------------
# Logout Request
# --------------------
class LogoutRequest(BaseModel):
    refresh_token: str

# --------------------
# Refresh Token Request
# --------------------
class RefreshTokenRequest(BaseModel):
    refresh_token: str

# For internal decoding
class TokenData(BaseModel):
    user_id: Optional[UUID] = None

# --------------------
# Forgot Password Flow
# --------------------
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6)
    code: str = Field(..., min_length=6, max_length=6)

# --------------------
# User Response
# --------------------
class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# --------------------
# Plan Schemas
# --------------------
class PlanBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]

class PlanResponse(PlanBase):
    id: UUID
    user_id: UUID
    conversation: Optional[str] = None
    is_save: bool = False
    pined_date: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
# --------------------
# Class Schemas
# --------------------
class ClassBase(BaseModel):
    title: str
    description: Optional[str] = None
    schedule_info: Optional[str] = None

class ClassCreate(BaseModel):
    title: str
    description: Optional[str] = None
    schedule_info: Optional[str] = None
    plan_ids: Optional[List[str]] = None

class ClassUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    schedule_info: Optional[str] = None
    plan_ids: Optional[List[str]] = None  # ✅ Add this

class ClassResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None
    schedule_info: Optional[str] = None
    plan_ids: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
# --------------------
# Chat & Message Schemas
# --------------------
class MessageBase(BaseModel):
    message_text: str

class MessageCreate(MessageBase):
    # ✅ receiver_id REMOVED since it's always the AI
    pass

class MessageResponse(MessageBase):
    id: UUID
    chat_id: UUID
    sender_id: UUID
    receiver_id: UUID
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }

class ChatResponse(BaseModel):
    id: UUID
    participants: List[UUID]
    last_message: Optional[MessageResponse] = None
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# --------------------
# PlanRequest
# --------------------
class PlanRequest(BaseModel):
    plan: str  # "monthly" or "yearly"
