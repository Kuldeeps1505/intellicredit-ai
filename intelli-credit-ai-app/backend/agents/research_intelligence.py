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

# anthropic removed � using llm_service instead
import httpx

from app.services.redis_service import get_session, set_session, publish_event
from app.services.db_helper import log_agent, save_risk_flag, _AgentSession
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


# ── News sentiment via LLM ────────────────────────────────
async def analyze_news_sentiment(articles: list[dict], company_name: str) -> float:
    """
    Analyze sentiment of news articles using Ollama → Anthropic → keyword fallback.
    Returns score from -1.0 (very negative) to +1.0 (very positive).
    """
    if not articles:
        return 0.0

    article_texts = "\n\n".join([
        f"Title: {a.get('title', '')}\nContent: {a.get('content', '')[:300]}"
        for a in articles[:5]
    ])

    from app.services.llm_service import llm_complete
    prompt = (
        f"Analyze the sentiment of these news articles about '{company_name}' "
        "from a credit risk perspective.\n\n"
        f"{article_texts}\n\n"
        "Respond with ONLY a JSON object: "
        '{"score": <float -1.0 to 1.0>, "summary": "<one sentence>"}'
    )
    try:
        text = await llm_complete(prompt, max_tokens=150,
                                   system="You are a credit risk analyst. Respond only with valid JSON.")
        if text:
            import re, json
            match = re.search(r'\{.*?\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return float(data.get("score", 0.0))
    except Exception:
        pass

    # Keyword fallback
    all_text = " ".join(a.get("title", "") + " " + a.get("content", "") for a in articles).lower()
    neg = sum(all_text.count(w) for w in ["fraud", "default", "nclt", "npa", "loss", "penalty", "seized"])
    pos = sum(all_text.count(w) for w in ["growth", "profit", "award", "expansion", "strong"])
    if neg > pos: return -0.5
    if pos > neg: return 0.3
    return 0.0


# ── Zaubacorp scraper (free, no auth) ────────────────────
async def scrape_zaubacorp(cin: str, company_name: str) -> dict:
    """Scrape company info from Zaubacorp — free public data."""
    result = {"directors": [], "status": "unknown", "charges": []}
    if not cin:
        return result
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True,
                                      headers={"User-Agent": "Mozilla/5.0"}) as client:
            resp = await client.get(f"https://www.zaubacorp.com/company/{cin}")
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                # Extract company status
                status_el = soup.find(string=lambda t: t and "Active" in t)
                result["status"] = "Active" if status_el else "Unknown"
                # Extract directors
                dir_table = soup.find("table", {"id": "example1"})
                if dir_table:
                    for row in dir_table.find_all("tr")[1:6]:  # max 5 directors
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            result["directors"].append({
                                "name": cols[0].get_text(strip=True),
                                "din": cols[1].get_text(strip=True) if len(cols) > 1 else "",
                                "designation": cols[2].get_text(strip=True) if len(cols) > 2 else "Director",
                            })
    except Exception:
        pass
    return result


# ── eCourts scraper ───────────────────────────────────────
async def search_ecourts(company_name: str) -> list[dict]:
    """Search eCourts for cases involving the company."""
    cases = []
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True,
                                      headers={"User-Agent": "Mozilla/5.0"}) as client:
            resp = await client.get(
                "https://services.ecourts.gov.in/ecourtindiaapi/",
                params={"party_name": company_name, "state_code": "0", "dist_code": "0"},
            )
            if resp.status_code == 200:
                data = resp.json()
                for case in data.get("cases", [])[:5]:
                    cases.append({
                        "case_id": case.get("case_no", ""),
                        "court": case.get("court_name", "District Court"),
                        "type": "CIVIL",
                        "status": case.get("case_status", "Pending"),
                        "filed_date": case.get("date_of_filing", ""),
                        "claim_amount_cr": 0,
                        "material": True,
                    })
    except Exception:
        pass
    return cases


