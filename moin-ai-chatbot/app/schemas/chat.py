"""
Request/response models for POST /api/v1/chat/messages (SRS 4.9).
"""
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_token: str | None = Field(
        default=None,
        description="Omit on the visitor's first message; the server issues one and the "
        "client must send it back on every following message for conversation continuity.",
    )
    source_page: str | None = Field(default=None, max_length=512)


class ChatMessageResponse(BaseModel):
    session_token: str
    reply: str
    intent: str | None = None
    lead_state: str | None = None
