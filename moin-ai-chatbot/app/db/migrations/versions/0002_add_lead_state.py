"""add lead_state + lead_draft to chat_session (Day 5 state machine)

Revision ID: 0002
Revises: 0001
Create Date: Day 5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_session",
        sa.Column("lead_state", sa.String(32), nullable=False, server_default="not_active"),
    )
    op.add_column(
        "chat_session",
        sa.Column("lead_draft", postgresql.JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chat_session", "lead_draft")
    op.drop_column("chat_session", "lead_state")
