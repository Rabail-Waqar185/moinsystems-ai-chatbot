"""
Deterministic lead-capture state machine (SRS section 15-16 / 5.4).

Backend owns the state and the validated data; the LLM is only ever told
WHAT state we're in and asked to phrase the next question naturally (see
app/rag/prompt.py's Intent/State layer). This module never calls the LLM
and never talks to the DB directly — it mutates the ChatSession object
passed in; the caller (app/chat/service.py) is responsible for committing.
"""
from dataclasses import dataclass

from app.chat.validation import (
    looks_like_a_question,
    validate_contact_number,
    validate_email_field,
    validate_full_name,
)
from app.db.models import ChatSession


class LeadState:
    NOT_ACTIVE = "not_active"
    COLLECTING_NAME = "collecting_name"
    COLLECTING_EMAIL = "collecting_email"
    COLLECTING_PHONE = "collecting_phone"
    COMPLETE = "complete"


@dataclass
class LeadCaptureResult:
    consumed: bool  # True if this message was treated as an answer attempt (valid or not)
    validation_error: str | None
    new_state: str
    completed: bool  # True exactly on the turn required fields finish validating


def maybe_start_lead_capture(session: ChatSession, intent: str, lead_triggering_intents: set[str]) -> None:
    """Called once per turn before process_turn(). Starts the flow if an
    appropriate intent fires and nothing is already in progress."""
    if session.lead_state == LeadState.NOT_ACTIVE and intent in lead_triggering_intents:
        session.lead_state = LeadState.COLLECTING_NAME


def process_turn(session: ChatSession, message: str) -> LeadCaptureResult:
    state = session.lead_state
    if state in (LeadState.NOT_ACTIVE, LeadState.COMPLETE):
        return LeadCaptureResult(consumed=False, validation_error=None, new_state=state, completed=False)

    # SRS Day 5 checklist: "ask another question after lead capture begins →
    # preserve state correctly" — an unrelated question shouldn't be force-fit
    # into the current field or advance/reset state.
    if looks_like_a_question(message):
        return LeadCaptureResult(consumed=False, validation_error=None, new_state=state, completed=False)

    draft = dict(session.lead_draft or {})

    if state == LeadState.COLLECTING_NAME:
        ok, err = validate_full_name(message)
        if not ok:
            return LeadCaptureResult(consumed=True, validation_error=err, new_state=state, completed=False)
        draft["full_name"] = message.strip()
        session.lead_draft = draft
        session.lead_state = LeadState.COLLECTING_EMAIL
        return LeadCaptureResult(consumed=True, validation_error=None, new_state=LeadState.COLLECTING_EMAIL, completed=False)

    if state == LeadState.COLLECTING_EMAIL:
        ok, normalized, err = validate_email_field(message)
        if not ok:
            return LeadCaptureResult(consumed=True, validation_error=err, new_state=state, completed=False)
        draft["email"] = normalized
        session.lead_draft = draft
        session.lead_state = LeadState.COLLECTING_PHONE
        return LeadCaptureResult(consumed=True, validation_error=None, new_state=LeadState.COLLECTING_PHONE, completed=False)

    if state == LeadState.COLLECTING_PHONE:
        ok, err = validate_contact_number(message)
        if not ok:
            return LeadCaptureResult(consumed=True, validation_error=err, new_state=state, completed=False)
        draft["contact_number"] = message.strip()
        session.lead_draft = draft
        session.lead_state = LeadState.COMPLETE
        return LeadCaptureResult(consumed=True, validation_error=None, new_state=LeadState.COMPLETE, completed=True)

    # Unreachable given the states above, but fail safe rather than crash.
    return LeadCaptureResult(consumed=False, validation_error=None, new_state=state, completed=False)
