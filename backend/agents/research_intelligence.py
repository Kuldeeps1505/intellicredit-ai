"""
Agent 3 — Research Intelligence Agent
Day 3 deliverable. Runs parallel after Agent 1.

Gathers:
  - Web search: company news, fraud, NPA mentions
  - MCA/ROC directorship (mock data for prototype)
  - Court database search (mock data for prototype)
  - IBBI insolvency check (mock data)
  - News sentiment analysis via Claude API
  - Industry outlook (20 sectors pre-mapped)
"""
from __future__ import annotations
import time
import uuid
import json
from datetime import datetime

import anthropic
import httpx

from app.services.redis_service import get_session, set_session, publish_event
from app.services.db_helpers import log_agent, save_risk_flag, _AgentSession
from app.models import ResearchData
from app.config import settings

AGENT = "research_intelligence"

# ── Industry outlook map (20 sectors) ────────────────────
SECTOR_OUTLOOK = {
    "IT": {"outlook": "POSITIVE", "score": 8, "note": "Strong demand; digital transformation spend high."},
    "PHARMA": {"outlook": "POSITIVE", "score": 7, "note": "Export market healthy; API demand stable."},
    "FMCG": {"outlook": "POSITIVE", "score": 7, "note": "Rural demand recovering; premium segment growing."},
    "AUTO": {"outlook": "NEUTRAL", "score": 6, "note": "EV transition uncertainty; ICE demand mixed."},
    "BANKING": {"outlook": "POSITIVE", "score": 7, "note": "NPA levels declining; credit growth robust."},
    "REAL_ESTATE": {"outlook": "NEUTRAL", "score": 5, "note": "Residential recovering; commercial office demand weak."},
    "STEEL": {"outlook": "NEUTRAL", "score": 5, "note": "China oversupply pressure; domestic demand stable."},
    "CEMENT": {"outlook": "POSITIVE", "score": 6, "note": "Infrastructure push supporting demand."},
    "TEXTILE": {"outlook": "NEGATIVE", "score": 3, "note": "China import surge; GST rate uncertainty; weak exports."},
    "CHEMICALS": {"outlook": "NEUTRAL", "score": 5, "note": "Feedstock costs volatile; specialty chemicals growing."},
    "POWER": {"outlook": "POSITIVE", "score": 7, "note": "Renewable energy push; PLI scheme benefits."},
    "TELECOM": {"outlook": "POSITIVE", "score": 6, "note": "5G rollout driving capex; ARPU improving."},
    "LOGISTICS": {"outlook": "POSITIVE", "score": 6, "note": "GST normalization; infrastructure investment benefits."},
    "HOSPITALITY": {"outlook": "NEUTRAL", "score": 5, "note": "Post-COVID recovery continuing; business travel weak."},
    "EDUCATION": {"outlook": "NEUTRAL", "score": 5, "note": "Edtech rerating; physical institutes recovering."},
    "AGRI": {"outlook": "NEUTRAL", "score": 5, "note": "MSP support; monsoon variability risk."},
    "MINING": {"outlook": "NEUTRAL", "score": 5, "note": "Coal demand high; metals mixed."},
    "MEDIA": {"outlook": "NEGATIVE", "score": 4, "note": "OTT disruption; ad revenue pressure."},
    "RETAIL": {"outlook": "NEUTRAL", "score": 5, "note": "Quick commerce disrupting traditional retail."},
    "CONSTRUCTION": {"outlook": "POSITIVE", "score": 6, "note": "Government capex high; infra orders robust."},
}

# ── Mock NPA / Fraud database ─────────────────────────────
MOCK_NPA_DB = [
    {"din": "00234567", "company": "Beta Fabrics Ltd", "npa_year": 2022, "amount_cr": 18.0},
    {"din": "00234567", "company": "Delta Yarns Pvt Ltd", "npa_year": 2023, "amount_cr": 9.0},
    {"din": "00987654", "company": "Sigma Steel Ltd", "npa_year": 2021, "amount_cr": 45.0},
    {"din": "00111222", "company": "Alpha Infra Corp", "npa_year": 2022, "amount_cr": 12.0},
]

