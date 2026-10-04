from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "365152c7eb5b"
down_revision: Union[str, Sequence[str], None] = "41585cd84b24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


document_status = postgresql.ENUM(
    "PROCESSING",
    "READY",
    "FAILED",
    name="documentstatus",
)


def upgrade() -> None:
    document_status.create(op.get_bind(), checkfirst=True)

    op.alter_column(
        "documents",
        "status",
        existing_type=sa.VARCHAR(),
        type_=document_status,
        existing_nullable=False,
        postgresql_using="status::text::documentstatus",
    )


def downgrade() -> None:
    op.alter_column(
        "documents",
        "status",
        existing_type=document_status,
        type_=sa.VARCHAR(),
        existing_nullable=False,
        postgresql_using="status::text",
    )

    document_status.drop(op.get_bind(), checkfirst=True)
