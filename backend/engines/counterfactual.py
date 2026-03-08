"""
Counterfactual Explainability Engine — Day 4 deliverable.

Most novel feature of IntelliCredit AI.

For REJECTED/CONDITIONAL: computes minimum changes needed to reach APPROVE (score >= 75).
For APPROVED: computes safety buffer and how close to rejection.

Output:
{
  current_score: 42,
  approve_threshold: 75,
  gap: 33,
  status: "REJECTED",
  counterfactuals: [
    {
      factor: "de_ratio",
      current_value: 3.4,
      target_value: 2.0,
      delta: 1.4,
      score_impact: 8.0,
      estimated_action: "Repay ₹X Cr debt OR infuse ₹Y Cr equity",
      priority_rank: 1,
      feasibility: "MEDIUM"
    }
  ]
}

Endpoint: GET /api/applications/{id}/counterfactuals
"""
from __future__ import annotations
import uuid, time
from datetime import datetime

from app.services.redis_service import get_session, set_session, publish_event
from app.services.db_helpers import log_agent, _AgentSession
from app.models import CAMReport, Financial, RiskScore
from sqlalchemy import select

AGENT = "counterfactual_engine"
APPROVE_THRESHOLD = 75.0

# ── Per-factor score impact weights (calibrated to Five-Cs) ──────────────────
# Each factor maps to: (score_per_unit_improvement, target_value, feasibility_rank)
# feasibility_rank: 1 = easiest/fastest to fix, 5 = hardest
FACTOR_CONFIG = {
    "collateral": {
        "label": "Collateral Coverage",
        "unit": "₹ Cr additional collateral",
        "score_per_unit": 1.5,    # per ₹1Cr extra collateral → +1.5 score points
        "target_fn": lambda cur, net_worth, loan: max(0, loan * 0.5 - (net_worth or 0) * 0.3),
        "feasibility": "HIGH",
        "priority_base": 1,
        "action_template": "Provide additional collateral of ₹{delta:.1f}Cr (property/FD/securities)",
    },
    "de_ratio": {
        "label": "Debt/Equity Ratio",
        "unit": "ratio reduction",
        "score_per_unit": 5.0,    # reducing D/E by 1.0 → +5 score points (capital component)
        "target_value": 2.0,
        "feasibility": "MEDIUM",
        "priority_base": 2,
        "action_template": (
            "Reduce D/E from {current:.2f} to below {target:.1f} — "
            "requires repaying ₹{debt_repay:.0f}L debt OR equity infusion of ₹{equity_needed:.0f}L"
        ),
    },
    "dscr": {
        "label": "Debt Service Coverage Ratio",
        "unit": "ratio improvement",
        "score_per_unit": 8.0,    # improving DSCR by 0.1 → +0.8 score points
        "target_value": 1.30,
        "feasibility": "MEDIUM",
        "priority_base": 3,
        "action_template": (
            "Improve DSCR from {current:.2f} to above {target:.2f} — "
            "requires EBITDA increase of ₹{ebitda_delta:.0f}L (approx {ebitda_pct:.0f}% improvement)"
        ),
    },
    "litigation": {
        "label": "Active Litigation",
        "unit": "cases resolved",
        "score_per_unit": 4.0,    # resolving 1 material case → +4 score points
        "target_value": 0,
        "feasibility": "LOW",
        "priority_base": 4,
        "action_template": "Resolve {count} material litigation case(s) totalling ₹{total_claim:.1f}Cr",
    },
    "itc_fraud": {
        "label": "ITC Reconciliation",
        "unit": "₹Cr reconciled",
        "score_per_unit": 2.0,    # per ₹1Cr ITC reconciled → +2 score points (character)
        "target_value": 0,
        "feasibility": "LOW",
        "priority_base": 4,
        "action_template": "Resolve ₹{suspect_itc:.1f}Cr ITC discrepancy with GSTN records — file revised GSTR-3B",
    },
    "buyer_concentration": {
        "label": "Buyer Concentration",
        "unit": "% reduction in top buyer share",
        "score_per_unit": 0.3,    # reducing top buyer by 1% → +0.3 score points (conditions)
        "target_value": 40.0,
        "feasibility": "LOW",
        "priority_base": 5,
        "action_template": (
            "Diversify revenue — reduce top buyer from {current:.0f}% to below {target:.0f}% "
            "by onboarding {new_customers} new customers"
        ),
    },
}


