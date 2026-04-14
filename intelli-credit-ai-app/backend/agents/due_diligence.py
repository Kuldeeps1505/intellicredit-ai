"""
Agent 5 — Due Diligence Agent
Day 4 deliverable.

Triggered by: POST /api/applications/{id}/dd-notes
Flow:
  1. Receive free-text officer observations
  2. Claude API parses observations → structured risk signals
  3. Recalculate final risk score (base + all DD deltas)
  4. Update risk_scores table
  5. Publish DD_SCORE_UPDATED WebSocket event
"""
from __future__ import annotations
import re, json, uuid, time
from datetime import datetime

# anthropic removed � using llm_service instead

from app.services.redis_service import get_session, set_session, publish_event
from app.services.db_helper import log_agent, _AgentSession
from app.models import DDNote, RiskScore
from app.config import settings

AGENT = "due_diligence"

VALID_CATEGORIES = {
    "OPERATIONAL_EFFICIENCY",
    "MANAGEMENT_TRANSPARENCY",
    "ASSET_QUALITY",
    "COMPLIANCE",
    "MARKET_POSITION",
}

# Template fallback when Claude API unavailable
KEYWORD_MAP = [
    (["capacity", "utilization", "%", "percent"], "OPERATIONAL_EFFICIENCY", +8,
     "Low capacity utilization indicates operational stress and potential revenue shortfall."),
    (["inventory", "high", "excess", "piled"], "OPERATIONAL_EFFICIENCY", +5,
     "Unusually high inventory may signal demand collapse or circular trading."),
    (["reluctant", "refused", "deny", "auditor", "document", "share"], "MANAGEMENT_TRANSPARENCY", +6,
     "Management reluctance to share documents is a critical governance red flag."),
    (["idle", "equipment", "machinery", "shutdown"], "OPERATIONAL_EFFICIENCY", +5,
     "Idle equipment suggests reduced operational capacity."),
    (["litigation", "case", "court", "lawsuit", "notice"], "COMPLIANCE", +7,
     "Active litigation detected from site observation."),
    (["pledge", "encumber", "lien", "asset", "mortgaged"], "ASSET_QUALITY", +6,
     "Encumbered assets reduce effective collateral quality."),
    (["staff", "employees", "workforce", "reduced", "laid off"], "MARKET_POSITION", +5,
     "Workforce reduction indicates business stress."),
    (["expanding", "new order", "contract", "growing", "positive"], "MARKET_POSITION", -3,
     "Positive operational signals — reduces risk."),
    (["clean", "organized", "efficient", "transparent"], "MANAGEMENT_TRANSPARENCY", -2,
     "Management transparency and operational cleanliness — positive signal."),
]


def parse_observations_with_llm(officer_text: str) -> list[dict]:
    """Parse DD observations using Ollama → Anthropic → fallback."""
    from app.services.llm_service import llm_complete_sync
    prompt = f"""You are a senior credit risk analyst at an Indian bank.
Parse these field observations from a credit officer's site visit:

\"\"\"{officer_text}\"\"\"

Output a JSON array of risk signals. Each signal must have:
- signal_type: short identifier (snake_case)
- description: what was observed (1 sentence)
- risk_category: one of OPERATIONAL_EFFICIENCY | MANAGEMENT_TRANSPARENCY | ASSET_QUALITY | COMPLIANCE | MARKET_POSITION
- risk_points_delta: integer -10 to +15 (positive = increased risk)
- reasoning: why this matters for credit risk (1 sentence)

Respond with ONLY valid JSON array, no markdown."""

    try:
        text = llm_complete_sync(prompt, max_tokens=600,
                                  system="You are a credit risk analyst. Respond only with valid JSON.")
        if text:
            text = re.sub(r"^```(?:json)?\s*", "", text.strip())
            text = re.sub(r"\s*```$", "", text)
            signals = json.loads(text)
            for s in signals:
                if s.get("risk_category") not in VALID_CATEGORIES:
                    s["risk_category"] = "OPERATIONAL_EFFICIENCY"
            return signals
    except Exception:
        pass
    return []


