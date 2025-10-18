"""
Resume matching service using OpenAI Chat Completions.
Produces MATCHING_SECTIONS and FIT_SCORE (0-100) given job requirements and resume text.
"""

from __future__ import annotations

import json
import logging
from typing import Optional, Dict, Any
from openai.types.chat import ChatCompletionMessageParam

from app.config.settings import settings

logger = logging.getLogger(__name__)


def _build_messages(job_requirements: str, resume_text: str) -> list[ChatCompletionMessageParam]:
    resume_key_sections = (
        "Personal Information (Candidate Overview); Job Experience (Work History); "
        "Education;  Skills; Languages; Projects;Certifications and Achievements;"
    )

    extractor_prompt = f"""
    Job Requirements: {job_requirements}
    Resume Content: {resume_text}

    You are an expert resume analyzer. Follow PART A instructions below exactly.

    PART A — EXTRACT MATCH (Required):
    - From the Resume Content, locate and extract only the parts that directly match or demonstrate the skills, experience, education, projects, certifications, or other qualifications listed in the Job Requirements.
    - Consider the following sections when extracting: {resume_key_sections}
    - For each extracted item, include a one-line tag describing which requirement it matches (e.g. "Matches: Python, TensorFlow, AWS") when relevant.
    - Do not include unrelated resume text, commentary, or explanations in PART A — only the extracted resume lines/paragraphs and their tags.
    """

    grader_prompt = f"""
    Job Requirements: {job_requirements}
    Resume Content: {resume_text}

    PART B — GRADER (Score out of 100, Required):
    - Assign a single integer score between 0 and 100 representing overall fit (100 = perfect match).
    - Score composition guidance (use internally to compute the score; you only return the final number):
      * Core technical skills match (0-40): how many required technical skills are present and proficiently demonstrated.
      * Relevant experience & seniority (0-25): years and relevancy of work experience to the role.
      * Tooling / frameworks / cloud experience (0-15): presence of required frameworks or cloud platforms.
      * Education & certifications (0-10): degrees or certifications directly related to the role.
      * Soft skills & cultural fit signals (0-10): communication, agile/teamwork signals, leadership where relevant.
    - Provide the single final integer score only; do NOT include the internal breakdown in the response.

    OUTPUT FORMAT (Required — exact JSON ONLY):
    Return a JSON object with two keys:
    - "requirements": an array where each element has:
    * "vacancy_req": the specific job requirement (string)
    * "user_req_data": extracted resume text that demonstrates this requirement (string, empty if no match)
    * "match_percent": percentage match for this requirement (0-100 integer)
    - "FIT_SCORE": overall fit score (0-100 integer)

    Example structure:
    {{
    "requirements": [
        {{
        "vacancy_req": "3+ years Python experience",
        "user_req_data": "Skills: Python\\nExperience: 5 years as Python Developer at XYZ Corp",
        "match_percent": 95
        }},
        {{
        "vacancy_req": "Machine Learning frameworks (TensorFlow/PyTorch)",
        "user_req_data": "Skills: TensorFlow, PyTorch\\nProjects: Built ML models for predictive analytics",
        "match_percent": 85
        }}
    ],
    "FIT_SCORE": 88
    }}

    IMPORTANT:
    - The model must output valid JSON only. No extra text, no surrounding backticks, and no explanatory notes.
    - If a required field is missing in the resume, include an empty string for MATCHING_SECTIONS and score appropriately.
    """

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": "You are an expert resume analyzer. Follow instructions precisely."
        },
        {"role": "user", "content": extractor_prompt},
        {"role": "user", "content": grader_prompt},
        {
            "role": "user",
            "content": "Analyze the resume against the job requirements and return only the specified JSON with MATCHING SECTIONS and FIT SCORE."
        },
    ]
    return messages


async def match_resume_to_requirements(
    job_requirements: str,
    resume_text: str,
    *,
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 2000,
) -> Dict[str, Any] | Dict[str, str]:
    """
    Match resume against job requirements using OpenAI.
    
    Returns a dict with:
    - On success: {"requirements": [...], "FIT_SCORE": int}
    - On error: {"error": str, "raw": str (optional)}
    
    The full successful response is meant to be stored in Application.matching_sections (JSON field).
    """
    if not settings.openai_client or not settings.openai_api_key:
        return {"error": "OPENAI_API_KEY is not configured on the server."}

    client = settings.openai_client
    model_name = model or getattr(settings, "openai_model", "gpt-4o-mini")

    # Simple truncation to avoid overly long inputs. Adjust as needed.
    # This is a character-based proxy; you can make this token-aware later.
    def truncate(s: str, max_len: int) -> str:
        return s if len(s) <= max_len else s[:max_len]

    jr_trimmed = truncate(job_requirements, 6000)
    rt_trimmed = truncate(resume_text, 12000)

    messages = _build_messages(jr_trimmed, rt_trimmed)
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = resp.choices[0].message.content if resp.choices else None
        assistant_text = content.strip() if isinstance(content, str) else ""
        if not assistant_text:
            return {"error": "OpenAI returned empty response"}

        try:
            parsed = json.loads(assistant_text)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from model: {assistant_text[:200]}...")
            return {"error": "Invalid JSON returned by model", "raw": assistant_text}

        # Validate structure: must have "requirements" array and "FIT_SCORE"
        if not isinstance(parsed, dict):
            return {"error": "Response is not a JSON object", "raw": assistant_text}
        
        if "requirements" not in parsed or "FIT_SCORE" not in parsed:
            return {"error": "JSON missing 'requirements' or 'FIT_SCORE'", "raw": assistant_text}
        
        if not isinstance(parsed["requirements"], list):
            return {"error": "'requirements' must be an array", "raw": assistant_text}
        
        # Validate FIT_SCORE is numeric
        try:
            fit_score = float(parsed["FIT_SCORE"])
            if not (0 <= fit_score <= 100):
                logger.warning(f"FIT_SCORE out of range: {fit_score}")
        except (ValueError, TypeError):
            return {"error": "FIT_SCORE must be a number 0-100", "raw": assistant_text}

        # Valid response - return the full parsed object
        return parsed
    except Exception as e:
        logger.exception("OpenAI API call failed")
        return {"error": f"OpenAI API call failed: {e}"}
