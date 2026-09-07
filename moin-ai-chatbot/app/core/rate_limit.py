"""
Per-IP rate limiting (SRS 6.7) via slowapi. Applied to the LLM-backed and
lead-capture endpoints specifically — health checks stay unlimited.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])
