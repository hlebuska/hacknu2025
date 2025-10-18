from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

def utc_now():
    """Return current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)

class Application(SQLModel, table=True):
    """Job application model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    vacancy_id: str = Field(foreign_key="vacancy.id", index=True)
    first_name: str
    last_name: str
    email: str = Field(index=True)
    resume_pdf: Optional[str] = None  # Path to PDF file
    resume_parsed: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # Parsed resume data
    matching_score: Optional[float] = None  # AI-calculated fit score (0-100)
    matching_sections: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # AI-extracted relevant sections
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class ApplicationCreate(SQLModel):
    """Schema for creating a new application"""
    vacancy_id: str
    first_name: str
    last_name: str
    email: str

class ApplicationRead(SQLModel):
    """Schema for reading application data"""
    id: str
    vacancy_id: str
    first_name: str
    last_name: str
    email: str
    resume_pdf: Optional[str]
    resume_parsed: Optional[Dict[str, Any]]
    matching_score: Optional[float]
    matching_sections: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
