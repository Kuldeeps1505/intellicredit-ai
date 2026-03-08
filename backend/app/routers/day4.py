"""
Day 4 routers:
  POST /api/applications/{id}/dd-notes
  GET  /api/applications/{id}/cam
  GET  /api/applications/{id}/cam/download
  GET  /api/applications/{id}/counterfactuals
  GET  /api/promoter/{pan}/network
"""
from __future__ import annotations
import os
from typing import Optional, Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import CAMReport, Application, Company
from app.services.redis_service import get_session

router = APIRouter(tags=["day4"])


# ── Schemas ───────────────────────────────────────────────
class DDNoteRequest(BaseModel):
    officer_text: str


class DDSignal(BaseModel):
    signal_type: str
    description: str
    risk_category: str
    risk_points_delta: float
    reasoning: str


class DDNoteResponse(BaseModel):
    signals: List[DDSignal]
    total_delta: float
    score_update: dict


class CAMResponse(BaseModel):
    application_id: str
    recommendation: Optional[str]
    loan_amount_approved: Optional[float]
    interest_rate: Optional[float]
    tenor_months: Optional[int]
    pdf_path: Optional[str]
    docx_path: Optional[str]
    pdf_generated: bool
    docx_generated: bool
    generated_at: Optional[datetime]


class CounterfactualItem(BaseModel):
    factor: str
    label: str
    current_value: Any
    target_value: Any
    delta: float
    score_impact: float
    estimated_action: str
    priority_rank: int
    feasibility: str
    implementation_timeline: str


class CounterfactualsResponse(BaseModel):
    application_id: str
    current_score: float
    approve_threshold: float
    gap: float
    decision: str
    buffer_message: Optional[str]
    total_achievable_improvement: float
    would_achieve_approval: bool
    counterfactuals: List[CounterfactualItem]


# ── POST /api/applications/{id}/dd-notes ─────────────────
@router.post("/api/applications/{app_id}/dd-notes", response_model=DDNoteResponse)
async def submit_dd_notes(
    app_id: str,
    payload: DDNoteRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit field observations. Triggers Agent 5 synchronously (fast enough for demo).
    Returns structured signals + score update.
    """
    result = await db.execute(select(Application).where(Application.id == app_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Application not found")
    if not payload.officer_text.strip():
        raise HTTPException(status_code=422, detail="officer_text cannot be empty")

    try:
        from agents.due_diligence import run as dd_run
        result = await dd_run(app_id, payload.officer_text)
        return DDNoteResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Due diligence agent error: {str(e)}")


# ── GET /api/applications/{id}/cam ────────────────────────
@router.get("/api/applications/{app_id}/cam", response_model=CAMResponse)
async def get_cam(app_id: str, db: AsyncSession = Depends(get_db)):
    """Returns CAM metadata and download paths."""
    result = await db.execute(
        select(CAMReport).where(CAMReport.application_id == app_id)
    )
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(status_code=404,
                            detail="CAM not yet generated. Run full pipeline first.")

    pdf_exists = bool(cam.pdf_path and os.path.exists(cam.pdf_path))
    docx_exists = bool(cam.docx_path and os.path.exists(cam.docx_path))

    return CAMResponse(
        application_id=app_id,
        recommendation=cam.recommendation,
        loan_amount_approved=cam.loan_amount_approved,
        interest_rate=cam.interest_rate,
        tenor_months=cam.tenor_months,
        pdf_path=cam.pdf_path,
        docx_path=cam.docx_path,
        pdf_generated=pdf_exists,
        docx_generated=docx_exists,
        generated_at=cam.generated_at,
    )


# ── GET /api/applications/{id}/cam/download ──────────────
@router.get("/api/applications/{app_id}/cam/download")
async def download_cam(
    app_id: str,
    format: str = "pdf",
    db: AsyncSession = Depends(get_db),
):
    """
    Download CAM as PDF or DOCX.
    ?format=pdf  (default) | ?format=docx | ?format=html
    """
    result = await db.execute(
        select(CAMReport).where(CAMReport.application_id == app_id)
    )
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(status_code=404, detail="CAM not generated yet.")

    if format == "docx":
        path = cam.docx_path
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        suffix = ".docx"
    elif format == "html":
        path = cam.pdf_path.replace(".pdf", ".html") if cam.pdf_path else None
        media_type = "text/html"
        suffix = ".html"
    else:
        path = cam.pdf_path
        media_type = "application/pdf"
        suffix = ".pdf"

    if not path or not os.path.exists(path):
        # Try HTML fallback
        html_path = (cam.pdf_path or "").replace(".pdf", ".html")
        if html_path and os.path.exists(html_path):
            return FileResponse(
                path=html_path,
                media_type="text/html",
                filename=f"CAM_{app_id[:8]}.html",
            )
        raise HTTPException(
            status_code=404,
            detail=f"CAM file not found. Install weasyprint (PDF) or python-docx (DOCX) for full export."
        )

    filename = f"CAM_{app_id[:8]}{suffix}"
    return FileResponse(path=path, media_type=media_type, filename=filename)


# ── GET /api/applications/{id}/counterfactuals ───────────
@router.get("/api/applications/{app_id}/counterfactuals", response_model=CounterfactualsResponse)
async def get_counterfactuals(app_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns counterfactual explainability output — minimum changes to reach APPROVE.
    Triggers computation if not yet cached.
    """
    result = await db.execute(select(Application).where(Application.id == app_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Application not found")

    cached = await get_session(app_id, "counterfactuals")
    if not cached:
        # Trigger computation
        try:
            from engines.counterfactual import run as cf_run
            cached = await cf_run(app_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Counterfactual engine error: {str(e)}")

    if not cached:
        raise HTTPException(status_code=404, detail="Risk scores not yet computed.")

    return CounterfactualsResponse(
        application_id=app_id,
        **{k: v for k, v in cached.items() if k != "app_id"},
    )


# ── GET /api/promoter/{pan}/network ──────────────────────
@router.get("/api/promoter/{pan}/network")
async def get_promoter_network(pan: str, app_id: Optional[str] = None):
    """
    Returns NetworkX fraud detection graph as JSON for D3 visualization.
    pan: PAN of the promoter/company.
    app_id: optional — if provided, loads DINs from session.
    """
    from engines.fraud_network import build_network_graph, MOCK_NPA_DB

    # If app_id provided, get DINs from session
    dins = []
    company_name = f"Company-{pan}"
    if app_id:
        extracted = await get_session(app_id, "extracted_financials") or {}
        dins = extracted.get("director_dins", [])
        company_name = extracted.get("company_name", company_name)

    # Demo: always include NPA DINs for PAN associated with Dataset 2
    if pan.startswith("DEMO") or not dins:
        dins = ["00234567", "00111222"]

    graph = build_network_graph(app_id or "standalone", company_name, dins)

    # Add summary stats
    fraud_dins = [d for d in dins if len(MOCK_NPA_DB.get(d, [])) >= 2]
    return {
        "pan": pan,
        "company_name": company_name,
        "fraud_network_detected": len(fraud_dins) > 0,
        "flagged_dins": fraud_dins,
        "graph": graph,
    }