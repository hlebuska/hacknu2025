import json
import os
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional

try:
    # Prefer LangChain Chat wrapper if installed
    from langchain_openai import ChatOpenAI
    _HAS_LANGCHAIN = True
except Exception:
    ChatOpenAI = None
    _HAS_LANGCHAIN = False

try:
    import openai
    _HAS_OPENAI = True
except Exception:
    openai = None
    _HAS_OPENAI = False

# Optional retrieval tooling
try:
    # LangChain embeddings + Chroma vectorstore if available
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings
    _HAS_CHROMA = True
except Exception:
    Chroma = None
    OpenAIEmbeddings = None
    _HAS_CHROMA = False


# Auto-load dotenv files to make it easy to drop keys into the repo
# Look for `backend/app/models/chat-bot/.env` first, then fallback to `backend/.env`
try:
    _HERE = os.path.dirname(__file__)
    candidate1 = os.path.abspath(os.path.join(_HERE, '..', 'models', 'chat-bot', '.env'))
    candidate2 = os.path.abspath(os.path.join(_HERE, '..', '..', '.env'))
    if os.path.exists(candidate1):
        load_dotenv(candidate1)
    elif os.path.exists(candidate2):
        load_dotenv(candidate2)
    else:
        # still call load_dotenv() to allow normal .env lookups if any
        load_dotenv()
except Exception:
    pass


