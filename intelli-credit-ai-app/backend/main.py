"""
IntelliCredit AI — FastAPI entry point.
Registers all routers to match frontend API surface exactly.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.routers.applications import router as applications_router
from app.routers.websocket import router as websocket_router
from app.routers.intelligence import router as intelligence_router
from app.routers.promoter import router as promoter_router
from app.routers.bank_analytics import router as bank_analytics_router
from app.routers.diligence import router as diligence_router
from app.routers.audit import router as audit_router
from app.routers.facilities import router as facilities_router
from app.routers.cam import router as cam_router
from app.routers.aa import router as aa_router

app = FastAPI(
    title="IntelliCredit AI",
    version="2.0.0",
    description="Autonomous Corporate Credit Intelligence — IIT Hyderabad Hackathon 2026. "
                "7 AI agents + 5 engines. Full frontend-compatible API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Core routers ──────────────────────────────────────────────────────────────
app.include_router(applications_router)   # GET/POST /api/applications, /documents, /pipeline
app.include_router(websocket_router)      # WS /ws/applications/{id}

# ── Intelligence / Risk ───────────────────────────────────────────────────────
app.include_router(intelligence_router)   # GET /api/applications/{id}/risk, /gst-reconciliation, /buyer-concentration

# ── New page routers ──────────────────────────────────────────────────────────
app.include_router(promoter_router)       # GET /api/applications/{id}/promoter
app.include_router(bank_analytics_router) # GET /api/applications/{id}/bank-analytics
app.include_router(diligence_router)      # GET /api/applications/{id}/diligence
app.include_router(audit_router)          # GET /api/applications/{id}/audit + POST /audit/override
app.include_router(facilities_router)     # GET /api/applications/{id}/facilities
app.include_router(cam_router)            # GET/POST /api/applications/{id}/cam + /chat + /dd-notes + /counterfactuals
app.include_router(aa_router)             # POST /api/applications/{id}/aa/consent/initiate + /fi/fetch


@app.on_event("startup")
async def startup():
    await create_tables()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "IntelliCredit AI",
        "version": "2.0.0",
        "agents": 7,
        "engines": ["gst_reconciliation", "buyer_concentration", "counterfactual", "fraud_network", "litigation"],
        "api_endpoints": [
            "GET  /api/applications",
            "POST /api/applications",
            "GET  /api/applications/{id}",
            "POST /api/applications/{id}/documents",
            "GET  /api/applications/{id}/documents",
            "POST /api/applications/{id}/pipeline/start",
            "GET  /api/applications/{id}/pipeline/status",
            "POST /api/applications/{id}/aa-consent",
            "GET  /api/applications/{id}/financials",
            "GET  /api/applications/{id}/risk",
            "GET  /api/applications/{id}/promoter",
            "GET  /api/applications/{id}/bank-analytics",
            "GET  /api/applications/{id}/diligence",
            "GET  /api/applications/{id}/cam",
            "POST /api/applications/{id}/cam/generate",
            "GET  /api/applications/{id}/cam/download",
            "GET  /api/applications/{id}/facilities",
            "GET  /api/applications/{id}/audit",
            "POST /api/applications/{id}/audit/override",
            "GET  /api/applications/{id}/counterfactuals",
            "POST /api/applications/{id}/dd-notes",
            "POST /api/applications/{id}/chat",
            "WS   /ws/applications/{id}",
        ],
    }


@app.get("/api/demo-ids")
async def get_demo_ids():
    """Frontend dataset switcher — pre-seeded demo application IDs."""
    return {
        "demo_1": {
            "id": "11111111-1111-1111-1111-111111111111",
            "label": "Reliance Textiles Pvt Ltd — APPROVE",
            "emoji": "✅",
            "score": 81,
            "decision": "approve",
            "sector": "Textiles & Apparel",
        },
        "demo_2": {
            "id": "22222222-2222-2222-2222-222222222222",
            "label": "Shree Textiles — REJECT (Hero Demo)",
            "emoji": "🔴",
            "score": 28,
            "decision": "reject",
            "sector": "Textiles & Apparel",
        },
        "demo_3": {
            "id": "33333333-3333-3333-3333-333333333333",
            "label": "Prestige Realty — CONDITIONAL",
            "emoji": "⚠️",
            "score": 61,
            "decision": "conditional",
            "sector": "Real Estate",
        },
    }









