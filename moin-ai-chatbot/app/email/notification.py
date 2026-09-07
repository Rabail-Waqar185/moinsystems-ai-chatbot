"""
Lead notification email content (SRS 6.2). Every visitor-supplied field is
HTML-escaped before insertion (SRS 6.10) — a visitor typing HTML/script
into "project summary" or their name must not be able to break or inject
into the notification email your team reads.
"""
from datetime import datetime
from html import escape

from app.db.models import ChatMessage, LeadSubmission


def _row(label: str, value: str | None) -> str:
    if not value:
        return ""
    return f"<tr><td style='padding:4px 12px 4px 0;color:#666'><b>{escape(label)}</b></td><td>{escape(value)}</td></tr>"


def _build_conversation_summary(messages: list[ChatMessage]) -> str:
    """Simple, honest summary: the visitor's own messages in order, not an
    LLM-generated paraphrase — avoids the summary itself introducing an
    inaccuracy the team might act on."""
    user_lines = [m.content for m in messages if m.role == "user"]
    if not user_lines:
        return "(no prior messages)"
    return " | ".join(user_lines[-6:])  # last 6 visitor messages, bounded length


def build_lead_notification(lead: LeadSubmission, messages: list[ChatMessage]) -> tuple[str, str, str]:
    """Returns (subject, html_body, text_body)."""
    subject = f"New lead: {lead.full_name} — MoinSystems AI Chatbot"
    conversation_summary = _build_conversation_summary(messages)
    timestamp = (lead.created_at or datetime.utcnow()).strftime("%Y-%m-%d %H:%M UTC")

    rows = "".join([
        _row("Full name", lead.full_name),
        _row("Email", lead.email),
        _row("Contact number", lead.contact_number),
        _row("Company", lead.company_name),
        _row("Service interest", lead.service_interest),
        _row("Project summary", lead.project_summary),
        _row("Timeline", lead.timeline),
        _row("Budget range", lead.budget_range),
        _row("Source page", lead.source_page),
        _row("Timestamp", timestamp),
    ])

    html_body = f"""\
<html><body style="font-family:sans-serif">
<h2>New chatbot lead</h2>
<table>{rows}</table>
<h3>Conversation summary</h3>
<p>{escape(conversation_summary)}</p>
</body></html>"""

    text_lines = [
        f"New chatbot lead: {lead.full_name}",
        f"Email: {lead.email}",
        f"Contact number: {lead.contact_number}",
    ]
    if lead.company_name:
        text_lines.append(f"Company: {lead.company_name}")
    if lead.service_interest:
        text_lines.append(f"Service interest: {lead.service_interest}")
    if lead.project_summary:
        text_lines.append(f"Project summary: {lead.project_summary}")
    if lead.timeline:
        text_lines.append(f"Timeline: {lead.timeline}")
    if lead.budget_range:
        text_lines.append(f"Budget range: {lead.budget_range}")
    if lead.source_page:
        text_lines.append(f"Source page: {lead.source_page}")
    text_lines.append(f"Timestamp: {timestamp}")
    text_lines.append(f"Conversation summary: {conversation_summary}")
    text_body = "\n".join(text_lines)

    return subject, html_body, text_body
