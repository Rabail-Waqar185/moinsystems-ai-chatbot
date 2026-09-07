"""
Gemini implementation of ChatProvider (SRS 4.1).
"""
from google import genai
from google.genai import types

from app.core.config import get_settings
from app.llm.base import ChatProvider, ChatTurn

settings = get_settings()

# Gemini uses "model" instead of "assistant" for the AI turn role.
_ROLE_MAP = {"user": "user", "assistant": "model"}


class GeminiChatProvider(ChatProvider):
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. The chat endpoint requires a Gemini API key "
                "(https://aistudio.google.com/apikey)."
            )
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def generate(self, system_prompt: str, history: list[ChatTurn]) -> str:
        contents = [
            types.Content(role=_ROLE_MAP[turn.role], parts=[types.Part(text=turn.content)])
            for turn in history
        ]
        response = self._client.models.generate_content(
            model=settings.gemini_chat_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3,  # low temperature: grounded/factual support answers, not creative
                max_output_tokens=1024,
            ),
        )
        return (response.text or "").strip()


def get_chat_provider() -> ChatProvider:
    """Factory — this is the one place that would branch on
    settings.llm_provider if a second provider is ever added."""
    return GeminiChatProvider()
