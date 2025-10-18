import os
from fastapi import APIRouter, WebSocket, HTTPException, Depends, Body
from fastapi import status
from uuid import uuid4
from typing import Optional, Dict, Any, List

from app.services.ai_chat import AIChatService
from pydantic import BaseModel

from app.core import cache
from app.models.conversation import Conversation, ConversationMessage
from app.db.session import async_session
from sqlmodel import select


router = APIRouter(prefix="/chat")


class AnalyzeRequest(BaseModel):
    # Either pass the parsed JSONs directly or rely on files in cwd
    resume: Optional[Dict[str, Any]] = None
    vacancy: Optional[Dict[str, Any]] = None


@router.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest, use_retrieval: bool = False):
    svc = AIChatService()
    resume_data, vacancy_data = svc.load_data(req.resume, req.vacancy)
    if not resume_data or not vacancy_data:
        raise HTTPException(status_code=400, detail="resume or vacancy JSON not provided and files not found")

    # Toggle retrieval via environment variable for this call
    prev_val = os.environ.get("AI_USE_RETRIEVAL")
    if use_retrieval:
        os.environ["AI_USE_RETRIEVAL"] = "true"
    else:
        os.environ["AI_USE_RETRIEVAL"] = "false"

    differences = svc.analyze_differences(resume_data, vacancy_data)
    questions = svc.generate_interview_questions(differences, resume_data, vacancy_data)

    # restore previous env
    if prev_val is None:
        os.environ.pop("AI_USE_RETRIEVAL", None)
    else:
        os.environ["AI_USE_RETRIEVAL"] = prev_val

    return {"differences": differences, "questions": questions}


class CreateSessionResponse(BaseModel):
    session_id: str


class MessagePayload(BaseModel):
    text: str


class HistoryResponse(BaseModel):
    messages: List[Dict[str, Any]]


@router.post("/session", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(vacancy_id: Optional[str] = Body(None), resume_id: Optional[str] = Body(None)):
    """Create a short-lived chat session and return `session_id`."""
    session_id = str(uuid4())
    meta = {"vacancy_id": vacancy_id, "resume_id": resume_id}
    # Persist conversation in DB
    conversation = Conversation(session_id=session_id, vacancy_id=vacancy_id, resume_id=resume_id)
    async with async_session() as session:
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

    # Store conversation_id into redis meta for later reference
    meta["conversation_id"] = conversation.id
    await cache.create_session(session_id, meta=meta)
    return {"session_id": session_id}


@router.post("/{session_id}/message")
async def post_message(session_id: str, payload: MessagePayload):
    """Append a user message to session and generate assistant response.

    This endpoint enqueues the message, triggers local LLM processing synchronously
    (for now) and returns an acknowledgement. Assistant messages are published to
    Redis pub/sub so WebSocket clients can receive them.
    """
    # Validate session
    meta = await cache.get_session_meta(session_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Session not found")

    # Append user message
    user_msg = {"id": str(uuid4()), "role": "user", "text": payload.text}
    await cache.append_message(session_id, user_msg)

    # Persist user message to DB
    conv_id = meta.get("conversation_id")
    if conv_id:
        async with async_session() as session:
            cm = ConversationMessage(conversation_id=conv_id, role="user", text=payload.text)
            session.add(cm)
            await session.commit()
            await session.refresh(cm)

    # Build context from DB-resources via AIChatService
    svc = AIChatService()
    resume_data, vacancy_data = svc.load_data()  # svc will fallback to files if meta not set

    differences = svc.analyze_differences(resume_data or {}, vacancy_data or {})
    questions = svc.generate_interview_questions(differences, resume_data or {}, vacancy_data or {})

    assistant_msg = {"id": str(uuid4()), "role": "assistant", "text": questions}
    await cache.append_message(session_id, assistant_msg)
    await cache.publish_message(session_id, assistant_msg)

    # Persist assistant message to DB
    if conv_id:
        async with async_session() as session:
            cm2 = ConversationMessage(conversation_id=conv_id, role="assistant", text=questions)
            session.add(cm2)
            await session.commit()
            await session.refresh(cm2)

    return {"status": "ok", "message_id": assistant_msg["id"]}


@router.get("/{session_id}/messages", response_model=HistoryResponse)
async def get_history(session_id: str):
    meta = await cache.get_session_meta(session_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await cache.get_messages(session_id)
    return {"messages": messages}


@router.websocket("/ws")
async def chat_ws(ws: WebSocket, session_id: Optional[str] = None):
    """WebSocket endpoint that relays published messages for a session.

    Client should connect with query param `?session_id=...`
    """
    await ws.accept()
    # Extract session_id from query params if not provided
    if not session_id:
        params = dict(ws.query_params)
        session_id = params.get("session_id")

    if not session_id:
        await ws.send_text("missing session_id query param")
        await ws.close()
        return

    # Validate session
    meta = await cache.get_session_meta(session_id)
    if not meta:
        await ws.send_text("session not found")
        await ws.close()
        return

    # Subscribe to redis pubsub channel
    pubsub = await cache.subscribe(session_id)

    try:
        await ws.send_text("connected")

        async for message in pubsub.listen():
            # pubsub may yield dicts for subscribe/unsubscribe events; handle only messages
            if not message:
                continue
            t = message.get("type")
            if t != "message":
                continue
            data = message.get("data")
            # Forward to client
            await ws.send_text(data)
    except Exception:
        await ws.close()
    finally:
        try:
            await pubsub.unsubscribe()
        except Exception:
            pass
import os
from fastapi import APIRouter, WebSocket, HTTPException
from app.core.config import JWT_SECRET
import jwt

from app.services.ai_chat import AIChatService
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/chat")


class AnalyzeRequest(BaseModel):
    # Either pass the parsed JSONs directly or rely on files in cwd
    resume: Optional[Dict[str, Any]] = None
    vacancy: Optional[Dict[str, Any]] = None


@router.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest, use_retrieval: bool = False):
    svc = AIChatService()
    resume_data, vacancy_data = svc.load_data(req.resume, req.vacancy)
    if not resume_data or not vacancy_data:
        raise HTTPException(status_code=400, detail="resume or vacancy JSON not provided and files not found")

    # Toggle retrieval via environment variable for this call
    prev_val = os.environ.get("AI_USE_RETRIEVAL")
    if use_retrieval:
        os.environ["AI_USE_RETRIEVAL"] = "true"
    else:
        os.environ["AI_USE_RETRIEVAL"] = "false"

    differences = svc.analyze_differences(resume_data, vacancy_data)
    questions = svc.generate_interview_questions(differences, resume_data, vacancy_data)

    # restore previous env
    if prev_val is None:
        os.environ.pop("AI_USE_RETRIEVAL", None)
    else:
        os.environ["AI_USE_RETRIEVAL"] = prev_val

    return {"differences": differences, "questions": questions}


@router.websocket("/ws")
async def chat_ws(ws: WebSocket):
    await ws.accept()
    await ws.send_text("connected")
    try:
        while True:
            msg = await ws.receive_text()
            await ws.send_text(f"echo: {msg}")
    except Exception:
        await ws.close()
