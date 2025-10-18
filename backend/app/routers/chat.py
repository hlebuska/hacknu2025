from fastapi import APIRouter, WebSocket, HTTPException, Query
from sqlmodel import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.db.session import async_session
from app.models.conversation import (
    Conversation, ConversationMessage, ConversationCreate, 
    ConversationRead, MessageCreate, MessageRead
)
from app.services.chatbot_service import ChatbotService
from app.models.application import Application
from app.models.vacancy import Vacancy
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Initialize chatbot service
chatbot_service = ChatbotService()


@router.post("/conversations", response_model=ConversationRead)
async def create_conversation(data: ConversationCreate):
    """Create a new conversation"""
    async with async_session() as session:
        conversation = Conversation(**data.dict())
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        return conversation


@router.get("/conversations/{session_id}", response_model=List[ConversationRead])
async def get_conversations(session_id: str):
    """Get all conversations for a session"""
    async with async_session() as session:
        result = await session.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        conversations = result.scalars().all()
        return conversations


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageRead])
async def get_conversation_messages(conversation_id: str):
    """Get all messages in a conversation"""
    async with async_session() as session:
        result = await session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(desc(ConversationMessage.created_at))
        )
        messages = result.scalars().all()
        return messages


@router.post("/conversations/{conversation_id}/messages", response_model=MessageRead)
async def add_message(
    conversation_id: str,
    message: MessageCreate
):
    """Add a message to a conversation"""
    async with async_session() as session:
        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=message.role,
            content=message.content
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return msg


@router.post("/analyze-resume-vacancy")
async def analyze_resume_vacancy(
    resume_data: dict,
    vacancy_data: dict
):
    """Analyze differences between resume and vacancy"""
    try:
        analysis = chatbot_service.analyze_resume_vacancy_differences(
            resume_data, vacancy_data
        )
        return {
            "success": True,
            "data": analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing resume-vacancy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-questions")
async def generate_interview_questions(
    resume_data: dict,
    vacancy_data: dict,
    differences: Optional[List[dict]] = None
):
    """Generate interview questions based on differences"""
    try:
        if differences is None:
            analysis = chatbot_service.analyze_resume_vacancy_differences(
                resume_data, vacancy_data
            )
            differences = analysis['differences']
        
        questions = chatbot_service.generate_interview_questions(
            resume_data, vacancy_data, differences if differences else []
        )
        return {
            "success": True,
            "questions": questions
        }
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_message(
    message: str = Query(...),
    conversation_id: Optional[str] = Query(None),
    application_id: Optional[str] = Query(None),
    vacancy_id: Optional[str] = Query(None)
):
    """Send a chat message and get a response with optional resume/vacancy context"""
    try:
        async with async_session() as session:
            # Load context if provided
            resume_data = None
            vacancy_data = None
            
            if application_id:
                application = await session.get(Application, application_id)
                if application and application.resume_parsed:
                    resume_data = application.resume_parsed
            
            if vacancy_id:
                vacancy = await session.get(Vacancy, vacancy_id)
                if vacancy:
                    # Convert vacancy to dict
                    vacancy_data = {
                        'job_title': getattr(vacancy, 'title', ''),
                        'description': getattr(vacancy, 'description', ''),
                        'requirements': getattr(vacancy, 'requirements', [])
                    }
            
            # Get conversation history if provided
            conversation_history = []
            if conversation_id:
                result = await session.execute(
                    select(ConversationMessage)
                    .where(ConversationMessage.conversation_id == conversation_id)
                    .order_by(desc(ConversationMessage.created_at))
                )
                messages = result.scalars().all()[-10:]  # Last 10 messages for context
                conversation_history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ]
            
            # Generate response
            response = chatbot_service.chat_with_context(
                message, resume_data, vacancy_data, conversation_history
            )
            
            # Save messages to DB if conversation_id provided
            if conversation_id:
                user_msg = ConversationMessage(
                    conversation_id=conversation_id,
                    role="user",
                    content=message
                )
                assistant_msg = ConversationMessage(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response
                )
                session.add(user_msg)
                session.add(assistant_msg)
                await session.commit()
            
            return {
                "success": True,
                "response": response
            }
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-knowledge-base")
async def query_knowledge_base(query: str = Query(...)):
    """Query the vector database knowledge base"""
    try:
        result = chatbot_service.query_knowledge_base(query)
        return result
    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    conversation_id = None
    
    try:
        # Receive initial message to set up conversation
        initial_data = await websocket.receive_json()
        conversation_id = initial_data.get("conversation_id")
        
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to chatbot",
            "session_id": session_id,
            "conversation_id": conversation_id
        })
        
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "")
            application_id = data.get("application_id")
            vacancy_id = data.get("vacancy_id")
            
            if not user_message:
                continue
            
            async with async_session() as session:
                # Load context
                resume_data = None
                vacancy_data = None
                
                if application_id:
                    application = await session.get(Application, application_id)
                    if application and application.resume_parsed:
                        resume_data = application.resume_parsed
                
                if vacancy_id:
                    vacancy = await session.get(Vacancy, vacancy_id)
                    if vacancy:
                        vacancy_data = {
                            'job_title': getattr(vacancy, 'title', ''),
                            'description': getattr(vacancy, 'description', ''),
                        }
                
                # Get conversation history
                conversation_history = []
                if conversation_id:
                    result = await session.execute(
                        select(ConversationMessage)
                        .where(ConversationMessage.conversation_id == conversation_id)
                        .order_by(desc(ConversationMessage.created_at))
                    )
                    messages = result.scalars().all()[-10:]
                    conversation_history = [
                        {"role": msg.role, "content": msg.content}
                        for msg in messages
                    ]
                
                # Generate response
                response = chatbot_service.chat_with_context(
                    user_message, resume_data, vacancy_data, conversation_history
                )
                
                # Save to DB
                if conversation_id:
                    user_msg = ConversationMessage(
                        conversation_id=conversation_id,
                        role="user",
                        content=user_message
                    )
                    assistant_msg = ConversationMessage(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=response
                    )
                    session.add(user_msg)
                    session.add(assistant_msg)
                    await session.commit()
                
                # Send response
                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": response
                })
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()
