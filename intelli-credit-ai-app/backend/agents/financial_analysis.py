"""
Agent 2 — Financial Analysis Agent
Day 3 deliverable. Runs parallel after Agent 1.

Computes:
  - 15 financial ratios across 3 years
  - 7 anomaly detection rules → risk flags
"""
from __future__ import annotations
import time
import uuid
from datetime import datetime

from app.services.redis_service import set_session, get_session, publish_event
from app.services.db_helpers import log_agent, save_risk_flag, _AgentSession
from app.models import Financial, Ratio

AGENT = "financial_analysis"


# ── Ratio computation ─────────────────────────────────────
def compute_ratios(fin: dict) -> dict:
    """
    fin keys (all in ₹ Lakhs):
      revenue, ebitda, net_profit, total_debt, net_worth,
      cash_from_operations, total_assets, current_assets,
      current_liabilities, related_party_transactions,
      interest_expense (optional), debt_service (optional),
      inventory (optional), receivables (optional)
    """
    def safe_div(a, b, default=None):
        try:
            return round(a / b, 4) if b and b != 0 else default
        except Exception:
            return default

    r = {}
    rev = fin.get("revenue")
    ebitda = fin.get("ebitda")
    net_profit = fin.get("net_profit")
    total_debt = fin.get("total_debt")
    net_worth = fin.get("net_worth")
    cfo = fin.get("cash_from_operations")
    total_assets = fin.get("total_assets")
    current_assets = fin.get("current_assets")
    current_liab = fin.get("current_liabilities")
    rpt = fin.get("related_party_transactions")
    interest = fin.get("interest_expense")
    debt_service = fin.get("debt_service", total_debt * 0.15 if total_debt else None)
    inventory = fin.get("inventory")
    receivables = fin.get("receivables")

    # ── Liquidity ─────────────────────────────────────────
    r["current_ratio"] = safe_div(current_assets, current_liab)
    quick_assets = (current_assets - inventory) if (current_assets and inventory) else current_assets
    r["quick_ratio"] = safe_div(quick_assets, current_liab)
    cash = fin.get("cash_and_equivalents")
    r["cash_ratio"] = safe_div(cash, current_liab)

    # ── Leverage ──────────────────────────────────────────
    r["de_ratio"] = safe_div(total_debt, net_worth)
    r["debt_to_assets"] = safe_div(total_debt, total_assets)
    r["interest_coverage"] = safe_div(ebitda, interest) if interest else None

    # ── Profitability ─────────────────────────────────────
    r["net_profit_margin"] = safe_div(net_profit, rev)
    r["roe"] = safe_div(net_profit, net_worth)
    r["roa"] = safe_div(net_profit, total_assets)
    r["ebitda_margin"] = safe_div(ebitda, rev)

    # ── Efficiency ────────────────────────────────────────
    r["asset_turnover"] = safe_div(rev, total_assets)
    r["receivables_days"] = safe_div(receivables * 365, rev) if receivables else None
    r["inventory_days"] = safe_div(inventory * 365, rev) if inventory else None

    # ── Debt Service ──────────────────────────────────────
    r["dscr"] = safe_div(cfo, debt_service) if debt_service else None
    r["fixed_charge_coverage"] = safe_div(ebitda, debt_service) if debt_service else None

    # ── GST Health (filled by reconciliation engine) ──────
    r["gst_itr_variance"] = fin.get("gst_itr_variance_pct")  # populated later

    return {k: v for k, v in r.items()}


# ── Anomaly detection ─────────────────────────────────────
def detect_anomalies(
    ratios: dict,
    financials_by_year: list[dict],  # sorted ascending by year
) -> list[dict]:
    """
    Returns list of anomaly dicts:
    {flag_type, severity, description}
    """
    flags = []

    def flag(flag_type, severity, description):
        flags.append({"flag_type": flag_type, "severity": severity, "description": description})

    current = ratios  # most recent year ratios

    # ── 1. GST-ITR Mismatch ───────────────────────────────
    gst_itr_var = current.get("gst_itr_variance")
    if gst_itr_var is not None and abs(gst_itr_var) > 15:
        flag(
            "GST_ITR_MISMATCH",
            "HIGH",
            f"GST turnover vs ITR income variance is {gst_itr_var:.1f}% (threshold: 15%). "
            "Revenue underreporting suspected.",
        )

    # ── 2. Circular Trading ───────────────────────────────
    rec_days = current.get("receivables_days")
    if rec_days and rec_days > 180:
        flag(
            "CIRCULAR_TRADING",
            "HIGH",
            f"Receivables days = {rec_days:.0f} (threshold: 180). "
            "Circular trading pattern suspected.",
        )

    # ── 3. Inventory Inflation ────────────────────────────
    if len(financials_by_year) >= 2:
        prev = financials_by_year[-2]
        curr = financials_by_year[-1]
        inv_prev = prev.get("inventory")
        inv_curr = curr.get("inventory")
        rev_prev = prev.get("revenue")
        rev_curr = curr.get("revenue")
        if inv_prev and inv_curr and rev_prev and rev_curr and inv_prev > 0 and rev_prev > 0:
            inv_growth = (inv_curr - inv_prev) / inv_prev * 100
            rev_growth = (rev_curr - rev_prev) / rev_prev * 100
            if inv_growth > 40 and rev_growth < 5:
                flag(
                    "INVENTORY_INFLATION",
                    "HIGH",
                    f"Inventory grew {inv_growth:.1f}% but revenue grew only {rev_growth:.1f}%. "
                    "Inventory inflation or demand collapse suspected.",
                )

    # ── 4. Profit-Cash Divergence ─────────────────────────
    cfo = current.get("cash_from_operations") if hasattr(current, "get") else None
    # We need raw financial values here
    # This check is done directly below using raw_fin dict
    # (passed separately — see run() below)

    # ── 5. Related Party Risk ─────────────────────────────
    rpt_val = None  # fetched from financials in run()
    # Placeholder — computed in run() with access to raw financials

    # ── 6. High Leverage ──────────────────────────────────
    de = current.get("de_ratio")
    if de and de > 3:
        flag(
            "HIGH_LEVERAGE",
            "HIGH",
            f"D/E ratio = {de:.2f} (threshold: 3.0). Excessive leverage detected.",
        )

    # ── 7. Revenue Decline ────────────────────────────────
    if len(financials_by_year) >= 3:
        revenues = [f.get("revenue") for f in financials_by_year if f.get("revenue")]
        if len(revenues) >= 2 and revenues[-1] < revenues[0]:
            cagr = ((revenues[-1] / revenues[0]) ** (1 / (len(revenues) - 1)) - 1) * 100
            if cagr < 0:
                flag(
                    "REVENUE_DECLINE",
                    "MEDIUM",
                    f"3-year revenue CAGR = {cagr:.1f}%. Declining revenue trend.",
                )

    return flags


