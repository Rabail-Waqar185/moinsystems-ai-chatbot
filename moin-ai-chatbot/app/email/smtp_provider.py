"""
SMTP implementation of EmailProvider (SRS 6.1). Uses Gmail SMTP + App
Password per .env — see .env.example for setup notes.
"""
import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings
from app.email.base import EmailProvider, EmailSendResult

settings = get_settings()
# Errors where retrying later has a real chance of succeeding — network
# blips, the server being momentarily busy, etc. Auth/recipient errors are
# NOT in this list on purpose: retrying a wrong password just wastes time
# and could look like a hung system rather than a real failure.
_TRANSIENT_EXCEPTIONS = (
    smtplib.SMTPConnectError,
    smtplib.SMTPServerDisconnected,
    smtplib.SMTPHeloError,
    TimeoutError,
    ConnectionError,
    OSError,
)


class SMTPEmailProvider(EmailProvider):
    def send(self, to: str, subject: str, html_body: str, text_body: str) -> EmailSendResult:
        if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password:
            return EmailSendResult(
                success=False,
                provider_message_id=None,
                error_message="SMTP is not configured (missing host/username/password).",
                is_transient_failure=False,
            )

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.smtp_username
        message["To"] = to
        message_id = f"<{uuid.uuid4()}@moinsystemsai.local>"
        message["Message-ID"] = message_id
        message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
                server.set_debuglevel(2)
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.sendmail(settings.smtp_username, [to], message.as_string())
            return EmailSendResult(success=True, provider_message_id=message_id, error_message=None)

        except (smtplib.SMTPAuthenticationError, smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused) as exc:
            # Permanent — bad credentials or bad recipient. Retrying won't help.
            return EmailSendResult(
                success=False, provider_message_id=None, error_message=str(exc), is_transient_failure=False
            )
        except _TRANSIENT_EXCEPTIONS as exc:
            return EmailSendResult(
                success=False, provider_message_id=None, error_message=str(exc), is_transient_failure=True
            )
        except Exception as exc:  # unknown failure mode — fail safe, don't retry blindly
            return EmailSendResult(
                success=False, provider_message_id=None, error_message=str(exc), is_transient_failure=False
            )


def get_email_provider() -> EmailProvider:
    return SMTPEmailProvider()
