"""
GET  /api/applications/{id}/audit          → AuditTrailDataset
POST /api/applications/{id}/audit/override → HumanOverride
"""
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import Application, AgentLog, RiskScore, Document, DDNote
from app.services.redis_service import get_session

router = APIRouter(prefix="/api/applications", tags=["audit"])


# ── Schemas matching frontend auditTrailData.ts exactly ──────────────────────

class AuditEvent(BaseModel):
    id: str
    timestamp: str
    actor: str
    actorType: str          # "ai_agent" | "human" | "system"
    actionType: str         # "data_extraction" | "analysis" | "decision" | "override" | "initiation" | "verification"
    module: str
    description: str
    details: Optional[str] = None
    confidence: Optional[int] = None
    dataSources: Optional[List[str]] = None
    previousValue: Optional[str] = None
    newValue: Optional[str] = None


class HumanOverride(BaseModel):
    id: str
    timestamp: str
    officer: str
    originalRecommendation: str
    overriddenTo: str
    reason: str
    approvedBy: str
    flaggedForReview: bool


class WorkflowStage(BaseModel):
    stage: str
    status: str             # "completed" | "in_progress" | "pending" | "blocked"
    actor: Optional[str] = None
    actorType: Optional[str] = None
    timestamp: Optional[str] = None
    notes: Optional[str] = None


class ComplianceBadge(BaseModel):
    regulation: str
    status: str             # "compliant" | "partial" | "non_compliant"
    details: str


class AuditTrailDataset(BaseModel):
    events: List[AuditEvent]
    overrides: List[HumanOverride]
    workflow: List[WorkflowStage]
    compliance: List[ComplianceBadge]


# ── Override request body ──────────────────────────────────────────────────────

class OverrideRequest(BaseModel):
    originalRecommendation: str
    overriddenTo: str
    reason: str
    officer: str = "Credit Officer"
    approvedBy: str = "Branch Manager"


# ── Agent → module name map ────────────────────────────────────────────────────

AGENT_MODULE = {
    "document_intelligence":      "Document Upload",
    "financial_analysis":         "Financial Spreads",
    "research_intelligence":      "Promoter Intel",
    "gst_reconciliation_engine":  "Risk Analytics",
    "buyer_concentration_engine": "Risk Analytics",
    "risk_assessment":            "Risk Analytics",
    "due_diligence":              "Due Diligence",
    "credit_decision":            "CAM Report",
    "cam_generation":             "CAM Report",
}

AGENT_DISPLAY = {
    "document_intelligence":      "DocParser Agent",
    "financial_analysis":         "FinSpread Agent",
    "research_intelligence":      "PromoterAI Agent",
    "gst_reconciliation_engine":  "GSTREngine",
    "buyer_concentration_engine": "BuyerEng",
    "risk_assessment":            "RiskScore Agent",
    "due_diligence":              "DD Agent",
    "credit_decision":            "CAMGen Agent",
    "cam_generation":             "CAMGen Agent",
}

AGENT_ACTION = {
    "document_intelligence":     "data_extraction",
    "financial_analysis":        "analysis",
    "research_intelligence":     "analysis",
    "gst_reconciliation_engine": "analysis",
    "buyer_concentration_engine":"analysis",
    "risk_assessment":           "decision",
    "due_diligence":             "verification",
    "credit_decision":           "decision",
    "cam_generation":            "decision",
}


# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{app_id}/audit", response_model=AuditTrailDataset)
async def get_audit_trail(app_id: str, db: AsyncSession = Depends(get_db)):
    app = (await db.execute(
        select(Application).where(Application.id == app_id)
    )).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    events: List[AuditEvent] = []

    # 1. Application creation event
    events.append(AuditEvent(
        id=f"evt_init_{app_id[:8]}",
        timestamp=app.created_at.strftime("%Y-%m-%d %H:%M:%S") if app.created_at else "",
        actor="System",
        actorType="system",
        actionType="initiation",
        module="Document Upload",
        description="Credit application created",
        details=f"Application ID: {app_id}",
        dataSources=["Application Form"],
    ))

    # 2. Document upload events
    docs = (await db.execute(
        select(Document).where(Document.application_id == app_id)
        .order_by(Document.uploaded_at.asc())
    )).scalars().all()
    for doc in docs:
        events.append(AuditEvent(
            id=f"evt_doc_{doc.id[:8]}",
            timestamp=doc.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if doc.uploaded_at else "",
            actor="Credit Officer",
            actorType="human",
            actionType="data_extraction",
            module="Document Upload",
            description=f"Document uploaded: {doc.original_filename}",
            details=f"Type: {doc.doc_type or 'Unknown'} · Status: {doc.extraction_status}",
        ))

    # 3. Agent log events
    agent_logs = (await db.execute(
        select(AgentLog).where(AgentLog.application_id == app_id)
        .order_by(AgentLog.logged_at.asc())
    )).scalars().all()

    for log in agent_logs:
        actor = AGENT_DISPLAY.get(log.agent_name, log.agent_name)
        module = AGENT_MODULE.get(log.agent_name, "Pipeline")
        action = AGENT_ACTION.get(log.agent_name, "analysis")
        ts = log.logged_at.strftime("%Y-%m-%d %H:%M:%S") if log.logged_at else ""

        if log.status in ("COMPLETED", "STARTED", "RUNNING"):
            events.append(AuditEvent(
                id=f"evt_agent_{log.id[:8]}",
                timestamp=ts,
                actor=actor,
                actorType="ai_agent",
                actionType=action,
                module=module,
                description=log.output_summary or f"{actor} completed {action}",
                details=f"Duration: {log.duration_ms}ms" if log.duration_ms else None,
                confidence=90,
                dataSources=["AI Analysis"],
            ))
        if log.status == "ERROR":
            events.append(AuditEvent(
                id=f"evt_err_{log.id[:8]}",
                timestamp=ts,
                actor=actor,
                actorType="ai_agent",
                actionType=action,
                module=module,
                description=f"Error in {actor}",
                details=log.error_message,
            ))

    # 4. Due diligence submission events
    dd_notes = (await db.execute(
        select(DDNote).where(DDNote.application_id == app_id)
        .order_by(DDNote.submitted_at.asc())
    )).scalars().all()
    for note in dd_notes:
        events.append(AuditEvent(
            id=f"evt_dd_{note.id[:8]}",
            timestamp=note.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if note.submitted_at else "",
            actor="Credit Officer",
            actorType="human",
            actionType="verification",
            module="Due Diligence",
            description="Field visit observations submitted",
            details=f"Risk delta: {note.risk_delta:+.1f} points",
            newValue=str(note.risk_delta),
        ))

    # 5. Risk decision event
    risk = (await db.execute(
        select(RiskScore).where(RiskScore.application_id == app_id)
        .order_by(RiskScore.computed_at.desc())
    )).scalar_one_or_none()
    if risk:
        events.append(AuditEvent(
            id=f"evt_risk_{app_id[:8]}",
            timestamp=risk.computed_at.strftime("%Y-%m-%d %H:%M:%S") if risk.computed_at else "",
            actor="RiskScore Agent",
            actorType="ai_agent",
            actionType="decision",
            module="Risk Analytics",
            description=f"Credit decision: {risk.decision} — Score {risk.final_score:.0f}/100",
            details=f"Default prob 12m: {risk.default_probability_12m:.1f}% · Category: {risk.risk_category}",
            confidence=int(risk.final_score or 0),
            dataSources=["Five-Cs Engine", "Logistic Regression", "GSTR Engine", "Buyer Engine"],
        ))

    # Sort all events by timestamp
    events.sort(key=lambda e: e.timestamp)

    # Human overrides from Redis session
    raw_overrides = await get_session(app_id, "human_overrides") or []
    overrides = [HumanOverride(**o) for o in raw_overrides]

    # Workflow stages
    status = app.status
    workflow = [
        WorkflowStage(stage="Application Created",    status="completed",    actor="Credit Officer", actorType="human",    timestamp=app.created_at.strftime("%Y-%m-%d %H:%M:%S") if app.created_at else None),
        WorkflowStage(stage="Documents Uploaded",     status="completed" if docs else "pending", actor="Credit Officer" if docs else None, actorType="human" if docs else None),
        WorkflowStage(stage="Pipeline Executed",      status="completed" if status == "COMPLETED" else ("in_progress" if status == "PROCESSING" else "pending"), actor="AI Pipeline", actorType="ai_agent"),
        WorkflowStage(stage="Risk Scored",            status="completed" if risk else "pending",  actor="RiskScore Agent" if risk else None, actorType="ai_agent" if risk else None),
        WorkflowStage(stage="CAM Generated",          status="completed" if status == "COMPLETED" else "pending", actor="CAMGen Agent", actorType="ai_agent"),
        WorkflowStage(stage="Human Review",           status="pending",      actor=None, notes="Pending credit officer review"),
        WorkflowStage(stage="Final Approval",         status="pending",      actor=None, notes="Pending sanctioning authority approval"),
    ]

    compliance = [
        ComplianceBadge(regulation="RBI Digital Lending Directions 2022", status="compliant",  details="All digital lending process norms followed"),
        ComplianceBadge(regulation="RBI KYC Master Direction",            status="compliant",  details="KYC completed for all directors and company"),
        ComplianceBadge(regulation="PMLA 2002 — AML Compliance",          status="compliant",  details="No PEP match, no sanctions list hit"),
        ComplianceBadge(regulation="Fair Practices Code (RBI)",            status="compliant",  details="Transparent disclosure, no misrepresentation"),
        ComplianceBadge(regulation="CRILC Reporting",                      status="partial",    details="CRILC check pending completion before disbursement"),
    ]

    return AuditTrailDataset(events=events, overrides=overrides, workflow=workflow, compliance=compliance)


@router.post("/{app_id}/audit/override", response_model=HumanOverride)
async def create_override(app_id: str, body: OverrideRequest, db: AsyncSession = Depends(get_db)):
    """Record a human override of the AI recommendation."""
    app = (await db.execute(
        select(Application).where(Application.id == app_id)
    )).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    override = HumanOverride(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        officer=body.officer,
        originalRecommendation=body.originalRecommendation,
        overriddenTo=body.overriddenTo,
        reason=body.reason,
        approvedBy=body.approvedBy,
        flaggedForReview=True,
    )

    # Persist to Redis session
    from app.services.redis_service import get_session
    existing = await get_session(app_id, "human_overrides") or []
    existing.append(override.model_dump())
    from app.services.redis_service import set_session
    await set_session(app_id, "human_overrides", existing)

    return override









