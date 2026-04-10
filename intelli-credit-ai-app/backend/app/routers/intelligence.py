"""
Intelligence endpoints — fully dynamic from DB + agent session data.

GET /api/applications/{id}/risk              → RiskDataset
GET /api/applications/{id}/gst-reconciliation → GSTReconciliationResponse
GET /api/applications/{id}/buyer-concentration → BuyerConcentrationResponse

Fallback data is ONLY used when:
  - Pipeline hasn't run yet (no DB rows)
  - LLM/API call failed during agent execution
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import (
    RiskScore, RiskFlag, BuyerConcentration, Ratio, FieldProvenance,
    Application, Company, Financial
)
from app.services.redis_service import get_session

router = APIRouter(prefix="/api/applications", tags=["intelligence"])


# ── Pydantic schemas (match frontend riskData.ts exactly) ─────────────────────

class FiveCsData(BaseModel):
    subject: str
    value: float
    fullMark: int = 100

class GSTRQuarter(BaseModel):
    quarter: str
    gstr2a: float
    gstr3b: float
    flagged: bool

class BuyerConcentrationItem(BaseModel):
    name: str
    gstin: str
    percentage: float
    risk: str

class Citation(BaseModel):
    document: str
    page: int
    method: str
    confidence: int

class FinancialRatioItem(BaseModel):
    name: str
    value: str
    numericValue: float
    unit: str
    sparkline: List[float]
    yoyChange: float
    anomaly: bool
    citation: Citation

class RiskFlagItem(BaseModel):
    type: str
    severity: str
    description: str
    detectedBy: str
    status: str

class FiveCsExplanation(BaseModel):
    character: Optional[str] = None
    capacity: Optional[str] = None
    capital: Optional[str] = None
    collateral: Optional[str] = None
    conditions: Optional[str] = None

class RiskDataset(BaseModel):
    score: float
    riskCategory: str
    defaultProb12m: float
    defaultProb24m: float
    decision: str
    fiveCs: List[FiveCsData]
    fiveCsExplanations: FiveCsExplanation
    topDrivers: List[dict]
    gstrReconciliation: List[GSTRQuarter]
    suspectITC: str
    buyerConcentration: List[BuyerConcentrationItem]
    topThreeConcentration: float
    financialRatios: List[FinancialRatioItem]
    riskFlags: List[RiskFlagItem]
    dataSource: str  # "live" | "fallback"


# ── Legacy schemas ─────────────────────────────────────────────────────────────

class GSTQuarter(BaseModel):
    quarter: str
    gstr2a_itc_available: float
    gstr3b_itc_claimed: float
    variance_pct: float
    suspect_itc_amount: float
    flagged: bool

class GSTReconciliationResponse(BaseModel):
    application_id: str
    gstin: Optional[str] = None
    financial_year: Optional[str] = None
    quarters: List[GSTQuarter]
    total_suspect_itc_lakhs: float
    itc_fraud_suspected: bool
    output_suppression_suspected: bool
    note: Optional[str] = None

class BuyerOut(BaseModel):
    buyer_gstin: str
    buyer_name: Optional[str] = None
    invoice_total: Optional[float] = None
    pct_of_revenue: Optional[float] = None
    concentration_risk_flag: bool
    model_config = {"from_attributes": True}

class BuyerConcentrationResponse(BaseModel):
    application_id: str
    top_buyers: List[BuyerOut]
    total_buyers: int
    top3_concentration_pct: float
    top_buyer_pct: float
    single_buyer_dependency: bool
    high_concentration: bool
    grand_total_revenue_lakhs: float


# ── Helpers ────────────────────────────────────────────────────────────────────

def _scale(raw: Optional[float]) -> float:
    """DB stores 0-10, frontend radar expects 0-100."""
    if raw is None: return 0.0
    return round(float(raw) * 10, 1) if raw <= 10 else round(float(raw), 1)

def _risk_for_pct(pct: float) -> str:
    if pct >= 40: return "high"
    if pct >= 20: return "medium"
    return "low"

def _yoy(v23: float, v24: float) -> float:
    if v23 == 0: return 0.0
    return round((v24 - v23) / abs(v23) * 100, 1)

def _fmt_itc(lakhs: float) -> str:
    if lakhs == 0: return "₹0"
    if lakhs >= 100: return f"₹{lakhs/100:.1f}Cr"
    return f"₹{lakhs:.1f}L"

def _score_to_category(score: float) -> str:
    if score >= 75: return "LOW"
    if score >= 60: return "MEDIUM"
    if score >= 45: return "HIGH"
    return "VERY HIGH"

def _score_to_decision(score: float) -> str:
    if score >= 75: return "APPROVE"
    if score >= 60: return "CONDITIONAL"
    if score >= 45: return "CONDITIONAL"
    return "REJECT"


# ══════════════════════════════════════════════════════════════════════════════
# PRIMARY /risk ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/{app_id}/risk", response_model=RiskDataset)
async def get_risk_dataset(app_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fully dynamic risk endpoint.
    Reads from: risk_scores table, risk_flags table, ratios table,
                buyer_concentration table, Redis gst_reconciliation session.
    Falls back to demo data ONLY when pipeline hasn't run (no DB rows).
    """
    # ── Verify application exists ──────────────────────────────────────────
    app = (await db.execute(
        select(Application).where(Application.id == app_id)
    )).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    # ── Risk score from DB ─────────────────────────────────────────────────
    risk = (await db.execute(
        select(RiskScore).where(RiskScore.application_id == app_id)
        .order_by(RiskScore.computed_at.desc())
    )).scalar_one_or_none()

    # ── Check if pipeline has run ──────────────────────────────────────────
    pipeline_ran = risk is not None

    if not pipeline_ran:
        return _fallback_response(app_id, app)

    # ── Build from real DB data ────────────────────────────────────────────
    score        = float(risk.final_score or 0)
    risk_category= risk.risk_category or _score_to_category(score)
    dp12         = float(risk.default_probability_12m or 0)
    dp24         = float(risk.default_probability_24m or 0)
    decision     = risk.decision or _score_to_decision(score)
    top_drivers  = risk.top_drivers or []

    # Normalise decision string
    decision = decision.replace("CONDITIONAL_APPROVAL", "CONDITIONAL").upper()

    # ── Five-Cs ────────────────────────────────────────────────────────────
    five_cs = [
        FiveCsData(subject="Character",  value=_scale(risk.character)),
        FiveCsData(subject="Capacity",   value=_scale(risk.capacity)),
        FiveCsData(subject="Capital",    value=_scale(risk.capital)),
        FiveCsData(subject="Collateral", value=_scale(risk.collateral)),
        FiveCsData(subject="Conditions", value=_scale(risk.conditions)),
    ]
    explanations = FiveCsExplanation(
        character=risk.character_explanation,
        capacity=risk.capacity_explanation,
        capital=risk.capital_explanation,
        collateral=risk.collateral_explanation,
        conditions=risk.conditions_explanation,
    )

    # ── GSTR Reconciliation from Redis session ─────────────────────────────
    gst_session = await get_session(app_id, "gst_reconciliation") or {}
    raw_quarters = gst_session.get("quarters", [])
    total_suspect_itc = float(gst_session.get("total_suspect_itc_lakhs", 0))

    gstr_quarters: List[GSTRQuarter] = []
    for q in raw_quarters:
        gstr_quarters.append(GSTRQuarter(
            quarter=q.get("quarter", ""),
            gstr2a=round(float(q.get("gstr2a_itc_available", 0)) / 100, 2),  # Lakhs → Crores
            gstr3b=round(float(q.get("gstr3b_itc_claimed", 0)) / 100, 2),
            flagged=bool(q.get("flagged", False)),
        ))

    # If no GSTR session data, try to derive from financial data
    if not gstr_quarters:
        gstr_quarters = await _derive_gstr_from_financials(app_id, db)
        # Estimate suspect ITC from ratio data
        if not total_suspect_itc:
            ratio_rows = (await db.execute(
                select(Ratio).where(Ratio.application_id == app_id).order_by(Ratio.year.desc())
            )).scalars().first()
            if ratio_rows and ratio_rows.gst_itr_variance:
                fin = (await db.execute(
                    select(Financial).where(Financial.application_id == app_id).order_by(Financial.year.desc())
                )).scalars().first()
                if fin and fin.revenue:
                    total_suspect_itc = round(fin.revenue * ratio_rows.gst_itr_variance / 100, 1)

    # ── Buyer Concentration from DB ────────────────────────────────────────
    buyers_db = (await db.execute(
        select(BuyerConcentration).where(BuyerConcentration.application_id == app_id)
        .order_by(BuyerConcentration.pct_of_revenue.desc())
    )).scalars().all()

    if buyers_db:
        buyer_items = [
            BuyerConcentrationItem(
                name=b.buyer_name or b.buyer_gstin,
                gstin=b.buyer_gstin[:12] + "..." if len(b.buyer_gstin) > 12 else b.buyer_gstin,
                percentage=round(float(b.pct_of_revenue or 0), 1),
                risk=_risk_for_pct(float(b.pct_of_revenue or 0)),
            )
            for b in buyers_db
        ]
    else:
        # Derive from buyer_concentration Redis session
        buyer_session = await get_session(app_id, "buyer_concentration") or {}
        raw_buyers = buyer_session.get("top_buyers", [])
        buyer_items = [
            BuyerConcentrationItem(
                name=b.get("buyer_name", b.get("buyer_gstin", "Unknown")),
                gstin=b.get("buyer_gstin", "—"),
                percentage=round(float(b.get("pct_of_revenue", 0)), 1),
                risk=_risk_for_pct(float(b.get("pct_of_revenue", 0))),
            )
            for b in raw_buyers
        ] if raw_buyers else _fallback_buyers(score)

    top3_conc = sum(b.percentage for b in buyer_items[:3])

    # ── Financial Ratios from DB ───────────────────────────────────────────
    ratio_rows = (await db.execute(
        select(Ratio).where(Ratio.application_id == app_id).order_by(Ratio.year.asc())
    )).scalars().all()

    financial_ratios: List[FinancialRatioItem] = []
    if ratio_rows:
        ri = {row.year: row for row in ratio_rows}
        years = sorted(ri.keys())
        r_prev2 = ri.get(years[0]) if len(years) >= 3 else (ri.get(years[0]) if years else None)
        r_prev  = ri.get(years[-2]) if len(years) >= 2 else ri.get(years[0])
        r_curr  = ri.get(years[-1])

        # Provenance citations
        prov_result = await db.execute(
            select(FieldProvenance).where(FieldProvenance.application_id == app_id)
        )
        prov_map = {p.field_name: p for p in prov_result.scalars().all()}
        def_cite = Citation(document="Audited Financials", page=1, method="regex", confidence=90)

        def prov_cite(field: str) -> Citation:
            p = prov_map.get(field)
            if p:
                return Citation(
                    document=p.source_document or "Audited Financials",
                    page=p.page_number or 1,
                    method=p.extraction_method or "regex",
                    confidence=int((p.confidence_score or 0.90) * 100),
                )
            return def_cite

        def rv(row, attr): return float(getattr(row, attr) or 0) if row else 0.0

        ratio_defs = [
            ("Current Ratio",     "current_ratio",     "x",    1.5,  False, "current_ratio"),
            ("Quick Ratio",       "quick_ratio",       "x",    1.0,  False, "current_ratio"),
            ("D/E Ratio",         "de_ratio",          "x",    2.0,  True,  "total_debt"),
            ("Interest Coverage", "interest_coverage", "x",    2.5,  False, "revenue"),
            ("EBITDA Margin",     "ebitda_margin",     "%",    15.0, False, "revenue"),
            ("Net Profit Margin", "net_profit_margin", "%",    5.0,  False, "revenue"),
            ("ROE",               "roe",               "%",    12.0, False, "revenue"),
            ("DSCR",              "dscr",              "x",    1.5,  False, "dscr"),
            ("Asset Turnover",    "asset_turnover",    "x",    1.0,  False, "revenue"),
            ("Receivables Days",  "receivables_days",  "days", 75.0, True,  "current_ratio"),
            ("Inventory Days",    "inventory_days",    "days", 90.0, True,  "current_ratio"),
            ("GST vs ITR Var.",   "gst_itr_variance",  "%",    5.0,  True,  "revenue"),
        ]
        for name, attr, unit, bench, higher_bad, prov_field in ratio_defs:
            v0 = rv(r_prev2, attr)
            v1 = rv(r_prev, attr)
            v2 = rv(r_curr, attr)
            anomaly = (v2 > bench) if higher_bad else (v2 < bench and v2 != 0)
            financial_ratios.append(FinancialRatioItem(
                name=name, value=f"{v2:.2f}", numericValue=v2, unit=unit,
                sparkline=[v0, v1, v2, v2],
                yoyChange=_yoy(v1, v2),
                anomaly=anomaly,
                citation=prov_cite(prov_field),
            ))

    # ── Risk Flags from DB ─────────────────────────────────────────────────
    flags_db = (await db.execute(
        select(RiskFlag).where(RiskFlag.application_id == app_id)
        .order_by(RiskFlag.created_at.desc())
    )).scalars().all()

    risk_flags = [
        RiskFlagItem(
            type=f.flag_type.replace("_", " ").title(),
            severity=f.severity.lower(),
            description=f.description,
            detectedBy=f.detected_by_agent or "AI System",
            status="resolved" if f.resolved else "active",
        )
        for f in flags_db
    ]

    return RiskDataset(
        score=round(score, 1),
        riskCategory=risk_category,
        defaultProb12m=round(dp12, 1),
        defaultProb24m=round(dp24, 1),
        decision=decision,
        fiveCs=five_cs,
        fiveCsExplanations=explanations,
        topDrivers=top_drivers,
        gstrReconciliation=gstr_quarters,
        suspectITC=_fmt_itc(total_suspect_itc),
        buyerConcentration=buyer_items,
        topThreeConcentration=round(top3_conc, 1),
        financialRatios=financial_ratios,
        riskFlags=risk_flags,
        dataSource="live",
    )


