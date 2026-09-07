"""
Lightweight intent classification (SRS 5.3). Deliberately keyword-based,
not an LLM call — SRS calls for "lightweight" routing, and a deterministic
classifier means lead-capture triggering never depends on the LLM's mood
that turn. Categories map directly onto the SRS state diagram (section 15).
"""
import re

from app.rag.retriever import RetrievedChunk

# Ordered so more specific/higher-commitment intents are checked first —
# a message can plausibly contain both service and pricing language
# ("what does a chatbot cost"), and pricing should win that tie.
_BUYING_INTENT_PATTERNS = [
    r"\bhire\b", r"\bwork with you\b", r"\bget started\b", r"\bsign\s?up\b",
    r"\bstart(ing)? a project\b", r"\bcontact me\b", r"\breach out\b",
    r"\bwant to build\b", r"\bready to (start|move forward|proceed)\b",
    r"\bnext steps?\b", r"\bsend (my|us) (details|information)\b",
]
_PRICING_PATTERNS = [
    r"\bprice\b", r"\bpricing\b", r"\bcost\b", r"\bhow much\b",
    r"\bquote\b", r"\bbudget\b", r"\brates?\b",
]
_SERVICE_PATTERNS = [
    r"\bbuild\b", r"\bdevelop\b", r"\bcreate\b", r"\bcan you\b", r"\bdo you (offer|provide|do)\b",
]


def _matches_any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text) for p in patterns)


def classify_intent(message: str, retrieved: list[RetrievedChunk]) -> str:
    """Returns one of: buying_intent, pricing_quote, service_inquiry,
    general_query, unknown. `retrieved` should be the ABOVE-THRESHOLD
    results — an empty list here means retrieval found nothing adequate,
    which is its own signal regardless of keyword matches."""
    text = message.lower().strip()

    if _matches_any(_BUYING_INTENT_PATTERNS, text):
        return "buying_intent"
    if _matches_any(_PRICING_PATTERNS, text):
        return "pricing_quote"
    if not retrieved:
        return "unknown"
    if _matches_any(_SERVICE_PATTERNS, text):
        return "service_inquiry"
    return "general_query"


# Intents that should trigger starting lead capture, if it isn't already active.
LEAD_TRIGGERING_INTENTS = {"pricing_quote", "buying_intent"}
