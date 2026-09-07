"""
Email provider abstraction (SRS 6.1) — mirrors the ChatProvider pattern in
app/llm/base.py. Orchestration only ever talks to this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmailSendResult:
    success: bool
    provider_message_id: str | None
    error_message: str | None
    is_transient_failure: bool = False  # True = safe to retry, False = permanent (e.g. bad auth)


class EmailProvider(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, html_body: str, text_body: str) -> EmailSendResult:
        raise NotImplementedError
