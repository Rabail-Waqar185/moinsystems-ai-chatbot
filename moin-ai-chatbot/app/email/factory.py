"""
Email provider factory (SRS 6.1). This is the one place that branches on
EMAIL_PROVIDER — app/email/service.py imports get_email_provider() from
here, never directly from smtp_provider.py or resend_provider.py, so
switching providers is a one-line .env change with no code touched.
"""
from app.core.config import get_settings
from app.email.base import EmailProvider

settings = get_settings()


def get_email_provider() -> EmailProvider:
    if settings.email_provider == "resend":
        from app.email.resend_provider import get_resend_provider

        return get_resend_provider()

    from app.email.smtp_provider import get_email_provider as get_smtp_provider

    return get_smtp_provider()