class AIChatService:
    """Service to analyze resume vs vacancy JSONs and generate interview questions.

    Behavior:
    - Loads JSON files from cwd (resume_parsed.json, vacancy_parsed.json) if not provided
    - Computes structured differences
    - Generates 3-5 interview questions using LangChain ChatOpenAI if available,
      otherwise falls back to OpenAI's chat completion API. If no API is available,
      returns a deterministic prompt that the developer can use to call an LLM.
    """

    RESUME_FILE = "resume_parsed.json"
    VACANCY_FILE = "vacancy_parsed.json"
    CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma")

    def load_data(self, resume: Optional[Dict[str, Any]] = None, vacancy: Optional[Dict[str, Any]] = None):
        if resume is not None and vacancy is not None:
            return resume, vacancy

        # attempt to load from disk
        try:
            with open(self.RESUME_FILE, "r", encoding="utf-8") as f:
                resume_data = json.load(f)
        except Exception:
            resume_data = None

        try:
            with open(self.VACANCY_FILE, "r", encoding="utf-8") as f:
                vacancy_data = json.load(f)
        except Exception:
            vacancy_data = None

        return resume_data, vacancy_data

    def analyze_differences(self, resume_data: Dict[str, Any], vacancy_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        differences: List[Dict[str, Any]] = []

        comparison_fields = [
            ("experience_years", "work_experience", "years of experience"),
            ("skills", "required_skills", "technical skills"),
            ("education", "education_requirements", "education background"),
            ("certifications", "required_certifications", "certifications"),
            ("languages", "language_requirements", "language skills"),
        ]

        for resume_field, vacancy_field, field_name in comparison_fields:
            resume_value = resume_data.get(resume_field)
            vacancy_value = vacancy_data.get(vacancy_field)

            # skip empty
            if not resume_value or not vacancy_value:
                continue

            if isinstance(resume_value, list) and isinstance(vacancy_value, list):
                missing_items = set(vacancy_value) - set(resume_value)
                if missing_items:
                    differences.append({
                        "field": field_name,
                        "type": "missing_items",
                        "resume_value": resume_value,
                        "vacancy_value": vacancy_value,
                        "description": f"Missing {field_name}: {', '.join(sorted(missing_items))}",
                    })
            else:
                if str(resume_value).strip().lower() != str(vacancy_value).strip().lower():
                    differences.append({
                        "field": field_name,
                        "type": "mismatch",
                        "resume_value": resume_value,
                        "vacancy_value": vacancy_value,
                        "description": f"Resume shows '{resume_value}' but vacancy requires '{vacancy_value}' for {field_name}",
                    })

        # Check missing skills / requirements if available
        resume_skills = set(resume_data.get("skills", []) or [])
        vacancy_reqs = set((vacancy_data.get("required_skills", []) or []) + (vacancy_data.get("requirements", []) or []))
        missing_skills = vacancy_reqs - resume_skills
        if missing_skills:
            differences.append({
                "field": "missing_skills",
                "type": "missing_items",
                "resume_value": list(resume_skills),
                "vacancy_value": list(vacancy_reqs),
                "description": f"Missing required skills: {', '.join(sorted(missing_skills))}",
            })

        return differences

    def _build_prompt(self, differences: List[Dict[str, Any]], resume_data: Dict[str, Any], vacancy_data: Dict[str, Any]) -> str:
        diffs_text = "\n".join([f"- {d['description']}" for d in differences]) if differences else "No significant differences found."

        prompt = f"""
You are an experienced HR recruiter. Based on the following differences between a candidate's resume and job requirements, generate 3-5 targeted interview questions.

Candidate:
{json.dumps(resume_data, indent=2, ensure_ascii=False)}

Vacancy:
{json.dumps(vacancy_data, indent=2, ensure_ascii=False)}

DIFFERENCES:
{diffs_text}

GUIDELINES:
1. Ask about specific gaps in experience or skills
2. Inquire how the candidate would compensate for missing qualifications
3. Ask for examples that demonstrate relevant capabilities
4. Be professional but conversational
5. Focus on understanding potential rather than criticizing gaps

Generate 3-5 concise, targeted interview questions as a natural conversation starter.
"""
        return prompt

    # ------------------ Retrieval helpers ------------------
    def build_vectorstore(self, resume_data: Dict[str, Any], vacancy_data: Dict[str, Any]):
        """Create or load a Chroma vectorstore with resume and vacancy text segments.

        Returns the Chroma DB object and the embedding function instance.
        """
        if not _HAS_CHROMA:
            raise RuntimeError("Chroma/embeddings not available. Install required packages to enable retrieval.")

        # Prepare documents to index (flatten selected fields)
        docs = []
        metadata = []

        def push_items(prefix: str, obj: Dict[str, Any]):
            # Flatten primitive and list fields into text chunks
            for k, v in obj.items():
                if isinstance(v, list):
                    text = f"{k}: {', '.join(map(str, v))}"
                else:
                    text = f"{k}: {v}"
                docs.append(text)
                metadata.append({"source": prefix, "field": k})

        push_items("resume", resume_data)
        push_items("vacancy", vacancy_data)

        embedding_function = OpenAIEmbeddings()

        db = Chroma(persist_directory=self.CHROMA_PATH, embedding_function=embedding_function)
        # If DB empty, add docs
        try:
            existing = db._collection.count()
        except Exception:
            existing = 0

        if existing == 0:
            db.add_texts(docs, metadatas=metadata)

        return db, embedding_function

    def retrieve_context(self, db, question: str, k: int = 3) -> str:
        """Retrieve top-k relevant documents as context text."""
        results = db.similarity_search_with_relevance_scores(question, k=k)
        if not results:
            return ""
        texts = [doc.page_content for doc, _score in results]
        return "\n\n---\n\n".join(texts)

    def generate_interview_questions(self, differences: List[Dict[str, Any]], resume_data: Dict[str, Any], vacancy_data: Dict[str, Any]) -> str:
        if not differences:
            return "No significant differences found. The candidate appears to be a good match."

        prompt = self._build_prompt(differences, resume_data, vacancy_data)

        # Try retrieval augmentation if requested via env flag
        use_retrieval = os.getenv("AI_USE_RETRIEVAL", "false").lower() in ("1", "true", "yes")
        retrieval_context = None
        if use_retrieval and _HAS_CHROMA:
            try:
                db, _ = self.build_vectorstore(resume_data, vacancy_data)
                retrieval_context = self.retrieve_context(db, prompt, k=3)
                if retrieval_context:
                    prompt = f"Context:\n{retrieval_context}\n\n" + prompt
            except Exception:
                # ignore retrieval errors and continue
                retrieval_context = None

        # Try LangChain ChatOpenAI first
        if _HAS_LANGCHAIN and ChatOpenAI is not None:
            try:
                model = ChatOpenAI(temperature=0.2)
                # LangChain ChatOpenAI accepts a string prompt with predict
                return model.predict(prompt)
            except Exception:
                pass

        # Fallback to openai package (Chat Completions)
        if _HAS_OPENAI and openai is not None and os.getenv("OPENAI_API_KEY"):
            try:
                resp = openai.ChatCompletion.create(
                    model=os.getenv("                    cd /d C:\Users\Daulet\Desktop\new_hacknu\hacknu2025\backend
                    echo %OPENAI_API_KEY%_CHAT_MODEL", "gpt-3.5-turbo"),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=512,
                    temperature=0.2,
                )
                return resp["choices"][0]["message"]["content"].strip()
            except Exception as e:
                return f"LLM call failed: {e}"

        # If no model is available, return the prompt so developer can run it manually
                            # Allow overriding model via OPENAI_CHAT_MODEL or OPENAI_MODEL env vars
                            model_name = os.getenv("OPENAI_CHAT_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-3.5-turbo"
                            resp = openai.ChatCompletion.create(
                                model=model_name,

def _example_run():
    svc = AIChatService()
    resume, vacancy = svc.load_data()
    if not resume or not vacancy:
        print("No resume_parsed.json or vacancy_parsed.json found in cwd.")
        return
    diffs = svc.analyze_differences(resume, vacancy)
    print("Differences:", diffs)
    print("Questions:\n", svc.generate_interview_questions(diffs, resume, vacancy))


if __name__ == "__main__":
    _example_run()
