from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.current_user import get_current_user
from app.auth.schemas import TokenUser
from app.core.config import config

engine = create_async_engine(
    config.DATABASE_URL,
    echo=config.DEBUG,
    connect_args=config.DATABASE_CONNECT_ARGS,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[TokenUser, Depends(get_current_user)]
