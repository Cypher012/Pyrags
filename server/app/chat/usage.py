import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import TokenUser
from app.model.query_usage import DailyQueryUsage, QueryUsageResponse

DAILY_QUERY_LIMIT = 6
UNLIMITED_EMAIL = "ayoojoade@gmail.com"
QUERY_TIMEZONE = ZoneInfo("Africa/Lagos")
logger = logging.getLogger(__name__)


def current_query_day() -> date:
    return datetime.now(QUERY_TIMEZONE).date()


def usage_response(user: TokenUser, day: date, used: int) -> QueryUsageResponse:
    unlimited = user.email.strip().casefold() == UNLIMITED_EMAIL
    return QueryUsageResponse(
        limit=None if unlimited else DAILY_QUERY_LIMIT,
        used=0 if unlimited else used,
        remaining=None if unlimited else max(0, DAILY_QUERY_LIMIT - used),
        unlimited=unlimited,
        resets_at=datetime.combine(day + timedelta(days=1), time.min, QUERY_TIMEZONE),
    )


async def get_query_usage(session: AsyncSession, user: TokenUser) -> QueryUsageResponse:
    day = current_query_day()
    if user.email.strip().casefold() == UNLIMITED_EMAIL:
        return usage_response(user, day, 0)
    usage = await session.get(DailyQueryUsage, (user.id, day))
    return usage_response(user, day, usage.used if usage else 0)


async def reserve_query(session: AsyncSession, user: TokenUser) -> date | None:
    if user.email.strip().casefold() == UNLIMITED_EMAIL:
        return None
    day = current_query_day()
    result = await session.execute(
        insert(DailyQueryUsage)
        .values(user_id=user.id, day=day, used=1)
        .on_conflict_do_update(
            index_elements=["user_id", "day"],
            set_={"used": DailyQueryUsage.used + 1},
            where=DailyQueryUsage.used < DAILY_QUERY_LIMIT,
        )
        .returning(DailyQueryUsage.used)
    )
    used = result.scalar_one_or_none()
    await session.commit()
    if used is None:
        usage = usage_response(user, day, DAILY_QUERY_LIMIT)
        retry_after = max(1, int((usage.resets_at - datetime.now(QUERY_TIMEZONE)).total_seconds()))
        raise HTTPException(
            status_code=429,
            detail={
                "message": "You have used all 6 queries for today. Your limit resets at midnight (Lagos time).",
                "usage": usage.model_dump(mode="json"),
            },
            headers={"Retry-After": str(retry_after)},
        )
    return day


async def refund_query(session: AsyncSession, user: TokenUser, day: date | None) -> None:
    if day is None:
        return
    try:
        await session.rollback()
        await session.execute(
            update(DailyQueryUsage)
            .where(
                DailyQueryUsage.user_id == user.id,
                DailyQueryUsage.day == day,
                DailyQueryUsage.used > 0,
            )
            .values(used=DailyQueryUsage.used - 1)
        )
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception("Could not refund failed query for user %s", user.id)
