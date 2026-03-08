"""
GST Reconciliation Engine — Day 3 deliverable.

Checks:
  GSTR-2A (auto-populated from supplier filings — what ITC is actually available)
  vs GSTR-3B (self-declared by borrower — what ITC they claimed)

If borrower claimed more ITC than available → ITC_FRAUD_SUSPECTED (CRITICAL)
If outward supplies in GSTR-1 don't match GSTR-3B → OUTPUT_SUPPRESSION_SUSPECTED

Endpoint: GET /api/applications/{id}/gst-reconciliation
"""
from __future__ import annotations
import time
import uuid
from datetime import datetime

from app.services.redis_service import get_session, set_session, publish_event
from app.services.db_helpers import log_agent, save_risk_flag, _AgentSession
from app.config import settings

AGENT = "gst_reconciliation_engine"
ITC_VARIANCE_THRESHOLD = 10.0   # % — flag if claimed ITC > available ITC by this %
OUTPUT_VARIANCE_THRESHOLD = 15.0  # % — flag if output supply mismatch


def reconcile_quarters(gstr2a: dict, gstr3b: dict) -> dict:
    """
    Reconcile per quarter.
    gstr2a.quarterly_itc_available: [{quarter, itc_available}]
    gstr3b.quarterly_turnover: [{quarter, turnover, itc_claimed}]
    Returns reconciliation waterfall.
    """
    itc_map = {q["quarter"]: q["itc_available"] for q in gstr2a.get("quarterly_itc_available", [])}
    quarters_output = []
    total_suspect_itc = 0.0
    any_flagged = False

    for q_data in gstr3b.get("quarterly_turnover", []):
        quarter = q_data["quarter"]
        itc_claimed = q_data.get("itc_claimed", 0) or 0
        itc_available = itc_map.get(quarter, 0) or 0

        if itc_available > 0:
            variance_pct = ((itc_claimed - itc_available) / itc_available) * 100
        else:
            variance_pct = 100.0 if itc_claimed > 0 else 0.0

        flagged = variance_pct > ITC_VARIANCE_THRESHOLD
        if flagged:
            suspect_amount = itc_claimed - itc_available
            total_suspect_itc += max(suspect_amount, 0)
            any_flagged = True

        quarters_output.append({
            "quarter": quarter,
            "gstr2a_itc_available": round(itc_available, 2),
            "gstr3b_itc_claimed": round(itc_claimed, 2),
            "variance_pct": round(variance_pct, 2),
            "suspect_itc_amount": round(max(itc_claimed - itc_available, 0), 2),
            "flagged": flagged,
        })

    return {
        "quarters": quarters_output,
        "total_suspect_itc_lakhs": round(total_suspect_itc, 2),
        "any_flagged": any_flagged,
        "itc_fraud_suspected": any_flagged,
    }


async def run(app_id: str) -> dict:
    """
    Main entry point called by LangGraph DAG (parallel with Agent 2+3).
    Reads gst_raw from Redis (written by Agent 1 via Sandbox.co.in).
    """
    t = time.time()
    await log_agent(app_id, AGENT, "RUNNING")
    await publish_event(app_id, {
        "event_type": "AGENT_STARTED",
        "agent_name": AGENT,
        "payload": {},
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Read GST raw data set by Agent 1
    gst_raw = await get_session(app_id, "gst_raw") or {}
    gstr2a = gst_raw.get("gstr2a", {})
    gstr3b = gst_raw.get("gstr3b", {})

    result = {
        "app_id": app_id,
        "gstin": gstr3b.get("gstin", "UNKNOWN"),
        "financial_year": gstr3b.get("financial_year", "FY2024"),
        "quarters": [],
        "total_suspect_itc_lakhs": 0.0,
        "itc_fraud_suspected": False,
        "output_suppression_suspected": False,
        "source": gstr2a.get("source", "UNKNOWN"),
    }

    if gstr2a and gstr3b:
        recon = reconcile_quarters(gstr2a, gstr3b)
        result.update(recon)

        # ── Save risk flags ───────────────────────────────
        if recon["itc_fraud_suspected"]:
            await save_risk_flag(
                app_id,
                "ITC_FRAUD_SUSPECTED",
                "CRITICAL",
                (
                    f"GSTR-2A vs GSTR-3B reconciliation detected ₹{recon['total_suspect_itc_lakhs']:.2f}L "
                    f"in excess ITC claims across {sum(1 for q in recon['quarters'] if q['flagged'])} quarter(s). "
                    "Borrower has claimed Input Tax Credit not matched by supplier filings."
                ),
                AGENT,
            )

        # ── Check output suppression (GSTR-1 vs GSTR-3B) ─
        # If GSTR-1 outward supply total (from gst_raw if available) differs from 3B declared turnover
        gstr1 = gst_raw.get("gstr1", {})
        if gstr1:
            gstr1_total = sum(q.get("invoice_total", 0) for q in gstr1.get("invoices", []))
            gstr3b_turnover = sum(q.get("turnover", 0) for q in gstr3b.get("quarterly_turnover", []))
            if gstr3b_turnover > 0:
                out_var = abs((gstr1_total - gstr3b_turnover) / gstr3b_turnover) * 100
                if out_var > OUTPUT_VARIANCE_THRESHOLD:
                    result["output_suppression_suspected"] = True
                    await save_risk_flag(
                        app_id,
                        "OUTPUT_SUPPRESSION_SUSPECTED",
                        "CRITICAL",
                        (
                            f"GSTR-1 declared outward supply (₹{gstr1_total:.0f}L) "
                            f"differs from GSTR-3B turnover (₹{gstr3b_turnover:.0f}L) "
                            f"by {out_var:.1f}%. Output suppression suspected."
                        ),
                        AGENT,
                    )
    else:
        # No GST data — flag for manual review
        result["note"] = "GST data not available. Manual GST review required."

    await set_session(app_id, "gst_reconciliation", result)

    duration_ms = int((time.time() - t) * 1000)
    summary = (
        f"GST reconciliation complete. "
        f"ITC fraud suspected: {result['itc_fraud_suspected']}. "
        f"Suspect ITC: ₹{result['total_suspect_itc_lakhs']:.2f}L."
    )
    await log_agent(app_id, AGENT, "COMPLETED", output_summary=summary, duration_ms=duration_ms)
    await publish_event(app_id, {
        "event_type": "AGENT_COMPLETED",
        "agent_name": AGENT,
        "payload": {"summary": summary, "duration_ms": duration_ms},
        "timestamp": datetime.utcnow().isoformat(),
    })

    return result