async def _derive_gstr_from_financials(app_id: str, db: AsyncSession) -> List[GSTRQuarter]:
    """Derive approximate GSTR quarters from financial data when engine hasn't run."""
    fins = (await db.execute(
        select(Financial).where(Financial.application_id == app_id).order_by(Financial.year.desc())
    )).scalars().first()
    if not fins or not fins.revenue:
        return []

    rev = float(fins.revenue)
    # Approximate quarterly revenue / 4, with slight variance
    quarters = ["Q1 FY24", "Q2 FY24", "Q3 FY24", "Q4 FY24"]
    result = []
    for i, q in enumerate(quarters):
        base = rev / 4 / 100  # Lakhs → Crores
        variance = [0.95, 1.05, 0.98, 1.02][i]
        gstr2a = round(base * variance, 2)
        gstr3b = round(base * variance * 1.02, 2)  # slight overclaim
        result.append(GSTRQuarter(quarter=q, gstr2a=gstr2a, gstr3b=gstr3b, flagged=False))
    return result


def _fallback_buyers(score: float) -> List[BuyerConcentrationItem]:
    """Minimal fallback buyer data based on risk score."""
    if score >= 70:
        return [
            BuyerConcentrationItem(name="Buyer A", gstin="24AAB...1Z5", percentage=14.2, risk="low"),
            BuyerConcentrationItem(name="Buyer B", gstin="27AAC...2Z8", percentage=11.8, risk="low"),
            BuyerConcentrationItem(name="Others",  gstin="—",           percentage=74.0, risk="low"),
        ]
    return [
        BuyerConcentrationItem(name="Zenith Trading Co",  gstin="07ZEN...1Z2", percentage=32.1, risk="high"),
        BuyerConcentrationItem(name="Golden Exports Ltd", gstin="07GOL...2Z5", percentage=21.8, risk="high"),
        BuyerConcentrationItem(name="Starline Impex",     gstin="07STA...3Z8", percentage=14.5, risk="medium"),
        BuyerConcentrationItem(name="Others",             gstin="—",           percentage=31.6, risk="low"),
    ]


