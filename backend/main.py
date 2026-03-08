"""IntelliCredit AI — FastAPI entry point (final)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.routers import applications, websocket, intelligence
from app.routers.day4 import router as day4_router

app = FastAPI(title="IntelliCredit AI", version="1.0.0",
    description="Autonomous Corporate Credit Intelligence — IIT Hyderabad Hackathon 2025. 7 AI agents + 4 engines.")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(applications.router)
app.include_router(websocket.router)
app.include_router(intelligence.router)
app.include_router(day4_router)

@app.on_event("startup")
async def startup():
    await create_tables()

@app.get("/health")
async def health():
    return {"status":"ok","service":"IntelliCredit AI","version":"1.0.0",
            "agents":7,"engines":["gst_reconciliation","buyer_concentration",
                                  "counterfactual","fraud_network","litigation"]}

@app.get("/api/demo-ids")
async def get_demo_ids():
    """Frontend quick-switch — pre-seeded demo application IDs."""
    return {
        "demo_1":{"id":"11111111-1111-1111-1111-111111111111",
                  "label":"TechNova Solutions — APPROVE","score":81,"decision":"APPROVE","sector":"IT"},
        "demo_2":{"id":"22222222-2222-2222-2222-222222222222",
                  "label":"Shree Textiles — REJECT (Hero Demo)","score":28,"decision":"REJECT","sector":"TEXTILE"},
        "demo_3":{"id":"33333333-3333-3333-3333-333333333333",
                  "label":"Prestige Realty — CONDITIONAL","score":61,"decision":"CONDITIONAL_APPROVAL","sector":"REAL_ESTATE"},
    }