# ── DB write ──────────────────────────────────────────────
async def save_ratios(app_id: str, year: int, ratios: dict):
    import uuid as _uuid
    async with _AgentSession() as session:
        ratio = Ratio(
            id=str(_uuid.uuid4()),
            application_id=app_id,
            year=year,
            **{k: v for k, v in ratios.items() if v is not None},
        )
        session.add(ratio)
        await session.commit()


# ── Main entry point ──────────────────────────────────────
async def run(app_id: str, extracted_financials: dict) -> dict:
    t = time.time()
    await log_agent(app_id, AGENT, "RUNNING")
    await publish_event(app_id, {
        "event_type": "AGENT_STARTED",
        "agent_name": AGENT,
        "payload": {},
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Fetch multi-year financials from DB
    from sqlalchemy import select
    async with _AgentSession() as session:
        result = await session.execute(
            select(Financial).where(Financial.application_id == app_id).order_by(Financial.year)
        )
        db_financials = result.scalars().all()

    financials_by_year = [
        {
            "year": f.year,
            "revenue": f.revenue,
            "ebitda": f.ebitda,
            "net_profit": f.net_profit,
            "total_debt": f.total_debt,
            "net_worth": f.net_worth,
            "cash_from_operations": f.cash_from_operations,
            "total_assets": f.total_assets,
            "current_assets": f.current_assets,
            "current_liabilities": f.current_liabilities,
            "related_party_transactions": f.related_party_transactions,
        }
        for f in db_financials
    ]

    # Fall back to extracted_financials if DB is empty (first run)
    if not financials_by_year and extracted_financials:
        financials_by_year = [extracted_financials]

    all_ratios = {}
    all_flags = []

    for fin in financials_by_year:
        year = fin.get("year", datetime.utcnow().year)
        ratios = compute_ratios(fin)
        all_ratios[year] = ratios
        await save_ratios(app_id, year, ratios)

    # ── Anomaly detection on latest year ─────────────────
    if financials_by_year:
        latest_ratios = all_ratios.get(max(all_ratios.keys()), {}) if all_ratios else {}
        flags = detect_anomalies(latest_ratios, financials_by_year)

        # Extra checks with raw financial values
        latest_fin = financials_by_year[-1]
        rev = latest_fin.get("revenue", 1) or 1
        cfo = latest_fin.get("cash_from_operations")
        net_profit = latest_fin.get("net_profit")
        rpt = latest_fin.get("related_party_transactions")

        if cfo is not None and net_profit is not None and cfo < 0 and net_profit > 0:
            flags.append({
                "flag_type": "PROFIT_CASH_DIVERGENCE",
                "severity": "CRITICAL",
                "description": (
                    f"Cash from operations (₹{cfo:.0f}L) is negative while "
                    f"net profit (₹{net_profit:.0f}L) is positive. "
                    "Classic earnings manipulation signal."
                ),
            })

        if rpt and rev:
            rpt_pct = (rpt / rev) * 100
            if rpt_pct > 30:
                flags.append({
                    "flag_type": "RELATED_PARTY_RISK",
                    "severity": "HIGH",
                    "description": (
                        f"Related party transactions = {rpt_pct:.1f}% of revenue "
                        "(threshold: 30%). Tunnelling risk."
                    ),
                })

        # Save flags and emit WebSocket events
        for f in flags:
            await save_risk_flag(app_id, f["flag_type"], f["severity"], f["description"], AGENT)
        all_flags = flags

    # ── Write to Redis ────────────────────────────────────
    await set_session(app_id, "ratios", all_ratios)
    await set_session(app_id, "anomaly_flags", all_flags)

    duration_ms = int((time.time() - t) * 1000)
    summary = f"Computed ratios for {len(all_ratios)} year(s). Detected {len(all_flags)} anomalies."
    await log_agent(app_id, AGENT, "COMPLETED", output_summary=summary, duration_ms=duration_ms)
    await publish_event(app_id, {
        "event_type": "AGENT_COMPLETED",
        "agent_name": AGENT,
        "payload": {"summary": summary, "duration_ms": duration_ms},
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {"ratios": all_ratios, "anomaly_flags": all_flags}