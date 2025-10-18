"""
PDF Analyzer - Clean analysis logic moved from services
"""

import time
import json
import logging
from app.config.settings import settings
from app.backend_models.response import StructuredAnalysis

logger = logging.getLogger(__name__)


async def analyze_with_openai(text: str) -> StructuredAnalysis:
    """Analyze resume text using OpenAI GPT and return structured JSON data"""
    start_time = time.time()
    logger.info(f"🤖 Starting OpenAI analysis - Text length: {len(text)} chars")
    
    try:
        if not settings.openai_api_key or not settings.openai_client:
            logger.error("❌ OpenAI API key not configured")
            return StructuredAnalysis(
                error="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
            )
        
        # Prepare prompt for structured JSON output
        prompt_start = time.time()
        resume_analysis_prompt = f"""
Analyze this resume/CV document and return the information as a structured JSON object with the following format:

{{
  "personal_information": {{
    "full_name": "string",
    "email": "string",
    "phone": "string", 
    "location": "string",
    "professional_title": "string",
    "linkedin": "string",
    "portfolio": "string"
  }},
  "professional_summary": {{
    "career_level": "Entry/Mid/Senior",
    "years_of_experience": "number or string",
    "key_expertise": ["area1", "area2", "area3"],
    "professional_strengths": ["strength1", "strength2"]
  }},
  "work_experience": [
    {{
      "company": "string",
      "position": "string",
      "duration": "string",
      "responsibilities": ["resp1", "resp2"],
      "achievements": ["achievement1", "achievement2"],
      "technologies": ["tech1", "tech2"]
    }}
  ],
  "education": [
    {{
      "degree": "string",
      "institution": "string",
      "graduation_date": "string",
      "gpa": "string",
      "coursework": ["course1", "course2"],
      "honors": ["honor1", "honor2"]
    }}
  ],
  "technical_skills": {{
    "programming_languages": ["lang1", "lang2"],
    "frameworks": ["framework1", "framework2"],
    "databases": ["db1", "db2"],
    "cloud_platforms": ["platform1", "platform2"],
    "tools": ["tool1", "tool2"]
  }},
  "soft_skills": ["skill1", "skill2", "skill3"],
  "languages": [
    {{
      "language": "string",
      "proficiency": "Native/Fluent/Intermediate/Basic"
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "duration": "string",
      "technologies": ["tech1", "tech2"],
      "description": "string",
      "role": "string",
      "impact": "string"
    }}
  ],
  "certifications": [
    {{
      "name": "string",
      "issuer": "string",
      "date": "string"
    }}
  ],
  "additional_information": {{
    "volunteer_work": ["work1", "work2"],
    "memberships": ["membership1", "membership2"],
    "conferences": ["conference1", "conference2"]
  }}
}}

Document Content:
{text}

IMPORTANT: Return ONLY valid JSON. If any information is not found, use "Not specified" for strings, empty arrays [] for lists, or empty objects {{}} as appropriate. Ensure all JSON is properly formatted and parseable.
"""
        prompt_time = time.time() - prompt_start
        logger.info(f"📝 Prompt prepared in {prompt_time:.2f}s - Length: {len(resume_analysis_prompt)} chars")
        
        # Make API call
        api_start = time.time()
        logger.info("🌐 Making OpenAI API call...")
        
        response = settings.openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an expert HR professional and resume analyst. Return structured JSON data only. Ensure all JSON is valid and parseable."},
                {"role": "user", "content": resume_analysis_prompt}
            ],
            max_tokens=settings.max_tokens,
            temperature=settings.temperature
        )
        
        api_time = time.time() - api_start
        total_time = time.time() - start_time
        
        response_text = response.choices[0].message.content
        
        # Handle None response
        if not response_text:
            logger.error("❌ OpenAI returned empty response")
            return StructuredAnalysis(
                error="OpenAI returned empty response"
            )
        
        logger.info(f"✅ OpenAI API call completed in {api_time:.2f}s")
        logger.info(f"📊 Response length: {len(response_text)} chars")
        logger.info(f"🏁 Total OpenAI analysis time: {total_time:.2f}s")
        
        # Parse JSON response
        try:
            # Clean the response text (remove code blocks if present)
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            structured_data = json.loads(cleaned_response)
            logger.info("✅ Successfully parsed JSON response")
            
            # Convert to StructuredAnalysis Pydantic model
            return StructuredAnalysis(**structured_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {str(e)}")
            logger.error(f"Raw response: {response_text}")
            
            # Return fallback structure with the raw text
            return StructuredAnalysis(
                error=f"Failed to parse structured response: {str(e)}",
                raw_response=response_text
            )
        except Exception as e:
            logger.error(f"❌ Failed to create StructuredAnalysis: {str(e)}")
            # Return fallback structure
            return StructuredAnalysis(
                error=f"Failed to create structured response: {str(e)}",
                raw_response=response_text
            )
        
    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"❌ OpenAI analysis failed after {error_time:.2f}s: {str(e)}")
        return StructuredAnalysis(
            error=f"OpenAI analysis failed: {str(e)}. Please check your API key and network connection."
        )