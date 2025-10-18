import os
from google import genai
from google.genai import types

def parse_resume_with_requirements_gemini(job_requirements, resume_text):
    """
    Parses a resume against job requirements using the official Gemini API SDK.
    """
    try:
   
        client = genai.Client()
    except Exception as e:
      
        return f"Error initializing Gemini client: {e}. Ensure GOOGLE_API_KEY is set."

    key_sections="Personal Information (Candidate Overview); Job Experience (Work History); Education;  Skills; Languages; Projects;Certifications and Achievements;"
    
    system_instruction = f"""
    Job Requirements: {job_requirements}
    Resume Content: {resume_text}

    You are an expert resume analyzer. Your task is to perform two actions based on the job requirements:

    1.  **Extract Match:** Provide only the sections from the 'Resume Content' ({key_sections}) that are most **relevant to the 'Job Requirements'**.
    2.  **Calculate Fit Score:** Assign a **single numerical score** from **0 to 100** that represents how well the candidate's background matches the requirements (100 being a perfect fit).

    Your final output MUST follow this exact, structured json format:

    'MATCHING SECTIONS':'[Relevant extracted resume text goes here]',
    'FIT SCORE': [The calculated score (0-100) goes here]
    """

    # Configuration for the API call
    generation_config = types.GenerateContentConfig(
        max_output_tokens=100000,
        temperature=0.7,
    )

    user_prompt = "Analyze the resume against the job requirements and return only the specified JSON with MATCHING SECTIONS and FIT SCORE."

    try:
        # Call the Gemini API using the correct method and model name
        response = client.models.generate_content(
            model="gemini-1.5-flash", # Use the correct model identifier
            contents=f"{system_instruction}\n\n{user_prompt}",
            config=generation_config
        )
        
        return response.text

    except Exception as e:
        return f"An error occurred during API call: {e}"

job_requirements = """
We are looking for a software engineer with strong experience in Python and machine learning. The candidate should be familiar with frameworks such as TensorFlow or PyTorch, and have experience with cloud platforms like AWS or Google Cloud. The role involves working in an an agile environment and contributing to system architecture.
"""

resume_text = """
John Doe
Skills: Python, JavaScript, SQL, TensorFlow, AWS
Experience: Software Engineer at XYZ Corp (Jan 2020 - Present)
- Developed machine learning models for predictive analytics.
- Worked with cloud platforms, specifically AWS, to deploy solutions.
Education: B.S. in Computer Science, XYZ University (Graduated 2019)
"""

parsed_output = parse_resume_with_requirements_gemini(job_requirements, resume_text)

print("Parsed Output:")
print(parsed_output)