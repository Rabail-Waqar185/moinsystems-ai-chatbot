"""
Server-side lead field validation (SRS section 16's exact rules table).
Deliberately independent of the LLM — the backend is the source of truth
for whether a field is acceptable, never the model's judgment.
"""
import re

from email_validator import EmailNotValidError, validate_email as _validate_email_syntax

_PLACEHOLDER_NAMES = {"test", "asdf", "n/a", "na", "none", "xxx", "abc", "idk", "unknown"}
_MIN_PHONE_DIGITS = 7  # SRS 16: "validate basic presence and reasonable length", no assumed country format


def looks_like_a_question(text: str) -> bool:
    """Heuristic used by the state machine to tell 'answering the prompted
    field' apart from 'asking something else mid-capture' (milestone Day 5
    checklist: 'ask another question after lead capture begins → preserve
    state correctly')."""
    return "?" in text


def validate_full_name(value: str) -> tuple[bool, str | None]:
    """Returns (is_valid, error_message)."""
    cleaned = value.strip()
    if len(cleaned.replace(" ", "")) < 2:
        return False, "That doesn't look like a full name — could you share your name?"
    if cleaned.lower() in _PLACEHOLDER_NAMES:
        return False, "Could you share your actual name so our team can reach you?"
    if not re.search(r"[A-Za-z]", cleaned):
        return False, "Could you share your name using letters?"
    return True, None


def validate_email_field(value: str) -> tuple[bool, str | None, str | None]:
    """Returns (is_valid, normalized_email_or_None, error_message)."""
    try:
        result = _validate_email_syntax(value.strip(), check_deliverability=False)
        # SRS 16: "preserve exactly as entered after normalization" — use
        # the library's normalized form (fixes casing/unicode) but don't
        # alter what the visitor actually typed beyond that.
        return True, result.normalized, None
    except EmailNotValidError:
        return False, None, "That email address doesn't look valid — could you double-check it?"


def validate_contact_number(value: str) -> tuple[bool, str | None]:
    digits = re.sub(r"\D", "", value)
    if len(digits) < _MIN_PHONE_DIGITS:
        return False, "Could you share a valid phone number our team can reach you on?"
    return True, None
