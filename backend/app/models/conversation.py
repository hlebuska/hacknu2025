"""Conversation and message models for chatbot functionality"""
from sqlmodel import SQLModel, Field, Column, TIMESTAMP
from sqlalchemy import JSON
from typing import Optional
from datetime import datetime, timezone
import uuid


def utc_now():
    """Return current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)


class Conversation(SQLModel, table=True):
    """Conversation / chat session persisted to the DB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    session_id: str = Field(index=True)
    user_id: Optional[str] = None
    vacancy_id: Optional[str] = Field(foreign_key="vacancy.id", index=True)
    application_id: Optional[str] = Field(foreign_key="application.id", index=True)
    title: Optional[str] = None  # Conversation title/topic
    context_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # Additional context
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True)))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True)))


class ConversationMessage(SQLModel, table=True):
    """Single message in a conversation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id", index=True)
    role: str  # "user" or "assistant"
    content: str  # Message text
    message_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # Message metadata
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True)))


class ConversationCreate(SQLModel):
    """Schema for creating a new conversation"""
    session_id: str
    vacancy_id: Optional[str] = None
    application_id: Optional[str] = None
    title: Optional[str] = None


class ConversationRead(SQLModel):
    """Schema for reading conversation"""
    id: str
    session_id: str
    vacancy_id: Optional[str]
    application_id: Optional[str]
    title: Optional[str]
    created_at: datetime
    updated_at: datetime


class MessageCreate(SQLModel):
    """Schema for creating a new message"""
    conversation_id: str
    role: str
    content: str


class MessageRead(SQLModel):
    """Schema for reading a message"""
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime
