"""
Script to view vacancies in the database
"""
import asyncio
import json
from app.db.session import async_session
from app.models.vacancy import Vacancy
from sqlmodel import select

async def view_vacancies():
    """View all vacancies in the database"""
    async with async_session() as session:
        result = await session.execute(select(Vacancy))
        vacancies = result.scalars().all()
        
        print(f"\n{'='*80}")
        print(f"TOTAL VACANCIES IN DATABASE: {len(vacancies)}")
        print(f"{'='*80}\n")
        
        for i, vacancy in enumerate(vacancies, 1):
            print(f"[{i}] {vacancy.title}")
            print(f"    Company: {vacancy.company}")
            print(f"    Salary: {vacancy.salary_min:,} - {vacancy.salary_max:,} KZT")
            print(f"    Type: {vacancy.employment_type}")
            print(f"    ID: {vacancy.id}")
            print(f"    Description: {vacancy.description[:80]}...")
            print(f"    Requirements (JSON):")
            print(f"      {json.dumps(vacancy.requirements, indent=6)}")
            print(f"    Created: {vacancy.created_at}")
            print(f"{'-'*80}\n")

if __name__ == "__main__":
    asyncio.run(view_vacancies())
