"""
Intelligence endpoints — Day 3 additions.
GET /api/applications/{id}/risk-score
GET /api/applications/{id}/gst-reconciliation
GET /api/applications/{id}/buyer-concentration
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import RiskScore, BuyerConcentration
from app.services.redis_service import get_session

router = APIRouter(prefix="/api/applications", tags=["intelligence"])


# ── Schemas ───────────────────────────────────────────────
class FiveCsResponse(BaseModel):
    application_id: str
    character: Optional[float]
    character_explanation: Optional[str]
    capacity: Optional[float]
    capacity_explanation: Optional[str]
    capital: Optional[float]
    capital_explanation: Optional[str]
    collateral: Optional[float]
    collateral_explanation: Optional[str]
    conditions: Optional[float]
    conditions_explanation: Optional[str]
    final_score: Optional[float]
    risk_category: Optional[str]
    decision: Optional[str]
    default_probability_12m: Optional[float]
    default_probability_24m: Optional[float]
    top_drivers: Optional[Any]
    computed_at: Optional[datetime]
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
    gstin: Optional[str]
    financial_year: Optional[str]
    quarters: List[GSTQuarter]
    total_suspect_itc_lakhs: float
    itc_fraud_suspected: bool
    output_suppression_suspected: bool
    note: Optional[str] = None


class BuyerOut(BaseModel):
    buyer_gstin: str
    buyer_name: Optional[str]
    invoice_total: Optional[float]
    pct_of_revenue: Optional[float]
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


# ── GET /api/applications/{id}/risk-score ─────────────────
@router.get("/{app_id}/risk-score", response_model=FiveCsResponse)
async def get_risk_score(app_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns Five-Cs scores + explanations + default prediction.
    First checks DB, falls back to Redis session cache.
    """
    result = await db.execute(
        select(RiskScore).where(RiskScore.application_id == app_id)
        .order_by(RiskScore.computed_at.desc())
    )
    risk = result.scalar_one_or_none()

    if risk:
        return FiveCsResponse(application_id=app_id, **{
            c: getattr(risk, c) for c in FiveCsResponse.model_fields if c != "application_id"
        })

    # Fallback to Redis
    cached = await get_session(app_id, "risk_scores")
    if cached:
        return FiveCsResponse(application_id=app_id, **cached)

    raise HTTPException(status_code=404, detail="Risk score not yet computed. Pipeline may still be running.")


# ── GET /api/applications/{id}/gst-reconciliation ─────────
@router.get("/{app_id}/gst-reconciliation", response_model=GSTReconciliationResponse)
async def get_gst_reconciliation(app_id: str):
    """Returns GSTR-2A vs GSTR-3B reconciliation results from Redis session."""
    data = await get_session(app_id, "gst_reconciliation")
    if not data:
        raise HTTPException(status_code=404, detail="GST reconciliation not yet computed.")

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


# ── GET /api/applications/{id}/buyer-concentration ────────
@router.get("/{app_id}/buyer-concentration", response_model=BuyerConcentrationResponse)
async def get_buyer_concentration(app_id: str, db: AsyncSession = Depends(get_db)):
    """Returns buyer concentration analysis from DB or Redis."""
    result = await db.execute(
        select(BuyerConcentration)
        .where(BuyerConcentration.application_id == app_id)
        .order_by(BuyerConcentration.pct_of_revenue.desc())
    )
    buyers = result.scalars().all()

    if buyers:
        top3 = sum(b.pct_of_revenue or 0 for b in buyers[:3])
        top1 = buyers[0].pct_of_revenue or 0 if buyers else 0
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

    # Fallback to Redis
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

    raise HTTPException(status_code=404, detail="Buyer concentration not yet computed.")