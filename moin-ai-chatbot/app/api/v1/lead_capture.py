"""
POST /api/v1/lead-capture (SRS 5.9-5.10) — direct lead submission,
independent of the chat state machine (e.g. a standalone contact form
widget rather than the conversational flow in app/chat/service.py).
Reuses the exact same validation rules so both paths agree on what's valid.
"""
import logging
import secrets

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chat.validation import validate_contact_number, validate_email_field, validate_full_name
from app.db.models import ChatSession, LeadSubmission
from app.db.session import get_db
from app.email.service import send_lead_notification
from app.schemas.lead import LeadCaptureRequest, LeadCaptureResponse

router = APIRouter(prefix="/lead-capture", tags=["lead-capture"])
logger = logging.getLogger(__name__)


def _get_or_create_session(db: Session, request: LeadCaptureRequest) -> ChatSession:
    if request.session_token:
        session = db.execute(
            select(ChatSession).where(ChatSession.session_token == request.session_token)
        ).scalar_one_or_none()
        if session is not None:
            return session
    session = ChatSession(session_token=secrets.token_urlsafe(32), source_page=request.source_page)
    db.add(session)
    db.commit()  # commit immediately so the token is valid even if field validation fails below
    return session


@router.post("", response_model=LeadCaptureResponse)
def submit_lead(request: LeadCaptureRequest, db: Session = Depends(get_db)) -> LeadCaptureResponse:
    session = _get_or_create_session(db, request)

    errors: dict[str, str] = {}
    name_ok, name_err = validate_full_name(request.full_name)
    if not name_ok:
        errors["full_name"] = name_err

    email_ok, normalized_email, email_err = validate_email_field(request.email)
    if not email_ok:
        errors["email"] = email_err

    phone_ok, phone_err = validate_contact_number(request.contact_number)
    if not phone_ok:
        errors["contact_number"] = phone_err

    if errors:
        return LeadCaptureResponse(session_token=session.session_token, success=False, errors=errors)

    lead = LeadSubmission(
        session_id=session.id,
        full_name=request.full_name.strip(),
        email=normalized_email,
        contact_number=request.contact_number.strip(),
        company_name=request.company_name,
        project_summary=request.project_summary,
        service_interest=request.service_interest,
        timeline=request.timeline,
        budget_range=request.budget_range,
        source_page=request.source_page or session.source_page,
    )
    db.add(lead)
    db.flush()  # need lead.id before the notification row references it
    session.lead_state = "complete"
    db.commit()

    notification = send_lead_notification(db, lead)
    logger.info(
        "lead captured via direct endpoint",
        extra={"extra_fields": {"session_id": str(session.id), "email_status": notification.status}},
    )
    return LeadCaptureResponse(session_token=session.session_token, success=True, errors=None)