from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from typing import AsyncGenerator

DATABASE_URL_ASYNC="postgresql+asyncpg://postgres:postgres@localhost:5432/axiomly"

engine = create_async_engine(
    DATABASE_URL_ASYNC,
    pool_pre_ping=True,
    echo=True  # для отладки, уберу в продакшене
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session