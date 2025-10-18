This folder contains the AI chat analyzer service used to compare parsed resume and vacancy JSONs and generate targeted interview questions.

How to run locally

1. Install dependencies (preferably in a venv):

```bash
pip install -r requirements.txt
```

2. Place `resume_parsed.json` and `vacancy_parsed.json` in this folder (or provide them in the API body).

3. Run the example script:

```bash
python -m app.services.ai_chat
```

4. To run as an API, start the backend (uvicorn) and call POST /chat/analyze with optional JSON body:

```json
{
  "resume": { ... },
  "vacancy": { ... }
}
```

If you want LLM-generated questions, set `OPENAI_API_KEY` in your environment. The service will try LangChain's `ChatOpenAI` first, then fall back to `openai` package.

Where to put OPENAI_API_KEY
- Windows cmd.exe (temporary for the session):

```bat
set OPENAI_API_KEY=sk-<your-key-here>
```

- Windows PowerShell (temporary for the session):

```powershell
$env:OPENAI_API_KEY = "sk-<your-key-here>"
```

- Persistently (recommended): add it to your user environment variables via Windows Settings > Environment Variables.

Auto-loading a project .env (option C)
- You can drop a `.env` file at `backend/app/models/chat-bot/.env` (or `backend/.env`) and the analyzer will automatically load it at runtime. Typical file contents:

```
OPENAI_API_KEY=sk-<your-key-here>
AI_USE_RETRIEVAL=true
CHROMA_PATH=./chroma
```

Note: This is convenient for local dev, but do not commit your `.env` file into version control.

Enable retrieval (embeddings + Chroma)
- Install the extra packages (add to your venv):

```bat
pip install langchain langchain-openai chromadb langchain-community openai
```

- Optionally set CHROMA_PATH environment var to change where Chroma persists vectors (default: `./chroma` in backend folder):

```bat
set CHROMA_PATH=c:\path\to\chroma_dir
```

- Toggle retrieval for a single API call by passing the `use_retrieval=true` query parameter to `/chat/analyze`, or enable it globally by setting:

```bat
set AI_USE_RETRIEVAL=true
```