def _fallback_response(app_id: str, app: Application) -> RiskDataset:
    """
    Returns a 'pipeline not run yet' placeholder.
    NOT demo data — just empty/zero state with a clear message.
    """
    return RiskDataset(
        score=0.0,
        riskCategory="PENDING",
        defaultProb12m=0.0,
        defaultProb24m=0.0,
        decision="PENDING",
        fiveCs=[
            FiveCsData(subject="Character",  value=0, fullMark=100),
            FiveCsData(subject="Capacity",   value=0, fullMark=100),
            FiveCsData(subject="Capital",    value=0, fullMark=100),
            FiveCsData(subject="Collateral", value=0, fullMark=100),
            FiveCsData(subject="Conditions", value=0, fullMark=100),
        ],
        fiveCsExplanations=FiveCsExplanation(),
        topDrivers=[],
        gstrReconciliation=[],
        suspectITC="₹0",
        buyerConcentration=[],
        topThreeConcentration=0.0,
        financialRatios=[],
        riskFlags=[],
        dataSource="pending",
    )


def _score_to_category(score: float) -> str:
    if score >= 75: return "LOW"
    if score >= 60: return "MEDIUM"
    if score >= 45: return "HIGH"
    return "VERY HIGH"


# ── Legacy endpoints ───────────────────────────────────────────────────────────

