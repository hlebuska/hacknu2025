"""
Resume matching service using OpenAI Chat Completions.
Produces a list of per-requirement matches and an overall FIT_SCORE (0-100).
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
        "Education; Skills; Languages; Projects; Certifications and Achievements;"
    )

    prompt = f"""
Job Requirements:
{job_requirements}

Resume Content:
{resume_text}

You are an expert resume analyzer. Your task is to:

1. Parse the Job Requirements into individual requirement items (skills, experience, education, etc.)
2. For EACH requirement, find matching evidence in the Resume Content
3. Calculate a match percentage (0-100) for each requirement
4. Calculate an overall FIT_SCORE (0-100) for the entire resume

OUTPUT FORMAT (Required — valid JSON array ONLY):

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
- Return ONLY valid JSON. No markdown code blocks, no extra text.
- If a requirement has no matching resume data, set "user_req_data" to empty string and "match_percent" to 0.
- Consider these resume sections when extracting: {resume_key_sections}
- FIT_SCORE should be a weighted average considering importance of each requirement.
"""

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": "You are an expert resume analyzer. You parse job requirements and match them against resume content. You return only valid JSON with no additional text."
        },
        {"role": "user", "content": prompt}
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

    # Simple truncation to avoid overly long inputs
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

        # Try to parse JSON
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
        # This will be stored in matching_sections as JSON
        return parsed

    except Exception as e:
        logger.exception("OpenAI API call failed")
        return {"error": f"OpenAI API call failed: {e}"}
