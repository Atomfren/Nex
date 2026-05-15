"""AI Chat API endpoints (WebSocket)."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional

from loguru import logger
from backend.services.ai_assistant import LocalAssistant

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class AIChatMessage(BaseModel):
    """Сообщение в AI чате."""
    text: str
    role: str = "user"  # "user" | "assistant"


class AIChatResponse(BaseModel):
    """Ответ AI."""
    text: str
    confidence: float = 1.0
    source: str = "local"


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ai/chat")
async def ai_chat(websocket: WebSocket):
    """WebSocket endpoint для AI чата с streaming."""
    await websocket.accept()
    assistant = LocalAssistant()
    
    if not assistant.is_available:
        await websocket.send_json({
            "error": "AI model not found. Place a .gguf model file in the data directory.",
            "text": "AI модель не найдена."
        })
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("text", "")

            if not message:
                continue

            # Стриминг ответа
            full_text = ""
            async for token in assistant.ask_stream(message):
                full_text += token
                await websocket.send_json({
                    "token": token,
                    "partial": full_text,
                    "source": "local"
                })

            # Финальное сообщение
            await websocket.send_json({
                "text": full_text,
                "confidence": 1.0,
                "source": "local",
                "done": True
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"ai_chat error: {e}")
        await websocket.send_json({
            "error": str(e),
            "text": "Произошла ошибка"
        })


# ============================================================================
# REST Endpoint (без streaming)
# ============================================================================

@router.post("/ai/chat", response_model=AIChatResponse)
async def ai_chat_rest(message: AIChatMessage):
    """REST endpoint для простого вопроса AI (без streaming)."""
    assistant = LocalAssistant()
    if not assistant.is_available:
        return AIChatResponse(
            text="AI модель не найдена. Поместите .gguf файл в папку data.",
            confidence=0.0,
            source="local"
        )
    try:
        response = assistant.ask(message.text)
        return AIChatResponse(text=response, confidence=1.0, source="local")
    except Exception as e:
        logger.error(f"ai_chat_rest error: {e}")
        return AIChatResponse(text=f"Ошибка: {e}", confidence=0.0, source="local")
