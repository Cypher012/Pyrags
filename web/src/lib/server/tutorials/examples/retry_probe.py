from uuid import UUID

from sqlalchemy import text

from app.core.config import config
from app.core.database import async_session


async def fail_once(job_id: str) -> None:
    if config.APP_ENV != "development":
        raise RuntimeError("The retry probe is only available in development")
    async with async_session() as session, session.begin():
        result = await session.execute(
            text(
                "UPDATE tutorial_retry_faults SET fired = true "
                "WHERE job_id = :job_id AND fired = false RETURNING job_id"
            ),
            {"job_id": UUID(job_id)},
        )
        should_fail = result.scalar_one_or_none() is not None
    if should_fail:
        raise RuntimeError("Local retry exercise")
