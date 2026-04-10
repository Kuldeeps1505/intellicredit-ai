"""
Async SQLAlchemy engine + session factory.
Alembic uses SYNC_DATABASE_URL for migrations.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine, event, text
from app.config import settings
from app.models.models import Base

# ── Async engine (used by FastAPI + agents) ───────────────────────────────────
connect_args = {}
if "sqlite" in settings.database_url:
    connect_args = {"check_same_thread": False}

async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args,
)

# Enable WAL mode for SQLite so reads don't block writes
if "sqlite" in settings.database_url:
    from sqlalchemy import event as _event
    @_event.listens_for(async_engine.sync_engine, "connect")
    def set_wal_mode(dbapi_conn, connection_record):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")
        dbapi_conn.execute("PRAGMA synchronous=NORMAL")

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