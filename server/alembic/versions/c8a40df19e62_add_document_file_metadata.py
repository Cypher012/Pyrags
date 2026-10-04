import sqlalchemy as sa

from alembic import op

revision: str = "c8a40df19e62"
down_revision: str = "b7f3a91c2e04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("size_bytes", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "page_count")
    op.drop_column("documents", "size_bytes")
