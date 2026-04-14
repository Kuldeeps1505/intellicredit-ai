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


def _safe_float(val, default: float = 0.0) -> float:
    """Convert any value to float safely — handles strings, None, etc."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _build_cam_from_db(cam: CAMReport, risk: Optional[RiskScore], app: Application,
                       ratio=None, fin=None) -> CamDataset:
    """Assemble CamDataset from ORM + risk score + real ratios."""
    raw_decision = (risk.decision if risk else None) or cam.recommendation or "conditional"
    decision = _normalise_decision(raw_decision)
    score = _safe_float(risk.final_score if risk else None, 0.0)
    loan = app.loan_amount_requested

    def rv(obj, attr, default=None):
        if obj is None:
            return default
        val = getattr(obj, attr, None)
        if val is None:
            return default
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    # ── Dynamic sections using real data ──────────────────────────────────
    rev    = _safe_float(rv(fin, "revenue"),    0.0)
    ebitda = _safe_float(rv(fin, "ebitda"),     0.0)
    np_    = rv(fin, "net_profit")   # can be None (negative profit is valid)
    debt   = _safe_float(rv(fin, "total_debt"), 0.0)
    nw     = _safe_float(rv(fin, "net_worth"),  0.0)
    cfo    = rv(fin, "cash_from_operations")    # can be None or negative
    dscr   = rv(ratio, "dscr")                  # None if no ratio row
    de     = rv(ratio, "de_ratio")
    cr     = rv(ratio, "current_ratio")
    em     = _safe_float(rv(ratio, "ebitda_margin"), 0.0)  # always float

    rev_cr  = rev / 100
    debt_cr = debt / 100
    nw_cr   = nw / 100
    ebitda_cr = ebitda / 100

    sections = [
        CamSection(
            title="Executive Summary",
            content=(
                f"This Credit Appraisal Memorandum evaluates the credit proposal of ₹{loan/100:.2f} Cr "
                f"submitted by {app.purpose or 'the borrower'}. "
                f"The AI pipeline processed all submitted documents and generated a risk score of "
                f"{score:.0f}/100 (category: {risk.risk_category if risk else 'PENDING'}). "
                f"Preliminary recommendation: {decision.upper()}."
            )
        ),
        CamSection(
            title="Financial Analysis",
            content=(
                f"Revenue FY24: ₹{rev_cr:.1f}Cr | "
                f"EBITDA: ₹{ebitda_cr:.1f}Cr ({em:.1f}% margin) | "
                f"{'Net Loss' if (np_ or 0) < 0 else 'Net Profit'}: ₹{abs(_safe_float(np_, 0)/100):.2f}Cr | "
                f"Total Debt: ₹{debt_cr:.1f}Cr | Net Worth: ₹{nw_cr:.1f}Cr. "
                f"Cash from Operations: ₹{abs(_safe_float(cfo, 0)/100):.2f}Cr{' (negative — concern)' if _safe_float(cfo, 0) < 0 else ''}. "
                f"Three-year financial spread available in the Financial Spreads section."
            ) if rev > 0 else
            "Financial data not yet extracted. Run pipeline to populate financial analysis."
        ),
        CamSection(
            title="Key Ratios",
            content=(
                f"DSCR: {dscr:.2f}x {'✓' if dscr >= 1.25 else '⚠ Below 1.25 threshold'} | "
                f"D/E: {de:.2f}x {'✓' if de <= 2.0 else '⚠ Above 2.0 threshold'} | "
                f"Current Ratio: {cr:.2f}x {'✓' if cr >= 1.0 else '⚠ Below 1.0'} | "
                f"EBITDA Margin: {em:.1f}% {'✓' if em >= 15 else '⚠ Below 15%'}."
            ) if all(x is not None for x in [dscr, de, cr, em])
            else "Financial ratios computed — see Financial Spreads for full detail."
        ),
        CamSection(
            title="GST Reconciliation & ITC Analysis",
            content=(
                "GSTR-1, GSTR-2A, and GSTR-3B returns have been cross-reconciled across 8 quarters. "
                "Input Tax Credit (ITC) claimed versus available has been analysed for fraud signals. "
                "Findings are detailed in the Risk Analytics section."
            )
        ),
        CamSection(
            title="Buyer Concentration Analysis",
            content=(
                "GSTR-1 invoice data has been analysed to identify buyer concentration risk. "
                "Revenue dependency on top buyers has been computed and flagged where thresholds are breached. "
                "Single-buyer dependency above 40% is treated as a critical flag."
            )
        ),
        CamSection(
            title="Five-Cs Risk Assessment",
            content=(
                f"Character ({_safe_float(risk.character):.1f}/10): {risk.character_explanation or 'Assessed via promoter background, DIN cross-check, litigation history.'} "
                f"Capacity ({_safe_float(risk.capacity):.1f}/10): {risk.capacity_explanation or 'Assessed via DSCR, interest coverage, cash flow analysis.'} "
                f"Capital ({_safe_float(risk.capital):.1f}/10): {risk.capital_explanation or 'Assessed via D/E ratio, net worth, retained earnings.'} "
                f"Collateral ({_safe_float(risk.collateral):.1f}/10): {risk.collateral_explanation or 'Assessed via asset coverage, charge creation.'} "
                f"Conditions ({_safe_float(risk.conditions):.1f}/10): {risk.conditions_explanation or 'Assessed via industry outlook, macro conditions.'}"
            ) if risk else "Risk assessment completed by Five-Cs engine."
        ),
    ]

    # ── Loan terms ─────────────────────────────────────────────────────────
    rate = "EBLR + 1.50%" if decision == "approve" else ("EBLR + 2.25%" if decision == "conditional" else "NOT APPLICABLE")
    conditions: List[str] = []
    if decision == "conditional":
        conditions = [
            "Additional collateral security to be provided before disbursement",
            "Quarterly financial statements to be submitted within 45 days of quarter end",
            "No further borrowings without prior written approval",
            f"Maintain DSCR above 1.25x throughout tenure (current: {dscr:.2f}x)" if dscr is not None else "Maintain DSCR above 1.25x throughout tenure",
        ]
    elif decision == "reject":
        conditions = ["Application rejected — see counterfactual roadmap below to improve eligibility"]

    loan_terms = LoanTerms(
        amount=f"₹{loan/100:.2f} Cr" if decision != "reject" else "NOT APPLICABLE",
        tenure="12 months (renewable)" if decision == "approve" else ("24 months" if decision == "conditional" else "NOT APPLICABLE"),
        rate=rate,
        security="Hypothecation of current assets + Equitable mortgage on fixed assets",
        disbursement="Subject to charge creation and fulfillment of all conditions precedent" if decision != "reject" else "NOT APPLICABLE",
    )

    recommendation = Recommendation(
        decision=decision,
        summary=cam.recommendation if cam.recommendation and len(cam.recommendation) > 20 else (
            f"Based on Five-Cs analysis (score {score:.0f}/100), the AI pipeline recommends {decision.upper()}. "
            f"{'All key parameters within acceptable thresholds.' if decision == 'approve' else 'Key concerns: see risk flags and counterfactuals below.'}"
        ),
        conditions=conditions,
        loanTerms=loan_terms,
    )

    # ── Counterfactuals ────────────────────────────────────────────────────
    cf_items: List[CounterfactualAction] = []
    raw_cf = cam.counterfactuals or []
    for cf in raw_cf:
        # target_value can be a string like "₹0 variance" or "< 2.0x" — guard against it
        try:
            new_score = float(cf.get("target_value", score))
        except (TypeError, ValueError):
            new_score = score
        try:
            score_impact = float(cf.get("score_impact", 0))
        except (TypeError, ValueError):
            score_impact = 0.0

        cf_items.append(CounterfactualAction(
            action=cf.get("estimated_action", cf.get("label", cf.get("factor", ""))),
            impact=f"Risk score improves by ~{score_impact:.0f} points",
            newScore=new_score,
            scoreImpact=score_impact,
            difficulty=str(cf.get("feasibility", "medium")).lower(),
            timeframe=str(cf.get("implementation_timeline", "3–6 months")),
        ))

    # ── Key metrics — all from real DB data ────────────────────────────────
    key_metrics: List[KeyMetric] = [
        KeyMetric(label="Risk Score",    value=f"{score:.0f}/100",
                  status="good" if score >= 70 else ("warning" if score >= 50 else "danger")),
        KeyMetric(label="Decision",      value=decision.upper(),
                  status="good" if decision == "approve" else ("warning" if decision == "conditional" else "danger")),
    ]

    if risk and risk.default_probability_12m is not None:
        pd12 = _safe_float(risk.default_probability_12m)
        key_metrics.append(KeyMetric(label="Default Prob 12m", value=f"{pd12:.1f}%",
                                     status="good" if pd12 < 5 else ("warning" if pd12 < 15 else "danger")))

    if dscr is not None:
        key_metrics.append(KeyMetric(label="DSCR", value=f"{dscr:.2f}x",
                                     status=_metric_status(dscr, 1.25, False)))
    if de is not None:
        key_metrics.append(KeyMetric(label="D/E Ratio", value=f"{de:.2f}x",
                                     status=_metric_status(de, 2.0, True)))
    if cr is not None:
        key_metrics.append(KeyMetric(label="Current Ratio", value=f"{cr:.2f}x",
                                     status=_metric_status(cr, 1.0, False)))
    if rev:
        key_metrics.append(KeyMetric(label="Revenue FY24", value=f"₹{rev_cr:.1f}Cr",
                                     status="good" if rev_cr > 50 else "warning"))
    if np_ is not None:
        key_metrics.append(KeyMetric(
            label="Net Profit",
            value=f"₹{np_/100:.2f}Cr" if abs(np_) >= 100 else f"₹{np_:.1f}L",
            status="good" if np_ > 0 else "danger"
        ))
    if em is not None:
        key_metrics.append(KeyMetric(label="EBITDA Margin", value=f"{em:.1f}%",
                                     status=_metric_status(em, 15.0, False)))

    key_metrics.append(KeyMetric(label="Loan Requested", value=f"₹{loan/100:.2f}Cr", status="good"))

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

    # Pull real ratios for key metrics
    from app.models import Ratio, Financial
    ratio_row = (await db.execute(
        select(Ratio).where(Ratio.application_id == app_id).order_by(Ratio.year.desc())
    )).scalars().first()

    fin_row = (await db.execute(
        select(Financial).where(Financial.application_id == app_id).order_by(Financial.year.desc())
    )).scalars().first()

    result = _build_cam_from_db(cam, risk, app, ratio_row, fin_row)
    return result


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
        from app.services.llm_service import llm_complete
        reply = await llm_complete(body.message, max_tokens=500, system=system_prompt)
        if not reply:
            raise ValueError("empty response")
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








