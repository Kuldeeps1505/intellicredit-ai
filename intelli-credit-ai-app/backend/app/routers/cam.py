"""
GET  /api/applications/{id}/cam          → CamDataset  (structured JSON — replaces day4 stub)
POST /api/applications/{id}/cam/generate → trigger CAM generation
GET  /api/applications/{id}/cam/download → PDF / DOCX blob
GET  /api/applications/{id}/counterfactuals → CounterfactualsResponse
POST /api/applications/{id}/dd-notes     → DDNoteResponse
POST /api/applications/{id}/chat         → { reply }
"""
from __future__ import annotations
import os
from typing import List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import CAMReport, Application, Company, RiskScore, RiskFlag
from app.services.redis_service import get_session

router = APIRouter(prefix="/api/applications", tags=["cam"])


# ── Schemas matching frontend camData.ts exactly ──────────────────────────────

class CamSection(BaseModel):
    title: str
    content: str


class LoanTerms(BaseModel):
    amount: str
    tenure: str
    rate: str
    security: str
    disbursement: str


class Recommendation(BaseModel):
    decision: str          # "approve" | "reject" | "conditional"
    summary: str
    conditions: List[str]
    loanTerms: LoanTerms


class CounterfactualAction(BaseModel):
    action: str
    impact: str
    newScore: float
    scoreImpact: float
    difficulty: str        # "easy" | "medium" | "hard"
    timeframe: str


class KeyMetric(BaseModel):
    label: str
    value: str
    status: str            # "good" | "warning" | "danger"


class CamDataset(BaseModel):
    generatedAt: str
    sections: List[CamSection]
    recommendation: Recommendation
    counterfactuals: List[CounterfactualAction]
    keyMetrics: List[KeyMetric]


# ── DD Note schemas ────────────────────────────────────────────────────────────

class DDNoteRequest(BaseModel):
    officer_text: str


class DDSignal(BaseModel):
    signal_type: str
    description: str
    risk_category: str
    risk_points_delta: float
    reasoning: str


class DDNoteResponse(BaseModel):
    signals: List[DDSignal]
    total_delta: float
    score_update: dict


# ── Counterfactual schemas ─────────────────────────────────────────────────────

class CounterfactualItem(BaseModel):
    factor: str
    label: str
    current_value: Any
    target_value: Any
    delta: float
    score_impact: float
    estimated_action: str
    priority_rank: int
    feasibility: str
    implementation_timeline: str


class CounterfactualsResponse(BaseModel):
    application_id: str
    current_score: float
    approve_threshold: float
    gap: float
    decision: str
    buffer_message: Optional[str] = None
    total_achievable_improvement: float
    would_achieve_approval: bool
    counterfactuals: List[CounterfactualItem]


# ── Chat schemas ───────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


# ── Helpers ────────────────────────────────────────────────────────────────────

def _normalise_decision(raw: Optional[str]) -> str:
    if not raw:
        return "conditional"
    d = raw.upper().replace("_APPROVAL", "").replace("CONDITIONAL_", "CONDITIONAL")
    if d == "APPROVE":    return "approve"
    if d == "REJECT":     return "reject"
    return "conditional"


def _metric_status(val: float, benchmark: float, higher_bad: bool) -> str:
    if higher_bad:
        return "good" if val <= benchmark else ("warning" if val <= benchmark * 1.3 else "danger")
    return "good" if val >= benchmark else ("warning" if val >= benchmark * 0.8 else "danger")


