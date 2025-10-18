from sqlmodel import SQLModel, Field, Column, TIMESTAMP
from sqlalchemy import JSON
from typing import Optional
from datetime import datetime, timezone
import uuid


def utc_now():
    return datetime.now(timezone.utc)


class Conversation(SQLModel, table=True):
    """Conversation / chat session persisted to the DB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    session_id: str
    vacancy_id: Optional[str] = None
    resume_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True)))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True)))


class ConversationMessage(SQLModel, table=True):
    """Single message in a conversation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(index=True)
    role: str
    text: Optional[str] = None
    metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True)))
