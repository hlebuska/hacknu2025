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
    Return only a single JSON object with exactly two keys in this order:
    {{
        "MATCHING_SECTIONS": "[A single string containing the extracted resume snippets and short tags — keep reasonably concise]",
        "FIT_SCORE": [integer 0-100]
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
    max_tokens: int = 600,
) -> Dict[str, Any] | Dict[str, str]:
    """
    Call OpenAI to compute matching sections and a fit score.

    Returns either a dict with keys MATCHING_SECTIONS and FIT_SCORE, or a dict with an 'error' key on failure.
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
            return {"error": "Invalid JSON returned by model", "raw": assistant_text}

        if not ("MATCHING_SECTIONS" in parsed and "FIT_SCORE" in parsed):
            return {"error": "JSON missing required keys", "raw": assistant_text}

        return parsed
    except Exception as e:
        logger.exception("OpenAI API call failed")
        return {"error": f"OpenAI API call failed: {e}"}
