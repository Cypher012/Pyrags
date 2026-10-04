"""add source_documents to messages

Revision ID: b7f3a91c2e04
Revises: 365152c7eb5b
Create Date: 2026-10-04 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7f3a91c2e04"
down_revision: Union[str, Sequence[str], None] = "365152c7eb5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Persist an assistant message's retrieved source documents."""
    op.add_column(
        "messages",
        sa.Column(
            "source_documents",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("messages", "source_documents")