# ── Mock litigation database ──────────────────────────────
MOCK_LITIGATION_DB = {
    "DEMO_FRAUD_COMPANY": [
        {
            "case_id": "IB/374/2023",
            "court": "NCLT Mumbai",
            "type": "INSOLVENCY",
            "claim_amount_cr": 4.2,
            "filed_date": "2023-02-14",
            "status": "PENDING",
            "last_hearing": "2025-01-20",
            "material": True,
        },
        {
            "case_id": "DRT/892/2022",
            "court": "DRT Mumbai",
            "type": "FINANCIAL_DISPUTE",
            "claim_amount_cr": 2.1,
            "filed_date": "2022-08-10",
            "status": "PENDING",
            "last_hearing": "2025-02-15",
            "material": True,
        },
        {
            "case_id": "CC/1043/2024",
            "court": "City Civil Court",
            "type": "COMMERCIAL_DISPUTE",
            "claim_amount_cr": 0.3,
            "filed_date": "2024-01-05",
            "status": "ACTIVE",
            "last_hearing": "2025-01-30",
            "material": False,
        },
    ]
}


# ── Web search ────────────────────────────────────────────
async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search via Tavily API."""
    if not settings.tavily_api_key:
        return [{"title": f"Mock result for: {query}", "content": "No real data — Tavily key not set.", "url": "#"}]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                },
            )
            if resp.status_code == 200:
                return resp.json().get("results", [])
    except Exception:
        pass
    return []


# ── News sentiment via Claude API ─────────────────────────
async def analyze_news_sentiment(articles: list[dict], company_name: str) -> float:
    """
    Use Claude API to analyze sentiment of news articles.
    Returns score from -1.0 (very negative) to +1.0 (very positive).
    """
    if not articles or not settings.anthropic_api_key:
        return 0.0

    article_texts = "\n\n".join([
        f"Title: {a.get('title', '')}\nContent: {a.get('content', '')[:500]}"
        for a in articles[:5]
    ])

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": (
                    f"Analyze the sentiment of these news articles about '{company_name}' "
                    "from a credit risk perspective.\n\n"
                    f"{article_texts}\n\n"
                    "Respond with ONLY a JSON object: "
                    '{\"score\": <float -1.0 to 1.0>, \"summary\": \"<one sentence>\"}'
                ),
            }],
        )
        import re, json
        text = response.content[0].text
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return float(data.get("score", 0.0))
    except Exception:
        pass
    return 0.0


# ── Litigation lookup ─────────────────────────────────────
def get_litigation(company_name: str, cin: str) -> list[dict]:
    """
    Look up litigation cases. Uses mock DB for prototype.
    In production: eCourts API, NCLT portal, IBBI database.
    """
    # Check mock DB by company name keywords
    for key in MOCK_LITIGATION_DB:
        if key.lower() in company_name.lower() or company_name.lower() in key.lower():
            return MOCK_LITIGATION_DB[key]
    return []


# ── Promoter reputation scoring ───────────────────────────
def score_promoter_reputation(
    litigation_cases: list[dict],
    news_sentiment: float,
    npa_linked: bool,
) -> str:
    """Returns GOOD | MEDIUM | HIGH_RISK"""
    if npa_linked:
        return "HIGH_RISK"
    material_count = sum(1 for c in litigation_cases if c.get("material"))
    if material_count >= 2 or news_sentiment < -0.3:
        return "HIGH_RISK"
    if material_count == 1 or news_sentiment < 0:
        return "MEDIUM"
    return "GOOD"


# ── DB write ──────────────────────────────────────────────
async def save_research(app_id: str, data: dict):
    async with _AgentSession() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(ResearchData).where(ResearchData.application_id == app_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
        else:
            rd = ResearchData(
                id=str(uuid.uuid4()),
                application_id=app_id,
                **data,
            )
            session.add(rd)
        await session.commit()


# ── Main entry point ──────────────────────────────────────
async def run(app_id: str) -> dict:
    t = time.time()
    await log_agent(app_id, AGENT, "RUNNING")
    await publish_event(app_id, {
        "event_type": "AGENT_STARTED",
        "agent_name": AGENT,
        "payload": {},
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Get company info from session
    extracted = await get_session(app_id, "extracted_financials") or {}
    company_name = extracted.get("company_name", "Unknown Company")
    cin = extracted.get("cin", "")
    sector = extracted.get("sector", "")

    await publish_event(app_id, {
        "event_type": "AGENT_PROGRESS",
        "agent_name": AGENT,
        "payload": {"message": f"Researching: {company_name}"},
        "timestamp": datetime.utcnow().isoformat(),
    })

    # ── Web search ────────────────────────────────────────
    news_articles = await web_search(f"{company_name} fraud NPA lawsuit India")
    news_sentiment = await analyze_news_sentiment(news_articles, company_name)

    # ── Litigation ────────────────────────────────────────
    litigation_cases = get_litigation(company_name, cin)

    # ── NPA check (mock) ──────────────────────────────────
    npa_linked = False  # Will be set by fraud detection engine in Day 4

    # ── Industry outlook ──────────────────────────────────
    sector_data = SECTOR_OUTLOOK.get(sector.upper(), SECTOR_OUTLOOK.get("RETAIL", {
        "outlook": "NEUTRAL", "score": 5, "note": "Sector not mapped."
    }))

    # ── Promoter reputation ───────────────────────────────
    reputation = score_promoter_reputation(litigation_cases, news_sentiment, npa_linked)

    # ── Build dossier ─────────────────────────────────────
    dossier = {
        "company_name": company_name,
        "promoter_reputation": reputation,
        "litigation_count": len(litigation_cases),
        "litigation_cases": litigation_cases,
        "industry_outlook": sector_data["outlook"],
        "industry_score": sector_data["score"],
        "industry_note": sector_data.get("note", ""),
        "news_sentiment_score": round(news_sentiment, 3),
        "news_articles": [
            {"title": a.get("title"), "url": a.get("url"), "snippet": a.get("content", "")[:200]}
            for a in news_articles[:5]
        ],
    }

    # ── Risk flags ────────────────────────────────────────
    material_lit = [c for c in litigation_cases if c.get("material")]
    if material_lit:
        nclt_cases = [c for c in material_lit if "NCLT" in c.get("court", "")]
        if nclt_cases:
            await save_risk_flag(
                app_id, "NCLT_LITIGATION", "CRITICAL",
                f"{len(nclt_cases)} active NCLT insolvency petition(s). "
                f"Largest claim: ₹{max(c.get('claim_amount_cr', 0) for c in nclt_cases):.1f}Cr.",
                AGENT,
            )
        elif material_lit:
            await save_risk_flag(
                app_id, "MATERIAL_LITIGATION", "HIGH",
                f"{len(material_lit)} material litigation case(s) totalling "
                f"₹{sum(c.get('claim_amount_cr', 0) for c in material_lit):.1f}Cr.",
                AGENT,
            )

    if sector_data["outlook"] == "NEGATIVE":
        await save_risk_flag(
            app_id, "NEGATIVE_SECTOR_OUTLOOK", "MEDIUM",
            f"Sector '{sector}' has NEGATIVE outlook. {sector_data.get('note', '')}",
            AGENT,
        )

    # ── Save to DB ────────────────────────────────────────
    await save_research(app_id, {
        "promoter_reputation": reputation,
        "litigation_count": len(litigation_cases),
        "industry_outlook": sector_data["outlook"],
        "news_sentiment_score": news_sentiment,
        "litigation_cases": litigation_cases,
        "news_articles": dossier["news_articles"],
        "raw_json": dossier,
    })

    await set_session(app_id, "research_dossier", dossier)

    duration_ms = int((time.time() - t) * 1000)
    summary = (
        f"Reputation: {reputation}. "
        f"Litigation: {len(litigation_cases)} cases ({len(material_lit)} material). "
        f"Industry: {sector_data['outlook']}. "
        f"News sentiment: {news_sentiment:.2f}."
    )
    await log_agent(app_id, AGENT, "COMPLETED", output_summary=summary, duration_ms=duration_ms)
    await publish_event(app_id, {
        "event_type": "AGENT_COMPLETED",
        "agent_name": AGENT,
        "payload": {"summary": summary, "duration_ms": duration_ms},
        "timestamp": datetime.utcnow().isoformat(),
    })

    return dossier