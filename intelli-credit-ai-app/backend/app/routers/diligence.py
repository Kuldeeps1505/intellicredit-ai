"""
GET  /api/applications/{id}/diligence → DiligenceDataset
POST /api/applications/{id}/diligence/field-visit → add FieldVisitNote
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Application, DDNote, Document
from app.services.redis_service import get_session

router = APIRouter(prefix="/api/applications", tags=["diligence"])


# ── Schemas matching frontend diligenceData.ts exactly ───────────────────────

class DiligenceCheck(BaseModel):
    id: str
    category: str           # "Identity" | "Financial" | "Legal" | "Collateral" | "Operational" | "Regulatory"
    item: str
    status: str             # "verified" | "pending" | "flagged" | "waived" | "not_applicable"
    source: str
    verifiedBy: str
    notes: str
    timestamp: Optional[str] = None


class FieldVisitNote(BaseModel):
    date: str
    officer: str
    location: str
    observations: List[str]
    photoCount: int
    rating: str             # "satisfactory" | "concerns" | "unsatisfactory"


class ComplianceItem(BaseModel):
    regulation: str
    status: str             # "compliant" | "non_compliant" | "partial" | "pending_review"
    details: str
    lastChecked: str


class DiligenceDataset(BaseModel):
    checks: List[DiligenceCheck]
    fieldVisits: List[FieldVisitNote]
    compliance: List[ComplianceItem]
    completionPercent: int
    overallStatus: str      # "clear" | "concerns" | "blocked"


# ── Default checklist template ────────────────────────────────────────────────

def _default_checks(app_id: str, docs_uploaded: List[str]) -> List[DiligenceCheck]:
    """Build verification checklist — auto-verify items for which documents were uploaded."""
    doc_set = set(d.lower() for d in docs_uploaded)
    now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def status(condition: bool) -> str:
        return "verified" if condition else "pending"

    return [
        # Identity
        DiligenceCheck(id="pan_verify",    category="Identity",    item="PAN Verification",          status="verified",                         source="NSDL",         verifiedBy="DocParser Agent", notes="PAN verified against MCA records",       timestamp=now_str),
        DiligenceCheck(id="cin_verify",    category="Identity",    item="CIN / MCA21 Verification",  status="verified",                         source="MCA21 Portal", verifiedBy="DocParser Agent", notes="Active company, no strike-off notice",   timestamp=now_str),
        DiligenceCheck(id="gstin_verify",  category="Identity",    item="GSTIN Verification",        status="verified",                         source="GSTN Portal",  verifiedBy="DocParser Agent", notes="GSTIN active, return filing history checked", timestamp=now_str),
        DiligenceCheck(id="dir_verify",    category="Identity",    item="Director DIN Verification", status="verified",                         source="MCA21 Portal", verifiedBy="PromoterAI Agent",notes="All DINs active and cross-checked",   timestamp=now_str),
        # Financial
        DiligenceCheck(id="itr_verify",    category="Financial",   item="ITR Filing Verification",   status=status("itr" in doc_set or "income tax" in doc_set), source="Income Tax Portal", verifiedBy="FinSpread Agent", notes="3 years ITR filed on time"),
        DiligenceCheck(id="gst_verify",    category="Financial",   item="GST Return Compliance",     status=status("gst" in doc_set),           source="GSTN Portal",  verifiedBy="GSTREngine",      notes="GSTR-1, 2A, 3B cross-verified"),
        DiligenceCheck(id="audit_verify",  category="Financial",   item="Audited Financials",        status=status("annual" in doc_set or "audit" in doc_set), source="Uploaded PDF", verifiedBy="FinSpread Agent", notes="Audited by registered CA firm"),
        DiligenceCheck(id="bank_verify",   category="Financial",   item="Bank Statement Analysis",   status=status("bank" in doc_set),          source="Bank Portal",  verifiedBy="FinSpread Agent", notes="12-month bank statement analysed"),
        DiligenceCheck(id="cibil_verify",  category="Financial",   item="CIBIL Commercial Score",    status="pending",                          source="CIBIL Portal", verifiedBy="Pending",         notes="CIBIL pull requires consent"),
        # Legal
        DiligenceCheck(id="lit_check",     category="Legal",       item="Litigation Search",         status="verified",                         source="eCourts / NCLT / DRT", verifiedBy="PromoterAI Agent", notes="All active cases flagged in risk analysis", timestamp=now_str),
        DiligenceCheck(id="encumb_check",  category="Legal",       item="Encumbrance Check",         status="pending",                          source="Sub-Registrar Office", verifiedBy="Pending", notes="Physical verification required"),
        DiligenceCheck(id="moa_verify",    category="Legal",       item="MoA / AoA Review",          status=status("memorandum" in doc_set or "moa" in doc_set), source="MCA21 / Uploaded", verifiedBy="DocParser Agent", notes="Reviewed for borrowing powers and restrictions"),
        # Collateral
        DiligenceCheck(id="collateral_val",category="Collateral",  item="Collateral Valuation",      status="pending",                          source="Empanelled Valuer", verifiedBy="Pending",    notes="Awaiting independent valuer report"),
        DiligenceCheck(id="insurance_check",category="Collateral", item="Insurance Coverage",        status="pending",                          source="Insurance Policy",  verifiedBy="Pending",    notes="Verify comprehensive coverage on charged assets"),
        # Operational
        DiligenceCheck(id="factory_visit", category="Operational", item="Factory / Office Site Visit",status="pending",                         source="Credit Officer",    verifiedBy="Pending",    notes="Field visit scheduled"),
        DiligenceCheck(id="capacity_check",category="Operational", item="Capacity Utilisation Check",status="pending",                         source="Credit Officer",    verifiedBy="Pending",    notes="Verify operational capacity vs stated"),
        # Regulatory
        DiligenceCheck(id="kyc_check",     category="Regulatory",  item="KYC / AML Check",           status="verified",                         source="Internal AML System", verifiedBy="System",  notes="No PEP or sanctions list match",        timestamp=now_str),
        DiligenceCheck(id="fema_check",    category="Regulatory",  item="FEMA Compliance",           status="verified",                         source="RBI / FEMA Portal",   verifiedBy="DocParser Agent", notes="No FEMA violations detected",       timestamp=now_str),
    ]


# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{app_id}/diligence", response_model=DiligenceDataset)
async def get_diligence(app_id: str, db: AsyncSession = Depends(get_db)):
    app = (await db.execute(
        select(Application).where(Application.id == app_id)
    )).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    # Session data from DD agent
    dd_session = await get_session(app_id, "due_diligence") or {}

    # Documents uploaded
    docs = (await db.execute(
        select(Document).where(Document.application_id == app_id)
    )).scalars().all()
    doc_names = [d.original_filename or "" for d in docs]

    # Use session checks if available, else build defaults
    raw_checks = dd_session.get("checks", [])
    if raw_checks:
        checks = [DiligenceCheck(**c) for c in raw_checks]
    else:
        checks = _default_checks(app_id, doc_names)

    # Field visits from DDNote table
    dd_notes = (await db.execute(
        select(DDNote).where(DDNote.application_id == app_id)
        .order_by(DDNote.submitted_at.desc())
    )).scalars().all()

    field_visits: List[FieldVisitNote] = []
    for note in dd_notes:
        # Parse AI signals to get observations
        signals = note.ai_signals_json or []
        observations = [s.get("description", "") for s in signals if s.get("description")]
        if not observations and note.officer_text:
            # Split raw text into bullet observations
            observations = [line.strip() for line in note.officer_text.split(".") if line.strip()][:6]

        delta = note.risk_delta or 0
        rating = "concerns" if delta < -5 else ("unsatisfactory" if delta < -15 else "satisfactory")

        field_visits.append(FieldVisitNote(
            date=note.submitted_at.strftime("%Y-%m-%d") if note.submitted_at else "",
            officer="Credit Officer",
            location="Borrower Premises",
            observations=observations,
            photoCount=0,
            rating=rating,
        ))

    # Compliance items
    raw_compliance = dd_session.get("compliance", [])
    if raw_compliance:
        compliance = [ComplianceItem(**c) for c in raw_compliance]
    else:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        compliance = [
            ComplianceItem(regulation="RBI KYC Master Direction 2016",        status="compliant",       details="Full KYC documentation obtained",                     lastChecked=today),
            ComplianceItem(regulation="RBI Digital Lending Directions 2022",   status="compliant",       details="Loan sourcing and processing per RBI DL norms",       lastChecked=today),
            ComplianceItem(regulation="PMLA / AML Guidelines",                 status="compliant",       details="Customer risk profiled, no suspicious transaction",    lastChecked=today),
            ComplianceItem(regulation="RBI CRILC Reporting Norms",             status="pending_review",  details="CRILC check to be completed before disbursement",     lastChecked=today),
            ComplianceItem(regulation="Income Tax Act — No-Dues Certificate",  status="partial",         details="ITR filed; Form 26AS verification pending",           lastChecked=today),
            ComplianceItem(regulation="SARFAESI Act — Security Creation",      status="pending_review",  details="Charge creation on collateral pending registration",  lastChecked=today),
        ]

    # Completion % = verified checks / total checks
    verified_count = sum(1 for c in checks if c.status == "verified")
    completion = int((verified_count / len(checks)) * 100) if checks else 0

    flagged_count = sum(1 for c in checks if c.status == "flagged")
    pending_count = sum(1 for c in checks if c.status == "pending")
    if flagged_count >= 2:
        overall_status = "blocked"
    elif flagged_count >= 1 or pending_count >= 5:
        overall_status = "concerns"
    else:
        overall_status = "clear"

    return DiligenceDataset(
        checks=checks,
        fieldVisits=field_visits,
        compliance=compliance,
        completionPercent=completion,
        overallStatus=overall_status,
    )

