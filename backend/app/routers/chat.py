from fastapi import APIRouter, WebSocket
from app.core.config import JWT_SECRET
import jwt

router = APIRouter(prefix="/chat")

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