def compute_counterfactuals(
    risk_scores: dict,
    ratios: dict,
    financials: dict,
    litigation_cases: list,
    gst_recon: dict,
    buyer_conc: dict,
    loan_amount: float,
) -> dict:
    """
    Core engine: compute minimum changes to reach APPROVE threshold.
    Returns structured counterfactual output.
    """
    current_score = risk_scores.get("final_score", 0) or 0
    decision = risk_scores.get("decision", "REJECT")
    gap = max(0, APPROVE_THRESHOLD - current_score)

    # Get latest ratios
    latest_year = max(ratios.keys(), default=None) if ratios else None
    latest_ratios = {}
    if latest_year:
        latest_ratios = ratios.get(str(latest_year), {}) or ratios.get(latest_year, {})

    dscr = latest_ratios.get("dscr") or 0
    de_ratio = latest_ratios.get("de_ratio") or 0
    total_debt = financials.get("total_debt") or 0
    net_worth = financials.get("net_worth") or 0
    ebitda = financials.get("ebitda") or 0
    revenue = financials.get("revenue") or 1

    # Litigation
    material_cases = [c for c in litigation_cases if c.get("material", False)]
    total_claim = sum(c.get("claim_amount_cr", 0) for c in material_cases)
    nclt_cases = [c for c in material_cases if "NCLT" in c.get("court", "")]

    # GST
    suspect_itc = gst_recon.get("total_suspect_itc_lakhs", 0) / 100  # convert to Cr
    itc_fraud = gst_recon.get("itc_fraud_suspected", False)

    # Buyer concentration
    top_buyer_pct = buyer_conc.get("top_buyer_pct", 0)

    counterfactuals = []
    score_accumulated = 0.0

    # ── 1. Collateral (easiest — fastest to implement) ────────────────────────
    if current_score < APPROVE_THRESHOLD:
        score_needed = gap - score_accumulated
        collateral_needed_cr = score_needed / FACTOR_CONFIG["collateral"]["score_per_unit"]
        collateral_needed_cr = max(1.0, round(collateral_needed_cr, 1))
        score_gain = min(collateral_needed_cr * FACTOR_CONFIG["collateral"]["score_per_unit"], score_needed)

        counterfactuals.append({
            "factor": "collateral",
            "label": "Collateral Coverage",
            "current_value": f"₹{loan_amount/100:.1f}Cr loan vs net worth ₹{net_worth/100:.1f}Cr",
            "target_value": f"Additional ₹{collateral_needed_cr:.1f}Cr collateral",
            "delta": collateral_needed_cr,
            "score_impact": round(score_gain, 1),
            "estimated_action": f"Provide additional collateral of ₹{collateral_needed_cr:.1f}Cr (property / FD / listed securities)",
            "priority_rank": 1,
            "feasibility": "HIGH",
            "implementation_timeline": "1–2 weeks",
        })
        score_accumulated += score_gain

    # ── 2. D/E Ratio reduction ────────────────────────────────────────────────
    target_de = FACTOR_CONFIG["de_ratio"]["target_value"]
    if de_ratio > target_de:
        de_improvement = de_ratio - target_de
        score_gain = de_improvement * FACTOR_CONFIG["de_ratio"]["score_per_unit"]
        score_gain = min(score_gain, max(0, gap - score_accumulated + 2))

        if net_worth > 0 and total_debt > 0:
            debt_to_repay = (de_ratio - target_de) * net_worth
            equity_needed = debt_to_repay * 0.6
        else:
            debt_to_repay = 500
            equity_needed = 300

        counterfactuals.append({
            "factor": "de_ratio",
            "label": "Debt/Equity Ratio",
            "current_value": round(de_ratio, 2),
            "target_value": target_de,
            "delta": round(de_ratio - target_de, 2),
            "score_impact": round(score_gain, 1),
            "estimated_action": (
                f"Reduce D/E from {de_ratio:.2f} to below {target_de:.1f} — "
                f"repay ₹{debt_to_repay/100:.1f}Cr debt OR infuse ₹{equity_needed/100:.1f}Cr equity"
            ),
            "priority_rank": 2,
            "feasibility": "MEDIUM",
            "implementation_timeline": "3–6 months",
        })
        score_accumulated += score_gain

    # ── 3. DSCR improvement ───────────────────────────────────────────────────
    target_dscr = FACTOR_CONFIG["dscr"]["target_value"]
    if dscr < target_dscr:
        dscr_improvement = target_dscr - dscr
        score_gain = dscr_improvement * FACTOR_CONFIG["dscr"]["score_per_unit"] * 10
        score_gain = min(score_gain, max(0, gap - score_accumulated + 2))

        debt_service = total_debt * 0.15 if total_debt else 1
        ebitda_needed = target_dscr * debt_service
        ebitda_delta = max(0, ebitda_needed - (ebitda or 0))
        ebitda_pct = (ebitda_delta / ebitda * 100) if ebitda and ebitda > 0 else 0

        counterfactuals.append({
            "factor": "dscr",
            "label": "Debt Service Coverage Ratio",
            "current_value": round(dscr, 2),
            "target_value": target_dscr,
            "delta": round(target_dscr - dscr, 2),
            "score_impact": round(score_gain, 1),
            "estimated_action": (
                f"Improve DSCR from {dscr:.2f} to above {target_dscr:.2f} — "
                f"requires EBITDA improvement of ₹{ebitda_delta/100:.1f}Cr "
                f"({ebitda_pct:.0f}% improvement from current ₹{(ebitda or 0)/100:.1f}Cr)"
            ),
            "priority_rank": 3,
            "feasibility": "MEDIUM",
            "implementation_timeline": "6–12 months (operational improvement)",
        })
        score_accumulated += score_gain

    # ── 4. ITC Fraud resolution ───────────────────────────────────────────────
    if itc_fraud and suspect_itc > 0:
        score_gain = suspect_itc * FACTOR_CONFIG["itc_fraud"]["score_per_unit"]
        score_gain = min(score_gain, 10.0)
        counterfactuals.append({
            "factor": "itc_fraud",
            "label": "ITC Reconciliation Discrepancy",
            "current_value": f"₹{suspect_itc:.1f}Cr suspect ITC",
            "target_value": "₹0 discrepancy",
            "delta": round(suspect_itc, 2),
            "score_impact": round(score_gain, 1),
            "estimated_action": (
                f"Resolve ₹{suspect_itc:.1f}Cr ITC discrepancy — "
                "file revised GSTR-3B with GSTN, reconcile with supplier invoices, "
                "obtain GSTN clearance certificate"
            ),
            "priority_rank": 4,
            "feasibility": "MEDIUM",
            "implementation_timeline": "1–3 months (GSTN processing time)",
        })
        score_accumulated += score_gain

    # ── 5. Litigation resolution ──────────────────────────────────────────────
    if material_cases:
        score_gain = len(material_cases) * FACTOR_CONFIG["litigation"]["score_per_unit"]
        nclt_detail = ""
        if nclt_cases:
            nclt_detail = f" including NCLT petition {nclt_cases[0].get('case_id', '')} ₹{nclt_cases[0].get('claim_amount_cr', 0):.1f}Cr"

        counterfactuals.append({
            "factor": "litigation",
            "label": "Material Litigation",
            "current_value": f"{len(material_cases)} material case(s) totalling ₹{total_claim:.1f}Cr",
            "target_value": "0 material cases",
            "delta": len(material_cases),
            "score_impact": round(score_gain, 1),
            "estimated_action": (
                f"Resolve {len(material_cases)} material litigation case(s) "
                f"totalling ₹{total_claim:.1f}Cr{nclt_detail} — "
                "obtain court clearance certificates before disbursement"
            ),
            "priority_rank": 4,
            "feasibility": "LOW",
            "implementation_timeline": "6–24 months (court resolution timeline)",
        })
        score_accumulated += score_gain

    # ── 6. Buyer concentration diversification ────────────────────────────────
    target_buyer = FACTOR_CONFIG["buyer_concentration"]["target_value"]
    if top_buyer_pct > target_buyer:
        pct_reduction = top_buyer_pct - target_buyer
        score_gain = pct_reduction * FACTOR_CONFIG["buyer_concentration"]["score_per_unit"]
        score_gain = min(score_gain, 5.0)
        new_customers = max(3, int(pct_reduction / 10))

        counterfactuals.append({
            "factor": "buyer_concentration",
            "label": "Buyer Revenue Concentration",
            "current_value": f"{top_buyer_pct:.0f}% revenue from top buyer",
            "target_value": f"Below {target_buyer:.0f}%",
            "delta": round(pct_reduction, 1),
            "score_impact": round(score_gain, 1),
            "estimated_action": (
                f"Diversify revenue — reduce top buyer from {top_buyer_pct:.0f}% to below {target_buyer:.0f}% "
                f"by acquiring {new_customers}+ new customers of comparable size"
            ),
            "priority_rank": 5,
            "feasibility": "LOW",
            "implementation_timeline": "12–24 months (business development cycle)",
        })

    # Sort by priority_rank (lowest = highest priority)
    counterfactuals.sort(key=lambda x: x["priority_rank"])

    # For approved: compute buffer
    buffer_msg = None
    if decision == "APPROVE":
        buffer = current_score - APPROVE_THRESHOLD
        buffer_msg = (
            f"This application was APPROVED with a buffer of {buffer:.1f} points above threshold. "
            f"Score: {current_score:.0f}/100. Approval threshold: {APPROVE_THRESHOLD:.0f}. "
            f"Risk category: {risk_scores.get('risk_category')}."
        )

    return {
        "current_score": round(current_score, 1),
        "approve_threshold": APPROVE_THRESHOLD,
        "gap": round(gap, 1),
        "decision": decision,
        "buffer_message": buffer_msg,
        "total_achievable_improvement": round(sum(c["score_impact"] for c in counterfactuals), 1),
        "would_achieve_approval": score_accumulated >= gap,
        "counterfactuals": counterfactuals,
    }


