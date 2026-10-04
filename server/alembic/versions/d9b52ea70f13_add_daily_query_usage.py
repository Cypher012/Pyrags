import sqlalchemy as sa

from alembic import op

revision: str = "d9b52ea70f13"
down_revision: str = "c8a40df19e62"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "daily_query_usage",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("used", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("user_id", "day"),
        sa.CheckConstraint("used >= 0", name="ck_daily_query_usage_used"),
    )
    op.execute(sa.text(
        "INSERT INTO daily_query_usage (user_id, day, used) "
        "SELECT conversations.user_id, "
        "(messages.created_at AT TIME ZONE 'Africa/Lagos')::date, count(*) "
        "FROM messages JOIN conversations ON conversations.id = messages.conversation_id "
        "WHERE messages.role = 'USER' "
        "AND (messages.created_at AT TIME ZONE 'Africa/Lagos')::date = "
        "(CURRENT_TIMESTAMP AT TIME ZONE 'Africa/Lagos')::date "
        "GROUP BY conversations.user_id, (messages.created_at AT TIME ZONE 'Africa/Lagos')::date"
    ))


def downgrade() -> None:
    op.drop_table("daily_query_usage")
