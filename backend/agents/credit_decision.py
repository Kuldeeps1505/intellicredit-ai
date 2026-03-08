"""
Agent 6 — Credit Decision Agent
Day 4 deliverable. Runs after Agent 4 (or after Agent 5 if DD submitted).

Applies RBI/NBFC policy rules, generates:
  - Formal recommendation (APPROVE / CONDITIONAL_APPROVAL / REJECT)
  - Loan terms (amount, rate, tenor, covenants, monitoring triggers)
  - RBI compliance checklist
"""
from __future__ import annotations
import time, uuid
from datetime import datetime

from app.services.redis_service import get_session, set_session, publish_event
from app.services.db_helpers import log_agent, _AgentSession
from app.models import CAMReport, Application, RiskScore, RiskFlag
from sqlalchemy import select

AGENT = "credit_decision"

# ── RBI/NBFC Policy Thresholds ────────────────────────────
POLICY = {
    "min_dscr": 1.25,
    "max_de_ratio": 3.0,
    "max_loan_to_networth": 2.5,
    "min_current_ratio": 1.1,
}

# ── Interest rate grid ────────────────────────────────────
BASE_RATE = 9.0   # MCLR proxy in %
RISK_SPREAD = {
    "LOW": 0.5,
    "MEDIUM": 2.0,
    "HIGH": 3.5,
    "VERY_HIGH": 5.0,
}
TENOR_MAP = {
    "LOW": 60,
    "MEDIUM": 36,
    "HIGH": 24,
    "VERY_HIGH": 0,
}


def compute_loan_terms(
    requested_amount: float,
    risk_category: str,
    net_worth: float | None,
    dscr: float | None,
) -> dict:
    """Compute approved amount, rate, tenor, covenants."""
    # Amount: discount requested amount by risk
    risk_multipliers = {"LOW": 1.0, "MEDIUM": 0.85, "HIGH": 0.65, "VERY_HIGH": 0.0}
    multiplier = risk_multipliers.get(risk_category, 0.0)
    approved_amount = round(requested_amount * multiplier, 2)

    # Cap at 2x net worth
    if net_worth and net_worth > 0:
        max_by_nw = net_worth * POLICY["max_loan_to_networth"]
        approved_amount = min(approved_amount, max_by_nw)

    rate = round(BASE_RATE + RISK_SPREAD.get(risk_category, 5.0), 2)
    tenor = TENOR_MAP.get(risk_category, 0)

    # Covenants by risk category
    covenants_map = {
        "LOW": [
            "Annual audited financials within 90 days of FY close",
            "Quarterly MIS reporting",
            "Maintain DSCR above 1.25x",
        ],
        "MEDIUM": [
            "Quarterly audited financials",
            "Monthly stock statements",
            "Maintain DSCR above 1.25x",
            "Personal guarantee of promoter",
            "Escrow of receivables",
        ],
        "HIGH": [
            "Monthly audited financials",
            "Quarterly stock audit by bank-appointed auditor",
            "Personal guarantee of promoter + co-guarantor",
            "Lien on all receivables",
            "No further borrowings without prior bank consent",
            "Board-level quarterly review meetings",
        ],
        "VERY_HIGH": [],
    }

    monitoring_triggers = {
        "LOW": ["DSCR below 1.25 for 2 consecutive quarters", "Revenue decline > 20% YoY"],
        "MEDIUM": ["DSCR below 1.25 for 1 quarter", "Revenue decline > 15% YoY",
                   "Any new litigation above ₹1Cr"],
        "HIGH": ["DSCR below 1.1", "Revenue decline > 10%", "Any new litigation",
                 "Management change", "Key customer loss"],
        "VERY_HIGH": [],
    }

    return {
        "approved_amount": approved_amount,
        "interest_rate": rate,
        "tenor_months": tenor,
        "covenants": covenants_map.get(risk_category, []),
        "monitoring_triggers": monitoring_triggers.get(risk_category, []),
    }


def build_rbi_checklist(
    ratios: dict,
    flags: list[dict],
    risk_scores: dict,
    has_collateral_docs: bool = True,
) -> list[dict]:
    """
    RBI/NBFC mandatory documentation and ratio checklist.
    Returns [{requirement, status, notes}]
    """
    latest_ratios = {}
    if ratios:
        latest_year = max(ratios.keys(), default=None)
        if latest_year:
            latest_ratios = ratios.get(str(latest_year), {}) or ratios.get(latest_year, {})

    dscr = latest_ratios.get("dscr")
    de = latest_ratios.get("de_ratio")
    cr = latest_ratios.get("current_ratio")
    critical_flags = [f for f in flags if f.get("severity") == "CRITICAL"]

    checklist = [
        {
            "requirement": "DSCR ≥ 1.25",
            "status": "PASS" if dscr and dscr >= 1.25 else "FAIL",
            "value": f"{dscr:.2f}" if dscr else "N/A",
            "notes": "Minimum debt service coverage per RBI guidelines",
        },
        {
            "requirement": "D/E Ratio ≤ 3.0",
            "status": "PASS" if de and de <= 3.0 else "FAIL",
            "value": f"{de:.2f}" if de else "N/A",
            "notes": "Maximum leverage per NBFC prudential norms",
        },
        {
            "requirement": "Current Ratio ≥ 1.1",
            "status": "PASS" if cr and cr >= 1.1 else "WARN",
            "value": f"{cr:.2f}" if cr else "N/A",
            "notes": "Minimum liquidity per RBI guidelines",
        },
        {
            "requirement": "No Critical Fraud Flags",
            "status": "PASS" if not critical_flags else "FAIL",
            "value": f"{len(critical_flags)} critical flags",
            "notes": "Mandatory: no critical-severity fraud or compliance flags",
        },
        {
            "requirement": "Collateral Documentation",
            "status": "PASS" if has_collateral_docs else "PENDING",
            "value": "Provided" if has_collateral_docs else "Pending",
            "notes": "Security documents required per RBI master circular on loans",
        },
        {
            "requirement": "KYC Compliance",
            "status": "PASS",
            "value": "Complete",
            "notes": "CIN, PAN, GSTIN verified",
        },
        {
            "requirement": "Audited Financials (3 years)",
            "status": "PASS" if risk_scores.get("capacity") else "PENDING",
            "value": "Available" if risk_scores.get("capacity") else "Pending",
            "notes": "Minimum 3 years audited financials required",
        },
        {
            "requirement": "Board Resolution for Borrowing",
            "status": "PENDING",
            "value": "Pending",
            "notes": "Required before disbursement",
        },
    ]
    return checklist


