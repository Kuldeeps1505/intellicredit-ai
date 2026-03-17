"""
GET /api/applications/{id}/promoter → PromoterDataset
Assembles from: research_data table + fraud_network engine + litigation_intelligence engine
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import ResearchData, Application, Company
from app.services.redis_service import get_session

router = APIRouter(prefix="/api/applications", tags=["promoter"])


# ── Schemas matching frontend promoterData.ts exactly ─────────────────────────

class Director(BaseModel):
    name: str
    din: str
    designation: str
    age: int
    experience: str
    linkedEntities: int
    npaLinks: int
    shellLinks: int
    riskLevel: str          # "clean" | "watchlist" | "flagged"
    cibilScore: int
    netWorth: str


class NetworkNode(BaseModel):
    id: str
    label: str
    type: str               # "director" | "company" | "shell" | "npa" | "related"
    risk: str               # "clean" | "warning" | "danger"


class NetworkEdge(BaseModel):
    source: str             # node id  (frontend uses "from" but "from" is Python keyword)
    target: str
    label: str
    suspicious: bool

    def model_dump(self, **kw):
        d = super().model_dump(**kw)
        d["from"] = d.pop("source")
        d["to"]   = d.pop("target")
        return d


class LitigationCase(BaseModel):
    date: str
    court: str
    caseType: str
    status: str             # "pending" | "disposed" | "settled"
    amount: str
    description: str
    severity: str           # "critical" | "high" | "medium" | "low"


class NewsItem(BaseModel):
    date: str
    source: str
    headline: str
    sentiment: str          # "positive" | "negative" | "neutral"
    relevance: int


class PromoterDataset(BaseModel):
    directors: List[Director]
    networkNodes: List[NetworkNode]
    networkEdges: List[NetworkEdge]
    litigation: List[LitigationCase]
    news: List[NewsItem]
    overallPromoterRisk: str   # "low" | "medium" | "high" | "critical"
    mca21Flags: List[str]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _risk_level(npa_links: int, shell_links: int) -> str:
    if npa_links >= 2 or shell_links >= 1:
        return "flagged"
    if npa_links == 1:
        return "watchlist"
    return "clean"


def _overall_risk(directors: List[Director], lit_count: int) -> str:
    flagged = sum(1 for d in directors if d.riskLevel == "flagged")
    watchlist = sum(1 for d in directors if d.riskLevel == "watchlist")
    if flagged >= 1 or lit_count >= 3:
        return "critical"
    if watchlist >= 1 or lit_count >= 1:
        return "high"
    if lit_count > 0:
        return "medium"
    return "low"


def _build_network(company_name: str, directors: List[Director],
                   npa_db: list) -> tuple[List[NetworkNode], List[NetworkEdge]]:
    nodes: List[NetworkNode] = []
    edges: List[NetworkEdge] = []

    # Central company node
    nodes.append(NetworkNode(id="company_main", label=company_name,
                              type="company", risk="clean"))

    for d in directors:
        d_id = f"dir_{d.din}"
        risk = "danger" if d.riskLevel == "flagged" else ("warning" if d.riskLevel == "watchlist" else "clean")
        nodes.append(NetworkNode(id=d_id, label=d.name, type="director", risk=risk))
        edges.append(NetworkEdge(source="company_main", target=d_id,
                                  label=d.designation, suspicious=False))

        # NPA linked companies
        for i, npa in enumerate(npa_db):
            if npa.get("din") == d.din:
                npa_id = f"npa_{d.din}_{i}"
                nodes.append(NetworkNode(id=npa_id, label=npa.get("company_name", "NPA Company"),
                                          type="npa", risk="danger"))
                edges.append(NetworkEdge(source=d_id, target=npa_id,
                                          label=f"NPA ₹{npa.get('amount_cr','?')}Cr",
                                          suspicious=True))
    return nodes, edges


# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{app_id}/promoter", response_model=PromoterDataset)
async def get_promoter(app_id: str, db: AsyncSession = Depends(get_db)):
    app = (await db.execute(
        select(Application).where(Application.id == app_id)
    )).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    co = (await db.execute(
        select(Company).where(Company.id == app.company_id)
    )).scalar_one_or_none()
    company_name = co.name if co else "Unknown Company"

    # Load from research_data table
    rd = (await db.execute(
        select(ResearchData).where(ResearchData.application_id == app_id)
    )).scalar_one_or_none()

    # Load from Redis (fraud_network + litigation engines write here)
    fraud_data  = await get_session(app_id, "fraud_network") or {}
    lit_data    = await get_session(app_id, "litigation") or {}
    research_session = await get_session(app_id, "research_intelligence") or {}

    # ── Directors ─────────────────────────────────────────────────────────────
    raw_dirs = []
    if rd and rd.directorship_history:
        raw_dirs = rd.directorship_history if isinstance(rd.directorship_history, list) else []
    elif fraud_data.get("directors"):
        raw_dirs = fraud_data["directors"]

    directors: List[Director] = []
    for d in raw_dirs:
        npa_links  = int(d.get("npa_links", 0))
        shell_links = int(d.get("shell_links", 0))
        directors.append(Director(
            name=d.get("name", "Unknown"),
            din=d.get("din", "00000000"),
            designation=d.get("designation", "Director"),
            age=int(d.get("age", 50)),
            experience=d.get("experience", "—"),
            linkedEntities=int(d.get("linked_entities", 1)),
            npaLinks=npa_links,
            shellLinks=shell_links,
            riskLevel=_risk_level(npa_links, shell_links),
            cibilScore=int(d.get("cibil_score", 700)),
            netWorth=d.get("net_worth", "—"),
        ))

    # ── Fraud network graph ───────────────────────────────────────────────────
    npa_db = fraud_data.get("npa_entries", [])
    nodes, edges = _build_network(company_name, directors, npa_db)

    # ── Litigation ────────────────────────────────────────────────────────────
    raw_lit = []
    if rd and rd.litigation_cases:
        raw_lit = rd.litigation_cases if isinstance(rd.litigation_cases, list) else []
    elif lit_data.get("cases"):
        raw_lit = lit_data["cases"]

    litigation: List[LitigationCase] = []
    for c in raw_lit:
        sev = c.get("severity", "medium").lower()
        litigation.append(LitigationCase(
            date=str(c.get("date", "")),
            court=c.get("court", "Unknown Court"),
            caseType=c.get("case_type", "Civil"),
            status=c.get("status", "pending").lower(),
            amount=c.get("amount", "—"),
            description=c.get("description", ""),
            severity=sev,
        ))

    # ── News ──────────────────────────────────────────────────────────────────
    raw_news = []
    if rd and rd.news_articles:
        raw_news = rd.news_articles if isinstance(rd.news_articles, list) else []
    elif research_session.get("news_articles"):
        raw_news = research_session["news_articles"]

    news: List[NewsItem] = []
    for n in raw_news:
        news.append(NewsItem(
            date=str(n.get("date", "")),
            source=n.get("source", "Web"),
            headline=n.get("headline", ""),
            sentiment=n.get("sentiment", "neutral").lower(),
            relevance=int(n.get("relevance", 70)),
        ))

    # ── MCA21 flags ───────────────────────────────────────────────────────────
    mca21_flags: List[str] = fraud_data.get("mca21_flags", [])
    if not mca21_flags and rd:
        rep = rd.promoter_reputation or "GOOD"
        if rep == "HIGH_RISK":
            mca21_flags = ["Director linked to NPA accounts", "Multiple company directorships with defaults"]
        elif rep == "MEDIUM":
            mca21_flags = ["One directorship with delayed payments"]

    overall_risk = _overall_risk(directors, len(litigation))

    return PromoterDataset(
        directors=directors,
        networkNodes=nodes,
        networkEdges=edges,
        litigation=litigation,
        news=news,
        overallPromoterRisk=overall_risk,
        mca21Flags=mca21_flags,
    )



