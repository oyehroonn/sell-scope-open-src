"""Database configuration and session management"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# When USE_CSV_STORE or USE_PANDAS_STORE is True, no Postgres connection is used.
if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
    engine = None
    async_session_maker = None
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db():
    if async_session_maker is None:
        # CSV store mode: yield a no-op session so routes that don't use db don't fail.
        class _DummySession:
            async def commit(self): pass
            async def flush(self): pass
            async def close(self): pass
            def add(self, x): pass
            async def execute(self, *a, **k):
                class _R:
                    def scalar(self): return None
                    def scalars(self): return _R()
                    def all(self): return []
                return _R()
        yield _DummySession()
        return
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    if engine is None:
        return
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
