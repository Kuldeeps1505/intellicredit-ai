"""
Core application endpoints — Day 1 stubs, filled in Day 2+.
POST /api/applications
POST /api/applications/{id}/documents
GET  /api/applications/{id}/status
GET  /api/applications/{id}/financials     (stub → filled Day 2)
GET  /api/applications/{id}/provenance     (stub → filled Day 2)
"""
import uuid
import asyncio
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import (
    Company, Application, Document, AgentLog,
    Financial, FieldProvenance
)
from app.schemas.schemas import (
    ApplicationCreate, ApplicationOut, ApplicationStatus,
    AgentStatus, DocumentOut, FinancialsResponse, FieldProvenanceOut
)
from app.services.minio_service import upload_document
from app.services.redis_service import get_session

router = APIRouter(prefix="/api/applications", tags=["applications"])

# Agent names in execution order — used for status reporting
AGENT_ORDER = [
    "document_intelligence",
    "financial_analysis",
    "research_intelligence",
    "risk_assessment",
    "due_diligence",
    "credit_decision",
    "cam_generation",
    "gst_reconciliation_engine",
    "buyer_concentration_engine",
]


# ── POST /api/applications ────────────────────────────────
@router.post("", response_model=ApplicationOut, status_code=201)
async def create_application(
    payload: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create company (upsert by CIN) + application record.
    Returns immediately — pipeline triggered separately after document upload.
    """
    # Upsert company by CIN
    result = await db.execute(select(Company).where(Company.cin == payload.company.cin))
    company = result.scalar_one_or_none()

    if company is None:
        company = Company(
            id=str(uuid.uuid4()),
            **payload.company.model_dump(exclude_none=True),
        )
        db.add(company)
        await db.flush()

    app = Application(
        id=str(uuid.uuid4()),
        company_id=company.id,
        loan_amount_requested=payload.loan_amount_requested,
        purpose=payload.purpose,
        status="PENDING",
        assigned_officer_id=payload.assigned_officer_id,
        aa_consent_handle=payload.aa_consent_handle,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


# ── POST /api/applications/{id}/documents ─────────────────
@router.post("/{app_id}/documents", response_model=List[DocumentOut], status_code=201)
async def upload_documents(
    app_id: str,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload one or more documents for an application.
    Saves to MinIO, creates Document records, triggers agent pipeline.
    """
    result = await db.execute(select(Application).where(Application.id == app_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    uploaded: List[DocumentOut] = []

    for file in files:
        file_bytes = await file.read()
        object_name = f"{app_id}/{uuid.uuid4()}_{file.filename}"
        file_path = upload_document(object_name, file_bytes, file.content_type or "application/pdf")

        doc = Document(
            id=str(uuid.uuid4()),
            application_id=app_id,
            file_path=object_name,
            original_filename=file.filename,
            ocr_status="PENDING",
            extraction_status="PENDING",
            file_size_bytes=len(file_bytes),
        )
        db.add(doc)
        await db.flush()
        uploaded.append(DocumentOut.model_validate(doc))

    # Update application status
    application.status = "PROCESSING"
    await db.commit()

    # Trigger pipeline in background (Day 2: replace with real LangGraph call)
    background_tasks.add_task(_trigger_pipeline, app_id)

    return uploaded


async def _trigger_pipeline(app_id: str):
    """Background task — triggers the full LangGraph agent DAG."""
    from app.services.redis_service import publish_event
    await publish_event(app_id, {
        "event_type": "PIPELINE_STARTED",
        "agent_name": None,
        "payload": {"app_id": app_id},
        "timestamp": datetime.utcnow().isoformat(),
    })
    try:
        from agents.dag import run_pipeline
        await run_pipeline(app_id)
    except Exception as e:
        from app.services.db_helpers import update_app_status
        await update_app_status(app_id, "ERROR")
        await publish_event(app_id, {
            "event_type": "PIPELINE_ERROR",
            "agent_name": None,
            "payload": {"error": str(e)},
            "timestamp": datetime.utcnow().isoformat(),
        })


# ── GET /api/applications/{id}/status ────────────────────
@router.get("/{app_id}/status", response_model=ApplicationStatus)
async def get_status(app_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Application).where(Application.id == app_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Fetch agent logs
    logs_result = await db.execute(
        select(AgentLog).where(AgentLog.application_id == app_id)
    )
    logs = logs_result.scalars().all()
    log_map = {log.agent_name: log for log in logs}

    agents = []
    completed = 0
    for name in AGENT_ORDER:
        log = log_map.get(name)
        if log:
            agents.append(AgentStatus(
                agent_name=name,
                status=log.status,
                duration_ms=log.duration_ms,
                output_summary=log.output_summary,
            ))
            if log.status == "COMPLETED":
                completed += 1
        else:
            agents.append(AgentStatus(agent_name=name, status="IDLE"))

    progress = int((completed / len(AGENT_ORDER)) * 100)

    return ApplicationStatus(
        application_id=app_id,
        pipeline_status=application.status,
        agents=agents,
        overall_progress_pct=progress,
    )


# ── GET /api/applications/{id}/financials ────────────────
@router.get("/{app_id}/financials", response_model=FinancialsResponse)
async def get_financials(app_id: str, db: AsyncSession = Depends(get_db)):
    """Returns extracted financials with provenance per field. Filled in Day 2."""
    fin_result = await db.execute(
        select(Financial).where(Financial.application_id == app_id)
    )
    financials = fin_result.scalars().all()

    prov_result = await db.execute(
        select(FieldProvenance).where(FieldProvenance.application_id == app_id)
    )
    provenance = prov_result.scalars().all()

    return FinancialsResponse(
        application_id=app_id,
        financials=[f.__dict__ for f in financials],
        provenance=[FieldProvenanceOut.model_validate(p) for p in provenance],
    )


# ── GET /api/applications/{id}/provenance ────────────────
@router.get("/{app_id}/provenance", response_model=List[FieldProvenanceOut])
async def get_provenance(app_id: str, db: AsyncSession = Depends(get_db)):
    """Full chain of evidence — every extracted field with source, page, method, confidence."""
    result = await db.execute(
        select(FieldProvenance).where(FieldProvenance.application_id == app_id)
    )
    records = result.scalars().all()
    return [FieldProvenanceOut.model_validate(r) for r in records]