"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-01 00:00:00.000000
"""

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("topic", sa.String(length=64), nullable=False),
        sa.Column("custom_topic", sa.String(length=128), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_posts_topic", "posts", ["topic"])
    op.create_index("ix_posts_created_at", "posts", ["created_at"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_posts_embedding_vector "
        "ON posts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.create_table(
        "generation_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("topic", sa.String(length=64), nullable=False),
        sa.Column("custom_topic", sa.String(length=128), nullable=True),
        sa.Column("user_request", sa.Text(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("generated_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("retrieved_post_ids", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generation_logs_topic", "generation_logs", ["topic"])
    op.create_index("ix_generation_logs_created_at", "generation_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_generation_logs_created_at", table_name="generation_logs")
    op.drop_index("ix_generation_logs_topic", table_name="generation_logs")
    op.drop_table("generation_logs")
    op.execute("DROP INDEX IF EXISTS ix_posts_embedding_vector")
    op.drop_index("ix_posts_created_at", table_name="posts")
    op.drop_index("ix_posts_topic", table_name="posts")
    op.drop_table("posts")
