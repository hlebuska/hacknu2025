import argparse
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

CHROMA_PATH = "chroma"

# NEW: Custom prompt template for resume-vacancy analysis
RESUME_VACANCY_ANALYSIS_TEMPLATE = """
You are an AI recruitment assistant analyzing differences between a candidate's resume and job vacancy requirements.

RESUME DATA:
{resume_data}

VACANCY DATA:
{vacancy_data}

KEY DIFFERENCES IDENTIFIED:
{differences}

INSTRUCTIONS:
Based on the differences above, generate targeted questions to ask the candidate. Focus on:
1. Addressing specific gaps or inconsistencies
2. Asking about their strengths that compensate for missing requirements
3. Seeking clarification on ambiguous or conflicting information
4. Understanding their relevant experience for missing skills

Generate 3-5 specific, professional questions that address the most critical differences.
Format the response as a natural conversation starter.

Your questions:
"""

def load_json_files():
    """Load and parse resume and vacancy JSON files"""
    try:
        with open('resume_parsed.json', 'r') as f:
            resume_data = json.load(f)
        with open('vacancy_parsed.json', 'r') as f:
            vacancy_data = json.load(f)
        return resume_data, vacancy_data
    except FileNotFoundError as e:
        print(f"Error loading JSON files: {e}")
        return {}, {}

def find_differences(resume_data, vacancy_data):
    """Identify key differences between resume and vacancy requirements"""
    differences = []
    
    # Compare common fields that typically exist in both resume and vacancy
    common_fields = ['work_experience', 'skills', 'education', 'requirements', 'experience_years']
    
    for field in common_fields:
        resume_value = resume_data.get(field)
        vacancy_value = vacancy_data.get(field)
        
        # NEW: Only add to differences if both values exist and are different
        if resume_value is not None and vacancy_value is not None:
            if str(resume_value).lower() != str(vacancy_value).lower():
                differences.append({
                    'field': field,
                    'resume_value': resume_value,
                    'vacancy_value': vacancy_value,
                    'description': f"Resume shows '{resume_value}' but vacancy requires '{vacancy_value}'"
                })
    
    # NEW: Check for missing skills/requirements
    resume_skills = set(resume_data.get('skills', []))
    vacancy_requirements = set(vacancy_data.get('required_skills', []) + vacancy_data.get('requirements', []))
    
    missing_skills = vacancy_requirements - resume_skills
    if missing_skills:
        differences.append({
            'field': 'missing_skills',
            'resume_value': list(resume_skills),
            'vacancy_value': list(vacancy_requirements),
            'description': f"Missing required skills: {', '.join(missing_skills)}"
        })
    
    return differences

def generate_targeted_questions(differences):
    """Generate AI questions based on identified differences"""
    if not differences:
        return "No significant differences found between resume and vacancy requirements."
    
    # Prepare data for the prompt
    resume_data, vacancy_data = load_json_files()
    
    differences_text = "\n".join([diff['description'] for diff in differences])
    
    prompt_template = ChatPromptTemplate.from_template(RESUME_VACANCY_ANALYSIS_TEMPLATE)
    prompt = prompt_template.format(
        resume_data=json.dumps(resume_data, indent=2),
        vacancy_data=json.dumps(vacancy_data, indent=2),
        differences=differences_text
    )
    
    model = ChatOpenAI()
    response_text = model.predict(prompt)
    
    return response_text

def main():
    # Create CLI
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text or 'analyze' to compare resume and vacancy")
    args = parser.parse_args()
    query_text = args.query_text
    
    # NEW: Special command to analyze resume-vacancy differences
    if query_text.lower() == "analyze":
        # Load JSON data
        resume_data, vacancy_data = load_json_files()
        
        if not resume_data or not vacancy_data:
            print("Error: Could not load resume_parsed.json or vacancy_parsed.json")
            return
        
        # Find differences
        differences = find_differences(resume_data, vacancy_data)
        
        print("=== RESUME-VACANCY ANALYSIS ===")
        print(f"Found {len(differences)} key differences:")
        
        for i, diff in enumerate(differences, 1):
            print(f"{i}. {diff['description']}")
        
        print("\n=== AI GENERATED QUESTIONS ===")
        questions = generate_targeted_questions(differences)
        print(questions)
        
        return
    
    # Original functionality for document querying
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0 or results[0][1] < 0.7:
        print(f"Unable to find matching results.")
        return

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    print(prompt)

    model = ChatOpenAI()
    response_text = model.predict(prompt)

    sources = [doc.metadata.get("source", None) for doc, _score in results]
    formatted_response = f"Response: {response_text}\nSources: {sources}"
    print(formatted_response)

# Keep the original prompt template for backward compatibility
PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

if __name__ == "__main__":
    main()