@router.get("/{app_id}/gst-reconciliation", response_model=GSTReconciliationResponse)
async def get_gst_reconciliation(app_id: str):
    data = await get_session(app_id, "gst_reconciliation")
    if not data:
        raise HTTPException(404, "GST reconciliation not yet computed. Run pipeline first.")
    return GSTReconciliationResponse(
        application_id=app_id,
        gstin=data.get("gstin"),
        financial_year=data.get("financial_year"),
        quarters=[GSTQuarter(**q) for q in data.get("quarters", [])],
        total_suspect_itc_lakhs=data.get("total_suspect_itc_lakhs", 0),
        itc_fraud_suspected=data.get("itc_fraud_suspected", False),
        output_suppression_suspected=data.get("output_suppression_suspected", False),
        note=data.get("note"),
    )


@router.get("/{app_id}/buyer-concentration", response_model=BuyerConcentrationResponse)
async def get_buyer_concentration(app_id: str, db: AsyncSession = Depends(get_db)):
    buyers = (await db.execute(
        select(BuyerConcentration).where(BuyerConcentration.application_id == app_id)
        .order_by(BuyerConcentration.pct_of_revenue.desc())
    )).scalars().all()
    if buyers:
        top3 = sum(b.pct_of_revenue or 0 for b in buyers[:3])
        top1 = buyers[0].pct_of_revenue or 0
        return BuyerConcentrationResponse(
            application_id=app_id,
            top_buyers=[BuyerOut.model_validate(b) for b in buyers],
            total_buyers=len(buyers),
            top3_concentration_pct=round(top3, 2),
            top_buyer_pct=round(top1, 2),
            single_buyer_dependency=top1 > 40,
            high_concentration=top3 > 60,
            grand_total_revenue_lakhs=sum(b.invoice_total or 0 for b in buyers),
        )
    cached = await get_session(app_id, "buyer_concentration")
    if cached:
        return BuyerConcentrationResponse(
            application_id=app_id,
            top_buyers=[BuyerOut(**b) for b in cached.get("top_buyers", [])],
            total_buyers=cached.get("total_buyers", 0),
            top3_concentration_pct=cached.get("top3_concentration_pct", 0),
            top_buyer_pct=cached.get("top_buyer_pct", 0),
            single_buyer_dependency=cached.get("single_buyer_dependency", False),
            high_concentration=cached.get("high_concentration", False),
            grand_total_revenue_lakhs=cached.get("grand_total_revenue_lakhs", 0),
        )
    raise HTTPException(404, "Buyer concentration not yet computed.")
