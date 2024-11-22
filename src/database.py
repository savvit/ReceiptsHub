from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from src.config import Config

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{Config.POSTGRES_USER}:"
    f"{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_DB}:"
    f"{Config.POSTGRES_PORT}/{Config.POSTGRES_DB_NAME}"
)

async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

async_sessionmaker = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_sessionmaker() as session:
        yield session
