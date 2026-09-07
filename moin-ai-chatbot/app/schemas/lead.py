"""
Schemas for POST /api/v1/lead-capture (SRS 5.10) — direct lead submission,
independent of the chat state machine (e.g. a standalone contact form).
"""
from pydantic import BaseModel, Field


class LeadCaptureRequest(BaseModel):
    session_token: str | None = Field(default=None, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=254)  # 254 = RFC 5321 max
    contact_number: str = Field(..., min_length=1, max_length=32)
    company_name: str | None = Field(default=None, max_length=200)
    project_summary: str | None = Field(default=None, max_length=2000)
    service_interest: str | None = Field(default=None, max_length=200)
    timeline: str | None = Field(default=None, max_length=100)
    budget_range: str | None = Field(default=None, max_length=100)
    source_page: str | None = Field(default=None, max_length=512)


class LeadCaptureResponse(BaseModel):
    session_token: str
    success: bool
    errors: dict[str, str] | None = None
