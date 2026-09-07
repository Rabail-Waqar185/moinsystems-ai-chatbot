"""
POST /api/v1/chat/messages (SRS 4.9).
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.chat.service import handle_chat_message
from app.db.session import get_db
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/messages", response_model=ChatMessageResponse)
def post_chat_message(
    request: ChatMessageRequest, db: Session = Depends(get_db)
) -> ChatMessageResponse:
    try:
        return handle_chat_message(db, request)
    except RuntimeError as exc:
        # e.g. GEMINI_API_KEY missing — a config problem, not a client error.
        logger.error("chat generation config error: %s", exc)
        raise HTTPException(status_code=503, detail="Chat is temporarily unavailable.") from exc
    except Exception:
        logger.exception("chat generation failed")
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.") from None
