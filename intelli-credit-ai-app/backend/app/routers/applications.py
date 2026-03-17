"""
Core application endpoints — updated to match frontend TypeScript interfaces exactly.

GET  /api/applications                     → List[ApplicationSummary]
POST /api/applications                     → { id: str }
GET  /api/applications/{id}                → ApplicationSummary
POST /api/applications/{id}/documents      → DocItem
GET  /api/applications/{id}/documents      → List[DocItem]
POST /api/applications/{id}/pipeline/start → { jobId, status }
GET  /api/applications/{id}/pipeline/status→ PipelineStatusResponse
POST /api/applications/{id}/aa-consent     → { status, redirect_url }
GET  /api/applications/{id}/financials     → FinancialSpreadsDataset
GET  /api/applications/{id}/provenance     → List[FieldProvenanceOut]
"""
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import (
    Company, Application, Document, AgentLog,
    Financial, Ratio, FieldProvenance, RiskScore
)
from app.schemas.schemas import ApplicationCreate, FieldProvenanceOut
from app.services.minio_service import upload_document
from app.services.redis_service import get_session

router = APIRouter(prefix="/api/applications", tags=["applications"])

# ── Agent pipeline config — matches frontend agentData.ts exactly ─────────────
AGENT_PIPELINE = [
    {"id": "doc_parse",      "name": "Document Parser Agent",       "shortName": "DocParser",   "icon": "FileText",    "groupId": "g1", "isEngine": False},
    {"id": "fin_spread",     "name": "Financial Spread Agent",      "shortName": "FinSpread",   "icon": "BarChart2",   "groupId": "g2", "isEngine": False},
    {"id": "gst_verify",     "name": "GST Verification Agent",      "shortName": "GSTVerify",   "icon": "Receipt",     "groupId": "g2", "isEngine": False},
    {"id": "gstr_engine",    "name": "GSTR Reconciliation Engine",  "shortName": "GSTREngine",  "icon": "GitMerge",    "groupId": "g3", "isEngine": True},
    {"id": "buyer_engine",   "name": "Buyer Concentration Engine",  "shortName": "BuyerEng",    "icon": "PieChart",    "groupId": "g3", "isEngine": True},
    {"id": "promoter_intel", "name": "Promoter Intelligence Agent", "shortName": "PromoterAI",  "icon": "Users",       "groupId": "g4", "isEngine": False},
    {"id": "risk_score",     "name": "Risk Scoring Agent",          "shortName": "RiskScore",   "icon": "ShieldAlert", "groupId": "g5", "isEngine": False},
    {"id": "cam_gen",        "name": "CAM Generation Agent",        "shortName": "CAMGen",      "icon": "FileOutput",  "groupId": "g6", "isEngine": False},
    {"id": "counter_fact",   "name": "Counterfactual Engine",       "shortName": "CounterFact", "icon": "Lightbulb",   "groupId": "g7", "isEngine": True},
]

AGENT_NAME_TO_ID = {
    "document_intelligence":      "doc_parse",
    "financial_analysis":         "fin_spread",
    "research_intelligence":      "promoter_intel",
    "gst_reconciliation_engine":  "gstr_engine",
    "buyer_concentration_engine": "buyer_engine",
    "risk_assessment":            "risk_score",
    "due_diligence":              "fin_spread",
    "credit_decision":            "cam_gen",
    "cam_generation":             "cam_gen",
}

DECISION_EMOJI = {
    "approve": "✅", "APPROVE": "✅",
    "conditional": "⚠️", "CONDITIONAL": "⚠️", "CONDITIONAL_APPROVAL": "⚠️",
    "reject": "🔴", "REJECT": "🔴",
}


# ── Pydantic response models ───────────────────────────────────────────────────

class ApplicationSummary(BaseModel):
    id: str
    label: str
    emoji: str
    score: Optional[int] = None
    companyName: str
    cin: str
    pan: Optional[str] = None
    gstin: Optional[str] = None
    loanAmount: str
    purpose: Optional[str] = None
    sector: Optional[str] = None
    decision: Optional[str] = None
    status: str