async def run(app_id: str) -> dict:
    """Main entry point — runs after Agent 6. Also called standalone for the endpoint."""
    t = time.time()
    await log_agent(app_id, AGENT, "RUNNING")

    # Load all session data
    risk_scores = await get_session(app_id, "risk_scores") or {}
    ratios = await get_session(app_id, "ratios") or {}
    gst_recon = await get_session(app_id, "gst_reconciliation") or {}
    buyer_conc = await get_session(app_id, "buyer_concentration") or {}
    research = await get_session(app_id, "research_dossier") or {}

    # Load financials from DB
    async with _AgentSession() as session:
        fin_result = await session.execute(
            select(Financial)
            .where(Financial.application_id == app_id)
            .order_by(Financial.year.desc())
        )
        latest_fin = fin_result.scalars().first()
        financials = {}
        if latest_fin:
            financials = {
                "total_debt": latest_fin.total_debt,
                "net_worth": latest_fin.net_worth,
                "ebitda": latest_fin.ebitda,
                "revenue": latest_fin.revenue,
                "cash_from_operations": latest_fin.cash_from_operations,
            }

        # Load loan amount
        from app.models import Application
        app_result = await session.execute(
            select(Application).where(Application.id == app_id)
        )
        app_obj = app_result.scalar_one_or_none()
        loan_amount = app_obj.loan_amount_requested if app_obj else 500.0

    litigation_cases = research.get("litigation_cases", [])

    result = compute_counterfactuals(
        risk_scores=risk_scores,
        ratios=ratios,
        financials=financials,
        litigation_cases=litigation_cases,
        gst_recon=gst_recon,
        buyer_conc=buyer_conc,
        loan_amount=loan_amount,
    )

    # Save to cam_reports.counterfactuals
    async with _AgentSession() as session:
        cam_result = await session.execute(
            select(CAMReport).where(CAMReport.application_id == app_id)
        )
        cam = cam_result.scalar_one_or_none()
        if cam:
            cam.counterfactuals = result["counterfactuals"]
            await session.commit()

    await set_session(app_id, "counterfactuals", result)

    duration_ms = int((time.time() - t) * 1000)
    await log_agent(app_id, AGENT, "COMPLETED",
                    output_summary=f"Gap: {result['gap']}. {len(result['counterfactuals'])} factors. "
                                   f"Would achieve approval: {result['would_achieve_approval']}.",
                    duration_ms=duration_ms)
    return result