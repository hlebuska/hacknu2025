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

    You are a precise evaluator. Your goal is to measure how accurately the resume satisfies each job requirement.

    PART B — SCORING RULES (STRICT):

    1. EXPERIENCE & DURATION:
    - Identify the start and end years of relevant positions.
    - Compute duration as of October 2025.
    - If requirement says "3+ years" and resume shows only ~1 year, assign ≤ 40% match.
    - Partial matches (e.g. 2 out of 3 years) should get proportional scores (≈ 65%).
    - If no date or duration is mentioned, assume 0% for experience-based requirements.

    2. LOCATION / REGION:
    - If the city or country exactly matches → 100%.
    - If within same country but different city → ≤ 60%.
    - Different country/region → ≤ 20%.
    - If remote acceptable but not stated → ≤ 50%.

    3. SKILLS & TECHNOLOGIES:
    - Match exact skill names (case-insensitive).
    - If skill appears with clear professional use (e.g. “Developed X using Y”) → 100%.
    - If only listed in skills section without examples → 70%.
    - Mentioned vaguely (e.g. “familiar with”) → ≤ 40%.
    - Not found → 0%.

    4. EDUCATION / CERTIFICATIONS:
    - Match exact degree field or certification name.
    - Related field but not exact → ≤ 70%.
    - Different or missing → ≤ 30%.

    5. SOFT SKILLS & COMMUNICATION:
    - Only consider explicitly shown evidence (e.g. “Led a team”, “collaborated”, “mentored”).
    - No evidence → 0%.

    6. TOOLS / FRAMEWORKS / CLOUD:
    - Apply same scoring as skills, but weigh multiple tools separately.

    PART C — OUTPUT FORMAT (STRICT JSON):
    Return only a valid JSON object with:
    - "requirements": an array where each element has:
        * "vacancy_req": (string) job requirement
        * "user_req_data": (string) matched resume text (empty if none)
        * "match_percent": integer 0–100
    - "FIT_SCORE": integer 0–100 (overall weighted average)

    Example:
    {{
    "requirements": [
        {{
        "vacancy_req": "location: Almaty, Kazakhstan",
        "user_req_data": "Astana, Kazakhstan",
        "match_percent": 50
        }},
        {{
        "vacancy_req": "Experience in React: > 3 years",
        "user_req_data": "Developed client app using React (2023–2024)",
        "match_percent": 40
        }}
    ],
    "FIT_SCORE": 55
    }}

    STRICT INSTRUCTIONS:
    - Do NOT infer missing details.
    - If duration or skill usage is unclear, reduce score significantly (≤ 40%).
    - Use October 2025 as current date when calculating experience.
    - Output valid JSON only — no comments, no text outside the JSON.
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
