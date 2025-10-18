from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store clarifications per session
clarifications_store = {}

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("connected")
    
    # Generate session ID
    session_id = id(websocket)
    clarifications_store[session_id] = {
        "current_question_index": 0,
        "clarifications": [],
        "requirements": []
    }
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse JSON payload
                payload = json.loads(data)
                message = payload.get("message", "")
                history = payload.get("history", [])
                context = payload.get("context", None)
                
                # Log the conversation
                print(f"Received message: {message}")
                print(f"Session {session_id} clarifications: {clarifications_store[session_id]}")
                
                # Initialize requirements on first message
                if context and not clarifications_store[session_id]["requirements"]:
                    clarifications_store[session_id]["requirements"] = context.get('matching_sections', {}).get('requirements', [])
                
                session_data = clarifications_store[session_id]
                requirements = session_data["requirements"]
                current_index = session_data["current_question_index"]
                
                # Get unresolved requirements (match < 80%)
                unresolved = [req for req in requirements if req['match_percent'] < 80] if requirements else []
                
                # Store clarification if user provided an answer
                if len(history) > 0 and history[-1]["role"] == "user" and message.lower() != "initialize conversation with application context":
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
                        
                        print(f"Stored clarification for: {current_req['vacancy_req']}")
                        print(f"Moving to question {session_data['current_question_index']}")
                
                # Prepare system message based on context
                if context and requirements and unresolved:
                    if current_index < len(unresolved):
                        current_req = unresolved[current_index]
                        
                        # Check if this is right after storing an answer
                        just_answered = (len(history) > 0 and 
                                       history[-1]["role"] == "user" and 
                                       message.lower() != "initialize conversation with application context")
                        
                        if just_answered:
                            system_message = f"""You are an HR assistant. The user just answered a question. 
                            
Now ask about this next requirement:
- Requirement: {current_req['vacancy_req']}
- Current info: {current_req['user_req_data']}

Rules:
1. Start with a brief acknowledgment (max 5 words: "Got it." or "Thanks.")
2. Immediately ask the next question
3. Keep total response under 25 words
4. Be direct and professional
5. Don't mention percentages or scores

Example: "Got it. How many years of React experience do you have?"
"""
                        else:
                            system_message = f"""You are an HR assistant. Ask ONE short, specific question to clarify this requirement.

Applicant: {context.get('first_name')} {context.get('last_name')}

Focus on this requirement:
- Requirement: {current_req['vacancy_req']}
- Current info: {current_req['user_req_data']}

Rules:
1. Ask ONE specific question
2. Keep it under 20 words
3. Be direct and professional
4. Don't mention percentages
"""
                    else:
                        system_message = f"""You are an HR assistant wrapping up.

All requirements clarified. Thank the applicant briefly (under 15 words) and confirm their score will be updated.

Clarifications: {len(session_data['clarifications'])}
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
                print(f"Error: {error_message}")
                await websocket.send_text(error_message)
            
    except WebSocketDisconnect:
        print(f"Client disconnected. Clarifications: {clarifications_store.get(session_id, {})}")
        # Clean up session data
        if session_id in clarifications_store:
            del clarifications_store[session_id]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)