from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
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

    sent_messages = relationship(
        "Message",
        back_populates="sender",
        cascade="all, delete-orphan",
        foreign_keys="[Message.sender_id]"
    )
    received_messages = relationship(
        "Message",
        back_populates="receiver",
        cascade="all, delete-orphan",
        foreign_keys="[Message.receiver_id]"
    )
    
    user_chats = relationship("UserChat", back_populates="user", cascade="all, delete-orphan")

class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = {"schema": "backend"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("backend.users.id"), nullable=False)

    refresh_token = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
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

    # ✅ New fields
    conversation = Column(JSONB, default=[])  # Array of JSON objects
    is_save = Column(Boolean, default=False, nullable=False)
    pined_date = Column(String, nullable=True)

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
    schedule_info = Column(Text, nullable=True)

    # ✅ New field
    plan_ids = Column(ARRAY(String), default=[])

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
    user_chats = relationship("UserChat", back_populates="chat", cascade="all, delete-orphan")

class UserChat(Base):
    __tablename__ = "user_chats"
    __table_args__ = (
        UniqueConstraint("user_id", "chat_id", name="uix_user_chat"),
        {"schema": "backend"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("backend.users.id"), nullable=False)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("backend.chats.id"), nullable=False)

    user = relationship("User", back_populates="user_chats")
    chat = relationship("Chat", back_populates="user_chats")

class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {"schema": "backend"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("backend.chats.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("backend.users.id"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("backend.users.id"), nullable=False)  # NEW FIELD
    message_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])