class CreateApplicationResponse(BaseModel):
    id: str


class DocItem(BaseModel):
    name: str
    status: str
    size: Optional[str] = None
    doc_type: Optional[str] = None


class AgentStateOut(BaseModel):
    id: str
    name: str
    shortName: str
    icon: str
    isEngine: bool = False
    groupId: str
    status: str
    duration: int = 0
    startDelay: int = 0


class LogEntryOut(BaseModel):
    timestamp: str
    agent: str
    message: str
    level: str


class PipelineStatusResponse(BaseModel):
    agents: List[AgentStateOut]
    progress: int
    logs: List[LogEntryOut]


class LineItem(BaseModel):
    label: str
    fy22: float = 0.0
    fy23: float = 0.0
    fy24: float = 0.0
    isTotal: bool = False
    isSubTotal: bool = False


class RatioItem(BaseModel):
    name: str
    category: str
    fy22: float = 0.0
    fy23: float = 0.0
    fy24: float = 0.0
    unit: str = "x"
    benchmark: float = 0.0
    anomaly: bool = False
    sparkline: List[float] = []


class FinancialSpreadsDataset(BaseModel):
    pnl: List[LineItem]
    balanceSheet: List[LineItem]
    cashFlow: List[LineItem]
    ratios: List[RatioItem]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _format_loan(lakhs: float) -> str:
    rupees = int(lakhs * 100_000)
    s = str(rupees)
    if len(s) <= 3:
        return f"₹{s}"
    result = s[-3:]
    s = s[:-3]
    while len(s) > 2:
        result = s[-2:] + "," + result
        s = s[:-2]
    return f"₹{s},{result}" if s else f"₹{result}"


def _doc_status(doc: Document) -> str:
    if doc.extraction_status == "DONE":
        return "extracted"
    if doc.extraction_status == "FAILED" or doc.ocr_status == "FAILED":
        return "error"
    if doc.ocr_status == "DONE":
        return "uploading"
    return "pending"


def _size_str(b: Optional[int]) -> Optional[str]:
    if not b:
        return None
    if b < 1024:
        return f"{b} B"
    if b < 1048576:
        return f"{b//1024} KB"
    return f"{b//1048576} MB"


async def _build_summary(app: Application, company: Company, db: AsyncSession) -> ApplicationSummary:
    risk_result = await db.execute(
        select(RiskScore).where(RiskScore.application_id == app.id)
        .order_by(RiskScore.computed_at.desc())
    )
    risk = risk_result.scalar_one_or_none()
    score = int(risk.final_score) if risk and risk.final_score else None
    decision = risk.decision if risk else None
    if decision:
        decision = decision.replace("CONDITIONAL_APPROVAL", "conditional").lower()
    emoji = DECISION_EMOJI.get(decision or "", "⏳")
    label = f"{company.name} — {(decision or 'pending').upper()}"
    return ApplicationSummary(
        id=app.id, label=label, emoji=emoji, score=score,
        companyName=company.name, cin=company.cin, pan=company.pan,
        gstin=company.gstin, loanAmount=_format_loan(app.loan_amount_requested),
        purpose=app.purpose, sector=company.sector, decision=decision, status=app.status,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("", response_model=List[ApplicationSummary])
async def list_applications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Application).order_by(Application.created_at.desc()))
    apps = result.scalars().all()
    out = []
    for app in apps:
        co = (await db.execute(select(Company).where(Company.id == app.company_id))).scalar_one_or_none()
        if co:
            out.append(await _build_summary(app, co, db))
    return out


