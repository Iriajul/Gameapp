from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import func
from app.database import get_db
from app.models import Chat, Message
from app.schemas import ChatResponse, MessageCreate, MessageResponse
from app.routers.dependencies import get_current_user
from app.models import User

router = APIRouter()

# List recent chats for current user
@router.get("/", response_model=List[ChatResponse])
def get_chats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Get all chats where user participates
    chats = db.query(Chat).join(Chat).filter(Chat.user_id == user.id).order_by(Chat.updated_at.desc()).all()
    return chats

# Get messages of a chat
@router.get("/{chat_id}", response_model=List[MessageResponse])
def get_chat_messages(chat_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = db.query(Chat).join(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found or access denied")

    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp).all()
    return messages

# Send a new message
@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(msg_in: MessageCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Check if chat exists between sender and receiver or create new chat
    # Simplified: assume one chat per user pair

    # Find chat involving both users
    chat = (
        db.query(Chat)
        .join(Chat, Chat.id == Chat.chat_id)
        .filter(Chat.user_id.in_([user.id, msg_in.receiver_id]))
        .group_by(Chat.id)
        .having(func.count(Chat.id) == 2)
        .first()
    )
    if not chat:
        # Create new chat
        chat = Chat(updated_at=datetime.utcnow())
        db.add(chat)
        db.commit()
        db.refresh(chat)

        # Add both users to UserChat
        db.add_all([
            Chat(chat_id=chat.id, user_id=user.id),
            Chat(chat_id=chat.id, user_id=msg_in.receiver_id)
        ])
        db.commit()

    # Add new message
    message = Message(
        chat_id=chat.id,
        sender_id=user.id,
        receiver_id=msg_in.receiver_id,
        message_text=msg_in.message_text,
        timestamp=datetime.utcnow()
    )
    db.add(message)
    chat.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    db.refresh(chat)
    return message
