"""
Dedicated analyzer for resume-vacancy comparison and question generation
"""
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

class ResumeVacancyAnalyzer:
    def __init__(self):
        self.model = ChatOpenAI()
        
    def load_data(self):
        """Load resume and vacancy JSON files"""
        try:
            with open('resume_parsed.json', 'r') as f:
                resume_data = json.load(f)
            with open('vacancy_parsed.json', 'r') as f:
                vacancy_data = json.load(f)
            return resume_data, vacancy_data
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return None, None
    
    def analyze_differences(self, resume_data, vacancy_data):
        """Comprehensive analysis of differences between resume and vacancy"""
        differences = []
        
        # NEW: Field-by-field comparison with specific logic
        comparison_fields = [
            ('experience_years', 'work_experience', 'years of experience'),
            ('skills', 'required_skills', 'technical skills'),
            ('education', 'education_requirements', 'education background'),
            ('certifications', 'required_certifications', 'certifications'),
            ('languages', 'language_requirements', 'language skills')
        ]
        
        for resume_field, vacancy_field, field_name in comparison_fields:
            resume_value = resume_data.get(resume_field)
            vacancy_value = vacancy_data.get(vacancy_field)
            
            # NEW: Skip if either value is missing or empty
            if not resume_value or not vacancy_value:
                continue
                
            # NEW: Handle different data types (list vs string vs number)
            if isinstance(resume_value, list) and isinstance(vacancy_value, list):
                missing_items = set(vacancy_value) - set(resume_value)
                if missing_items:
                    differences.append({
                        'field': field_name,
                        'type': 'missing_items',
                        'resume_value': resume_value,
                        'vacancy_value': vacancy_value,
                        'description': f"Missing {field_name}: {', '.join(missing_items)}"
                    })
            else:
                # Compare string/number values
                if str(resume_value).strip().lower() != str(vacancy_value).strip().lower():
                    differences.append({
                        'field': field_name,
                        'type': 'mismatch',
                        'resume_value': resume_value,
                        'vacancy_value': vacancy_value,
                        'description': f"Resume shows '{resume_value}' but vacancy requires '{vacancy_value}' for {field_name}"
                    })
        
        return differences
    
    def generate_interview_questions(self, differences):
        """Generate targeted interview questions based on differences"""
        if not differences:
            return "No significant differences found. The candidate appears to be a good match."
        
        prompt_template = ChatPromptTemplate.from_template("""
You are an experienced HR recruiter. Based on the following differences between a candidate's resume and job requirements, generate 3-5 targeted interview questions.

DIFFERENCES:
{differences}

GUIDELINES:
1. Ask about specific gaps in experience or skills
2. Inquire about how they would compensate for missing qualifications
3. Ask for examples that demonstrate relevant capabilities
4. Be professional but conversational
5. Focus on understanding their potential rather than criticizing gaps

Generate questions that would help assess if the candidate can succeed despite the identified differences.

Your questions:
""")
        
        differences_text = "\n".join([f"- {diff['description']}" for diff in differences])
        prompt = prompt_template.format(differences=differences_text)
        
        response = self.model.predict(prompt)
        return response
    
    def run_analysis(self):
        """Main method to run complete analysis"""
        resume_data, vacancy_data = self.load_data()
        
        if not resume_data or not vacancy_data:
            print("Could not load required JSON files.")
            return
        
        print("=== RESUMÉ AND VACANCY ANALYSIS ===")
        print(f"Vacancy: {vacancy_data.get('job_title', 'N/A')}")
        print(f"Candidate: {resume_data.get('name', 'N/A')}")
        print()
        
        # Find differences
        differences = self.analyze_differences(resume_data, vacancy_data)
        
        print("=== IDENTIFIED DIFFERENCES ===")
        for i, diff in enumerate(differences, 1):
            print(f"{i}. {diff['description']}")
        
        print("\n=== RECOMMENDED INTERVIEW QUESTIONS ===")
        questions = self.generate_interview_questions(differences)
        print(questions)

def main():
    analyzer = ResumeVacancyAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()