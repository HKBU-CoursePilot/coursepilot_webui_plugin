"""
Chat endpoint with WebSocket support for streaming LLM responses.

This is the core P0 functionality - a simple chat interface that:
1. Accepts user messages via WebSocket
2. Forwards to LLM gateway
3. Streams response tokens back to client
"""

import os
import sys
import json
import asyncio
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from typing import Any
from dataclasses import dataclass, asdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from managers.llm_gateway_manager import LLMGatewayManager, Message
from managers.llm_gateway_manager.exceptions import LLMError
from utils.logger_util import Logger

router = APIRouter()
logger = Logger(name="CoursePilotAPI.chat")


# ============================================================================
# Models
# ============================================================================


class ChatMessage(BaseModel):
    """A chat message for the REST endpoint."""

    content: str
    role: str = "user"


class ChatRequest(BaseModel):
    """Request model for non-streaming chat."""

    messages: list[ChatMessage]
    course_id: str | None = None


class ChatResponse(BaseModel):
    """Response model for non-streaming chat."""

    content: str
    model: str | None = None
    usage: dict | None = None


@dataclass
class WSMessage:
    """WebSocket message structure."""

    type: str  # "message", "token", "complete", "error", "ping", "pong"
    content: str = ""
    metadata: dict | None = None
    timestamp: str | None = None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = asdict(self)
        data["timestamp"] = datetime.utcnow().isoformat()
        return json.dumps(data)


# ============================================================================
# Connection Manager
# ============================================================================


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.debug(f"Client {client_id} connected. Active: {len(self.active_connections)}")

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.debug(f"Client {client_id} disconnected. Active: {len(self.active_connections)}")

    async def send_message(self, client_id: str, message: WSMessage) -> None:
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message.to_json())


manager = ConnectionManager()


# ============================================================================
# System Prompt (P0 - Simple passthrough)
# ============================================================================

SYSTEM_PROMPT = """You are CoursePilot, an educational AI assistant for HKBU students.

Your role is to:
- Help students understand course material
- Answer questions about their coursework
- Provide explanations tailored to the student's level
- Be encouraging and supportive

Guidelines:
- Be concise but thorough
- Use examples when helpful
- If you don't know something, say so
- Encourage active learning over just giving answers

Current context: This is a P0 prototype. Just be helpful and conversational."""


# ============================================================================
# Routes
# ============================================================================


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """
    Non-streaming chat endpoint for simple request/response.

    Use WebSocket endpoint /api/chat/ws for streaming.

    Args:
        request: Chat request with message history

    Returns:
        LLM response
    """
    try:
        gateway = LLMGatewayManager()

        # Build messages with system prompt
        messages = [Message(role="system", content=SYSTEM_PROMPT)]
        for msg in request.messages:
            messages.append(Message(role=msg.role, content=msg.content))

        response = await gateway.complete(messages)

        return ChatResponse(
            content=response.content,
            model=response.model,
            usage=asdict(response.usage) if response.usage else None,
        )

    except LLMError as e:
        logger.error(f"LLM error: {e}")
        raise HTTPException(status_code=503, detail=f"LLM service error: {e}")
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.websocket("/chat/ws")
async def chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat.

    Protocol:
    - Client sends: {"type": "message", "content": "user message"}
    - Server sends: {"type": "token", "content": "..."} (multiple)
    - Server sends: {"type": "complete", "content": "full response"}

    The connection persists for multiple exchanges.
    """
    # Generate a client ID (in production, use auth token)
    import uuid

    client_id = str(uuid.uuid4())[:8]

    await manager.connect(websocket, client_id)

    # Conversation history for this session
    conversation: list[Message] = [Message(role="system", content=SYSTEM_PROMPT)]

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_message(
                    client_id,
                    WSMessage(type="error", content="Invalid JSON"),
                )
                continue

            msg_type = msg.get("type", "message")

            # Handle ping/pong for keepalive
            if msg_type == "ping":
                await manager.send_message(client_id, WSMessage(type="pong"))
                continue

            # Handle user message
            if msg_type == "message":
                user_content = msg.get("content", "").strip()
                if not user_content:
                    await manager.send_message(
                        client_id,
                        WSMessage(type="error", content="Empty message"),
                    )
                    continue

                # Add user message to conversation
                conversation.append(Message(role="user", content=user_content))
                logger.debug(f"Client {client_id}: {user_content[:50]}...")

                try:
                    gateway = LLMGatewayManager()
                    full_response = ""

                    # Stream response tokens
                    async for chunk in gateway.stream(conversation):
                        full_response += chunk.content
                        await manager.send_message(
                            client_id,
                            WSMessage(type="token", content=chunk.content),
                        )

                    # Add assistant response to conversation history
                    conversation.append(
                        Message(role="assistant", content=full_response)
                    )

                    # Send completion message
                    await manager.send_message(
                        client_id,
                        WSMessage(
                            type="complete",
                            content=full_response,
                            metadata={
                                "message_count": len(conversation),
                            },
                        ),
                    )

                except LLMError as e:
                    logger.error(f"LLM error for client {client_id}: {e}")
                    await manager.send_message(
                        client_id,
                        WSMessage(type="error", content=f"LLM error: {e}"),
                    )
                except Exception as e:
                    logger.error(f"Unexpected error for client {client_id}: {e}")
                    await manager.send_message(
                        client_id,
                        WSMessage(type="error", content="Internal error"),
                    )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)


@router.get("/chat/history")
async def get_chat_history():
    """
    Placeholder for chat history endpoint.

    In P1+, this will retrieve persisted conversation history.
    For P0, we don't persist history - it's session-only via WebSocket.
    """
    return {
        "message": "Chat history not implemented in P0",
        "note": "Conversation history is maintained per WebSocket session only",
    }