def parse_observations_fallback(officer_text: str) -> list[dict]:
    """Rule-based fallback when Claude API unavailable."""
    text_lower = officer_text.lower()
    signals = []
    for keywords, category, delta, reasoning in KEYWORD_MAP:
        if any(kw in text_lower for kw in keywords):
            signals.append({
                "signal_type": category,
                "description": next((kw for kw in keywords if kw in text_lower), keywords[0]),
                "risk_category": category,
                "risk_points_delta": delta,
                "reasoning": reasoning,
            })
    return signals


async def recalculate_score(app_id: str, total_dd_delta: float) -> dict:
    """
    Recalculate final risk score = base_score + total_dd_delta.
    Updates risk_scores table and Redis.
    """
    from sqlalchemy import select
    async with _AgentSession() as session:
        result = await session.execute(
            select(RiskScore)
            .where(RiskScore.application_id == app_id)
            .order_by(RiskScore.computed_at.desc())
        )
        risk = result.scalar_one_or_none()
        if not risk:
            return {}

        old_score = risk.final_score or 0
        # DD delta is SUBTRACTED from score (risk increases = score decreases)
        new_score = max(0.0, min(100.0, old_score - total_dd_delta))
        risk.final_score = round(new_score, 1)

        # Recalculate category
        if new_score >= 75:
            risk.risk_category, risk.decision = "LOW", "APPROVE"
        elif new_score >= 60:
            risk.risk_category, risk.decision = "MEDIUM", "CONDITIONAL_APPROVAL"
        elif new_score >= 45:
            risk.risk_category, risk.decision = "HIGH", "CONDITIONAL"
        else:
            risk.risk_category, risk.decision = "VERY_HIGH", "REJECT"

        await session.commit()
        return {
            "old_score": old_score,
            "new_score": risk.final_score,
            "risk_category": risk.risk_category,
            "decision": risk.decision,
            "dd_delta": total_dd_delta,
        }


async def run(app_id: str, officer_text: str) -> dict:
    """Main entry point — called by POST /api/applications/{id}/dd-notes."""
    t = time.time()
    await log_agent(app_id, AGENT, "RUNNING")
    await publish_event(app_id, {
        "event_type": "AGENT_STARTED",
        "agent_name": AGENT,
        "payload": {"message": "Interpreting field observations..."},
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Parse observations — always try LLM first, fallback to rules
    signals = parse_observations_with_llm(officer_text)
    if not signals:
        signals = parse_observations_fallback(officer_text)

    total_delta = sum(s.get("risk_points_delta", 0) for s in signals)

    # Persist DD note
    async with _AgentSession() as session:
        note = DDNote(
            id=str(uuid.uuid4()),
            application_id=app_id,
            officer_text=officer_text,
            ai_signals_json=signals,
            risk_delta=total_delta,
        )
        session.add(note)
        await session.commit()

    # Recalculate score
    score_update = await recalculate_score(app_id, total_delta)

    # Update Redis
    cached = await get_session(app_id, "risk_scores") or {}
    cached.update(score_update)
    await set_session(app_id, "risk_scores", cached)
    await set_session(app_id, "dd_adjustments", {"signals": signals, "total_delta": total_delta})

    duration_ms = int((time.time() - t) * 1000)
    result = {
        "signals": signals,
        "total_delta": total_delta,
        "score_update": score_update,
    }

    await publish_event(app_id, {
        "event_type": "DD_SCORE_UPDATED",
        "agent_name": AGENT,
        "payload": result,
        "timestamp": datetime.utcnow().isoformat(),
    })
    await log_agent(app_id, AGENT, "COMPLETED",
                    output_summary=f"{len(signals)} signals. Score delta: -{total_delta}. "
                                   f"New score: {score_update.get('new_score')}.",
                    duration_ms=duration_ms)
    return result
