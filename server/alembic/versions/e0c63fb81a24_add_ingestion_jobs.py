import sqlalchemy as sa
from sqlmodel.sql.sqltypes import UTCDateTime
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e0c63fb81a24"
down_revision: str = "d9b52ea70f13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("source_parts", postgresql.JSONB(), nullable=False),
        sa.Column("prepared_chunks", postgresql.JSONB(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("updated_at", UTCDateTime(), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "progress BETWEEN 0 AND 100", name="ck_ingestion_job_progress"
        ),
        sa.CheckConstraint(
            "stage IN ('upload', 'extracting', 'chunking', 'embedding', "
            "'storing', 'completed', 'error')", name="ck_ingestion_job_stage"
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index("ix_ingestion_jobs_user_id", "ingestion_jobs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_jobs_user_id", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
