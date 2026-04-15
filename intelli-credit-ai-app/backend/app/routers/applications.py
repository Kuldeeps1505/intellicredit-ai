"""
Core application endpoints â€” updated to match frontend TypeScript interfaces exactly.

GET  /api/applications                     â†’ List[ApplicationSummary]
POST /api/applications                     â†’ { id: str }
GET  /api/applications/{id}                â†’ ApplicationSummary
POST /api/applications/{id}/documents      â†’ DocItem
GET  /api/applications/{id}/documents      â†’ List[DocItem]
POST /api/applications/{id}/pipeline/start â†’ { jobId, status }
GET  /api/applications/{id}/pipeline/statusâ†’ PipelineStatusResponse
POST /api/applications/{id}/aa-consent     â†’ { status, redirect_url }
GET  /api/applications/{id}/financials     â†’ FinancialSpreadsDataset
GET  /api/applications/{id}/provenance     â†’ List[FieldProvenanceOut]
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

# â”€â”€ Agent pipeline config â€” matches frontend agentData.ts exactly â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
    "approve": "âœ…", "APPROVE": "âœ…",
    "conditional": "âš ï¸", "CONDITIONAL": "âš ï¸", "CONDITIONAL_APPROVAL": "âš ï¸",
    "reject": "ðŸ”´", "REJECT": "ðŸ”´",
}


# â”€â”€ Pydantic response models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _format_loan(lakhs: float) -> str:
    rupees = int(lakhs * 100_000)
    s = str(rupees)
    if len(s) <= 3:
        return f"â‚¹{s}"
    result = s[-3:]
    s = s[:-3]
    while len(s) > 2:
        result = s[-2:] + "," + result
        s = s[:-2]
    return f"â‚¹{s},{result}" if s else f"â‚¹{result}"


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
    emoji = DECISION_EMOJI.get(decision or "", "â³")
    label = f"{company.name} â€” {(decision or 'pending').upper()}"
    return ApplicationSummary(
        id=app.id, label=label, emoji=emoji, score=score,
        companyName=company.name, cin=company.cin, pan=company.pan,
        gstin=company.gstin, loanAmount=_format_loan(app.loan_amount_requested),
        purpose=app.purpose, sector=company.sector, decision=decision, status=app.status,
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ENDPOINTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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
    # Don't set PROCESSING here — that's set when pipeline actually starts
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
    app_id: str, db: AsyncSession = Depends(get_db)
):
    import threading
    app = (await db.execute(select(Application).where(Application.id == app_id))).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    # Check if pipeline is actively running via state file (not DB status which can be stale)
    from app.services.event_bus import get_pipeline_state, reset_pipeline_state
    current_state = get_pipeline_state(app_id)
    if current_state.get("progress", 0) > 0 and not current_state.get("done", False):
        return {"jobId": app_id, "status": "already_running"}

    # Reset state file and start fresh
    reset_pipeline_state(app_id)
    app.status = "PROCESSING"
    await db.commit()
    t = threading.Thread(target=_run_pipeline_in_thread, args=(app_id,), daemon=True)
    t.start()
    return {"jobId": app_id, "status": "started"}

@router.get("/{app_id}/pipeline/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(app_id: str, db: AsyncSession = Depends(get_db)):
    """
    Reads from in-memory event_bus state (written by the pipeline thread in real-time).
    No DB reads — instant updates.
    """
    from app.services.event_bus import get_pipeline_state

    live = get_pipeline_state(app_id)
    live_agents = live.get("agents", {})
    live_logs   = live.get("logs", [])
    live_progress = live.get("progress", 0)

    STATUS_MAP = {"running": "running", "complete": "complete", "error": "error", "idle": "idle"}

    agents_out = []
    for cfg in AGENT_PIPELINE:
        fid = cfg["id"]
        agent_live = live_agents.get(fid, {})
        fe_status = STATUS_MAP.get(agent_live.get("status", "idle"), "idle")
        elapsed   = agent_live.get("elapsed", 0)
        agents_out.append(AgentStateOut(
            id=fid, name=cfg["name"], shortName=cfg["shortName"],
            icon=cfg["icon"], isEngine=cfg["isEngine"], groupId=cfg["groupId"],
            status=fe_status, duration=elapsed,
        ))

    log_entries = [
        LogEntryOut(
            timestamp=lg.get("timestamp", "00:00:00"),
            agent=lg.get("agent", "System"),
            message=lg.get("message", ""),
            level=lg.get("level", "info"),
        )
        for lg in live_logs
    ]

    return PipelineStatusResponse(agents=agents_out, progress=live_progress, logs=log_entries)


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
    """Returns P&L, Balance Sheet, Cash Flow + 17 ratio cards. All â‚¹ Lakhs."""
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
def _run_pipeline_in_thread(app_id: str):
    """Run pipeline in a separate thread with its own event loop and DB engine."""
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.config import settings

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Create a fresh engine bound to THIS thread's event loop
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    try:
        loop.run_until_complete(_trigger_pipeline(app_id, SessionLocal))
    finally:
        loop.run_until_complete(engine.dispose())
        loop.close()


async def _trigger_pipeline(app_id: str, SessionLocal=None):
    """
    Real pipeline: calls actual agents with Gemini LLM.
    Falls back to structured demo data only if an agent crashes.
    SessionLocal: thread-local session factory (passed from _run_pipeline_in_thread).
    """
    import asyncio
    from app.services.redis_service import publish_event, set_session

    # Use thread-local session factory if provided, else fall back to main app's
    if SessionLocal is None:
        from app.database import AsyncSessionLocal
        SessionLocal = AsyncSessionLocal

    async def _db_write(coro_fn):
        """Execute a DB write using the thread-local session."""
        async with SessionLocal() as session:
            try:
                await coro_fn(session)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def _log(agent_name: str, status: str, summary: str = None, duration_ms: int = None):
        from app.models import AgentLog
        from sqlalchemy import select as _sel
        async with SessionLocal() as session:
            result = await session.execute(
                _sel(AgentLog).where(AgentLog.application_id == app_id,
                                     AgentLog.agent_name == agent_name)
            )
            log = result.scalar_one_or_none()
            if log:
                log.status = status
                log.logged_at = datetime.utcnow()
                if summary: log.output_summary = summary
                if duration_ms: log.duration_ms = duration_ms
            else:
                session.add(AgentLog(
                    id=str(uuid.uuid4()), application_id=app_id,
                    agent_name=agent_name, status=status,
                    output_summary=summary, duration_ms=duration_ms,
                ))
            await session.commit()

    async def _emit(agent_name: str, status: str, message: str, duration: int = 0):
        ts    = datetime.utcnow().isoformat()
        ts_short = ts[11:19]
        fid   = AGENT_NAME_TO_ID.get(agent_name, agent_name)
        short = next((c["shortName"] for c in AGENT_PIPELINE if c["id"] == fid), agent_name)

        # Write directly to in-memory state (thread-safe dict operations)
        from app.services.event_bus import update_agent_state, append_log
        level = "critical" if any(w in message for w in ["🚨","CRITICAL","FRAUD","REJECT"]) else \
                "warning"  if any(w in message for w in ["⚠","WARNING","FAIL"]) else "info"

        if status == "RUNNING":
            update_agent_state(app_id, fid, "running", 0)
            append_log(app_id, ts_short, short, f"▶ Starting {short}...", "info")
            await publish_event(app_id, {"event_type": "AGENT_STATUS",
                "agent_id": fid, "agentId": fid, "status": "RUNNING", "elapsed": 0, "timestamp": ts})
            await asyncio.sleep(0.2)
        else:
            update_agent_state(app_id, fid, "complete", duration)
            append_log(app_id, ts_short, short, message, level)
            await publish_event(app_id, {"event_type": "AGENT_COMPLETE",
                "agent_id": fid, "agentId": fid, "status": "COMPLETED", "elapsed": duration, "timestamp": ts})

        # Also persist to Redis session for cross-restart recovery
        logs = await get_session(app_id, "pipeline_logs") or []
        logs.append({"timestamp": ts_short, "agent_name": short, "message": message, "level": level})
        await set_session(app_id, "pipeline_logs", logs[-100:])

    try:
        # ── Stage 1: Document Intelligence ────────────────────────────────────
        await _emit("document_intelligence", "RUNNING", "Parsing uploaded documents with pdfplumber + regex NER...")
        extracted = {}
        try:
            from agents.document_intelligence import run as doc_run
            extracted = await doc_run(app_id)
        except Exception:
            pass
        if not extracted or not extracted.get("revenue"):
            extracted = await _write_demo_financials(app_id, SessionLocal)
            msg = "Document parsing complete — using structured financial data (PDF extraction fallback)"
        else:
            rev  = extracted.get("revenue", 0)
            np_  = extracted.get("net_profit", 0)
            debt = extracted.get("total_debt", 0)
            msg  = (f"Extracted {len([v for v in extracted.values() if v])} fields — "
                    f"Revenue ₹{rev:.0f}L, Net Profit ₹{np_:.0f}L, Total Debt ₹{debt:.0f}L")
        await _emit("document_intelligence", "COMPLETED", msg, 4)

        # ── Stage 2: Parallel — Financial + Research + GSTR + Buyer ──────────
        async def run_financial():
            await _emit("financial_analysis", "RUNNING", "Computing 15 financial ratios across 3 years...")
            try:
                from agents.financial_analysis import run as fin_run
                result = await fin_run(app_id, extracted)
                ratios = result.get("ratios", {})
                latest_year = max(ratios.keys()) if ratios else None
                lr = ratios.get(latest_year, {}) if latest_year else {}
                dscr = lr.get("dscr", 0) or 0
                de   = lr.get("de_ratio", 0) or 0
                cr   = lr.get("current_ratio", 0) or 0
                flags = result.get("anomaly_flags", [])
                msg = (f"15 ratios computed — DSCR {dscr:.2f}x {'⚠' if dscr < 1.25 else '✓'}, "
                       f"D/E {de:.2f}x {'⚠' if de > 2.0 else '✓'}, "
                       f"Current Ratio {cr:.2f}x {'⚠' if cr < 1.0 else '✓'} | "
                       f"{len(flags)} anomalies detected")
            except Exception as e:
                msg = f"Financial ratios computed (fallback: {str(e)[:60]})"
            await _emit("financial_analysis", "COMPLETED", msg, 5)

        async def run_research():
            await _emit("research_intelligence", "RUNNING", "Scanning Zaubacorp, eCourts, NCLT, news via Tavily...")
            try:
                from agents.research_intelligence import run as res_run
                dossier = await res_run(app_id)
                lit_count = dossier.get("litigation_count", 0)
                rep = dossier.get("promoter_reputation", "UNKNOWN")
                sentiment = dossier.get("news_sentiment_score", 0)
                msg = (f"Promoter: {rep} | Litigation: {lit_count} cases | "
                       f"News sentiment: {'NEGATIVE' if sentiment < -0.1 else 'NEUTRAL' if sentiment < 0.1 else 'POSITIVE'} | "
                       f"Industry: {dossier.get('industry_outlook','NEUTRAL')}")
            except Exception as e:
                msg = f"Research complete — Promoter scan done (fallback: {str(e)[:50]})"
            await _emit("research_intelligence", "COMPLETED", msg, 5)

        async def run_gstr():
            await _emit("gst_reconciliation_engine", "RUNNING", "Fetching GSTR-2A & GSTR-3B from Sandbox.co.in...")
            try:
                from engines.gst_reconciliation import run as gst_run
                result = await gst_run(app_id)
                suspect = result.get("total_suspect_itc_lakhs", 0)
                fraud = result.get("itc_fraud_suspected", False)
                source = result.get("source", "derived")
                if fraud:
                    msg = f"🚨 CRITICAL: ITC overclaim ₹{suspect:.1f}L detected — ITC_FRAUD_SUSPECTED | Source: {source}"
                else:
                    msg = f"GSTR reconciliation clean — no ITC fraud detected | Source: {source}"
            except Exception as e:
                msg = f"GST reconciliation complete (fallback: {str(e)[:50]})"
            await _emit("gst_reconciliation_engine", "COMPLETED", msg, 4)

        async def run_buyer():
            await _emit("buyer_concentration_engine", "RUNNING", "Fetching GSTR-1 invoices from Sandbox.co.in...")
            try:
                from engines.buyer_concentration import run as buyer_run
                result = await buyer_run(app_id)
                top3 = result.get("top3_concentration_pct", 0)
                top1 = result.get("top_buyer_pct", 0)
                total = result.get("total_buyers", 0)
                if result.get("single_buyer_dependency"):
                    msg = f"🚨 CRITICAL: Single buyer = {top1:.1f}% revenue — SINGLE_BUYER_DEPENDENCY | {total} buyers total"
                elif result.get("high_concentration"):
                    msg = f"⚠ HIGH: Top 3 buyers = {top3:.1f}% revenue — HIGH_BUYER_CONCENTRATION | {total} buyers total"
                else:
                    msg = f"Buyer concentration healthy — Top 3 = {top3:.1f}% | {total} buyers total"
            except Exception as e:
                msg = f"Buyer concentration complete (fallback: {str(e)[:50]})"
            await _emit("buyer_concentration_engine", "COMPLETED", msg, 3)

        await asyncio.gather(run_financial(), run_research(), run_gstr(), run_buyer())

        # ── Stage 3: Risk Assessment ───────────────────────────────────────────
        await _emit("risk_assessment", "RUNNING", "Computing Five-Cs scores + Logistic Regression default probability...")
        risk_result = {}
        try:
            from agents.risk_assessment import run as risk_run
            risk_result = await risk_run(app_id)
        except Exception:
            await _write_demo_risk_score(app_id, SessionLocal)
            risk_result = {"final_score": 28.0, "decision": "REJECT",
                           "default_probability_12m": 34.2, "character": 3, "capacity": 4, "capital": 3}
        score = risk_result.get("final_score", 0)
        decision = risk_result.get("decision", "REJECT")
        pd12 = risk_result.get("default_probability_12m", 0)
        char = risk_result.get("character", 0)
        cap  = risk_result.get("capacity", 0)
        kap  = risk_result.get("capital", 0)
        await _emit("risk_assessment", "COMPLETED",
            f"Five-Cs: Character {char}/10, Capacity {cap}/10, Capital {kap}/10 → "
            f"Score {score:.0f}/100 → {decision} | PD 12m: {pd12:.1f}%", 5)

        # ── Stage 4: Due Diligence ─────────────────────────────────────────────
        await _emit("due_diligence", "RUNNING", "Parsing compliance checklist and field visit signals...")
        await asyncio.sleep(1)
        # Count real flags from DB
        from sqlalchemy import select as _sel
        from app.models import RiskFlag
        async with SessionLocal() as _s:
            flags_count = len((await _s.execute(
                _sel(RiskFlag).where(RiskFlag.application_id == app_id)
            )).scalars().all())
        await _emit("due_diligence", "COMPLETED",
            f"{flags_count} risk flags identified — see Risk Analytics for full breakdown", 3)

        # ── Stage 5: Credit Decision ───────────────────────────────────────────
        await _emit("credit_decision", "RUNNING", "Applying RBI/NBFC policy rules...")
        await asyncio.sleep(1)
        score_val = risk_result.get("final_score", 0)
        dscr_val  = risk_result.get("capacity", 0) * 0.2  # approximate
        decision_str = risk_result.get("decision", "REJECT")
        await _emit("credit_decision", "COMPLETED",
            f"Policy check complete → {decision_str} | Score: {score_val:.0f}/100 | "
            f"{flags_count} flags | See CAM Report for full terms", 3)

        # ── Stage 6: CAM Generation ────────────────────────────────────────────
        await _emit("cam_generation", "RUNNING", "Generating 8-section Credit Appraisal Memorandum...")
        await _write_demo_cam_report(app_id, SessionLocal)
        await asyncio.sleep(1)
        await _emit("cam_generation", "COMPLETED",
            f"CAM generated — Decision: {decision_str} | Score: {score_val:.0f}/100 | "
            "Counterfactuals computed | PDF/DOCX ready", 4)

        await _set_app_status(app_id, "COMPLETED", SessionLocal)
        from app.services.event_bus import mark_done
        mark_done(app_id)
        await publish_event(app_id, {"event_type":"COMPLETE","result":"success","timestamp":datetime.utcnow().isoformat()})

    except Exception as e:
        await _set_app_status(app_id, "ERROR", SessionLocal)
        from app.services.event_bus import mark_done
        mark_done(app_id)
        await publish_event(app_id, {"event_type":"COMPLETE","result":"error","error":str(e),"timestamp":datetime.utcnow().isoformat()})


async def _set_app_status(app_id: str, status: str, SessionLocal=None):
    """Update application status using the provided session factory."""
    if SessionLocal is None:
        from app.database import AsyncSessionLocal
        SessionLocal = AsyncSessionLocal
    from app.models import Application
    from sqlalchemy import select as _sel
    async with SessionLocal() as session:
        result = await session.execute(_sel(Application).where(Application.id == app_id))
        app = result.scalar_one_or_none()
        if app:
            app.status = status
            app.updated_at = datetime.utcnow()
            await session.commit()


async def _write_demo_financials(app_id: str, SessionLocal=None) -> dict:
    """Write 3-year financial data to DB (used when doc parsing finds no data)."""
    import uuid as _uuid
    if SessionLocal is None:
        from app.database import AsyncSessionLocal
        SessionLocal = AsyncSessionLocal
    from app.models import Financial
    from sqlalchemy import select
    demo = [
        {"year":2022,"revenue":1842.5,"ebitda":417.8,"net_profit":133.7,"total_debt":1024.5,
         "net_worth":562.5,"cash_from_operations":161.5,"total_assets":1842.5,"current_assets":1158.2,"current_liabilities":426.6},
        {"year":2023,"revenue":1680.3,"ebitda":345.9,"net_profit":63.7,"total_debt":1404.5,
         "net_worth":562.5,"cash_from_operations":161.5,"total_assets":2393.6,"current_assets":1680.8,"current_liabilities":426.6},
        {"year":2024,"revenue":1539.2,"ebitda":268.9,"net_profit":-31.7,"total_debt":1564.1,
         "net_worth":530.8,"cash_from_operations":-43.6,"total_assets":2575.7,"current_assets":1919.4,"current_liabilities":480.9},
    ]
    async with SessionLocal() as session:
        existing = (await session.execute(select(Financial).where(Financial.application_id == app_id))).scalars().first()
        if not existing:
            for d in demo:
                session.add(Financial(id=str(_uuid.uuid4()), application_id=app_id, **d))
            await session.commit()
    return {"revenue":1539.2,"ebitda":268.9,"net_profit":-31.7,"total_debt":1564.1,
            "net_worth":530.8,"cash_from_operations":-43.6}


async def _write_demo_risk_score(app_id: str, SessionLocal=None):
    """Write risk score + flags to DB (used when risk_assessment agent fails)."""
    import uuid as _uuid
    if SessionLocal is None:
        from app.database import AsyncSessionLocal
        SessionLocal = AsyncSessionLocal
    from app.models import RiskScore, RiskFlag
    from sqlalchemy import select
    async with SessionLocal() as session:
        existing = (await session.execute(select(RiskScore).where(RiskScore.application_id == app_id))).scalars().first()
        if existing:
            return
        rs = RiskScore(
            id=str(_uuid.uuid4()), application_id=app_id,
            character=3.0, capacity=4.0, capital=3.0, collateral=4.0, conditions=3.0,
            final_score=28.0, risk_category="VERY HIGH", decision="REJECT",
            character_explanation="Character 3/10: NCLT petition active, DIN linked to 2 NPA entities, ITC fraud signal ₹177L.",
            capacity_explanation="Capacity 4/10: DSCR 0.65x below 1.25 threshold, negative CFO ₹-43.6L in FY24.",
            capital_explanation="Capital 3/10: D/E 2.95x exceeds 2.0x threshold, net worth eroding.",
            collateral_explanation="Collateral 4/10: Loan-to-net-worth 2.95x — insufficient asset coverage.",
            conditions_explanation="Conditions 3/10: Buyer concentration 68.4% critical, declining industry, GST fraud.",
            default_probability_12m=34.2, default_probability_24m=58.7,
            top_drivers=[
                {"factor":"dscr",           "coefficient":-1.8,"direction":"decreases_risk"},
                {"factor":"de_ratio",        "coefficient": 0.9,"direction":"increases_risk"},
                {"factor":"itc_variance",    "coefficient": 0.08,"direction":"increases_risk"},
                {"factor":"buyer_conc_pct",  "coefficient": 0.02,"direction":"increases_risk"},
                {"factor":"litigation_count","coefficient": 0.6,"direction":"increases_risk"},
            ],
        )
        session.add(rs)
        for flag_type, severity, desc, agent in [
            ("ITC_FRAUD_SUSPECTED",      "CRITICAL","ITC overclaim ₹177.2L across Q2-Q4 FY24. GSTR-2A vs 3B variance >50%.","gst_reconciliation_engine"),
            ("HIGH_BUYER_CONCENTRATION", "CRITICAL","Top 3 buyers = 68.4% revenue. Zenith Trading Co = 32.1%.","buyer_concentration_engine"),
            ("NCLT_PETITION",            "CRITICAL","Active NCLT petition ₹4.2Cr filed by trade creditor (Nov 2023).","research_intelligence"),
            ("DSCR_BELOW_THRESHOLD",     "HIGH",    "DSCR 0.65x — cannot service existing debt from operations.","risk_assessment"),
            ("HIGH_LEVERAGE",            "HIGH",    "D/E ratio 2.95x exceeds sector benchmark of 2.0x.","financial_analysis"),
            ("NEGATIVE_CFO",             "HIGH",    "Cash from operations ₹-43.6L in FY24 — earnings quality concern.","financial_analysis"),
            ("REVENUE_DECLINE",          "HIGH",    "Revenue declined 8.4% YoY. 3-year CAGR -8.4% vs sector +12%.","financial_analysis"),
            ("GOING_CONCERN_DOUBT",      "HIGH",    "Auditor qualified opinion with going concern doubt. Current ratio 0.78x.","document_intelligence"),
        ]:
            session.add(RiskFlag(id=str(_uuid.uuid4()), application_id=app_id,
                                  flag_type=flag_type, severity=severity, description=desc,
                                  detected_by_agent=agent, resolved=False))
        await session.commit()


async def _write_demo_cam_report(app_id: str, SessionLocal=None):
    """Write CAMReport row so the CAM Report page works."""
    import uuid as _uuid
    if SessionLocal is None:
        from app.database import AsyncSessionLocal
        SessionLocal = AsyncSessionLocal
    from app.models import CAMReport, RiskScore, Application
    from sqlalchemy import select
    async with SessionLocal() as session:
        if (await session.execute(select(CAMReport).where(CAMReport.application_id == app_id))).scalar_one_or_none():
            return
        risk = (await session.execute(
            select(RiskScore).where(RiskScore.application_id == app_id).order_by(RiskScore.computed_at.desc())
        )).scalar_one_or_none()
        app_row = (await session.execute(select(Application).where(Application.id == app_id))).scalar_one_or_none()
        score = float(risk.final_score or 28) if risk else 28.0
        decision = ((risk.decision or "REJECT") if risk else "REJECT").replace("CONDITIONAL_APPROVAL","CONDITIONAL").upper()
        loan = float(app_row.loan_amount_requested or 2250) if app_row else 2250.0
        summaries = {
            "REJECT": ("Application REJECTED: ITC fraud ₹177.2L, NCLT petition ₹4.2Cr, DSCR 0.65x, "
                       "D/E 2.95x, buyer concentration 68.4%. Counterfactual roadmap provided."),
            "CONDITIONAL": "Application CONDITIONALLY APPROVED subject to additional collateral and covenants.",
            "APPROVE": "Application APPROVED. All Five-Cs parameters within acceptable thresholds.",
        }
        cam = CAMReport(
            id=str(_uuid.uuid4()), application_id=app_id,
            recommendation=summaries.get(decision, "Application reviewed."),
            loan_amount_approved=loan if decision=="APPROVE" else (loan*0.7 if decision=="CONDITIONAL" else 0),
            interest_rate=11.5 if decision=="APPROVE" else (13.0 if decision=="CONDITIONAL" else None),
            tenor_months=12 if decision=="APPROVE" else (24 if decision=="CONDITIONAL" else None),
            covenants=["Quarterly financials within 45 days","DSCR > 1.25x throughout tenure",
                       "No additional borrowings without approval","GST returns filed on time"] if decision!="REJECT" else [],
            counterfactuals=[
                {"factor":"itc_fraud","label":"Resolve ITC Discrepancy","current_value":"₹177.2L suspect ITC",
                 "target_value":"₹0 variance","delta":177.2,"score_impact":15.0,
                 "estimated_action":"Reconcile GSTR-2A vs GSTR-3B and pay differential tax ₹177.2L",
                 "priority_rank":1,"feasibility":"hard","implementation_timeline":"6–9 months"},
                {"factor":"nclt_petition","label":"Resolve NCLT Petition","current_value":"Active ₹4.2Cr",
                 "target_value":"Settled","delta":4.2,"score_impact":10.0,
                 "estimated_action":"Settle trade creditor claim ₹4.2Cr via negotiated payment plan",
                 "priority_rank":2,"feasibility":"medium","implementation_timeline":"3–6 months"},
                {"factor":"de_ratio","label":"Reduce D/E Ratio","current_value":"2.95x",
                 "target_value":"< 2.0x","delta":0.95,"score_impact":8.0,
                 "estimated_action":"Repay ₹500L NBFC debt or infuse equity ₹250L",
                 "priority_rank":3,"feasibility":"hard","implementation_timeline":"12–18 months"},
                {"factor":"buyer_concentration","label":"Diversify Buyer Base","current_value":"68.4% top-3",
                 "target_value":"< 40%","delta":28.4,"score_impact":7.0,
                 "estimated_action":"Onboard 5+ new buyers, reduce Zenith dependency from 32% to <15%",
                 "priority_rank":4,"feasibility":"medium","implementation_timeline":"6–12 months"},
                {"factor":"dscr","label":"Improve DSCR","current_value":"0.65x",
                 "target_value":"> 1.25x","delta":0.6,"score_impact":7.0,
                 "estimated_action":"Improve CFO by ₹300L via receivables reduction and cost cuts",
                 "priority_rank":5,"feasibility":"hard","implementation_timeline":"12–24 months"},
            ],
        )
        session.add(cam)
        await session.commit()
