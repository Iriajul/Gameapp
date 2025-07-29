from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid

from app.database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "backend"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    agreed_to_terms = Column(Boolean, nullable=False, default=False)
    email_verified = Column(Boolean, nullable=False, default=False)

    # Subscription and trial fields
    is_subscribed = Column(Boolean, default=False, nullable=False)
    subscription_id = Column(String, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    trial_ends_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="user", cascade="all, delete-orphan")
    classes = relationship("Class", back_populates="user", cascade="all, delete-orphan")
    sent_messages = relationship("Message", back_populates="sender", cascade="all, delete-orphan")

class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = {"schema": "backend"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("backend.users.id"), nullable=False)

    refresh_token = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)   # Optional: device info (e.g., browser or device name)
    ip_address = Column(String, nullable=True)   # Optional: IP address of the session
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))

    user = relationship("User", back_populates="sessions")


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = {"schema": "backend"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("backend.users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="plans")


class Class(Base):
    __tablename__ = "classes"
    __table_args__ = {"schema": "backend"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("backend.users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    schedule_info = Column(Text, nullable=True)  # Could store JSON string for schedule
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="classes")


class Chat(Base):
    __tablename__ = "chats"
    __table_args__ = {"schema": "backend"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {"schema": "backend"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("backend.chats.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("backend.users.id"), nullable=False)
    message_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")
