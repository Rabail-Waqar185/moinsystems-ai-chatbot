"""
Email orchestration (SRS 6.4-6.6). Sends the lead notification with
bounded retry for transient failures only, and ALWAYS persists an
EmailNotification row — success or failure — so delivery status is never
just "whatever the LLM assumed happened."
"""
import logging
import time
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ChatMessage, EmailNotification, LeadSubmission
from app.email.base import EmailProvider, EmailSendResult
from app.email.notification import build_lead_notification
from app.email.smtp_provider import get_email_provider

settings = get_settings()
logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3  # SRS 6.6: bounded, never open-ended — avoids uncontrolled duplicate sends
_BACKOFF_SECONDS = [1, 2]  # wait before attempt 2 and attempt 3


def _send_with_bounded_retry(provider: EmailProvider, to: str, subject: str, html_body: str, text_body: str) -> EmailSendResult:
    result: EmailSendResult | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = provider.send(to, subject, html_body, text_body)
        if result.success or not result.is_transient_failure:
            return result  # success, or a permanent failure not worth retrying
        logger.warning(
            "email send transient failure, attempt %d/%d: %s", attempt, MAX_ATTEMPTS, result.error_message
        )
        if attempt < MAX_ATTEMPTS:
            time.sleep(_BACKOFF_SECONDS[attempt - 1])
    return result


def send_lead_notification(db: Session, lead: LeadSubmission) -> EmailNotification:
    """Sends the notification for a just-completed lead and persists the
    delivery outcome. Returns the EmailNotification row — check .status."""
    messages = db.execute(
        select(ChatMessage).where(ChatMessage.session_id == lead.session_id).order_by(ChatMessage.created_at)
    ).scalars().all()

    subject, html_body, text_body = build_lead_notification(lead, list(messages))
    provider = get_email_provider()
    result = _send_with_bounded_retry(provider, settings.lead_email_to, subject, html_body, text_body)

    notification = EmailNotification(
        lead_id=lead.id,
        recipient=settings.lead_email_to,
        subject=subject,
        status="sent" if result.success else "failed",
        provider_message_id=result.provider_message_id,
        sent_at=datetime.utcnow() if result.success else None,
        error_message=result.error_message,
    )
    db.add(notification)
    db.commit()

    logger.info(
        "email notification %s",
        notification.status,
        extra={"extra_fields": {"lead_id": str(lead.id), "status": notification.status}},
    )
    return notification
