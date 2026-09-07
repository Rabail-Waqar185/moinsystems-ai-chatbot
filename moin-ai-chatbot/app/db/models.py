"""
ORM models for the operational + RAG schema:
chat_session, chat_message, lead_submission, email_notification,
knowledge_document, knowledge_chunk.
"""
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class ChatSession(Base):
    __tablename__ = "chat_session"

    id: Mapped[uuid.UUID] = _uuid_pk()
    session_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    source_page: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")  # active | closed
    lead_state: Mapped[str] = mapped_column(String(32), default="not_active")
    lead_draft: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id: Mapped[uuid.UUID] = _uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_session.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant | system
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class LeadSubmission(Base):
    __tablename__ = "lead_submission"

    id: Mapped[uuid.UUID] = _uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_session.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    contact_number: Mapped[str] = mapped_column(String(64))
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_interest: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timeline: Mapped[str | None] = mapped_column(String(128), nullable=True)
    budget_range: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_page: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class EmailNotification(Base):
    __tablename__ = "email_notification"

    id: Mapped[uuid.UUID] = _uuid_pk()
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lead_submission.id"), index=True)
    recipient: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|sent|failed
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"

    id: Mapped[uuid.UUID] = _uuid_pk()
    source_name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(64))
    source_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(back_populates="document")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunk"

    id: Mapped[uuid.UUID] = _uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_document.id"), index=True)
    record_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)  # stable source id, for idempotent upserts
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dimensions))
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    intents: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="chunks")
