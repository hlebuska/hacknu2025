from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlmodel import select, col
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
import aiofiles
from app.models.application import Application, ApplicationCreate, ApplicationRead
from app.models.vacancy import Vacancy
from app.db.session import async_session
from app.utils.file_upload import save_uploaded_file
from pathlib import Path
from app.services_pdf.pdf_parser import PDFParserService
from app.services_pdf.resume_matcher import match_resume_to_requirements

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/applications", tags=["Applications"])

async def get_session():
    """Dependency for database session"""
    async with async_session() as session:
        yield session

async def send_chat_notification(
    application_id: str,
    email: str,
    first_name: str,
    vacancy_title: str
):
    """Send notification to applicant with chat link"""
    try:
        chat_url = f"http://localhost:5173/chat/{application_id}"  # Update with your frontend URL
        
        logger.info(f"📧 Chat notification for {first_name} ({email})")
        logger.info(f"🔗 Chat URL: {chat_url}")
        logger.info(f"💼 Vacancy: {vacancy_title}")
        
        # TODO: Implement actual email sending here
        # For now, just log the notification
        
    except Exception as e:
        logger.error(f"Failed to send chat notification: {e}")

@router.post("", response_model=ApplicationRead, status_code=201)
async def submit_application(
    background_tasks: BackgroundTasks,
    vacancy_id: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Submit a job application
    
    - **vacancy_id**: ID of the vacancy being applied to
    - **first_name**: Applicant's first name
    - **last_name**: Applicant's last name
    - **email**: Applicant's email
    - **resume**: Resume file (PDF only)
    """
    # Verify vacancy exists
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    # Save resume file
    try:
        resume_path = await save_uploaded_file(resume)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    
    # Create application
    application = Application(
        vacancy_id=vacancy_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        resume_pdf=resume_path
    )
    
    session.add(application)
    await session.commit()
    await session.refresh(application)
    
    # Try to analyze resume vs job requirements (best-effort; non-blocking on errors)
    try:
        # Build requirements text
        reqs = vacancy.requirements
        if reqs:
            if isinstance(reqs, dict):
                job_requirements_text = "\n".join(
                    f"{k}: {v}" for k, v in reqs.items()
                )
            else:
                job_requirements_text = str(reqs)
        else:
            job_requirements_text = vacancy.description or ""

        # Read saved PDF bytes
        file_path = Path(resume_path)
        if not file_path.exists():
            alt_path = Path.cwd() / resume_path
            file_path = alt_path if alt_path.exists() else file_path

        pdf_bytes: Optional[bytes] = None
        if file_path.exists():
            async with aiofiles.open(file_path, 'rb') as f:
                pdf_bytes = await f.read()

        if pdf_bytes:
            parser = PDFParserService()
            extracted_text, _meta = parser.extract_text_from_pdf(pdf_bytes)
            if extracted_text:
                result = await match_resume_to_requirements(
                    job_requirements=job_requirements_text,
                    resume_text=extracted_text,
                    model="gpt-4o-mini",
                )
                if isinstance(result, dict) and not result.get("error"):
                    # Update application with analysis
                    fit_raw = result.get("FIT_SCORE")
                    score_val = None
                    if isinstance(fit_raw, (int, float)):
                        score_val = float(fit_raw)
                    elif isinstance(fit_raw, str):
                        try:
                            score_val = float(fit_raw.strip())
                        except Exception:
                            score_val = None
                    application.matching_score = score_val
                    # Store the full result (with requirements array) in matching_sections
                    application.matching_sections = result
                    session.add(application)
                    await session.commit()
                    await session.refresh(application)
                    logger.info(f"✅ Resume analyzed: FIT_SCORE={score_val}")
                    
                    # Send chat notification if score is below threshold
                    if score_val and score_val < 80:
                        background_tasks.add_task(
                            send_chat_notification,
                            str(application.id),
                            email,
                            first_name,
                            vacancy.title
                        )
                        logger.info(f"🤖 Chat notification queued for application {application.id}")
                else:
                    logger.warning(f"Resume matching failed or invalid response: {result}")
            else:
                logger.warning("No text extracted from uploaded resume for matching")
        else:
            logger.warning("Saved resume file not found or empty; skipping matching")
    except Exception as e:
        logger.exception(f"Resume matching pipeline failed: {e}")

    return application

@router.get("", response_model=List[ApplicationRead])
async def get_applications(
    vacancy_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    """
    Get list of applications (admin/HR only - authentication to be added)
    
    - **vacancy_id**: Filter by vacancy ID
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    query = select(Application)
    
    if vacancy_id:
        query = query.where(Application.vacancy_id == vacancy_id)
    
    query = query.offset(skip).limit(limit).order_by(col(Application.created_at).desc())
    
    result = await session.execute(query)
    applications = result.scalars().all()
    
    return applications

@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(
    application_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get details of a specific application
    
    - **application_id**: ID of the application
    """
    result = await session.execute(
        select(Application).where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application

@router.get("/{application_id}/resume")
async def download_application_resume(
    application_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Download the resume PDF for a specific application.
    """
    result = await session.execute(
        select(Application).where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if not application.resume_pdf:
        raise HTTPException(status_code=404, detail="No resume file associated with this application")

    file_path = Path(application.resume_pdf)
    if not file_path.exists() or not file_path.is_file():
        # Try resolving relative to current working dir
        alt_path = Path.cwd() / application.resume_pdf
        if not alt_path.exists() or not alt_path.is_file():
            raise HTTPException(status_code=404, detail="Resume file not found on server")
        file_path = alt_path

    return FileResponse(path=str(file_path), media_type="application/pdf", filename=file_path.name)


