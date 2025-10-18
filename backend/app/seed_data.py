"""
Seed script to add sample job vacancies to the database
Run with: python -m app.seed_data
"""
import asyncio
from app.db.session import async_session, init_db
from app.models.vacancy import Vacancy

sample_vacancies = [
    {
        "title": "Senior Software Engineer",
        "description": "We are looking for an experienced software engineer to join our team and work on cutting-edge projects.",
        "company": "TechCorp",
        "location": "Almaty, Kazakhstan",
        "salary_min": 500000,
        "salary_max": 800000,
        "employment_type": "Full-time",
        "requirements": {
            "experience": "5+ years of experience in software development",
            "skills": ["Python", "JavaScript", "Java", "Cloud platforms (AWS, GCP, Azure)"],
            "education": "Bachelor's degree in Computer Science or related field",
            "other": ["Excellent problem-solving skills", "Team collaboration"]
        }
    },
    {
        "title": "Frontend Developer",
        "description": "Join our team to build beautiful and intuitive user interfaces for our web applications.",
        "company": "DesignHub",
        "location": "Astana, Kazakhstan",
        "salary_min": 300000,
        "salary_max": 500000,
        "employment_type": "Full-time",
        "requirements": {
            "experience": "3+ years of experience with React or Vue.js",
            "skills": ["HTML", "CSS", "JavaScript", "TypeScript", "Responsive design"],
            "education": "Bachelor's degree preferred",
            "other": ["Portfolio of previous work"]
        }
    },
    {
        "title": "Data Scientist",
        "description": "Help us make data-driven decisions by analyzing complex datasets and building ML models.",
        "company": "DataMinds",
        "location": "Remote",
        "salary_min": 600000,
        "salary_max": 1000000,
        "employment_type": "Full-time",
        "requirements": {
            "experience": "4+ years of experience in data science",
            "skills": ["Python", "scikit-learn", "TensorFlow", "PyTorch", "SQL", "Big data tools"],
            "education": "Master's or PhD in Computer Science, Statistics, or related field",
            "other": ["Strong statistical knowledge"]
        }
    },
    {
        "title": "Marketing Intern",
        "description": "Great opportunity for students to gain real-world marketing experience.",
        "company": "GrowthLab",
        "location": "Almaty, Kazakhstan",
        "salary_min": 100000,
        "salary_max": 150000,
        "employment_type": "Internship",
        "requirements": {
            "experience": "No prior experience required",
            "skills": ["Social media", "Digital marketing basics", "Communication"],
            "education": "Currently enrolled in Marketing, Business, or related program",
            "other": ["Creative mindset"]
        }
    },
    {
        "title": "DevOps Engineer",
        "description": "We need a DevOps engineer to streamline our deployment processes and maintain our infrastructure.",
        "company": "CloudSystems",
        "location": "Shymkent, Kazakhstan",
        "salary_min": 400000,
        "salary_max": 700000,
        "employment_type": "Full-time",
        "requirements": {
            "experience": "3+ years of DevOps experience",
            "skills": ["Docker", "Kubernetes", "CI/CD pipelines", "Bash", "Python"],
            "education": "Bachelor's degree in Computer Science or related field",
            "other": ["AWS or Azure certification preferred"]
        }
    }
]

async def seed_vacancies():
    """Add sample vacancies to the database"""
    print("Initializing database...")
    await init_db()
    
    print("Adding sample vacancies...")
    async with async_session() as session:
        for vacancy_data in sample_vacancies:
            vacancy = Vacancy(**vacancy_data)
            session.add(vacancy)
        
        await session.commit()
        print(f"✅ Added {len(sample_vacancies)} sample vacancies")

if __name__ == "__main__":
    asyncio.run(seed_vacancies())