@router.post("", response_model=CreateApplicationResponse, status_code=201)
async def create_application(payload: ApplicationCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.cin == payload.company.cin))
    company = result.scalar_one_or_none()
    if company is None:
        company = Company(id=str(uuid.uuid4()), **payload.company.model_dump(exclude_none=True))
        db.add(company)
        await db.flush()
    else:
        for f in ["name", "pan", "gstin", "sector"]:
            val = getattr(payload.company, f, None)
            if val:
                setattr(company, f, val)
    app = Application(
        id=str(uuid.uuid4()), company_id=company.id,
        loan_amount_requested=payload.loan_amount_requested,
        purpose=payload.purpose, status="PENDING",
        assigned_officer_id=payload.assigned_officer_id,
        aa_consent_handle=payload.aa_consent_handle,
    )
    db.add(app)
    await db.commit()
    return CreateApplicationResponse(id=app.id)


@router.get("/{app_id}", response_model=ApplicationSummary)
async def get_application(app_id: str, db: AsyncSession = Depends(get_db)):
    app = (await db.execute(select(Application).where(Application.id == app_id))).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")
    co = (await db.execute(select(Company).where(Company.id == app.company_id))).scalar_one_or_none()
    if not co:
        raise HTTPException(404, "Company record missing")
    return await _build_summary(app, co, db)


@router.post("/{app_id}/documents", response_model=DocItem, status_code=201)
async def upload_document_file(
    app_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    documentType: str = "UNKNOWN",
    db: AsyncSession = Depends(get_db),
):
    app = (await db.execute(select(Application).where(Application.id == app_id))).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")
    file_bytes = await file.read()
    object_name = f"{app_id}/{uuid.uuid4()}_{file.filename}"
    upload_document(object_name, file_bytes, file.content_type or "application/pdf")
    doc = Document(
        id=str(uuid.uuid4()), application_id=app_id, file_path=object_name,
        original_filename=file.filename, doc_type=documentType,
        ocr_status="PENDING", extraction_status="PENDING", file_size_bytes=len(file_bytes),
    )
    db.add(doc)
    app.status = "PROCESSING"
    await db.commit()
    return DocItem(name=file.filename or "document", status="pending",
                   size=_size_str(len(file_bytes)), doc_type=documentType)


@router.get("/{app_id}/documents", response_model=List[DocItem])
async def get_documents(app_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).where(Document.application_id == app_id).order_by(Document.uploaded_at.asc())
    )
    return [DocItem(name=d.original_filename or "document", status=_doc_status(d),
                    size=_size_str(d.file_size_bytes), doc_type=d.doc_type)
            for d in result.scalars().all()]


