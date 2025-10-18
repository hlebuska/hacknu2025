import json
import sys
import os

# Ensure the backend package root (the `backend` folder) is on sys.path so tests can import `app`
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.services.ai_chat import AIChatService


def test_analyze_differences_basic():
    svc = AIChatService()
    resume = {
        "skills": ["python", "sql"],
        "experience_years": "2",
        "education": "B.S. Computer Science",
    }
    vacancy = {
        "required_skills": ["python", "aws", "sql"],
        "work_experience": "3",
        "education_requirements": "B.S. Computer Science",
    }

    diffs = svc.analyze_differences(resume, vacancy)
    assert any(d["field"] == "technical skills" or d["field"] == "missing_skills" for d in diffs)


def test_generate_interview_questions_no_model(monkeypatch):
    svc = AIChatService()
    resume = {"name": "Alice", "skills": ["python"]}
    vacancy = {"job_title": "ML Engineer", "required_skills": ["python", "pytorch"]}

    diffs = svc.analyze_differences(resume, vacancy)

    # Ensure generate_interview_questions returns a string even if no model is configured
    q = svc.generate_interview_questions(diffs, resume, vacancy)
    assert isinstance(q, str)
