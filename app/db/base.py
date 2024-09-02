import asyncio

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

from .create import settings

DATABASE_URL = f'postgresql+asyncpg://' \
               f'{settings.postgres_user}:{settings.postgres_password}' \
               f'@{settings.postgres_host}/{settings.postgres_db}'

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_reset_on_return=True,
    echo=True
)


class Base(DeclarativeBase):
    pass


async_session = sessionmaker(
    engine, class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info('Models initialisation is done')


def run_init_models():
    asyncio.run(init_models())


async def get_session():
    async with async_session() as session:
        yield session
