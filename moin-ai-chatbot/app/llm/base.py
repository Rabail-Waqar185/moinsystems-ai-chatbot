"""
LLM provider abstraction (SRS 4.1 / section 24-25).

The orchestration layer (app/chat/service.py) only ever talks to this
interface, never to a vendor SDK directly — so LLM_PROVIDER can change in
config without touching orchestration, prompt building, or the API layer.
Currently only "gemini" is implemented; the Literal in config.py is where
a future provider would be added.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatTurn:
    role: str  # "user" | "assistant"
    content: str


class ChatProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, history: list[ChatTurn]) -> str:
        """system_prompt: the fully-assembled layered prompt (see app/rag/prompt.py).
        history: prior turns plus the current user message as the last item,
        in chronological order. Returns the assistant's reply text."""
        raise NotImplementedError
