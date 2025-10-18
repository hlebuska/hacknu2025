from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select, col
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.models.vacancy import Vacancy, VacancyCreate, VacancyRead
from app.db.session import async_session

router = APIRouter(prefix="/api/vacancies", tags=["Vacancies"])

async def get_session():
    """Dependency for database session"""
    async with async_session() as session:
        yield session

@router.get("", response_model=List[VacancyRead])
async def get_vacancies(
    skip: int = 0,
    limit: int = 100,
    location: Optional[str] = None,
    employment_type: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Get list of job vacancies with optional filters
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **location**: Filter by location
    - **employment_type**: Filter by employment type (Full-time, Part-time, etc.)
    """
    query = select(Vacancy)
    
    if location:
        query = query.where(col(Vacancy.location).ilike(f"%{location}%"))
    
    if employment_type:
        query = query.where(Vacancy.employment_type == employment_type)
    
    query = query.offset(skip).limit(limit)
    
    result = await session.execute(query)
    vacancies = result.scalars().all()
    
    return vacancies

@router.get("/{vacancy_id}", response_model=VacancyRead)
async def get_vacancy(
    vacancy_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get details of a specific job vacancy
    
    - **vacancy_id**: ID of the vacancy
    """
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    return vacancy

@router.post("", response_model=VacancyRead, status_code=201)
async def create_vacancy(
    vacancy_data: VacancyCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new job vacancy (admin only - authentication to be added)
    
    - **vacancy_data**: Vacancy information
    """
    vacancy = Vacancy(**vacancy_data.model_dump())
    
    session.add(vacancy)
    await session.commit()
    await session.refresh(vacancy)
    
    return vacancy

@router.put("/{vacancy_id}", response_model=VacancyRead)
async def update_vacancy(
    vacancy_id: str,
    vacancy_data: VacancyCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Update an existing vacancy (admin only - authentication to be added)
    
    - **vacancy_id**: ID of the vacancy to update
    - **vacancy_data**: Updated vacancy information
    """
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    # Update fields
    for key, value in vacancy_data.model_dump().items():
        setattr(vacancy, key, value)
    
    from datetime import datetime, timezone
    vacancy.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    await session.refresh(vacancy)
    
    return vacancy

@router.delete("/{vacancy_id}")
async def delete_vacancy(
    vacancy_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a vacancy (admin only - authentication to be added)
    
    - **vacancy_id**: ID of the vacancy to delete
    """
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    # Hard delete
    await session.delete(vacancy)
    await session.commit()
    
    return {"message": "Vacancy deleted successfully", "id": vacancy_id}
