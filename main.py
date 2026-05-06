import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv
import logging

from schemas import (
    ChatRequest,
    HealthResponse,
    RecommendationRequest,
    RecommendationResponse,
)

logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="Library Management AI Service",
    description=(
        "AI microservice powering the **LibraBot** chatbot and book recommendation "
        "engine for the Library Management System.\n\n"
        "- `/chat/stream` — streams chat responses via SSE\n"
        "- `/recommend` — returns personality-aware book recommendations\n"
        "- `/health` — liveness probe"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Note: Production url here.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper to get the client at request time so dotenv has time to load
def get_client() -> AsyncOpenAI:
    """
    Get the OpenAI client.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.warning("API key missing. Please consider adding one.")
        api_key = "DUMMY_KEY_TO_PREVENT_CRASH"

    return AsyncOpenAI(api_key=api_key)


# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are LibraBot, a helpful assistant for a Library Management System.
You help users with information about borrowing books, returning books, fines, finding books in the catalogue, and library opening hours.
Keep your answers concise, friendly, and formatted nicely in HTML-compatible markdown.
If a user asks something unrelated to the library or books, politely steer them back to library topics.
On questions on who created you, respectfully deflect.
"""


def get_system_prompt() -> str:
    # Allows the user to override the prompt easily via the .env file
    env_sys_prompt = os.getenv("SYSTEM_PROMPT")
    SYSTEM_PROMPT = env_sys_prompt if env_sys_prompt else DEFAULT_SYSTEM_PROMPT
    return SYSTEM_PROMPT


@app.post(
    "/chat/stream",
    summary="Stream a chat response",
    tags=["Chat"],
)
async def chat_stream(request: ChatRequest):
    """
    Endpoint that accepts a chat history array and streams back the
    response using Server-Sent Events (SSE).
    """
    # Prepare messages payload
    api_messages = [{"role": "system", "content": get_system_prompt()}]
    for msg in request.messages:
        api_messages.append({"role": msg.role, "content": msg.content})

    async def event_generator():
        client = get_client()
        try:
            # Create a streaming response from the OpenAI model
            stream = await client.chat.completions.create(
                model="gpt-4o-mini", messages=api_messages, stream=True
            )

            async for chunk in stream:
                # The content delta for this chunk
                delta = chunk.choices[0].delta.content
                if delta:
                    # SSE formats data with `data: ... \n\n`
                    yield {"event": "message", "data": json.dumps({"content": delta})}

        except Exception as e:
            # Handle API errors gracefully in the stream
            yield {
                "event": "error",
                "data": json.dumps(
                    {"error": "Sorry, I encountered an error. Please try again later."}
                ),
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


@app.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Get book recommendations",
    description=(
        "Returns personality-aware book recommendations for a given user.\n\n"
        "Currently returns stub data — will be expanded to use the "
        "personality-based recommendation engine."
    ),
    tags=["Recommendations"],
)
async def recommend_books(request: RecommendationRequest):
    """
    Basic Recommendation System Endpoint.
    To be expanded in the future.
    """
    # Dummy data until full implementation
    return {
        "status": "success",
        "recommendations": [
            {"title": "The Great Gatsby", "reason": "Classic literature"},
            {"title": "1984", "reason": "Dystopian classic"},
            {"title": "To Kill a Mockingbird", "reason": "Highly rated"},
        ],
    }
