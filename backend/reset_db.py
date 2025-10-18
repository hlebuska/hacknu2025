"""
Script to reset the database by dropping all tables and recreating them.
Run this script to apply schema changes to the production database.
"""
import asyncio
from sqlmodel import SQLModel
from app.db.session import engine
from app.models.vacancy import Vacancy
from app.models.application import Application
from app.models.user import User


async def reset_database():
    """Drop all tables and recreate them."""
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    print("Creating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    print("Database reset complete!")


if __name__ == "__main__":
    asyncio.run(reset_database())
