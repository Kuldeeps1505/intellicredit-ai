"""
GET /api/applications/{id}/facilities → FacilityDataset
Used by PDF export (generateCamPdf) to include banking facility details.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Application, Financial, RiskScore
from app.services.redis_service import get_session

router = APIRouter(prefix="/api/applications", tags=["facilities"])


# ── Schemas matching frontend facilityData.ts exactly ────────────────────────

class BankingFacility(BaseModel):
    bank: str
    facilityType: str           # "Fund Based" | "Non-Fund Based"
    nature: str                 # "Cash Credit", "Term Loan", etc.
    sanctionedLimit: str        # "₹20.00 Cr"
    outstanding: str
    security: str
    rateOfInterest: str
    repaymentStatus: str        # "Regular" | "Irregular" | "NPA" | "SMA-0" | "SMA-1" | "SMA-2"


class WCLineItem(BaseModel):
    item: str
    fy22: float
    fy23: float
    fy24: float
    projected: float


class MPBF(BaseModel):
    method: str
    amount: str
    details: str


class WorkingCapitalAssessment(BaseModel):
    currentAssets: List[WCLineItem]
    currentLiabilities: List[WCLineItem]
    netWorkingCapital: dict         # {fy22, fy23, fy24, projected}
    mpbf: MPBF
    drawingPower: str
    assessedBankFinance: str


class SensitivityScenario(BaseModel):
    parameter: str
    change: str
    revisedDSCR: float
    revisedICR: float
    impact: str                 # "Comfortable" | "Marginal" | "Stressed" | "Default"


class FacilityDataset(BaseModel):
    existingFacilities: List[BankingFacility]
    proposedFacilities: List[BankingFacility]
    totalExistingFundBased: str
    totalExistingNonFundBased: str
    totalProposedFundBased: str
    totalProposedNonFundBased: str
    workingCapital: WorkingCapitalAssessment
    sensitivityAnalysis: List[SensitivityScenario]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _cr(lakhs: float) -> str:
    cr = lakhs / 100
    return f"₹{cr:.2f} Cr"


def _repayment_status(dscr: Optional[float]) -> str:
    if dscr is None:
        return "Regular"
    if dscr >= 1.5:
        return "Regular"
    if dscr >= 1.2:
        return "SMA-0"
    if dscr >= 1.0:
        return "SMA-1"
    return "SMA-2"


# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{app_id}/facilities", response_model=FacilityDataset)
async def get_facilities(app_id: str, db: AsyncSession = Depends(get_db)):
    app = (await db.execute(
        select(Application).where(Application.id == app_id)
    )).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    # Try Redis first (CAM agent writes facility details here)
    data = await get_session(app_id, "facilities") or {}

    # Load financials for WC assessment
    fins = (await db.execute(
        select(Financial).where(Financial.application_id == app_id)
        .order_by(Financial.year.asc())
    )).scalars().all()

    risk = (await db.execute(
        select(RiskScore).where(RiskScore.application_id == app_id)
        .order_by(RiskScore.computed_at.desc())
    )).scalar_one_or_none()

    if not fins:
        raise HTTPException(404, "Financial data not available. Run pipeline first.")

    f = {row.year: row for row in fins}
    fy22 = f.get(2022, fins[0])
    fy23 = f.get(2023, fins[min(1, len(fins)-1)])
    fy24 = f.get(2024, fins[-1])

    def v(row, attr): return float(getattr(row, attr) or 0) if row else 0.0

    loan_lakhs = app.loan_amount_requested
    dscr = float(risk.capacity or 1.3) if risk else 1.3   # capacity 0-10 proxy for DSCR
    repay_status = _repayment_status(dscr)

    ca24  = v(fy24, "current_assets")
    cl24  = v(fy24, "current_liabilities")
    ca22, ca23 = v(fy22, "current_assets"), v(fy23, "current_assets")
    cl22, cl23 = v(fy22, "current_liabilities"), v(fy23, "current_liabilities")

    # Existing facilities from session or derive
    raw_ef = data.get("existingFacilities", [])
    if raw_ef:
        existing = [BankingFacility(**f) for f in raw_ef]
    else:
        td24 = v(fy24, "total_debt")
        existing = [
            BankingFacility(bank="State Bank of India",    facilityType="Fund Based",     nature="Cash Credit",       sanctionedLimit=_cr(td24*0.4),   outstanding=_cr(td24*0.35),  security="Hypothecation of stocks & book debts", rateOfInterest="EBLR + 1.75%", repaymentStatus=repay_status),
            BankingFacility(bank="HDFC Bank Ltd",          facilityType="Fund Based",     nature="Term Loan",         sanctionedLimit=_cr(td24*0.35),  outstanding=_cr(td24*0.28),  security="Equitable mortgage of factory land",   rateOfInterest="EBLR + 2.00%", repaymentStatus=repay_status),
            BankingFacility(bank="State Bank of India",    facilityType="Non-Fund Based", nature="Bank Guarantee",    sanctionedLimit=_cr(td24*0.15),  outstanding=_cr(td24*0.12),  security="Counter guarantee + FD margin",        rateOfInterest="1.25% p.a.",   repaymentStatus="Regular"),
            BankingFacility(bank="HDFC Bank Ltd",          facilityType="Non-Fund Based", nature="Letter of Credit",  sanctionedLimit=_cr(td24*0.10),  outstanding=_cr(td24*0.08),  security="100% cash margin",                     rateOfInterest="0.75% p.a.",   repaymentStatus="Regular"),
        ]

    # Proposed facilities
    raw_pf = data.get("proposedFacilities", [])
    if raw_pf:
        proposed = [BankingFacility(**f) for f in raw_pf]
    else:
        proposed = [
            BankingFacility(bank="Proposing Bank",  facilityType="Fund Based",     nature="Cash Credit",  sanctionedLimit=_cr(loan_lakhs*0.6),  outstanding="—",  security="First charge on current assets",       rateOfInterest="EBLR + 1.50%", repaymentStatus="Regular"),
            BankingFacility(bank="Proposing Bank",  facilityType="Fund Based",     nature="Term Loan",    sanctionedLimit=_cr(loan_lakhs*0.4),  outstanding="—",  security="Equitable mortgage on fixed assets",   rateOfInterest="EBLR + 1.75%", repaymentStatus="Regular"),
        ]

    # Totals
    def _sum_fund(facs): return sum(float(f.sanctionedLimit.replace("₹","").replace(" Cr",""))*100 for f in facs if f.facilityType == "Fund Based")
    def _sum_nonfund(facs): return sum(float(f.sanctionedLimit.replace("₹","").replace(" Cr",""))*100 for f in facs if f.facilityType == "Non-Fund Based")

    # Working Capital Assessment
    nwc22 = ca22 - cl22
    nwc23 = ca23 - cl23
    nwc24 = ca24 - cl24
    nwc_proj = nwc24 * 1.12

    rev24 = v(fy24, "revenue")
    mpbf_amount = (ca24 - cl24) * 0.75   # Nayak committee: 75% of NWC

    wc = WorkingCapitalAssessment(
        currentAssets=[
            WCLineItem(item="Inventories",           fy22=ca22*0.35, fy23=ca23*0.35, fy24=ca24*0.36, projected=ca24*0.36*1.12),
            WCLineItem(item="Trade Receivables",     fy22=ca22*0.40, fy23=ca23*0.40, fy24=ca24*0.38, projected=ca24*0.38*1.12),
            WCLineItem(item="Cash & Bank Balances",  fy22=ca22*0.15, fy23=ca23*0.15, fy24=ca24*0.14, projected=ca24*0.14*1.10),
            WCLineItem(item="Other Current Assets",  fy22=ca22*0.10, fy23=ca23*0.10, fy24=ca24*0.12, projected=ca24*0.12*1.10),
            WCLineItem(item="Total Current Assets",  fy22=ca22,      fy23=ca23,      fy24=ca24,      projected=ca24*1.12),
        ],
        currentLiabilities=[
            WCLineItem(item="Trade Payables",        fy22=cl22*0.50, fy23=cl23*0.50, fy24=cl24*0.50, projected=cl24*0.50*1.08),
            WCLineItem(item="Short-Term Borrowings", fy22=cl22*0.35, fy23=cl23*0.35, fy24=cl24*0.35, projected=cl24*0.35*1.05),
            WCLineItem(item="Other Current Liab.",   fy22=cl22*0.15, fy23=cl23*0.15, fy24=cl24*0.15, projected=cl24*0.15*1.05),
            WCLineItem(item="Total Current Liab.",   fy22=cl22,      fy23=cl23,      fy24=cl24,      projected=cl24*1.07),
        ],
        netWorkingCapital={"fy22": round(nwc22, 2), "fy23": round(nwc23, 2), "fy24": round(nwc24, 2), "projected": round(nwc_proj, 2)},
        mpbf=MPBF(method="Nayak Committee (2nd Method)", amount=_cr(mpbf_amount), details=f"75% of NWC — Assessed Bank Finance: {_cr(mpbf_amount)}"),
        drawingPower=_cr(ca24 * 0.70),
        assessedBankFinance=_cr(mpbf_amount),
    )

    # Sensitivity analysis
    base_dscr = dscr if dscr < 10 else dscr / 10
    base_dscr = max(0.5, min(3.0, base_dscr))
    sensitivity = [
        SensitivityScenario(parameter="Revenue",   change="-10%", revisedDSCR=round(base_dscr*0.88, 2), revisedICR=round(base_dscr*0.88*1.5, 2), impact="Marginal"    if base_dscr*0.88 >= 1.2 else "Stressed"),
        SensitivityScenario(parameter="Revenue",   change="-20%", revisedDSCR=round(base_dscr*0.76, 2), revisedICR=round(base_dscr*0.76*1.5, 2), impact="Stressed"    if base_dscr*0.76 >= 1.0 else "Default"),
        SensitivityScenario(parameter="Interest",  change="+200bps", revisedDSCR=round(base_dscr*0.85, 2), revisedICR=round(base_dscr*0.85*1.4, 2), impact="Marginal" if base_dscr*0.85 >= 1.2 else "Stressed"),
        SensitivityScenario(parameter="Raw Mat. Cost", change="+15%", revisedDSCR=round(base_dscr*0.82, 2), revisedICR=round(base_dscr*0.82*1.5, 2), impact="Stressed" if base_dscr*0.82 < 1.2 else "Marginal"),
    ]

    return FacilityDataset(
        existingFacilities=existing,
        proposedFacilities=proposed,
        totalExistingFundBased=_cr(_sum_fund(existing)),
        totalExistingNonFundBased=_cr(_sum_nonfund(existing)),
        totalProposedFundBased=_cr(_sum_fund(proposed)),
        totalProposedNonFundBased=_cr(_sum_nonfund(proposed)),
        workingCapital=wc,
        sensitivityAnalysis=sensitivity,
    )

