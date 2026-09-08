"""
Chat orchestration (SRS section 25 "Chat Message Flow" / 4.9 / 5.x).

Day 5 adds: intent classification, the deterministic lead-capture state
machine, and LeadSubmission persistence once required fields validate.
Email sending (Day 6) is intentionally NOT here yet — see
app/rag/prompt.py's TOOL_POLICY for what the LLM is currently allowed to
claim has happened.
"""
import logging
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chat.intent import LEAD_TRIGGERING_INTENTS, classify_intent
from app.chat.lead_capture import LeadState, maybe_start_lead_capture, process_turn
from app.core.config import get_settings
from app.db.models import ChatMessage, ChatSession, LeadSubmission
from app.email.service import send_lead_notification
from app.llm.base import ChatTurn
from app.llm.gemini_provider import get_chat_provider
from app.rag.prompt import build_system_prompt
from app.rag.retriever import apply_threshold, retrieve
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse

settings = get_settings()
logger = logging.getLogger(__name__)

MAX_HISTORY_TURNS = 8  # SRS 4.4: bounded recent context, not unlimited history


def _get_or_create_session(db: Session, request: ChatMessageRequest) -> ChatSession:
    if request.session_token:
        session = db.execute(
            select(ChatSession).where(ChatSession.session_token == request.session_token)
        ).scalar_one_or_none()
        if session is not None:
            return session
        logger.info("chat session token not found, issuing new session")

    session = ChatSession(
        session_token=secrets.token_urlsafe(32),
        source_page=request.source_page,
    )
    db.add(session)
    db.flush()  # populate session.id without a full commit yet
    return session


def _recent_history(db: Session, session: ChatSession) -> list[ChatTurn]:
    rows = db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(MAX_HISTORY_TURNS)
    ).scalars().all()
    rows = list(reversed(rows))
    return [ChatTurn(role=m.role, content=m.content) for m in rows if m.role in ("user", "assistant")]


def _finalize_lead(db: Session, session: ChatSession) -> bool:
    """Called exactly once, the turn lead_state reaches COMPLETE. Creates the
    real LeadSubmission row, then attempts the email notification (SRS 6)
    and returns whether it actually succeeded — this is the ONLY source of
    truth the LLM is allowed to base a "we've notified the team" claim on."""
    draft = session.lead_draft or {}
    lead = LeadSubmission(
        session_id=session.id,
        full_name=draft.get("full_name", ""),
        email=draft.get("email", ""),
        contact_number=draft.get("contact_number", ""),
        source_page=session.source_page,
        # Optional fields (company_name, project_summary, service_interest,
        # timeline, budget_range) aren't captured by this simple sequential
        # flow yet — SRS 5.8 says capture them "when naturally available",
        # which is a refinement, not a blocker.
    )
    db.add(lead)
    db.flush()  # need lead.id before the notification row references it
    logger.info(
        "lead captured",
        extra={"extra_fields": {"session_id": str(session.id)}},  # never log email/phone at INFO
    )

    notification = send_lead_notification(db, lead)
    return notification.status == "sent"


def handle_chat_message(db: Session, request: ChatMessageRequest) -> ChatMessageResponse:
    session = _get_or_create_session(db, request)

    # 1. Retrieval (unchanged from Day 4).
    ranked = retrieve(request.message)
    context_chunks = apply_threshold(ranked)

    # 2. Intent classification, then possibly start lead capture.
    intent = classify_intent(request.message, context_chunks)
    maybe_start_lead_capture(session, intent, LEAD_TRIGGERING_INTENTS)

    # 3. Let the state machine try to consume this message as a field answer.
    lead_result = process_turn(session, request.message)
    email_sent: bool | None = None
    if lead_result.completed:
        email_sent = _finalize_lead(db, session)

    logger.info(
        "chat turn",
        extra={"extra_fields": {
            "session_id": str(session.id),
            "intent": intent,
            "retrieved": len(ranked),
            "above_threshold": len(context_chunks),
            "lead_state": session.lead_state,
            "lead_field_consumed": lead_result.consumed,
        }},
    )

    # 4. Recent conversation for continuity, then the current turn appended.
    history = _recent_history(db, session)
    history.append(ChatTurn(role="user", content=request.message))

    # 5. Compose the layered prompt (now genuinely state-aware) and generate.
    system_prompt = build_system_prompt(
        context_chunks,
        intent=intent,
        lead_state=session.lead_state,
        validation_error=lead_result.validation_error,
        email_sent=email_sent,
    )
    provider = get_chat_provider()
    reply_text = provider.generate(system_prompt, history)

    # 6. Persist both turns.
    db.add(ChatMessage(session_id=session.id, role="user", content=request.message, intent=intent))
    db.add(ChatMessage(session_id=session.id, role="assistant", content=reply_text))
    db.commit()

    return ChatMessageResponse(
        session_token=session.session_token, reply=reply_text, intent=intent, lead_state=session.lead_state
    )