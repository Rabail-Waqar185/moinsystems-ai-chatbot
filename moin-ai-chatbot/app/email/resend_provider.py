"""
Resend implementation of EmailProvider (SRS 6.1). Uses Resend's REST API
directly via httpx (already a dependency) rather than adding their SDK as
a new package. Chosen as the pragmatic fallback after Gmail SMTP proved
unreliable in testing (flaky account-level throttling unrelated to our
code — see Day 8 troubleshooting) — an API key has none of App Passwords'
2FA/account-flagging fragility.
"""
import httpx

from app.core.config import get_settings
from app.email.base import EmailProvider, EmailSendResult

settings = get_settings()

RESEND_API_URL = "https://api.resend.com/emails"

# Resend's own outage/rate-limit responses are worth retrying; a bad API
# key or bad request is not.
_TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}


class ResendEmailProvider(EmailProvider):
    def send(self, to: str, subject: str, html_body: str, text_body: str) -> EmailSendResult:
        if not settings.resend_api_key:
            return EmailSendResult(
                success=False,
                provider_message_id=None,
                error_message="RESEND_API_KEY is not set.",
                is_transient_failure=False,
            )

        payload = {
            "from": settings.resend_from_email,
            "to": [to],
            "subject": subject,
            "html": html_body,
            "text": text_body,
        }
        headers = {"Authorization": f"Bearer {settings.resend_api_key}"}

        try:
            response = httpx.post(RESEND_API_URL, json=payload, headers=headers, timeout=15)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            return EmailSendResult(
                success=False, provider_message_id=None, error_message=str(exc), is_transient_failure=True
            )

        if response.status_code == 200:
            data = response.json()
            return EmailSendResult(success=True, provider_message_id=data.get("id"), error_message=None)

        is_transient = response.status_code in _TRANSIENT_STATUS_CODES
        return EmailSendResult(
            success=False,
            provider_message_id=None,
            error_message=f"Resend API {response.status_code}: {response.text}",
            is_transient_failure=is_transient,
        )


def get_resend_provider() -> EmailProvider:
    return ResendEmailProvider()