"""
Async SQLAlchemy engine + session factory.
Alembic uses SYNC_DATABASE_URL for migrations.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from app.config import settings
from backend.app.models.models import Base

# ── Async engine (used by FastAPI) ────────────────────────
async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── Sync engine (used by Alembic) ─────────────────────────
sync_engine = create_engine(settings.sync_database_url, echo=False)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all tables on startup (dev only). Use Alembic in prod."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)