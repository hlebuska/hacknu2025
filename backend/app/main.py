from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
from app.routers import chat
from app.routers import vacancies, applications
from app.tasks.jobs import broker
from app.db.session import init_db, engine, async_session
from taskiq import TaskiqScheduler
from sqlmodel import SQLModel, select
import asyncio
import os
import json
from openai import OpenAI
from typing import Optional

from app.config.settings import settings
from app.backend_models.response import PDFAnalysisResponse
from app.services_pdf.pdf_request import PDFRequestService
from app.models.application import Application

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Store clarifications per session
clarifications_store = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: cleanup if needed

app = FastAPI(title="HackNU API", lifespan=lifespan)

origins = ["*"]  # later restrict to widget/dashboard domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat.router)
app.include_router(vacancies.router)
app.include_router(applications.router)

# Initialize PDF request service
pdf_request_service = PDFRequestService()

# Serve uploaded resumes statically under /files
uploads_dir = Path("uploads/resumes")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=str(uploads_dir)), name="files")

# WebSocket endpoint for chat
@app.websocket("/ws/chat/{application_id}")
async def websocket_chat_endpoint(websocket: WebSocket, application_id: str):
    await websocket.accept()
    
    # Send JSON response with "connected" status
    await websocket.send_json({"type": "status", "message": "connected"})
    
    # Fetch application from database
    async with async_session() as session:
        result = await session.execute(
            select(Application).where(Application.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            await websocket.send_json({
                "type": "error",
                "message": "Application not found"
            })
            await websocket.close()
            return
        
        context = {
            "id": str(application.id),
            "first_name": application.first_name,
            "last_name": application.last_name,
            "email": application.email,
            "matching_score": application.matching_score,
            "matching_sections": application.matching_sections or {}
        }
    
    # Initialize session
    session_id = id(websocket)
    requirements = context.get("matching_sections", {}).get("requirements", [])
    clarifications_store[session_id] = {
        "application_id": application_id,
        "current_question_index": 0,
        "clarifications": [],
        "requirements": requirements,
        "context": context
    }
    
    # Send initial greeting
    initial_message = f"Hello {context['first_name']}! I'm here to help clarify your application. Your current matching score is {context['matching_score']}%. Let me ask you a few questions."
    await websocket.send_json({
        "type": "message",
        "role": "assistant",
        "content": initial_message
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                payload = json.loads(data)
                message = payload.get("message", "")
                history = payload.get("history", [])
                
                session_data = clarifications_store[session_id]
                requirements = session_data["requirements"]
                current_index = session_data["current_question_index"]
                
                # Get unresolved requirements (match < 80%)
                unresolved = [req for req in requirements if req.get('match_percent', 0) < 80]
                
                # Store clarification if user provided an answer
                if len(history) > 0 and history[-1]["role"] == "user":
                    if current_index < len(unresolved):
                        current_req = unresolved[current_index]
                        session_data["clarifications"].append({
                            "requirement": current_req.get('vacancy_req', ''),
                            "original_data": current_req.get('user_req_data', ''),
                            "clarification": message,
                            "original_match": current_req.get('match_percent', 0)
                        })
                        session_data["current_question_index"] += 1
                        current_index = session_data["current_question_index"]
                
                # Prepare system message
                if requirements and unresolved:
                    if current_index < len(unresolved):
                        current_req = unresolved[current_index]
                        just_answered = (len(history) > 0 and history[-1]["role"] == "user")
                        
                        if just_answered and current_index > 0:
                            system_message = f"""You are an HR assistant. The user just answered a question.
                            
Now ask about this next requirement:
- Requirement: {current_req.get('vacancy_req', '')}
- Current info: {current_req.get('user_req_data', '')}

Rules:
1. Start with "Got it." or "Thanks."
2. Immediately ask the next question
3. Keep total response under 25 words
4. Be direct and professional
"""
                        else:
                            system_message = f"""You are an HR assistant. Ask ONE short question to clarify this requirement.

Requirement to clarify:
- {current_req.get('vacancy_req', '')}
- Current data: {current_req.get('user_req_data', '')}

Rules:
1. Ask ONE specific question
2. Keep it under 20 words
3. Be direct and professional
"""
                    else:
                        # All questions answered - save to database
                        async with async_session() as db_session:
                            result = await db_session.execute(
                                select(Application).where(Application.id == application_id)
                            )
                            app = result.scalar_one_or_none()
                            if app:
                                if not app.matching_sections:
                                    app.matching_sections = {}
                                app.matching_sections["clarifications"] = session_data["clarifications"]
                                db_session.add(app)
                                await db_session.commit()
                        
                        system_message = f"""You are an HR assistant wrapping up.

All requirements have been clarified. 
Thank the applicant briefly (under 15 words) and let them know their application will be reviewed.
"""
                else:
                    system_message = "You are a helpful assistant. Keep responses under 20 words."
                
                # Prepare messages for OpenAI
                messages = [{"role": "system", "content": system_message}]
                recent_history = history[-2:] if len(history) > 2 else history
                for msg in recent_history:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                
                # Call OpenAI API
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.5,
                    max_tokens=100
                )
                
                ai_response = response.choices[0].message.content
                
                # Send JSON response
                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": ai_response
                })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid format"
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error: {str(e)}"
                })
                
    except WebSocketDisconnect:
        if session_id in clarifications_store:
            del clarifications_store[session_id]

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HackNU API", 
        "endpoints": {
            "health": "/health",
            "analyze_pdf": "/api/v1/analyze-pdf (PDF → AI analysis)",
            "parse_pdf": "/api/v1/parse-pdf (PDF → text extraction only)",
            "websocket_chat": "/ws/chat/{application_id}",
            "docs": "/docs",
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    openai_status = "connected" if settings.openai_api_key and settings.openai_client else "no_api_key"
    return {
        "status": "ok",
        "openai_status": openai_status,
        "model": getattr(settings, 'openai_model', 'N/A')
    }

@app.post("/api/v1/analyze-pdf", response_model=PDFAnalysisResponse)
async def analyze_pdf(
    file: UploadFile = File(...),
    include_raw_text: bool = Form(False, description="Include extracted text in response")
):
    """Analyze PDF resume with comprehensive AI analysis using OpenAI GPT"""
    return await pdf_request_service.process_analyze_request(file, include_raw_text)

@app.post("/api/v1/parse-pdf", response_model=PDFAnalysisResponse)
async def parse_pdf(
    file: UploadFile = File(...),
    include_raw_text: bool = Form(True, description="Include extracted text in response")
):
    """Extract text from PDF using PyPDF only (no AI analysis)"""
    return await pdf_request_service.process_parse_request(file, include_raw_text)

@app.get("/test")
async def serve_test_interface():
    """Serve the HTML test interface"""
    html_file_path = os.path.join(os.path.dirname(__file__), "..", "pdf_test_interface.html")
    if os.path.exists(html_file_path):
        return FileResponse(html_file_path)
    else:
        raise HTTPException(status_code=404, detail="Test interface not found")

@app.post("/debug/reset-db")
async def reset_database():
    """
    Debug endpoint to reset the database by dropping and recreating all tables.
    WARNING: This will delete all data!
    """
    try:
        # Drop all tables
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        
        # Recreate all tables
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        
        return {
            "status": "success",
            "message": "Database has been reset successfully. All tables dropped and recreated."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to reset database: {str(e)}"
        }