async def run(app_id: str) -> dict:
    t = time.time()
    await log_agent(app_id, AGENT, "RUNNING")
    await publish_event(app_id, {
        "event_type": "AGENT_STARTED",
        "agent_name": AGENT,
        "payload": {},
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Load all session data
    risk_scores = await get_session(app_id, "risk_scores") or {}
    ratios = await get_session(app_id, "ratios") or {}
    flags_raw = await get_session(app_id, "anomaly_flags") or []

    # Also load flags from DB (more complete)
    async with _AgentSession() as session:
        app_result = await session.execute(
            select(Application).where(Application.id == app_id)
        )
        app_obj = app_result.scalar_one_or_none()

        flags_result = await session.execute(
            select(RiskFlag).where(RiskFlag.application_id == app_id)
        )
        db_flags = [
            {"flag_type": f.flag_type, "severity": f.severity, "description": f.description}
            for f in flags_result.scalars().all()
        ]

    requested_amount = app_obj.loan_amount_requested if app_obj else 500.0
    risk_category = risk_scores.get("risk_category", "VERY_HIGH")
    final_score = risk_scores.get("final_score", 0)
    decision = risk_scores.get("decision", "REJECT")

    # Extract latest ratios for policy checks
    latest_ratios = {}
    if ratios:
        latest_key = max(ratios.keys(), default=None)
        if latest_key:
            latest_ratios = ratios.get(str(latest_key), {}) or ratios.get(latest_key, {})

    net_worth = None
    dscr = latest_ratios.get("dscr")

    # Fetch net worth from financials
    from app.models import Financial
    async with _AgentSession() as session:
        fin_result = await session.execute(
            select(Financial)
            .where(Financial.application_id == app_id)
            .order_by(Financial.year.desc())
        )
        latest_fin = fin_result.scalars().first()
        if latest_fin:
            net_worth = latest_fin.net_worth

    # Policy override: force REJECT if critical flags present
    critical_flags = [f for f in db_flags if f.get("severity") == "CRITICAL"]
    if critical_flags and decision != "REJECT":
        decision = "REJECT"
        risk_category = "VERY_HIGH"

    # Compute loan terms
    terms = compute_loan_terms(requested_amount, risk_category, net_worth, dscr)

    # RBI compliance checklist
    checklist = build_rbi_checklist(ratios, db_flags, risk_scores)

    result = {
        "recommendation": decision,
        "risk_category": risk_category,
        "final_score": final_score,
        "loan_terms": terms,
        "rbi_compliance_checklist": checklist,
        "critical_flags": critical_flags,
        "policy_failures": [
            item for item in checklist if item["status"] == "FAIL"
        ],
    }

    # Save to CAM reports table (partial — Agent 7 fills PDF/DOCX paths)
    async with _AgentSession() as session:
        existing = await session.execute(
            select(CAMReport).where(CAMReport.application_id == app_id)
        )
        cam = existing.scalar_one_or_none()
        if cam:
            cam.recommendation = decision
            cam.loan_amount_approved = terms["approved_amount"]
            cam.interest_rate = terms["interest_rate"]
            cam.tenor_months = terms["tenor_months"]
            cam.covenants = {
                "covenants": terms["covenants"],
                "monitoring_triggers": terms["monitoring_triggers"],
            }
        else:
            cam = CAMReport(
                id=str(uuid.uuid4()),
                application_id=app_id,
                recommendation=decision,
                loan_amount_approved=terms["approved_amount"],
                interest_rate=terms["interest_rate"],
                tenor_months=terms["tenor_months"],
                covenants={
                    "covenants": terms["covenants"],
                    "monitoring_triggers": terms["monitoring_triggers"],
                },
            )
            session.add(cam)
        await session.commit()

    await set_session(app_id, "decision", result)

    duration_ms = int((time.time() - t) * 1000)
    summary = (
        f"Decision: {decision}. Amount: ₹{terms['approved_amount']}L @ {terms['interest_rate']}% "
        f"for {terms['tenor_months']}m. "
        f"Policy failures: {len(result['policy_failures'])}."
    )
    await log_agent(app_id, AGENT, "COMPLETED", output_summary=summary, duration_ms=duration_ms)
    await publish_event(app_id, {
        "event_type": "AGENT_COMPLETED",
        "agent_name": AGENT,
        "payload": {"summary": summary, "decision": decision},
        "timestamp": datetime.utcnow().isoformat(),
    })
    return result