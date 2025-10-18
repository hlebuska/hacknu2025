from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
from app.routers import chat
from app.routers import vacancies, applications
from app.tasks.jobs import broker
from app.db.session import init_db, engine
from taskiq import TaskiqScheduler
from sqlmodel import SQLModel
import asyncio
import os

from app.config.settings import settings
from app.backend_models.response import PDFAnalysisResponse
from app.services_pdf.pdf_request import PDFRequestService

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
# Ensure directory exists before mounting
uploads_dir = Path("uploads/resumes")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=str(uploads_dir)), name="files")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HackNU API", 
        "endpoints": {
            "health": "/health",
            "analyze_pdf": "/api/v1/analyze-pdf (PDF → AI analysis)",
            "parse_pdf": "/api/v1/parse-pdf (PDF → text extraction only)",
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
