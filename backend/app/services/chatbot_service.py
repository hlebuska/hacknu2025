"""
Chatbot service that integrates resume-vacancy analysis and conversation management.
"""
import json
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from app.models.application import Application
from app.models.vacancy import Vacancy
from app.config.settings import settings
import os


class ChatbotService:
    """Main chatbot service for handling AI conversations and analysis"""
    
    def __init__(self):
        self.model = ChatOpenAI(api_key=settings.openai_api_key)
        self.embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)
        self.chroma_path = os.getenv("CHROMA_PATH", "chroma")
    
    def analyze_resume_vacancy_differences(
        self, 
        resume_data: Dict[str, Any], 
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze differences between resume and vacancy requirements.
        
        Args:
            resume_data: Parsed resume data
            vacancy_data: Parsed vacancy data
            
        Returns:
            Dict containing differences and analysis
        """
        differences = []
        
        # Compare common fields
        common_fields = ['work_experience', 'skills', 'education', 'requirements', 'experience_years']
        
        for field in common_fields:
            resume_value = resume_data.get(field)
            vacancy_value = vacancy_data.get(field)
            
            if resume_value is not None and vacancy_value is not None:
                if str(resume_value).lower() != str(vacancy_value).lower():
                    differences.append({
                        'field': field,
                        'resume_value': resume_value,
                        'vacancy_value': vacancy_value,
                        'description': f"Resume shows '{resume_value}' but vacancy requires '{vacancy_value}'"
                    })
        
        # Check for missing skills
        resume_skills = set(resume_data.get('skills', []) if isinstance(resume_data.get('skills'), list) else [])
        vacancy_required_skills = set(
            vacancy_data.get('required_skills', []) if isinstance(vacancy_data.get('required_skills'), list) else []
        )
        vacancy_requirements = set(
            vacancy_data.get('requirements', []) if isinstance(vacancy_data.get('requirements'), list) else []
        )
        
        all_vacancy_requirements = vacancy_required_skills | vacancy_requirements
        missing_skills = all_vacancy_requirements - resume_skills
        
        if missing_skills:
            differences.append({
                'field': 'missing_skills',
                'resume_value': list(resume_skills),
                'vacancy_value': list(all_vacancy_requirements),
                'description': f"Missing required skills: {', '.join(missing_skills)}"
            })
        
        return {
            'differences': differences,
            'missing_count': len(differences),
            'resume_summary': {
                'name': resume_data.get('name'),
                'experience_years': resume_data.get('experience_years'),
                'skills': list(resume_skills)
            },
            'vacancy_summary': {
                'title': vacancy_data.get('job_title'),
                'requirements': list(all_vacancy_requirements),
                'experience_required': vacancy_data.get('experience_years')
            }
        }
    
    def generate_interview_questions(
        self, 
        resume_data: Dict[str, Any], 
        vacancy_data: Dict[str, Any],
        differences: List[Dict[str, Any]]
    ) -> str:
        """
        Generate targeted interview questions based on resume-vacancy differences.
        
        Args:
            resume_data: Parsed resume data
            vacancy_data: Parsed vacancy data
            differences: List of identified differences
            
        Returns:
            String containing AI-generated questions
        """
        if not differences:
            return "No significant differences found. The candidate appears to be a strong match!"
        
        differences_text = "\n".join([diff['description'] for diff in differences])
        
        prompt_template = ChatPromptTemplate.from_template("""
You are an experienced HR recruiter analyzing a candidate's fit for a position. 
Based on the differences between their resume and the job requirements, generate 3-5 targeted interview questions.

RESUME DATA:
{resume_data}

VACANCY DATA:
{vacancy_data}

KEY DIFFERENCES IDENTIFIED:
{differences}

GUIDELINES:
1. Ask about specific gaps in experience or skills
2. Inquire about how they would compensate for missing qualifications
3. Ask for examples that demonstrate relevant capabilities
4. Be professional but conversational
5. Focus on understanding their potential rather than criticizing gaps

Generate questions that would help assess if the candidate can succeed despite the identified differences.
Format the response as natural conversation starters, one per line.

Your questions:
""")
        
        prompt = prompt_template.format(
            resume_data=json.dumps(resume_data, indent=2),
            vacancy_data=json.dumps(vacancy_data, indent=2),
            differences=differences_text
        )
        
        response = self.model.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    def chat_with_context(
        self, 
        user_message: str, 
        resume_data: Optional[Dict[str, Any]] = None,
        vacancy_data: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Process a chat message with optional resume/vacancy context.
        
        Args:
            user_message: The user's message
            resume_data: Optional parsed resume data for context
            vacancy_data: Optional parsed vacancy data for context
            conversation_history: Optional previous messages for context
            
        Returns:
            String containing the AI response
        """
        if conversation_history is None:
            conversation_history = []
        
        system_prompt = "You are a helpful recruitment assistant. "
        
        if resume_data and vacancy_data:
            system_prompt += f"""You have access to the candidate's resume and the job vacancy requirements. 
            Help the candidate understand how their qualifications match the requirements and provide guidance on interviews or applications.
            
            CANDIDATE RESUME: {json.dumps(resume_data, indent=2)}
            JOB VACANCY: {json.dumps(vacancy_data, indent=2)}
            """
        
        messages = [
            {"role": "system", "content": system_prompt}
        ] + conversation_history + [
            {"role": "user", "content": user_message}
        ]
        
        response = self.model.invoke(messages)
        return response.content if hasattr(response, 'content') else str(response)
    
    def query_knowledge_base(self, query: str, k: int = 3) -> Dict[str, Any]:
        """
        Query the vector database for relevant information.
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            Dict containing search results and formatted response
        """
        try:
            db = Chroma(persist_directory=self.chroma_path, embedding_function=self.embeddings)
            results = db.similarity_search_with_relevance_scores(query, k=k)
            
            if len(results) == 0 or results[0][1] < 0.7:
                return {
                    'success': False,
                    'message': 'No relevant information found in knowledge base'
                }
            
            context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
            sources = [doc.metadata.get("source", "Unknown") for doc, _score in results]
            
            # Generate response using context
            prompt = f"""Based on the following context, answer this question: {query}

CONTEXT:
{context_text}

Please provide a helpful answer based on the context above."""
            
            response = self.model.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            return {
                'success': True,
                'response': response_text,
                'sources': sources,
                'context': context_text
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error querying knowledge base: {str(e)}'
            }
