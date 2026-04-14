"""
Buyer Concentration Engine — Day 3 deliverable.

Uses GSTR-1 (outward supply invoices — every B2B invoice the borrower raised)
to compute revenue concentration by buyer GSTIN.

This is genuinely novel: even Perfios and Crediwatch with full bank statement
analysis cannot compute this — they don't have GST invoice-level counterparty data.

Flags:
  SINGLE_BUYER_DEPENDENCY: single buyer > 40% of revenue → CRITICAL
  HIGH_BUYER_CONCENTRATION: top 3 buyers > 60% of revenue → HIGH

Endpoint: GET /api/applications/{id}/buyer-concentration
"""
from __future__ import annotations
import uuid
import time
import httpx
from datetime import datetime
from collections import defaultdict

from app.services.redis_service import get_session, set_session, publish_event
from app.services.db_helper import log_agent, save_risk_flag, _AgentSession
from app.models import BuyerConcentration
from app.config import settings

AGENT = "buyer_concentration_engine"
SINGLE_BUYER_THRESHOLD = 40.0   # % — critical if single buyer > this
TOP3_THRESHOLD = 60.0            # % — high risk if top 3 > this


async def fetch_gstr1_invoices(gstin: str, financial_year: str) -> list[dict]:
    """Fetch GSTR-1 B2B invoice data from Sandbox.co.in."""
    if not settings.sandbox_api_key:
        return []  # No fallback — return empty, caller handles it

    headers = {
        "x-api-key": settings.sandbox_api_key,
        "x-api-secret": getattr(settings, "sandbox_secret_key", ""),
        "x-api-version": "1.0",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.sandbox_base_url}/gsp/gstr1/b2b",
                headers=headers,
                params={"gstin": gstin, "financial_year": financial_year},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("invoices", data.get("b2b", []))
    except Exception:
        pass
    return []


async def resolve_buyer_name(buyer_gstin: str) -> str | None:
    """Lookup buyer name from GSTIN via Sandbox.co.in."""
    if not settings.sandbox_api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{settings.sandbox_base_url}/gstin/{buyer_gstin}",
                headers={"x-api-key": settings.sandbox_api_key},
            )
            if resp.status_code == 200:
                return resp.json().get("tradeName") or resp.json().get("legalName")
    except Exception:
        pass
    return None


def compute_concentration(invoices: list[dict]) -> dict:
    """
    Group invoices by buyer_gstin, sum totals, compute concentration %.
    """
    totals: dict[str, dict] = defaultdict(lambda: {"invoice_total": 0.0, "buyer_name": None})

    for inv in invoices:
        gstin = inv.get("buyer_gstin", "UNKNOWN")
        totals[gstin]["invoice_total"] += inv.get("invoice_total", 0)
        if inv.get("buyer_name"):
            totals[gstin]["buyer_name"] = inv["buyer_name"]

    grand_total = sum(v["invoice_total"] for v in totals.values()) or 1.0

    buyers = sorted(
        [
            {
                "buyer_gstin": gstin,
                "buyer_name": v["buyer_name"],
                "invoice_total": round(v["invoice_total"], 2),
                "pct_of_revenue": round((v["invoice_total"] / grand_total) * 100, 2),
            }
            for gstin, v in totals.items()
        ],
        key=lambda x: x["invoice_total"],
        reverse=True,
    )

    top3_pct = sum(b["pct_of_revenue"] for b in buyers[:3])
    top_buyer_pct = buyers[0]["pct_of_revenue"] if buyers else 0

    return {
        "top_buyers": buyers,
        "total_buyers": len(buyers),
        "top3_concentration_pct": round(top3_pct, 2),
        "top_buyer_pct": round(top_buyer_pct, 2),
        "single_buyer_dependency": top_buyer_pct > SINGLE_BUYER_THRESHOLD,
        "high_concentration": top3_pct > TOP3_THRESHOLD,
        "grand_total_revenue_lakhs": round(grand_total, 2),
    }


async def save_buyer_records(app_id: str, buyers: list[dict], flags: dict):
    """Write per-buyer records to buyer_concentration table."""
    async with _AgentSession() as session:
        for b in buyers:
            is_flagged = (
                b["pct_of_revenue"] > SINGLE_BUYER_THRESHOLD or
                flags.get("single_buyer_dependency") or
                flags.get("high_concentration")
            )
            rec = BuyerConcentration(
                id=str(uuid.uuid4()),
                application_id=app_id,
                buyer_gstin=b["buyer_gstin"],
                buyer_name=b.get("buyer_name"),
                invoice_total=b["invoice_total"],
                pct_of_revenue=b["pct_of_revenue"],
                concentration_risk_flag=is_flagged,
            )
            session.add(rec)
        await session.commit()


