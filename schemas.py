"""
Pydantic schemas for the Library Management AI Service.

All request and response models used by the API endpoints are defined here.
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


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
class RecommendationRequest(BaseModel):
    """Payload for the book recommendation endpoint."""

    user_id: int = Field(
        ...,
        description="ID of the library user to generate recommendations for.",
        json_schema_extra={"examples": [42]},
    )
    history: List[str] = Field(
        default_factory=list,
        description="List of ISBNs the user has previously borrowed.",
        json_schema_extra={"examples": [["978-0-13-468599-1", "978-0-06-112008-4"]]},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 42,
                    "history": ["978-0-13-468599-1", "978-0-06-112008-4"],
                }
            ]
        }
    }


class Recommendation(BaseModel):
    """A single book recommendation."""

    title: str
    reason: str


class RecommendationResponse(BaseModel):
    """Book recommendation response."""

    status: str
    recommendations: List[Recommendation]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "success",
                    "recommendations": [
                        {"title": "The Great Gatsby", "reason": "Classic literature"},
                        {"title": "1984", "reason": "Dystopian classic"},
                        {
                            "title": "To Kill a Mockingbird",
                            "reason": "Highly rated",
                        },
                    ],
                }
            ]
        }
    }