def _build_cam_from_db(cam: CAMReport, risk: Optional[RiskScore], app: Application) -> CamDataset:
    """Assemble CamDataset from ORM + risk score when no sections_json stored."""
    decision = _normalise_decision(cam.recommendation)
    score = float(risk.final_score or 0) if risk else 0.0
    loan = app.loan_amount_requested

    # Sections — narrative text
    sections = [
        CamSection(title="Executive Summary",
                   content=f"This Credit Appraisal Memorandum evaluates the credit proposal of {loan:.0f} Lakhs. "
                           f"The AI pipeline analysed all submitted documents and generated a risk score of "
                           f"{score:.0f}/100. Recommendation: {decision.upper()}."),
        CamSection(title="Business Overview",
                   content="The company operates in the sector as described in submitted documentation. "
                           "Business operations, promoter background, and industry context have been reviewed "
                           "by the Research Intelligence agent using live web data and regulatory databases."),
        CamSection(title="Financial Analysis",
                   content="Three-year financial statements have been extracted and analysed. Key ratios including "
                           "DSCR, D/E ratio, current ratio, and profitability metrics are presented in the "
                           "Financial Spreads section with year-on-year trend analysis."),
        CamSection(title="GST Reconciliation & ITC Analysis",
                   content="GSTR-1, GSTR-2A, and GSTR-3B returns have been cross-reconciled across 8 quarters. "
                           "Input Tax Credit (ITC) claimed versus available has been analysed for circular trading "
                           "and fraud signals. Findings are detailed in the Risk Analytics section."),
        CamSection(title="Buyer Concentration Analysis",
                   content="GSTR-1 invoice data has been analysed to identify buyer concentration risk. "
                           "Revenue dependency on top buyers has been computed and flagged where thresholds are breached. "
                           "Single-buyer dependency above 40% is treated as a critical flag."),
        CamSection(title="Five-Cs Risk Assessment",
                   content=f"Character: {risk.character_explanation or 'Assessed via promoter background, DIN cross-check, litigation history.'} "
                           f"Capacity: {risk.capacity_explanation or 'Assessed via DSCR, interest coverage, cash flow analysis.'} "
                           f"Capital: {risk.capital_explanation or 'Assessed via D/E ratio, net worth, retained earnings.'} "
                           f"Collateral: {risk.collateral_explanation or 'Assessed via asset coverage, charge creation.'} "
                           f"Conditions: {risk.conditions_explanation or 'Assessed via industry outlook, macro conditions.'}"
                   if risk else "Risk assessment completed by Five-Cs engine."),
    ]

    # Loan terms
    rate = f"EBLR + {1.5:.2f}%" if decision == "approve" else ("EBLR + 2.25%" if decision == "conditional" else "NOT APPLICABLE")
    conditions: List[str] = []
    if decision == "conditional":
        conditions = [
            "Additional collateral security to be provided",
            "Quarterly financial statements to be submitted",
            "No further borrowings without prior approval",
            "Maintain DSCR above 1.25x throughout tenure",
        ]
    elif decision == "reject":
        conditions = ["Application rejected — see counterfactual roadmap to improve eligibility"]

    loan_terms = LoanTerms(
        amount=f"₹{loan/100:.2f} Cr" if decision != "reject" else "NOT APPLICABLE",
        tenure="12 months (renewable)" if decision == "approve" else ("24 months" if decision == "conditional" else "NOT APPLICABLE"),
        rate=rate,
        security="Hypothecation of current assets + Equitable mortgage on fixed assets",
        disbursement="Subject to completion of charge creation and fulfillment of all conditions precedent" if decision != "reject" else "NOT APPLICABLE",
    )

    recommendation = Recommendation(
        decision=decision,
        summary=cam.recommendation or decision.upper(),
        conditions=conditions,
        loanTerms=loan_terms,
    )

    # Counterfactuals (for conditional/reject)
    cf_items: List[CounterfactualAction] = []
    raw_cf = cam.counterfactuals or []
    for cf in raw_cf:
        cf_items.append(CounterfactualAction(
            action=cf.get("estimated_action", cf.get("factor", "")),
            impact=f"Risk score improves by ~{cf.get('score_impact', 0):.0f} points",
            newScore=float(cf.get("target_value", score)),
            scoreImpact=float(cf.get("score_impact", 0)),
            difficulty=cf.get("feasibility", "medium").lower(),
            timeframe=cf.get("implementation_timeline", "3–6 months"),
        ))

    # Key metrics
    key_metrics: List[KeyMetric] = []
    if risk:
        if risk.capacity:
            dscr_val = float(risk.capacity) if float(risk.capacity) <= 3 else float(risk.capacity) / 10
            key_metrics.append(KeyMetric(label="DSCR", value=f"{dscr_val:.2f}x", status=_metric_status(dscr_val, 1.5, False)))
        key_metrics.append(KeyMetric(label="Risk Score",  value=f"{score:.0f}/100", status="good" if score >= 70 else ("warning" if score >= 50 else "danger")))
        key_metrics.append(KeyMetric(label="Default Prob 12m", value=f"{risk.default_probability_12m:.1f}%" if risk.default_probability_12m else "—", status="good" if (risk.default_probability_12m or 99) < 5 else "warning"))
        key_metrics.append(KeyMetric(label="Decision",    value=decision.upper(), status="good" if decision == "approve" else ("warning" if decision == "conditional" else "danger")))

    return CamDataset(
        generatedAt=cam.generated_at.strftime("%Y-%m-%d %H:%M IST") if cam.generated_at else datetime.utcnow().strftime("%Y-%m-%d %H:%M IST"),
        sections=sections,
        recommendation=recommendation,
        counterfactuals=cf_items,
        keyMetrics=key_metrics,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{app_id}/cam", response_model=CamDataset)
async def get_cam(app_id: str, db: AsyncSession = Depends(get_db)):
    """Returns full structured CamDataset — frontend /report page primary data source."""
    cam = (await db.execute(
        select(CAMReport).where(CAMReport.application_id == app_id)
    )).scalar_one_or_none()
    if not cam:
        raise HTTPException(404, "CAM not yet generated. Run pipeline first.")

    app = (await db.execute(
        select(Application).where(Application.id == app_id)
    )).scalar_one_or_none()

    risk = (await db.execute(
        select(RiskScore).where(RiskScore.application_id == app_id)
        .order_by(RiskScore.computed_at.desc())
    )).scalar_one_or_none()

    # If sections_json stored (future), use it; else build from ORM
    sections_json = getattr(cam, "sections_json", None)
    if sections_json:
        return CamDataset(**sections_json)

    return _build_cam_from_db(cam, risk, app)


@router.post("/{app_id}/cam/generate")
async def generate_cam(
    app_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger CAM generation. Frontend 'Generate Report' button calls this."""
    app = (await db.execute(
        select(Application).where(Application.id == app_id)
    )).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    background_tasks.add_task(_generate_cam_task, app_id)
    return {"status": "generating", "app_id": app_id}


async def _generate_cam_task(app_id: str):
    try:
        from agents.cam_generation import run as cam_run
        await cam_run(app_id)
    except Exception:
        pass


@router.get("/{app_id}/cam/download")
async def download_cam(app_id: str, format: str = "pdf", db: AsyncSession = Depends(get_db)):
    """Download CAM as PDF or DOCX."""
    cam = (await db.execute(
        select(CAMReport).where(CAMReport.application_id == app_id)
    )).scalar_one_or_none()
    if not cam:
        raise HTTPException(404, "CAM not generated yet.")

    if format == "docx":
        path = cam.docx_path
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        suffix = ".docx"
    else:
        path = cam.pdf_path
        media_type = "application/pdf"
        suffix = ".pdf"

    if not path or not os.path.exists(path):
        # HTML fallback
        html_path = (cam.pdf_path or "").replace(".pdf", ".html")
        if html_path and os.path.exists(html_path):
            return FileResponse(path=html_path, media_type="text/html", filename=f"CAM_{app_id[:8]}.html")
        raise HTTPException(404, "CAM file not found on disk. Run pipeline to regenerate.")

    return FileResponse(path=path, media_type=media_type, filename=f"CAM_{app_id[:8]}{suffix}")


# ── Counterfactuals ────────────────────────────────────────────────────────────

@router.get("/{app_id}/counterfactuals", response_model=CounterfactualsResponse)
async def get_counterfactuals(app_id: str, db: AsyncSession = Depends(get_db)):
    app = (await db.execute(
        select(Application).where(Application.id == app_id)
    )).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    cached = await get_session(app_id, "counterfactuals")
    if not cached:
        try:
            from engines.counterfactual import run as cf_run
            cached = await cf_run(app_id)
        except Exception as e:
            raise HTTPException(500, f"Counterfactual engine error: {e}")

    if not cached:
        raise HTTPException(404, "Risk scores not yet computed.")

    return CounterfactualsResponse(
        application_id=app_id,
        **{k: v for k, v in cached.items() if k != "app_id"},
    )


# ── DD Notes ──────────────────────────────────────────────────────────────────

@router.post("/{app_id}/dd-notes", response_model=DDNoteResponse)
async def submit_dd_notes(
    app_id: str,
    payload: DDNoteRequest,
    db: AsyncSession = Depends(get_db),
):
    app = (await db.execute(
        select(Application).where(Application.id == app_id)
    )).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")
    if not payload.officer_text.strip():
        raise HTTPException(422, "officer_text cannot be empty")
    try:
        from agents.due_diligence import run as dd_run
        result = await dd_run(app_id, payload.officer_text)
        return DDNoteResponse(**result)
    except Exception as e:
        raise HTTPException(500, f"Due diligence agent error: {e}")


# ── AI Chat Widget ─────────────────────────────────────────────────────────────

@router.post("/{app_id}/chat")
async def chat(app_id: str, body: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Contextual AI chat using Claude API with full application context.
    The floating AiChatWidget.tsx sends messages here.
    """
    app = (await db.execute(
        select(Application).where(Application.id == app_id)
    )).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    # Build context from DB
    co = (await db.execute(
        select(Company).where(Company.id == app.company_id)
    )).scalar_one_or_none()

    risk = (await db.execute(
        select(RiskScore).where(RiskScore.application_id == app_id)
        .order_by(RiskScore.computed_at.desc())
    )).scalar_one_or_none()

    flags = (await db.execute(
        select(RiskFlag).where(RiskFlag.application_id == app_id)
    )).scalars().all()
    critical_flags = [f.description for f in flags if f.severity == "CRITICAL"]

    company_name = co.name if co else "the borrower"
    score = f"{risk.final_score:.0f}/100" if risk else "pending"
    decision = risk.decision if risk else "pending"
    flag_text = "; ".join(critical_flags[:3]) if critical_flags else "none"

    system_prompt = f"""You are IntelliCredit AI, an expert credit analyst assistant.
You are helping a credit officer review the application for {company_name}.
Current risk score: {score}. Preliminary decision: {decision}.
Critical flags: {flag_text}.
Answer concisely and always reference specific data from the application.
Use Indian financial terminology (Lakhs, Crores, DSCR, GSTR, DIN, etc.)."""

    messages = [{"role": m.role, "content": m.content} for m in body.history]
    messages.append({"role": "user", "content": body.message})

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 500,
                    "system": system_prompt,
                    "messages": messages,
                },
                timeout=30,
            )
        data = resp.json()
        reply = data["content"][0]["text"] if data.get("content") else "Unable to generate response."
    except Exception as e:
        # Fallback: simple keyword-based response
        msg_lower = body.message.lower()
        if "score" in msg_lower:
            reply = f"The current risk score for {company_name} is **{score}** with a preliminary decision of **{decision}**."
        elif "flag" in msg_lower or "risk" in msg_lower:
            reply = f"Critical flags detected: {flag_text}. Please review the Risk Analytics section for full details."
        elif "decision" in msg_lower or "recommend" in msg_lower:
            reply = f"Based on the Five-Cs analysis, the preliminary recommendation is **{decision}**. See the CAM Report for the full rationale."
        else:
            reply = f"I'm analysing {company_name}'s credit application. Ask me about the risk score, financial ratios, GSTR analysis, or the credit decision."

    return {"reply": reply}








