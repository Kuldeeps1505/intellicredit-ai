"""
Intelligence endpoints — updated to match frontend TypeScript interfaces exactly.

GET /api/applications/{id}/risk              → RiskDataset  (unified — replaces /risk-score)
GET /api/applications/{id}/gst-reconciliation → GSTReconciliationResponse (unchanged)
GET /api/applications/{id}/buyer-concentration → BuyerConcentrationResponse (unchanged)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import RiskScore, RiskFlag, BuyerConcentration, Ratio, FieldProvenance
from app.services.redis_service import get_session

router = APIRouter(prefix="/api/applications", tags=["intelligence"])


# ── Schemas matching frontend riskData.ts exactly ─────────────────────────────

class FiveCsData(BaseModel):
    subject: str       # "Character" | "Capacity" | "Capital" | "Collateral" | "Conditions"
    value: float       # 0-100 (scaled from 0-10 stored in DB)
    fullMark: int = 100


class GSTRQuarter(BaseModel):
    quarter: str
    gstr2a: float      # ₹ Crores
    gstr3b: float
    flagged: bool


class BuyerConcentrationItem(BaseModel):
    name: str
    gstin: str
    percentage: float
    risk: str          # "high" | "medium" | "low"


class Citation(BaseModel):
    document: str
    page: int
    method: str
    confidence: int    # 0-100


class FinancialRatioItem(BaseModel):
    name: str
    value: str         # formatted e.g. "1.82"
    numericValue: float
    unit: str
    sparkline: List[float]
    yoyChange: float
    anomaly: bool
    citation: Citation


class RiskFlagItem(BaseModel):
    type: str
    severity: str      # "critical" | "high" | "medium" | "low"
    description: str
    detectedBy: str
    status: str        # "active" | "resolved" | "monitoring"


class RiskDataset(BaseModel):
    score: float
    riskCategory: str
    defaultProb12m: float
    defaultProb24m: float
    fiveCs: List[FiveCsData]
    gstrReconciliation: List[GSTRQuarter]
    suspectITC: str
    buyerConcentration: List[BuyerConcentrationItem]
    topThreeConcentration: float
    financialRatios: List[FinancialRatioItem]
    riskFlags: List[RiskFlagItem]


# ── Legacy schemas (kept for backward compat) ─────────────────────────────────

class FiveCsResponse(BaseModel):
    application_id: str
    character: Optional[float] = None
    character_explanation: Optional[str] = None
    capacity: Optional[float] = None
    capacity_explanation: Optional[str] = None
    capital: Optional[float] = None
    capital_explanation: Optional[str] = None
    collateral: Optional[float] = None
    collateral_explanation: Optional[str] = None
    conditions: Optional[float] = None
    conditions_explanation: Optional[str] = None
    final_score: Optional[float] = None
    risk_category: Optional[str] = None
    decision: Optional[str] = None
    default_probability_12m: Optional[float] = None
    default_probability_24m: Optional[float] = None
    top_drivers: Optional[Any] = None
    computed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


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

def _scale_five_c(raw: Optional[float]) -> float:
    """DB stores 0-10, frontend radar expects 0-100."""
    if raw is None:
        return 0.0
    return round(float(raw) * 10, 1) if raw <= 10 else round(float(raw), 1)


def _risk_for_pct(pct: float) -> str:
    if pct >= 40:
        return "high"
    if pct >= 20:
        return "medium"
    return "low"


def _yoy(fy23: float, fy24: float) -> float:
    if fy23 == 0:
        return 0.0
    return round((fy24 - fy23) / abs(fy23) * 100, 1)


def _format_suspect_itc(lakhs: float) -> str:
    if lakhs == 0:
        return "₹0"
    if lakhs >= 100:
        return f"₹{lakhs/100:.1f}Cr"
    return f"₹{lakhs:.1f}L"


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED /risk ENDPOINT — primary one used by frontend RiskAnalytics page
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{app_id}/risk", response_model=RiskDataset)
async def get_risk_dataset(app_id: str, db: AsyncSession = Depends(get_db)):
    """
    Unified risk endpoint. Assembles RiskDataset from:
    - risk_scores table (Five-Cs, default probability)
    - Redis gst_reconciliation session (GSTR quarters)
    - buyer_concentration table
    - ratios table (financial ratio cards with sparklines)
    - risk_flags table
    """
    # ── Risk score ──────────────────────────────────────────────────────────
    risk = (await db.execute(
        select(RiskScore).where(RiskScore.application_id == app_id)
        .order_by(RiskScore.computed_at.desc())
    )).scalar_one_or_none()

    if not risk:
        cached = await get_session(app_id, "risk_scores")
        if not cached:
            raise HTTPException(404, "Risk score not yet computed. Run pipeline first.")

    score = float(risk.final_score or 0) if risk else float((await get_session(app_id, "risk_scores") or {}).get("final_score", 0))
    risk_category = (risk.risk_category if risk else None) or _score_to_category(score)
    dp12 = float(risk.default_probability_12m or 0) if risk else 0.0
    dp24 = float(risk.default_probability_24m or 0) if risk else 0.0

    # ── Five-Cs (radar chart) ───────────────────────────────────────────────
    five_cs = [
        FiveCsData(subject="Character",  value=_scale_five_c(risk.character if risk else None)),
        FiveCsData(subject="Capacity",   value=_scale_five_c(risk.capacity if risk else None)),
        FiveCsData(subject="Capital",    value=_scale_five_c(risk.capital if risk else None)),
        FiveCsData(subject="Collateral", value=_scale_five_c(risk.collateral if risk else None)),
        FiveCsData(subject="Conditions", value=_scale_five_c(risk.conditions if risk else None)),
    ]

    # ── GSTR Reconciliation quarters ────────────────────────────────────────
    gst_data = await get_session(app_id, "gst_reconciliation") or {}
    raw_quarters = gst_data.get("quarters", [])
    gstr_quarters = []
    total_suspect_itc = float(gst_data.get("total_suspect_itc_lakhs", 0))

    for q in raw_quarters:
        gstr_quarters.append(GSTRQuarter(
            quarter=q.get("quarter", ""),
            gstr2a=round(float(q.get("gstr2a_itc_available", 0)) / 100, 2),   # Lakhs → Crores
            gstr3b=round(float(q.get("gstr3b_itc_claimed", 0)) / 100, 2),
            flagged=bool(q.get("flagged", False)),
        ))

    # Pad to 8 quarters if fewer returned
    quarters_needed = ["Q1 FY22","Q2 FY22","Q3 FY22","Q4 FY22","Q1 FY23","Q2 FY23","Q3 FY23","Q4 FY23"]
    if not gstr_quarters:
        gstr_quarters = [GSTRQuarter(quarter=q, gstr2a=0, gstr3b=0, flagged=False)
                         for q in quarters_needed]

    # ── Buyer Concentration ──────────────────────────────────────────────────
    buyers_db = (await db.execute(
        select(BuyerConcentration).where(BuyerConcentration.application_id == app_id)
        .order_by(BuyerConcentration.pct_of_revenue.desc())
    )).scalars().all()

    buyer_items = [
        BuyerConcentrationItem(
            name=b.buyer_name or b.buyer_gstin,
            gstin=b.buyer_gstin[:12] + "..." if len(b.buyer_gstin) > 12 else b.buyer_gstin,
            percentage=round(float(b.pct_of_revenue or 0), 1),
            risk=_risk_for_pct(float(b.pct_of_revenue or 0)),
        )
        for b in buyers_db
    ]
    top3_conc = sum(b.percentage for b in buyer_items[:3])

    # ── Financial Ratios with sparklines ────────────────────────────────────
    ratio_rows = (await db.execute(
        select(Ratio).where(Ratio.application_id == app_id).order_by(Ratio.year.asc())
    )).scalars().all()
    ri = {row.year: row for row in ratio_rows}
    r22 = ri.get(2022, ratio_rows[0] if ratio_rows else None)
    r23 = ri.get(2023, ratio_rows[min(1, len(ratio_rows)-1)] if ratio_rows else None)
    r24 = ri.get(2024, ratio_rows[-1] if ratio_rows else None)

    # Provenance citation for ratios
    prov_result = await db.execute(
        select(FieldProvenance).where(FieldProvenance.application_id == app_id)
        .where(FieldProvenance.field_name.in_(["revenue", "dscr", "current_ratio"]))
    )
    prov_map = {p.field_name: p for p in prov_result.scalars().all()}
    default_citation = Citation(document="Audited Financials FY24", page=1, method="Camelot", confidence=95)

    def rv(row, a): return float(getattr(row, a) or 0) if row else 0.0
    def prov_cite(field): 
        p = prov_map.get(field)
        if p:
            return Citation(document=p.source_document or "Audited Financials FY24",
                           page=p.page_number or 1,
                           method=p.extraction_method or "Camelot",
                           confidence=int((p.confidence_score or 0.95) * 100))
        return default_citation

    financial_ratios: List[FinancialRatioItem] = []
    if r24:
        ratio_defs = [
            ("Current Ratio",      "current_ratio",        "x",    1.5,  False, "current_ratio"),
            ("Quick Ratio",        "quick_ratio",          "x",    1.0,  False, "current_ratio"),
            ("D/E Ratio",          "de_ratio",             "x",    2.0,  True,  "total_debt"),
            ("Interest Coverage",  "interest_coverage",    "x",    2.5,  False, "revenue"),
            ("EBITDA Margin",      "ebitda_margin",        "%",    15.0, False, "revenue"),
            ("Net Profit Margin",  "net_profit_margin",    "%",    5.0,  False, "revenue"),
            ("ROE",                "roe",                  "%",    12.0, False, "revenue"),
            ("DSCR",               "dscr",                 "x",    1.5,  False, "dscr"),
            ("Asset Turnover",     "asset_turnover",       "x",    1.0,  False, "revenue"),
            ("Receivables Days",   "receivables_days",     "days", 75.0, True,  "current_ratio"),
            ("Inventory Days",     "inventory_days",       "days", 90.0, True,  "current_ratio"),
            ("GST vs ITR Var.",    "gst_itr_variance",     "%",    5.0,  True,  "revenue"),
        ]
        for name, attr, unit, bench, higher_bad, prov_field in ratio_defs:
            v22, v23, v24 = rv(r22,attr), rv(r23,attr), rv(r24,attr)
            anomaly = (v24 > bench) if higher_bad else (v24 < bench)
            financial_ratios.append(FinancialRatioItem(
                name=name,
                value=f"{v24:.2f}",
                numericValue=v24,
                unit=unit,
                sparkline=[v22, v23, v24, v24],    # 4 points as frontend expects
                yoyChange=_yoy(v23, v24),
                anomaly=anomaly,
                citation=prov_cite(prov_field),
            ))

    # ── Risk Flags ───────────────────────────────────────────────────────────
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
        fiveCs=five_cs,
        gstrReconciliation=gstr_quarters,
        suspectITC=_format_suspect_itc(total_suspect_itc),
        buyerConcentration=buyer_items,
        topThreeConcentration=round(top3_conc, 1),
        financialRatios=financial_ratios,
        riskFlags=risk_flags,
    )


def _score_to_category(score: float) -> str:
    if score >= 70: return "LOW"
    if score >= 50: return "MEDIUM"
    if score >= 30: return "HIGH"
    return "VERY HIGH"


# ── Legacy /risk-score (kept for backward compat) ─────────────────────────────
@router.get("/{app_id}/risk-score", response_model=FiveCsResponse)
async def get_risk_score(app_id: str, db: AsyncSession = Depends(get_db)):
    risk = (await db.execute(
        select(RiskScore).where(RiskScore.application_id == app_id)
        .order_by(RiskScore.computed_at.desc())
    )).scalar_one_or_none()
    if risk:
        return FiveCsResponse(application_id=app_id, **{
            c: getattr(risk, c) for c in FiveCsResponse.model_fields if c != "application_id"
        })
    cached = await get_session(app_id, "risk_scores")
    if cached:
        return FiveCsResponse(application_id=app_id, **cached)
    raise HTTPException(404, "Risk score not yet computed.")


# ── /gst-reconciliation ───────────────────────────────────────────────────────
@router.get("/{app_id}/gst-reconciliation", response_model=GSTReconciliationResponse)
async def get_gst_reconciliation(app_id: str):
    data = await get_session(app_id, "gst_reconciliation")
    if not data:
        raise HTTPException(404, "GST reconciliation not yet computed.")
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


# ── /buyer-concentration ──────────────────────────────────────────────────────
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


