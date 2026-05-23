"""
Pydantic schemas for the Library Management AI Service.

Only chat-related models live here. Recommendation schemas have been
removed — the recommendation engine is a separate microservice.
"""

from typing import List
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class Message(BaseModel):
    """A single chat message."""

    role: str = Field(
        ...,
        description="The role of the message author.",
        json_schema_extra={"examples": ["user"]},
    )
    content: str = Field(
        ...,
        description="The text content of the message.",
        json_schema_extra={"examples": ["How do I borrow a book?"]},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"role": "user", "content": "How do I borrow a book?"}]
        }
    }


class ChatRequest(BaseModel):
    """Payload for the chat streaming endpoint."""

    messages: List[Message] = Field(
        ...,
        description="Ordered conversation history sent to the model.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "messages": [
                        {"role": "user", "content": "How do I borrow a book?"},
                    ]
                },
                {
                    "messages": [
                        {"role": "user", "content": "What are the library opening hours?"},
                        {"role": "assistant", "content": "We are open Mon–Fri 8 AM – 8 PM."},
                        {"role": "user", "content": "Are you open on weekends?"},
                    ]
                },
            ]
        }
    }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service status.")

    model_config = {
        "json_schema_extra": {"examples": [{"status": "healthy"}]}
    }
