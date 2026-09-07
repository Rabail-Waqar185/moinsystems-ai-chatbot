"""
POST /api/v1/sessions (SRS 5.10) — creates a bare session, e.g. on widget
page-load, before the visitor has sent a first message.
"""
import secrets

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import ChatSession
from app.db.session import get_db
from app.schemas.session import SessionCreateRequest, SessionCreateResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionCreateResponse)
def create_session(
    request: SessionCreateRequest, db: Session = Depends(get_db)
) -> SessionCreateResponse:
    session = ChatSession(session_token=secrets.token_urlsafe(32), source_page=request.source_page)
    db.add(session)
    db.commit()
    return SessionCreateResponse(session_token=session.session_token)
