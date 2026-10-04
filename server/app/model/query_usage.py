from datetime import date, datetime

from pydantic import BaseModel
from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel


class DailyQueryUsage(SQLModel, table=True):
    __tablename__ = "daily_query_usage"
    __table_args__ = (CheckConstraint("used >= 0", name="ck_daily_query_usage_used"),)

    user_id: str = Field(primary_key=True)
    day: date = Field(primary_key=True)
    used: int = Field(default=0, nullable=False)


class QueryUsageResponse(BaseModel):
    limit: int | None
    used: int
    remaining: int | None
    unlimited: bool
    resets_at: datetime
