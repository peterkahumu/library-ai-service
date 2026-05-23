"""
AI Service — LibraBot Chat Backend.

Handles streaming chat responses via Server-Sent Events (SSE).
The recommendation engine has its own dedicated microservice
(recommendation_service) and is not part of this service.
"""

import os
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

from schemas import ChatRequest, HealthResponse

load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # No DB connection needed — chat is stateless.
    yield


app = FastAPI(
    title="Library Management AI Service",
    description=(
        "AI microservice powering the **LibraBot** chatbot.\n\n"
        "- `/chat/stream` — streams chat responses via SSE\n"
        "- `/health` — liveness probe"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to Django origin in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client() -> AsyncOpenAI:
    """Instantiate the OpenAI async client, using the key from env."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY is missing. Requests will fail.")
        api_key = "DUMMY_KEY_TO_PREVENT_CRASH"
    return AsyncOpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

DEFAULT_SYSTEM_PROMPT = (
    "You are LibraBot, a helpful assistant for a Library Management System. "
    "You help users with information about borrowing books, returning books, "
    "fines, finding books in the catalogue, and library opening hours. "
    "Keep your answers concise, friendly, and formatted nicely in HTML-compatible markdown. "
    "If a user asks something unrelated to the library or books, politely steer them back to library topics. "
    "On questions about who created you, respectfully deflect."
)


def get_system_prompt() -> str:
    """Return the active system prompt (env override or default)."""
    return os.getenv("SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post(
    "/chat/stream",
    summary="Stream a chat response",
    tags=["Chat"],
)
async def chat_stream(request: ChatRequest):
    """
    Accepts a chat history array and streams back the assistant response
    using Server-Sent Events (SSE).
    """
    api_messages = [{"role": "system", "content": get_system_prompt()}]
    for msg in request.messages:
        api_messages.append({"role": msg.role, "content": msg.content})

    async def event_generator():
        client = get_client()
        try:
            stream = await client.chat.completions.create(
                model="gpt-4o-mini", messages=api_messages, stream=True
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield {"event": "message", "data": json.dumps({"content": delta})}
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": "Sorry, I encountered an error. Please try again later."}),
            }
        finally:
            yield {"event": "done", "data": json.dumps({"done": True})}

    return EventSourceResponse(event_generator())


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Liveness probe. Returns `healthy` when the service is running.",
    tags=["Ops"],
)
def health_check():
    return {"status": "healthy"}
