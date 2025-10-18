from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent))

# Import database session from your app
from app.db.session import async_session
from app.models.application import Application
from sqlmodel import select

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store clarifications per session
clarifications_store = {}

async def get_application_context(application_id: str) -> Optional[dict]:
    """Fetch application data from database"""
    try:
        print(f"📋 Fetching application: {application_id}")
        
        async with async_session() as session:
            result = await session.execute(
                select(Application).where(Application.id == application_id)
            )
            application = result.scalar_one_or_none()
            
            if application:
                print(f"✅ Application found: {application.first_name} {application.last_name}")
                print(f"   Score: {application.matching_score}%")
                print(f"   Requirements: {len(application.matching_sections.get('requirements', [])) if application.matching_sections else 0}")
                
                return {
                    "id": str(application.id),
                    "vacancy_id": str(application.vacancy_id),
                    "first_name": application.first_name,
                    "last_name": application.last_name,
                    "email": application.email,
                    "resume_pdf": application.resume_pdf,
                    "matching_score": application.matching_score,
                    "matching_sections": application.matching_sections,
                    "created_at": application.created_at.isoformat() if application.created_at else None,
                    "updated_at": application.updated_at.isoformat() if application.updated_at else None,
                }
            else:
                print(f"❌ No application found with ID: {application_id}")
                return None
    except Exception as e:
        print(f"❌ Error fetching application: {e}")
        import traceback
        traceback.print_exc()
        return None

async def update_application_clarifications(application_id: str, clarifications: list, new_score: int = None):
    """Update application with clarifications in database"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Application).where(Application.id == application_id)
            )
            application = result.scalar_one_or_none()
            
            if application:
                # Store clarifications in matching_sections
                if application.matching_sections:
                    application.matching_sections["clarifications"] = clarifications
                else:
                    application.matching_sections = {"clarifications": clarifications}
                
                if new_score:
                    application.matching_score = new_score
                
                session.add(application)
                await session.commit()
                
                print(f"✅ Updated application {application_id}")
                print(f"   Clarifications: {len(clarifications)}")
                if new_score:
                    print(f"   New score: {new_score}%")
            else:
                print(f"❌ Application not found for update: {application_id}")
    except Exception as e:
        print(f"❌ Error updating application: {e}")
        import traceback
        traceback.print_exc()

@app.websocket("/ws/chat/{application_id}")
async def websocket_endpoint(websocket: WebSocket, application_id: str):
    await websocket.accept()
    await websocket.send_text("connected")
    
    # Fetch application context from database
    context = await get_application_context(application_id)
    
    if not context:
        await websocket.send_text("Error: Application not found")
        await websocket.close()
        return
    
    # Generate session ID
    session_id = id(websocket)
    clarifications_store[session_id] = {
        "application_id": application_id,
        "current_question_index": 0,
        "clarifications": [],
        "requirements": context.get('matching_sections', {}).get('requirements', []),
        "context": context
    }
    
    # Send initial greeting
    initial_message = f"Hello {context['first_name']}! I'm here to help clarify your application. Your current matching score is {context['matching_score']}%. Let me ask you a few questions."
    await websocket.send_text(initial_message)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse JSON payload
                payload = json.loads(data)
                message = payload.get("message", "")
                history = payload.get("history", [])
                
                # Log the conversation
                print(f"💬 Received: {message}")
                
                session_data = clarifications_store[session_id]
                requirements = session_data["requirements"]
                current_index = session_data["current_question_index"]
                
                # Get unresolved requirements (match < 80%)
                unresolved = [req for req in requirements if req['match_percent'] < 80] if requirements else []
                
                # Store clarification if user provided an answer
                if len(history) > 0 and history[-1]["role"] == "user":
                    if current_index < len(unresolved):
                        current_req = unresolved[current_index]
                        session_data["clarifications"].append({
                            "requirement": current_req['vacancy_req'],
                            "original_data": current_req['user_req_data'],
                            "clarification": message,
                            "original_match": current_req['match_percent']
                        })
                        session_data["current_question_index"] += 1
                        current_index = session_data["current_question_index"]
                        
                        print(f"✅ Stored clarification {current_index}/{len(unresolved)}")
                
                # Prepare system message based on context
                if requirements and unresolved:
                    if current_index < len(unresolved):
                        current_req = unresolved[current_index]
                        
                        # Check if this is right after storing an answer
                        just_answered = (len(history) > 0 and history[-1]["role"] == "user")
                        
                        if just_answered and current_index > 0:
                            system_message = f"""You are an HR assistant. The user just answered a question. 
                            
Now ask about this next requirement:
- Requirement: {current_req['vacancy_req']}
- Current info: {current_req['user_req_data']}

Rules:
1. Start with "Got it." or "Thanks."
2. Immediately ask the next question
3. Keep total response under 25 words
4. Be direct and professional
5. Don't mention percentages

Example: "Got it. How many years of React experience do you have?"
"""
                        else:
                            system_message = f"""You are an HR assistant. Ask ONE short question to clarify this requirement.

Applicant: {context['first_name']} {context['last_name']}

Requirement to clarify:
- {current_req['vacancy_req']}
- Current data: {current_req['user_req_data']}
 
Rules:
1. Ask ONE specific question
2. Keep it under 20 words
3. Be direct and professional
4. Don't mention percentages
"""
                    else:
                        # All questions answered - save to database
                        await update_application_clarifications(
                            application_id, 
                            session_data["clarifications"]
                        )
                        
                        system_message = f"""You are an HR assistant wrapping up.

All {len(unresolved)} requirements have been clarified. 
Thank the applicant briefly (under 15 words) and let them know their application will be reviewed.

Clarifications collected: {len(session_data['clarifications'])}
"""
                else:
                    system_message = "You are a helpful assistant. Keep responses under 20 words."
                
                # Prepare messages for OpenAI
                messages = [
                    {"role": "system", "content": system_message}
                ]
                
                # Add only last 2 messages from history
                recent_history = history[-2:] if len(history) > 2 else history
                for msg in recent_history:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                
                # Call OpenAI API
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.5,
                    max_tokens=100
                )
                
                # Get the response text
                ai_response = response.choices[0].message.content
                
                # Send response back to client
                await websocket.send_text(ai_response)
                
            except json.JSONDecodeError:
                error_message = "Error: Invalid format"
                await websocket.send_text(error_message)
            except Exception as e:
                error_message = f"Error: {str(e)}"
                print(f"❌ Error: {error_message}")
                await websocket.send_text(error_message)
            
    except WebSocketDisconnect:
        # Save clarifications to database before closing
        if session_id in clarifications_store:
            session_data = clarifications_store[session_id]
            if session_data["clarifications"]:
                await update_application_clarifications(
                    application_id,
                    session_data["clarifications"]
                )
            del clarifications_store[session_id]
        
        print(f"👋 Client disconnected")

@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": "database"}

@app.get("/applications/{application_id}")
async def get_application(application_id: str):
    """Debug endpoint to see application data"""
    app_data = await get_application_context(application_id)
    if app_data:
        return app_data
    return {"error": "Application not found"}

if __name__ == "__main__":
    print("🚀 Starting WebSocket server...")
    print(f"   OpenAI: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
    print(f"   Database: {'✅' if os.getenv('DATABASE_URL') else '❌'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
