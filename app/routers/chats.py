from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import func
from app.database import get_db
from app.models import Chat, Message, UserChat, User
from app.schemas import ChatResponse, MessageCreate, MessageResponse
from app.routers.dependencies import get_current_user
from app.ai.agent import generate_ai_response

router = APIRouter()

# Fixed AI user UUID
AI_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


# -------------------------------
# Get Recent Chats (Recent Plans)
# -------------------------------
@router.get("/", response_model=List[ChatResponse])
def get_chats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user_chats = (
        db.query(Chat)
        .join(UserChat, Chat.id == UserChat.chat_id)
        .filter(UserChat.user_id == user.id)
        .order_by(Chat.updated_at.desc())
        .all()
    )

    response = []
    for chat in user_chats:
        participants = db.query(UserChat.user_id).filter(UserChat.chat_id == chat.id).all()
        participant_ids = [p[0] for p in participants]

        last_msg = (
            db.query(Message)
            .filter(Message.chat_id == chat.id)
            .order_by(Message.timestamp.desc())
            .first()
        )

        response.append(
            ChatResponse(
                id=chat.id,
                participants=participant_ids,
                last_message=last_msg,
                updated_at=chat.updated_at,
            )
        )
    return response


# -------------------------------
# Create New Blank Chat (New Plan)
# -------------------------------
@router.post("/new", response_model=UUID)
def create_new_chat(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ai_user_id = AI_USER_ID

    chat = Chat(updated_at=datetime.utcnow())
    db.add(chat)
    db.commit()
    db.refresh(chat)

    db.add_all([
        UserChat(chat_id=chat.id, user_id=user.id),
        UserChat(chat_id=chat.id, user_id=ai_user_id)
    ])
    db.commit()

    return chat.id


# -------------------------------
# Get Last Chat (Last Plan)
# -------------------------------
@router.get("/last", response_model=ChatResponse)
def get_last_chat(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    last_chat = (
        db.query(Chat)
        .join(UserChat, Chat.id == UserChat.chat_id)
        .filter(UserChat.user_id == user.id)
        .order_by(Chat.updated_at.desc())
        .first()
    )
    if not last_chat:
        raise HTTPException(status_code=404, detail="No previous chats found")

    participants = db.query(UserChat.user_id).filter(UserChat.chat_id == last_chat.id).all()
    participant_ids = [p[0] for p in participants]

    last_msg = (
        db.query(Message)
        .filter(Message.chat_id == last_chat.id)
        .order_by(Message.timestamp.desc())
        .first()
    )

    return ChatResponse(
        id=last_chat.id,
        participants=participant_ids,
        last_message=last_msg,
        updated_at=last_chat.updated_at
    )


# -------------------------------
# Get Messages from a Chat
# -------------------------------
@router.get("/{chat_id}", response_model=List[MessageResponse])
def get_chat_messages(chat_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user_chat = (
        db.query(UserChat)
        .filter(UserChat.chat_id == chat_id, UserChat.user_id == user.id)
        .first()
    )
    if not user_chat:
        raise HTTPException(status_code=404, detail="Chat not found or access denied")

    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.timestamp)
        .all()
    )
    return messages


# -------------------------------
# Send a Message and Get AI Response
# -------------------------------
@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(msg_in: MessageCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ai_user_id = AI_USER_ID

    # Find chat between user and AI
    chat = (
        db.query(Chat)
        .join(UserChat, Chat.id == UserChat.chat_id)
        .filter(UserChat.user_id.in_([user.id, ai_user_id]))
        .group_by(Chat.id)
        .having(func.count(Chat.id) == 2)
        .first()
    )

    if not chat:
        chat = Chat(updated_at=datetime.utcnow())
        db.add(chat)
        db.commit()
        db.refresh(chat)

        db.add_all([
            UserChat(chat_id=chat.id, user_id=user.id),
            UserChat(chat_id=chat.id, user_id=ai_user_id)
        ])
        db.commit()

    # Store user message
    user_message = Message(
        chat_id=chat.id,
        sender_id=user.id,
        receiver_id=ai_user_id,
        message_text=msg_in.message_text,
        timestamp=datetime.utcnow()
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Generate AI response
    ai_response_text = generate_ai_response(msg_in.message_text)

    # Store AI response
    ai_message = Message(
        chat_id=chat.id,
        sender_id=ai_user_id,
        receiver_id=user.id,
        message_text=ai_response_text,
        timestamp=datetime.utcnow()
    )
    db.add(ai_message)

    chat.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ai_message)
    db.refresh(chat)

    return ai_message