# ── NCLT/IBBI check via web search ───────────────────────
async def check_nclt_ibbi(company_name: str, cin: str) -> list[dict]:
    """Search for NCLT/IBBI insolvency proceedings via Tavily."""
    results = await web_search(
        f'"{company_name}" NCLT insolvency petition site:ibbi.gov.in OR site:nclt.gov.in'
    )
    cases = []
    for r in results[:3]:
        combined = (r.get("title", "") + r.get("content", "")).lower()
        if any(w in combined for w in ["nclt", "insolvency", "ibbi", "liquidation"]):
            cases.append({
                "case_id": "NCLT/search",
                "court": "NCLT",
                "type": "INSOLVENCY",
                "status": "Pending",
                "filed_date": "",
                "claim_amount_cr": _extract_amount_cr(r.get("content", "")),
                "material": True,
                "source_url": r.get("url", ""),
                "description": r.get("title", ""),
            })
    return cases
    """
    Check if a director (by DIN + name) is linked to NPA accounts.
    Uses Tavily to search RBI defaulter list, CIBIL, news.
    Returns: { npa_links: int, shell_links: int, npa_entries: [...], flags: [...] }
    """
    npa_entries = []
    flags = []
    npa_links = 0
    shell_links = 0

    if not settings.tavily_api_key:
        return {"npa_links": 0, "shell_links": 0, "npa_entries": [], "flags": []}

    # Search 1: Director name + NPA/default
    results = await web_search(
        f'"{director_name}" DIN {din} NPA "non performing" bank default India',
        max_results=5
    )
    for r in results:
        title = r.get("title", "").lower()
        content = r.get("content", "").lower()
        combined = title + " " + content
        if any(w in combined for w in ["npa", "non performing", "default", "wilful defaulter", "cibil"]):
            npa_links += 1
            # Try to extract company name and amount from snippet
            npa_entries.append({
                "din": din,
                "company_name": _extract_company_from_snippet(r.get("title", ""), company_name),
                "amount_cr": _extract_amount_cr(r.get("content", "")),
                "source": r.get("url", ""),
                "description": r.get("title", "")[:100],
            })
            flags.append(f"Director {director_name} (DIN: {din}) linked to NPA — {r.get('title','')[:60]}")

    # Search 2: Director + shell company / SFIO / ED
    shell_results = await web_search(
        f'"{director_name}" DIN {din} "shell company" OR "SFIO" OR "Enforcement Directorate" India',
        max_results=3
    )
    for r in shell_results:
        combined = (r.get("title", "") + r.get("content", "")).lower()
        if any(w in combined for w in ["shell", "sfio", "enforcement directorate", "money laundering"]):
            shell_links += 1
            flags.append(f"Director {director_name} linked to shell company / SFIO — {r.get('title','')[:60]}")

    # Search 3: NCLT petition against company
    nclt_results = await web_search(
        f'"{company_name}" NCLT insolvency petition "section 7" OR "section 9" India',
        max_results=3
    )
    for r in nclt_results:
        combined = (r.get("title", "") + r.get("content", "")).lower()
        if "nclt" in combined or "insolvency" in combined:
            flags.append(f"NCLT petition found — {r.get('title','')[:60]}")

    return {
        "npa_links": npa_links,
        "shell_links": shell_links,
        "npa_entries": npa_entries[:3],  # cap at 3 per director
        "flags": flags,
    }


def _extract_company_from_snippet(title: str, fallback: str) -> str:
    """Try to extract a company name from a news title."""
    # Look for patterns like "XYZ Ltd" or "ABC Pvt Ltd"
    import re
    match = re.search(r'([A-Z][A-Za-z\s]+(?:Ltd|Limited|Pvt|Corp|Industries|Exports|Trading))', title)
    return match.group(1).strip() if match else fallback