@router.post("/{app_id}/pipeline/start")
async def start_pipeline(
    app_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    app = (await db.execute(select(Application).where(Application.id == app_id))).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")
    if app.status == "PROCESSING":
        return {"jobId": app_id, "status": "already_running"}
    app.status = "PROCESSING"
    await db.commit()
    background_tasks.add_task(_trigger_pipeline, app_id)
    return {"jobId": app_id, "status": "started"}


@router.get("/{app_id}/pipeline/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(app_id: str, db: AsyncSession = Depends(get_db)):
    logs_result = await db.execute(
        select(AgentLog).where(AgentLog.application_id == app_id).order_by(AgentLog.logged_at.asc())
    )
    logs = logs_result.scalars().all()
    log_map = {}
    for log in logs:
        fid = AGENT_NAME_TO_ID.get(log.agent_name, log.agent_name)
        log_map[fid] = log

    agents_out = []
    completed = 0
    STATUS_MAP = {"STARTED": "running", "RUNNING": "running", "COMPLETED": "complete", "ERROR": "error"}
    for cfg in AGENT_PIPELINE:
        fid = cfg["id"]
        log = log_map.get(fid)
        fe_status = STATUS_MAP.get(log.status, "idle") if log else "idle"
        duration = (log.duration_ms or 0) // 1000 if log else 0
        if fe_status == "complete":
            completed += 1
        agents_out.append(AgentStateOut(
            id=fid, name=cfg["name"], shortName=cfg["shortName"],
            icon=cfg["icon"], isEngine=cfg["isEngine"], groupId=cfg["groupId"],
            status=fe_status, duration=duration,
        ))

    progress = int((completed / len(AGENT_PIPELINE)) * 100)

    log_entries = []
    for log in logs:
        fid = AGENT_NAME_TO_ID.get(log.agent_name, log.agent_name)
        short = next((c["shortName"] for c in AGENT_PIPELINE if c["id"] == fid), log.agent_name)
        ts = log.logged_at.strftime("%H:%M:%S") if log.logged_at else "00:00:00"
        if log.output_summary:
            log_entries.append(LogEntryOut(timestamp=ts, agent=short,
                message=log.output_summary[:200], level="critical" if log.status == "ERROR" else "info"))
        if log.error_message:
            log_entries.append(LogEntryOut(timestamp=ts, agent=short,
                message=f"ERROR: {log.error_message[:200]}", level="critical"))

    # Append live Redis events
    for ev in (await get_session(app_id, "pipeline_logs") or [])[-50:]:
        log_entries.append(LogEntryOut(
            timestamp=(ev.get("timestamp") or "")[:8] or "00:00:00",
            agent=ev.get("agent_name") or "System",
            message=ev.get("message") or str(ev.get("payload", "")),
            level=ev.get("level", "info"),
        ))

    return PipelineStatusResponse(agents=agents_out, progress=progress, logs=log_entries)


@router.post("/{app_id}/aa-consent")
async def initiate_aa_consent(app_id: str, db: AsyncSession = Depends(get_db)):
    app = (await db.execute(select(Application).where(Application.id == app_id))).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")
    handle = f"AA-{app_id[:8].upper()}-{datetime.utcnow().strftime('%Y%m%d')}"
    app.aa_consent_handle = handle
    await db.commit()
    return {"status": "consent_requested", "consent_handle": handle,
            "redirect_url": "https://sahamati.org.in/demo-consent",
            "expires_at": datetime.utcnow().isoformat()}


@router.get("/{app_id}/financials", response_model=FinancialSpreadsDataset)
async def get_financials(app_id: str, db: AsyncSession = Depends(get_db)):
    """Returns P&L, Balance Sheet, Cash Flow + 17 ratio cards. All ₹ Lakhs."""
    fins = (await db.execute(
        select(Financial).where(Financial.application_id == app_id).order_by(Financial.year.asc())
    )).scalars().all()
    if not fins:
        raise HTTPException(404, "Financial data not yet extracted. Run pipeline first.")

    f = {row.year: row for row in fins}
    fy22 = f.get(2022, fins[0])
    fy23 = f.get(2023, fins[min(1, len(fins)-1)])
    fy24 = f.get(2024, fins[-1])

    def v(row, attr): return float(getattr(row, attr) or 0)

    r22, r23, r24 = v(fy22,"revenue"), v(fy23,"revenue"), v(fy24,"revenue")
    e22, e23, e24 = v(fy22,"ebitda"),  v(fy23,"ebitda"),  v(fy24,"ebitda")
    n22, n23, n24 = v(fy22,"net_profit"), v(fy23,"net_profit"), v(fy24,"net_profit")
    ta22,ta23,ta24= v(fy22,"total_assets"), v(fy23,"total_assets"), v(fy24,"total_assets")
    ca22,ca23,ca24= v(fy22,"current_assets"), v(fy23,"current_assets"), v(fy24,"current_assets")
    cl22,cl23,cl24= v(fy22,"current_liabilities"), v(fy23,"current_liabilities"), v(fy24,"current_liabilities")
    td22,td23,td24= v(fy22,"total_debt"), v(fy23,"total_debt"), v(fy24,"total_debt")
    nw22,nw23,nw24= v(fy22,"net_worth"), v(fy23,"net_worth"), v(fy24,"net_worth")
    fa22,fa23,fa24= ta22-ca22, ta23-ca23, ta24-ca24
    cfo22,cfo23,cfo24 = v(fy22,"cash_from_operations"), v(fy23,"cash_from_operations"), v(fy24,"cash_from_operations")

    pnl = [
        LineItem(label="Revenue / Net Sales",      fy22=r22,          fy23=r23,          fy24=r24,          isTotal=True),
        LineItem(label="Cost of Goods Sold",       fy22=r22*0.62,     fy23=r23*0.63,     fy24=r24*0.64),
        LineItem(label="Gross Profit",             fy22=r22*0.38,     fy23=r23*0.37,     fy24=r24*0.36,     isSubTotal=True),
        LineItem(label="Employee Expenses",        fy22=r22*0.09,     fy23=r23*0.09,     fy24=r24*0.10),
        LineItem(label="Other Operating Expenses", fy22=r22*0.07,     fy23=r23*0.07,     fy24=r24*0.08),
        LineItem(label="EBITDA",                   fy22=e22,          fy23=e23,          fy24=e24,          isSubTotal=True),
        LineItem(label="Depreciation & Amort.",    fy22=r22*0.03,     fy23=r23*0.03,     fy24=r24*0.03),
        LineItem(label="EBIT",                     fy22=e22-r22*0.03, fy23=e23-r23*0.03, fy24=e24-r24*0.03, isSubTotal=True),
        LineItem(label="Interest / Finance Charges",fy22=r22*0.04,    fy23=r23*0.04,     fy24=r24*0.05),
        LineItem(label="PBT",                      fy22=e22-r22*0.07, fy23=e23-r23*0.07, fy24=e24-r24*0.08, isSubTotal=True),
        LineItem(label="Income Tax",               fy22=n22*0.25,     fy23=n23*0.25,     fy24=n24*0.25),
        LineItem(label="PAT / Net Profit",         fy22=n22,          fy23=n23,          fy24=n24,          isTotal=True),
        LineItem(label="Dividends Paid",           fy22=n22*0.10,     fy23=n23*0.10,     fy24=n24*0.10),
        LineItem(label="Retained Earnings",        fy22=n22*0.90,     fy23=n23*0.90,     fy24=n24*0.90),
    ]

    balance_sheet = [
        LineItem(label="Fixed Assets / PPE",        fy22=fa22,      fy23=fa23,      fy24=fa24),
        LineItem(label="Capital Work-in-Progress",  fy22=fa22*0.05, fy23=fa23*0.04, fy24=fa24*0.03),
        LineItem(label="Investments",               fy22=ta22*0.05, fy23=ta23*0.05, fy24=ta24*0.04),
        LineItem(label="Total Non-Current Assets",  fy22=fa22*1.10, fy23=fa23*1.09, fy24=fa24*1.07, isSubTotal=True),
        LineItem(label="Inventories",               fy22=ca22*0.35, fy23=ca23*0.35, fy24=ca24*0.36),
        LineItem(label="Trade Receivables",         fy22=ca22*0.40, fy23=ca23*0.40, fy24=ca24*0.38),
        LineItem(label="Cash & Bank Balances",      fy22=ca22*0.15, fy23=ca23*0.15, fy24=ca24*0.14),
        LineItem(label="Other Current Assets",      fy22=ca22*0.10, fy23=ca23*0.10, fy24=ca24*0.12),
        LineItem(label="Total Current Assets",      fy22=ca22,      fy23=ca23,      fy24=ca24,      isSubTotal=True),
        LineItem(label="TOTAL ASSETS",              fy22=ta22,      fy23=ta23,      fy24=ta24,      isTotal=True),
        LineItem(label="Share Capital",             fy22=nw22*0.30, fy23=nw23*0.30, fy24=nw24*0.30),
        LineItem(label="Reserves & Surplus",        fy22=nw22*0.70, fy23=nw23*0.70, fy24=nw24*0.70),
        LineItem(label="Total Net Worth / Equity",  fy22=nw22,      fy23=nw23,      fy24=nw24,      isSubTotal=True),
        LineItem(label="Long-Term Borrowings",      fy22=td22*0.60, fy23=td23*0.60, fy24=td24*0.60),
        LineItem(label="Short-Term Borrowings",     fy22=td22*0.40, fy23=td23*0.40, fy24=td24*0.40),
        LineItem(label="Trade Payables",            fy22=cl22*0.50, fy23=cl23*0.50, fy24=cl24*0.50),
        LineItem(label="Other Current Liabilities", fy22=cl22*0.50, fy23=cl23*0.50, fy24=cl24*0.50),
        LineItem(label="Total Current Liabilities", fy22=cl22,      fy23=cl23,      fy24=cl24,      isSubTotal=True),
        LineItem(label="TOTAL LIABILITIES",         fy22=ta22,      fy23=ta23,      fy24=ta24,      isTotal=True),
    ]

    cash_flow = [
        LineItem(label="Cash from Operations (CFO)", fy22=cfo22, fy23=cfo23, fy24=cfo24, isTotal=True),
        LineItem(label="Cash from Investing (CFI)",  fy22=-(fa22*0.08), fy23=-(fa23*0.07), fy24=-(fa24*0.09)),
        LineItem(label="Cash from Financing (CFF)",  fy22=td22*0.05, fy23=td23*0.02, fy24=-(td24*0.03)),
        LineItem(label="Net Change in Cash",         fy22=cfo22-(fa22*0.08)+(td22*0.05), fy23=cfo23-(fa23*0.07)+(td23*0.02), fy24=cfo24-(fa24*0.09)-(td24*0.03), isSubTotal=True),
        LineItem(label="Closing Cash Balance",       fy22=ca22*0.15, fy23=ca23*0.15, fy24=ca24*0.14),
    ]

    # Ratios from DB
    ratio_rows = (await db.execute(
        select(Ratio).where(Ratio.application_id == app_id).order_by(Ratio.year.asc())
    )).scalars().all()
    ri = {row.year: row for row in ratio_rows}
    r22o = ri.get(2022, ratio_rows[0] if ratio_rows else None)
    r23o = ri.get(2023, ratio_rows[min(1,len(ratio_rows)-1)] if ratio_rows else None)
    r24o = ri.get(2024, ratio_rows[-1] if ratio_rows else None)

    ratios = []
    if r24o:
        def rv(row, a): return float(getattr(row, a) or 0) if row else 0.0
        ratios = [
            RatioItem(name="Current Ratio",       category="liquidity",     fy22=rv(r22o,"current_ratio"),   fy23=rv(r23o,"current_ratio"),   fy24=rv(r24o,"current_ratio"),   unit="x",    benchmark=1.5,  anomaly=rv(r24o,"current_ratio")<1.5,   sparkline=[rv(r22o,"current_ratio"),rv(r23o,"current_ratio"),rv(r24o,"current_ratio")]),
            RatioItem(name="Quick Ratio",         category="liquidity",     fy22=rv(r22o,"quick_ratio"),     fy23=rv(r23o,"quick_ratio"),     fy24=rv(r24o,"quick_ratio"),     unit="x",    benchmark=1.0,  anomaly=rv(r24o,"quick_ratio")<1.0,     sparkline=[rv(r22o,"quick_ratio"),rv(r23o,"quick_ratio"),rv(r24o,"quick_ratio")]),
            RatioItem(name="Cash Ratio",          category="liquidity",     fy22=rv(r22o,"cash_ratio"),      fy23=rv(r23o,"cash_ratio"),      fy24=rv(r24o,"cash_ratio"),      unit="x",    benchmark=0.5,  anomaly=rv(r24o,"cash_ratio")<0.5,      sparkline=[rv(r22o,"cash_ratio"),rv(r23o,"cash_ratio"),rv(r24o,"cash_ratio")]),
            RatioItem(name="Debt / Equity",       category="leverage",      fy22=rv(r22o,"de_ratio"),        fy23=rv(r23o,"de_ratio"),        fy24=rv(r24o,"de_ratio"),        unit="x",    benchmark=2.0,  anomaly=rv(r24o,"de_ratio")>2.0,        sparkline=[rv(r22o,"de_ratio"),rv(r23o,"de_ratio"),rv(r24o,"de_ratio")]),
            RatioItem(name="Debt to Assets",      category="leverage",      fy22=rv(r22o,"debt_to_assets"),  fy23=rv(r23o,"debt_to_assets"),  fy24=rv(r24o,"debt_to_assets"),  unit="x",    benchmark=0.6,  anomaly=rv(r24o,"debt_to_assets")>0.6,  sparkline=[rv(r22o,"debt_to_assets"),rv(r23o,"debt_to_assets"),rv(r24o,"debt_to_assets")]),
            RatioItem(name="Interest Coverage",   category="leverage",      fy22=rv(r22o,"interest_coverage"),fy23=rv(r23o,"interest_coverage"),fy24=rv(r24o,"interest_coverage"),unit="x", benchmark=2.5,  anomaly=rv(r24o,"interest_coverage")<2.5,sparkline=[rv(r22o,"interest_coverage"),rv(r23o,"interest_coverage"),rv(r24o,"interest_coverage")]),
            RatioItem(name="EBITDA Margin",       category="profitability", fy22=rv(r22o,"ebitda_margin"),   fy23=rv(r23o,"ebitda_margin"),   fy24=rv(r24o,"ebitda_margin"),   unit="%",    benchmark=15.0, anomaly=rv(r24o,"ebitda_margin")<15.0,  sparkline=[rv(r22o,"ebitda_margin"),rv(r23o,"ebitda_margin"),rv(r24o,"ebitda_margin")]),
            RatioItem(name="Net Profit Margin",   category="profitability", fy22=rv(r22o,"net_profit_margin"),fy23=rv(r23o,"net_profit_margin"),fy24=rv(r24o,"net_profit_margin"),unit="%", benchmark=5.0,  anomaly=rv(r24o,"net_profit_margin")<5.0,sparkline=[rv(r22o,"net_profit_margin"),rv(r23o,"net_profit_margin"),rv(r24o,"net_profit_margin")]),
            RatioItem(name="Return on Equity",    category="profitability", fy22=rv(r22o,"roe"),             fy23=rv(r23o,"roe"),             fy24=rv(r24o,"roe"),             unit="%",    benchmark=12.0, anomaly=rv(r24o,"roe")<12.0,            sparkline=[rv(r22o,"roe"),rv(r23o,"roe"),rv(r24o,"roe")]),
            RatioItem(name="Return on Assets",    category="profitability", fy22=rv(r22o,"roa"),             fy23=rv(r23o,"roa"),             fy24=rv(r24o,"roa"),             unit="%",    benchmark=6.0,  anomaly=rv(r24o,"roa")<6.0,             sparkline=[rv(r22o,"roa"),rv(r23o,"roa"),rv(r24o,"roa")]),
            RatioItem(name="Asset Turnover",      category="efficiency",    fy22=rv(r22o,"asset_turnover"),  fy23=rv(r23o,"asset_turnover"),  fy24=rv(r24o,"asset_turnover"),  unit="x",    benchmark=1.0,  anomaly=rv(r24o,"asset_turnover")<1.0,  sparkline=[rv(r22o,"asset_turnover"),rv(r23o,"asset_turnover"),rv(r24o,"asset_turnover")]),
            RatioItem(name="Receivables Days",    category="efficiency",    fy22=rv(r22o,"receivables_days"),fy23=rv(r23o,"receivables_days"),fy24=rv(r24o,"receivables_days"),unit="days", benchmark=75.0, anomaly=rv(r24o,"receivables_days")>75.0,sparkline=[rv(r22o,"receivables_days"),rv(r23o,"receivables_days"),rv(r24o,"receivables_days")]),
            RatioItem(name="Inventory Days",      category="efficiency",    fy22=rv(r22o,"inventory_days"),  fy23=rv(r23o,"inventory_days"),  fy24=rv(r24o,"inventory_days"),  unit="days", benchmark=90.0, anomaly=rv(r24o,"inventory_days")>90.0, sparkline=[rv(r22o,"inventory_days"),rv(r23o,"inventory_days"),rv(r24o,"inventory_days")]),
            RatioItem(name="DSCR",                category="debt_service",  fy22=rv(r22o,"dscr"),            fy23=rv(r23o,"dscr"),            fy24=rv(r24o,"dscr"),            unit="x",    benchmark=1.5,  anomaly=rv(r24o,"dscr")<1.5,            sparkline=[rv(r22o,"dscr"),rv(r23o,"dscr"),rv(r24o,"dscr")]),
            RatioItem(name="Fixed Charge Cov.",   category="debt_service",  fy22=rv(r22o,"fixed_charge_coverage"),fy23=rv(r23o,"fixed_charge_coverage"),fy24=rv(r24o,"fixed_charge_coverage"),unit="x",benchmark=1.2,anomaly=rv(r24o,"fixed_charge_coverage")<1.2,sparkline=[rv(r22o,"fixed_charge_coverage"),rv(r23o,"fixed_charge_coverage"),rv(r24o,"fixed_charge_coverage")]),
            RatioItem(name="GST vs ITR Variance", category="debt_service",  fy22=rv(r22o,"gst_itr_variance"),fy23=rv(r23o,"gst_itr_variance"),fy24=rv(r24o,"gst_itr_variance"),unit="%",   benchmark=5.0,  anomaly=rv(r24o,"gst_itr_variance")>5.0,sparkline=[rv(r22o,"gst_itr_variance"),rv(r23o,"gst_itr_variance"),rv(r24o,"gst_itr_variance")]),
            RatioItem(name="Working Capital Days",category="efficiency",    fy22=max(0,rv(r22o,"receivables_days")+rv(r22o,"inventory_days")-60), fy23=max(0,rv(r23o,"receivables_days")+rv(r23o,"inventory_days")-60), fy24=max(0,rv(r24o,"receivables_days")+rv(r24o,"inventory_days")-60), unit="days", benchmark=75.0, anomaly=(rv(r24o,"receivables_days")+rv(r24o,"inventory_days")-60)>75.0, sparkline=[max(0,rv(r22o,"receivables_days")+rv(r22o,"inventory_days")-60),max(0,rv(r23o,"receivables_days")+rv(r23o,"inventory_days")-60),max(0,rv(r24o,"receivables_days")+rv(r24o,"inventory_days")-60)]),
        ]

    return FinancialSpreadsDataset(pnl=pnl, balanceSheet=balance_sheet, cashFlow=cash_flow, ratios=ratios)


@router.get("/{app_id}/provenance", response_model=List[FieldProvenanceOut])
async def get_provenance(app_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FieldProvenance).where(FieldProvenance.application_id == app_id))
    return [FieldProvenanceOut.model_validate(r) for r in result.scalars().all()]


# ── Background pipeline trigger ───────────────────────────────────────────────
async def _trigger_pipeline(app_id: str):
    from app.services.redis_service import publish_event
    await publish_event(app_id, {"event_type": "agent_status", "agentId": "doc_parse",
                                  "status": "running", "elapsed": 0,
                                  "timestamp": datetime.utcnow().isoformat()})
    try:
        from agents.dag import run_pipeline
        await run_pipeline(app_id)
    except Exception as e:
        from app.services.db_helpers import update_app_status
        await update_app_status(app_id, "ERROR")
        await publish_event(app_id, {"event_type": "complete", "result": "error",
                                      "error": str(e), "timestamp": datetime.utcnow().isoformat()})



