"""
Pydantic models for HackNU25 Backend API
"""

from typing import Optional, Dict, List, Any, Union
from pydantic import BaseModel


class PersonalInformation(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    professional_title: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None


class ProfessionalSummary(BaseModel):
    career_level: Optional[str] = None
    years_of_experience: Optional[Union[str, int]] = None
    key_expertise: List[str] = []
    professional_strengths: List[str] = []


class WorkExperience(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    duration: Optional[str] = None
    responsibilities: List[str] = []
    achievements: List[str] = []
    technologies: List[str] = []


class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[str] = None
    coursework: List[str] = []
    honors: List[str] = []


class TechnicalSkills(BaseModel):
    programming_languages: List[str] = []
    frameworks: List[str] = []
    databases: List[str] = []
    cloud_platforms: List[str] = []
    tools: List[str] = []


class Language(BaseModel):
    language: Optional[str] = None
    proficiency: Optional[str] = None


class Project(BaseModel):
    name: Optional[str] = None
    duration: Optional[str] = None
    technologies: List[str] = []
    description: Optional[str] = None
    role: Optional[str] = None
    impact: Optional[str] = None


class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None


class AdditionalInformation(BaseModel):
    volunteer_work: List[str] = []
    memberships: List[str] = []
    conferences: List[str] = []


class StructuredAnalysis(BaseModel):
    """Structured analysis data model"""
    personal_information: PersonalInformation = PersonalInformation()
    professional_summary: ProfessionalSummary = ProfessionalSummary()
    work_experience: List[WorkExperience] = []
    education: List[Education] = []
    technical_skills: TechnicalSkills = TechnicalSkills()
    soft_skills: List[str] = []
    languages: List[Language] = []
    projects: List[Project] = []
    certifications: List[Certification] = []
    additional_information: AdditionalInformation = AdditionalInformation()
    error: Optional[str] = None
    raw_response: Optional[str] = None


class PDFAnalysisResponse(BaseModel):
    """Response model for PDF analysis endpoints"""
    success: bool
    extracted_text: Optional[str] = None
    analysis: Optional[Union[StructuredAnalysis, str]] = None
    metadata: Optional[dict] = None
    error: Optional[str] = None