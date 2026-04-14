"""
Shared DB helper functions used by all agents.
Uses the same engine as the main app to avoid SQLite locking issues.
"""
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


@asynccontextmanager
async def _AgentSession():
    """Yields a DB session using the main app engine (avoids SQLite locking)."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def log_agent(
    app_id: str,
    agent_name: str,
    status: str,
    output_summary: str = None,
    error_message: str = None,
    duration_ms: int = None,
):
    """Upsert an agent log record."""
    from app.models import AgentLog
    async with _AgentSession() as session:
        result = await session.execute(
            select(AgentLog).where(
                AgentLog.application_id == app_id,
                AgentLog.agent_name == agent_name,
            )
        )
        log = result.scalar_one_or_none()
        if log:
            log.status = status
            log.logged_at = datetime.utcnow()
            if output_summary:
                log.output_summary = output_summary
            if error_message:
                log.error_message = error_message
            if duration_ms:
                log.duration_ms = duration_ms
        else:
            log = AgentLog(
                id=str(uuid.uuid4()),
                application_id=app_id,
                agent_name=agent_name,
                status=status,
                output_summary=output_summary,
                error_message=error_message,
                duration_ms=duration_ms,
            )
            session.add(log)


async def update_app_status(app_id: str, status: str):
    """Update application.status field."""
    from app.models import Application
    async with _AgentSession() as session:
        result = await session.execute(select(Application).where(Application.id == app_id))
        app = result.scalar_one_or_none()
        if app:
            app.status = status
            app.updated_at = datetime.utcnow()


async def save_risk_flag(app_id: str, flag_type: str, severity: str, description: str, agent: str):
    """Save a risk flag and publish event."""
    from app.models import RiskFlag
    from app.services.redis_service import publish_event
    async with _AgentSession() as session:
        flag = RiskFlag(
            id=str(uuid.uuid4()),
            application_id=app_id,
            flag_type=flag_type,
            severity=severity,
            description=description,
            detected_by_agent=agent,
        )
        session.add(flag)

    await publish_event(app_id, {
        "event_type": "FLAG_DETECTED",
        "agent_name": agent,
        "payload": {"flag_type": flag_type, "severity": severity, "description": description},
        "timestamp": datetime.utcnow().isoformat(),
    })


async def save_provenance(app_id: str, records: list[dict]):
    """Bulk-save field provenance records."""
    from app.models import FieldProvenance
    async with _AgentSession() as session:
        for r in records:
            prov = FieldProvenance(
                id=str(uuid.uuid4()),
                application_id=app_id,
                **r,
            )
            session.add(prov)