def _extract_amount_cr(text: str) -> float:
    """Extract crore amount from text."""
    import re
    # Match patterns like "Rs.4.2 Cr" or "₹18 crore" or "4.2 crores"
    match = re.search(r'(?:rs\.?|₹)?\s*(\d+\.?\d*)\s*(?:crore|cr)', text.lower())
    if match:
        return float(match.group(1))
    return 0.0


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
    await publish_event(app_id, {"event_type": "AGENT_STARTED", "agent_name": AGENT,
                                  "payload": {}, "timestamp": datetime.utcnow().isoformat()})

    extracted = await get_session(app_id, "extracted_financials") or {}
    company_name = extracted.get("company_name", "Unknown Company")
    cin  = extracted.get("cin", "")
    gstin= extracted.get("gstin", "")
    sector = extracted.get("sector", "")

    await publish_event(app_id, {"event_type": "AGENT_PROGRESS", "agent_name": AGENT,
        "payload": {"message": f"Researching: {company_name} | CIN: {cin}"}, "timestamp": datetime.utcnow().isoformat()})

    # ── 1. Web search (Tavily) ────────────────────────────
    news_articles = await web_search(f'"{company_name}" fraud NPA default lawsuit India credit')
    news_sentiment = await analyze_news_sentiment(news_articles, company_name)

    # ── 2. Zaubacorp — director & company data ────────────
    zauba_data = await scrape_zaubacorp(cin, company_name)
    directors_from_zauba = zauba_data.get("directors", [])

    # ── 3. eCourts — litigation search ───────────────────
    ecourt_cases = await search_ecourts(company_name)

    # ── 4. NCLT/IBBI check via Tavily ────────────────────
    nclt_cases = await check_nclt_ibbi(company_name, cin)

    # Merge litigation sources
    litigation_cases = ecourt_cases + nclt_cases
    if not litigation_cases:
        for key in MOCK_LITIGATION_DB:
            if key.lower() in company_name.lower():
                litigation_cases = MOCK_LITIGATION_DB[key]
                break

    # ── 5. NPA check per director (real Tavily) ───────────
    all_npa_entries = []
    all_fraud_flags = []
    enriched_directors = []
    for d in directors_from_zauba:
        din  = d.get("din", "")
        name = d.get("name", "")
        if din and name and settings.tavily_api_key:
            npa_result = await check_director_npa(name, din, company_name)
            d["npa_links"]   = npa_result["npa_links"]
            d["shell_links"] = npa_result["shell_links"]
            all_npa_entries.extend(npa_result["npa_entries"])
            all_fraud_flags.extend(npa_result["flags"])
        enriched_directors.append(d)

    # Write fraud_network session — consumed by promoter router to build graph
    await set_session(app_id, "fraud_network", {
        "directors":   enriched_directors,
        "npa_entries": all_npa_entries,
        "mca21_flags": all_fraud_flags[:5],
        "source":      "zaubacorp+tavily",
        "scraped_at":  datetime.utcnow().isoformat(),
    })

    # ── 5b. Company-level NPA check ───────────────────────
    npa_results = await web_search(f'"{company_name}" NPA "non performing asset" bank')
    npa_linked = (
        any("npa" in r.get("title","").lower() or "non performing" in r.get("content","").lower()
            for r in npa_results)
        or len(all_npa_entries) > 0
    )

    # ── 6. Industry outlook ───────────────────────────────
    sector_key = sector.upper().replace(" ", "_").replace("/", "_")
    sector_data = SECTOR_OUTLOOK.get(sector_key, None)
    if not sector_data:
        # Try partial match
        for k, v in SECTOR_OUTLOOK.items():
            if k in sector_key or sector_key in k:
                sector_data = v
                break
    if not sector_data:
        sector_data = {"outlook": "NEUTRAL", "score": 5, "note": f"Sector '{sector}' not mapped."}

    # ── 7. Promoter reputation ────────────────────────────
    reputation = score_promoter_reputation(litigation_cases, news_sentiment, npa_linked)

    dossier = {
        "company_name": company_name,
        "cin": cin,
        "promoter_reputation": reputation,
        "litigation_count": len(litigation_cases),
        "litigation_cases": litigation_cases,
        "industry_outlook": sector_data["outlook"],
        "industry_score": sector_data["score"],
        "industry_note": sector_data.get("note", ""),
        "news_sentiment_score": round(news_sentiment, 3),
        "news_articles": [{"title": a.get("title"), "url": a.get("url"),
                           "snippet": a.get("content", "")[:200]} for a in news_articles[:5]],
        "directors": enriched_directors if enriched_directors else directors_from_zauba,
        "npa_linked": npa_linked,
        "zauba_status": zauba_data.get("status", "unknown"),
    }

    # ── Risk flags ────────────────────────────────────────
    material_lit = [c for c in litigation_cases if c.get("material")]
    if material_lit:
        nclt_found = [c for c in material_lit if "NCLT" in c.get("court", "")]
        if nclt_found:
            await save_risk_flag(app_id, "NCLT_LITIGATION", "CRITICAL",
                f"{len(nclt_found)} active NCLT insolvency petition(s). "
                f"Largest: ₹{max(c.get('claim_amount_cr',0) for c in nclt_found):.1f}Cr.", AGENT)
        else:
            await save_risk_flag(app_id, "MATERIAL_LITIGATION", "HIGH",
                f"{len(material_lit)} material litigation case(s) totalling "
                f"₹{sum(c.get('claim_amount_cr',0) for c in material_lit):.1f}Cr.", AGENT)

    if npa_linked:
        await save_risk_flag(app_id, "NPA_LINKED", "CRITICAL",
            f"Company or promoters linked to NPA accounts per web search.", AGENT)

    if sector_data["outlook"] == "NEGATIVE":
        await save_risk_flag(app_id, "NEGATIVE_SECTOR_OUTLOOK", "MEDIUM",
            f"Sector '{sector}' has NEGATIVE outlook. {sector_data.get('note','')}", AGENT)

    await save_research(app_id, {
        "promoter_reputation": reputation,
        "litigation_count": len(litigation_cases),
        "industry_outlook": sector_data["outlook"],
        "news_sentiment_score": news_sentiment,
        "litigation_cases": litigation_cases,
        "news_articles": dossier["news_articles"],
        "directorship_history": directors_from_zauba,
        "raw_json": dossier,
    })
    await set_session(app_id, "research_dossier", dossier)

    duration_ms = int((time.time() - t) * 1000)
    summary = (f"Reputation: {reputation} | Litigation: {len(litigation_cases)} cases | "
               f"Industry: {sector_data['outlook']} | News sentiment: {news_sentiment:.2f} | "
               f"NPA linked: {npa_linked} | Directors from Zaubacorp: {len(directors_from_zauba)}")
    await log_agent(app_id, AGENT, "COMPLETED", output_summary=summary, duration_ms=duration_ms)
    await publish_event(app_id, {"event_type": "AGENT_COMPLETED", "agent_name": AGENT,
        "payload": {"summary": summary, "duration_ms": duration_ms}, "timestamp": datetime.utcnow().isoformat()})
    return dossier

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


