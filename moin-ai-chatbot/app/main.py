import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1 import chat, health, lead_capture, sessions
from app.core.config import get_settings
from app.core.logging import configure_logging, new_request_id, request_id_ctx
from app.core.rate_limit import limiter

settings = get_settings()
configure_logging()
logger = logging.getLogger("app.request")

app = FastAPI(
    title="MoinSystems AI Chatbot API",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429, content={"detail": "Too many requests. Please slow down and try again shortly."}
    )


app.add_middleware(SlowAPIMiddleware)

MAX_REQUEST_BODY_BYTES = 100_000  # 100KB — generous for chat/lead JSON, blocks abusive oversized payloads


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request body too large."})
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    token = request_id_ctx.set(new_request_id())
    start = time.monotonic()
    try:
        response = await call_next(request)
        return response
    finally:
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        logger.info(
            "request completed",
            extra={"extra_fields": {"path": request.url.path, "method": request.method, "latency_ms": latency_ms}},
        )
        request_id_ctx.reset(token)


app.include_router(health.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(lead_capture.router, prefix="/api/v1")

# Day 6+ routers (feedback, admin) are added here once their modules exist.