async def run(app_id: str) -> dict:
    """
    Main entry point called by LangGraph DAG (parallel).
    Reads gst_raw (for GSTIN) from Redis — set by Agent 1.
    """
    t = time.time()
    await log_agent(app_id, AGENT, "RUNNING")
    await publish_event(app_id, {
        "event_type": "AGENT_STARTED",
        "agent_name": AGENT,
        "payload": {},
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Get GSTIN and financial year from session
    extracted = await get_session(app_id, "extracted_financials") or {}
    gstin = extracted.get("gstin", "")
    year = extracted.get("year", datetime.utcnow().year)
    financial_year = f"{year - 1}-{str(year)[2:]}"  # e.g. "2023-24"

    result = {
        "app_id": app_id,
        "gstin": gstin,
        "financial_year": financial_year,
        "top_buyers": [],
        "total_buyers": 0,
        "top3_concentration_pct": 0.0,
        "top_buyer_pct": 0.0,
        "single_buyer_dependency": False,
        "high_concentration": False,
        "grand_total_revenue_lakhs": 0.0,
    }

    if not gstin:
        result["note"] = "GSTIN not found — buyer concentration analysis skipped."
        await set_session(app_id, "buyer_concentration", result)
        await log_agent(app_id, AGENT, "COMPLETED",
                        output_summary="Skipped — GSTIN not available.", duration_ms=0)
        return result

    # Fetch GSTR-1 invoice data
    invoices = await fetch_gstr1_invoices(gstin, financial_year)

    if invoices:
        concentration = compute_concentration(invoices)
        result.update(concentration)

        # ── Save to DB ────────────────────────────────────
        await save_buyer_records(app_id, concentration["top_buyers"], concentration)

        # ── Risk flags ────────────────────────────────────
        top_buyer = concentration["top_buyers"][0] if concentration["top_buyers"] else {}

        if concentration["single_buyer_dependency"]:
            await save_risk_flag(
                app_id,
                "SINGLE_BUYER_DEPENDENCY",
                "CRITICAL",
                (
                    f"Single buyer '{top_buyer.get('buyer_name', top_buyer.get('buyer_gstin'))}' "
                    f"accounts for {concentration['top_buyer_pct']:.1f}% of total revenue "
                    f"(₹{top_buyer.get('invoice_total', 0):.0f}L). "
                    f"GSTIN: {top_buyer.get('buyer_gstin')}. "
                    "Critical single-customer dependency — any loss of this buyer directly threatens debt servicing."
                ),
                AGENT,
            )

        elif concentration["high_concentration"]:
            await save_risk_flag(
                app_id,
                "HIGH_BUYER_CONCENTRATION",
                "HIGH",
                (
                    f"Top 3 buyers account for {concentration['top3_concentration_pct']:.1f}% of revenue "
                    f"(threshold: {TOP3_THRESHOLD}%). "
                    "High revenue concentration — loss of key buyers materially impacts debt repayment."
                ),
                AGENT,
            )

        await publish_event(app_id, {
            "event_type": "FIELD_EXTRACTED",
            "agent_name": AGENT,
            "payload": {
                "field": "buyer_concentration",
                "top3_pct": concentration["top3_concentration_pct"],
                "top_buyer_pct": concentration["top_buyer_pct"],
            },
            "timestamp": datetime.utcnow().isoformat(),
        })
    else:
        result["note"] = "No GSTR-1 invoice data available."

    await set_session(app_id, "buyer_concentration", result)

    duration_ms = int((time.time() - t) * 1000)
    summary = (
        f"Buyer concentration: Top buyer {result['top_buyer_pct']:.1f}%, "
        f"Top 3: {result['top3_concentration_pct']:.1f}%. "
        f"Single buyer dependency: {result['single_buyer_dependency']}."
    )
    await log_agent(app_id, AGENT, "COMPLETED", output_summary=summary, duration_ms=duration_ms)
    await publish_event(app_id, {
        "event_type": "AGENT_COMPLETED",
        "agent_name": AGENT,
        "payload": {"summary": summary, "duration_ms": duration_ms},
        "timestamp": datetime.utcnow().isoformat(),
    })

    return result