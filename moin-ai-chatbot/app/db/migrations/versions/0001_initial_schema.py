"""initial schema: pgvector extension + core tables

Revision ID: 0001
Revises:
Create Date: Day 1
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

EMBEDDING_DIM = 768  # must match settings.embedding_dimensions at ingestion time — gemini-embedding-001 truncated to 768


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "chat_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_token", sa.String(64), unique=True, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_page", sa.String(512), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
    )
    op.create_index("ix_chat_session_session_token", "chat_session", ["session_token"])

    op.create_table(
        "chat_message",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_session.id"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("intent", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_chat_message_session_id", "chat_message", ["session_id"])

    op.create_table(
        "lead_submission",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_session.id"), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("contact_number", sa.String(64), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("project_summary", sa.Text, nullable=True),
        sa.Column("service_interest", sa.String(255), nullable=True),
        sa.Column("timeline", sa.String(128), nullable=True),
        sa.Column("budget_range", sa.String(128), nullable=True),
        sa.Column("source_page", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_lead_submission_session_id", "lead_submission", ["session_id"])

    op.create_table(
        "email_notification",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lead_submission.id"), nullable=False),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(512), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
    )
    op.create_index("ix_email_notification_lead_id", "email_notification", ["lead_id"])

    op.create_table(
        "knowledge_document",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("source_uri", sa.String(512), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "knowledge_chunk",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_document.id"), nullable=False),
        sa.Column("record_id", sa.String(255), unique=True, nullable=False),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("intents", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("meta", postgresql.JSONB, nullable=True),
    )
    op.create_index("ix_knowledge_chunk_document_id", "knowledge_chunk", ["document_id"])
    op.create_index("ix_knowledge_chunk_record_id", "knowledge_chunk", ["record_id"])
    # IVFFlat index for approximate nearest-neighbor search; requires ANALYZE
    # after data is loaded, and `lists` should be tuned to dataset size later.
    op.execute(
        "CREATE INDEX ix_knowledge_chunk_embedding ON knowledge_chunk "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_table("knowledge_chunk")
    op.drop_table("knowledge_document")
    op.drop_table("email_notification")
    op.drop_table("lead_submission")
    op.drop_table("chat_message")
    op.drop_table("chat_session")
    op.execute("DROP EXTENSION IF EXISTS vector")