async def check_director_npa(director_name: str, din: str, company_name: str) -> dict:
    """
    Check if a director is linked to NPA accounts via Tavily search.
    Searches: RBI defaulter list mentions, CIBIL, news, SFIO/ED.
    Returns: { npa_links, shell_links, npa_entries, flags }
    """
    npa_entries = []
    flags = []
    npa_links = 0
    shell_links = 0

    if not settings.tavily_api_key:
        return {"npa_links": 0, "shell_links": 0, "npa_entries": [], "flags": []}

    # Search 1: Director + NPA/default
    results = await web_search(
        f'"{director_name}" DIN {din} NPA "non performing" bank default India',
        max_results=5
    )
    for r in results:
        combined = (r.get("title", "") + " " + r.get("content", "")).lower()
        if any(w in combined for w in ["npa", "non performing", "default", "wilful defaulter"]):
            npa_links += 1
            npa_entries.append({
                "din": din,
                "company_name": _extract_company_from_snippet(r.get("title", ""), company_name),
                "amount_cr": _extract_amount_cr(r.get("content", "")),
                "source": r.get("url", ""),
                "description": r.get("title", "")[:100],
            })
            flags.append(f"Director {director_name} (DIN: {din}) — {r.get('title','')[:60]}")

    # Search 2: Director + shell company / SFIO
    shell_results = await web_search(
        f'"{director_name}" DIN {din} "shell company" OR "SFIO" OR "Enforcement Directorate" India',
        max_results=3
    )
    for r in shell_results:
        combined = (r.get("title", "") + r.get("content", "")).lower()
        if any(w in combined for w in ["shell", "sfio", "enforcement directorate", "money laundering"]):
            shell_links += 1
            flags.append(f"Director {director_name} — shell/SFIO: {r.get('title','')[:60]}")

    return {
        "npa_links": npa_links,
        "shell_links": shell_links,
        "npa_entries": npa_entries[:3],
        "flags": flags,
    }
