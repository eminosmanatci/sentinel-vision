from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.is_development,
    future=True,
    pool_size=20,
    max_overflow=0,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a new session per request."""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()