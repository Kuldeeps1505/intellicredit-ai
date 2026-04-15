"""
Account Aggregator (AA) Router — India Stack
============================================
Endpoints for the full AA consent + FI fetch flow.

POST /api/applications/{id}/aa/consent/initiate   → create consent request
GET  /api/applications/{id}/aa/consent/status     → poll consent status
POST /api/applications/{id}/aa/fi/fetch           → fetch FI data after consent
GET  /api/applications/{id}/aa/status             → full AA session status
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import Application, Company
from app.services.redis_service import set_session, get_session
from app.services.aa_service import (
    create_consent_request,
    get_consent_status,
    fetch_financial_data,
    compute_bank_analytics_from_aa,
)

router = APIRouter(prefix="/api/applications", tags=["account-aggregator"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class AAConsentInitiateRequest(BaseModel):
    mobile: str                    # borrower's registered mobile
    purpose: Optional[str] = "Loan Appraisal"


class AAConsentInitiateResponse(BaseModel):
    consentHandle: str
    redirectUrl: str               # borrower opens this on their AA app
    txnId: str
    provider: str                  # "setu" | "sahamati" | "mock"
    status: str
    message: Optional[str] = None
    aaApp: Optional[str] = None
    expiresIn: Optional[str] = None


class AAConsentStatusResponse(BaseModel):
    consentHandle: str
    consentId: Optional[str] = None
    status: str                    # "PENDING" | "ACTIVE" | "REJECTED" | "EXPIRED"
    provider: str
    approvedAt: Optional[str] = None
    approvedBy: Optional[str] = None


class AAFetchResponse(BaseModel):
    success: bool
    source: str
    provider: str
    accountsFetched: int
    bankStatementsFetched: bool
    gstDataFetched: bool
    fetchedAt: str
    message: str


class AASessionStatus(BaseModel):
    appId: str
    step: str                      # "not_started" | "consent_pending" | "consent_active" | "data_fetched"
    consentHandle: Optional[str] = None
    consentStatus: Optional[str] = None
    provider: Optional[str] = None
    dataFetched: bool = False
    bankStatements: bool = False
    gstData: bool = False
    fetchedAt: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/{app_id}/aa/consent/initiate", response_model=AAConsentInitiateResponse)
async def initiate_aa_consent(
    app_id: str,
    body: AAConsentInitiateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 1: FIU creates consent request.
    Borrower receives OTP on their AA app (OneMoney / Finvu / CAMS Finserv).
    Returns a redirectUrl the borrower opens to approve consent.
    """
    app = (await db.execute(select(Application).where(Application.id == app_id))).scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    company = (await db.execute(select(Company).where(Company.id == app.company_id))).scalar_one_or_none()

    result = await create_consent_request(
        mobile=body.mobile,
        app_id=app_id,
        loan_amount=float(app.loan_amount_requested or 0),
        purpose=body.purpose or "Loan Appraisal",
    )

    # Persist AA session state
    await set_session(app_id, "aa_session", {
        "step": "consent_pending",
        "mobile": body.mobile,
        "consentHandle": result["consentHandle"],
        "txnId": result["txnId"],
        "provider": result["provider"],
        "initiatedAt": datetime.utcnow().isoformat(),
        "companyName": company.name if company else "Unknown",
        "gstin": company.gstin if company else "",
    })

    # Update application with consent handle
    app.aa_consent_handle = result["consentHandle"]
    await db.commit()

    return AAConsentInitiateResponse(**result)


@router.get("/{app_id}/aa/consent/status", response_model=AAConsentStatusResponse)
async def get_aa_consent_status(app_id: str, db: AsyncSession = Depends(get_db)):
    """
    Step 2: Poll consent status.
    Frontend polls this every 3s until status = ACTIVE.
    """
    session = await get_session(app_id, "aa_session")
    if not session:
        raise HTTPException(404, "No AA session found. Initiate consent first.")

    handle = session.get("consentHandle", "")
    provider = session.get("provider", "mock")

    status_data = await get_consent_status(handle, provider)

    # Update session with latest status
    session["consentStatus"] = status_data["status"]
    if status_data["status"] == "ACTIVE":
        session["step"] = "consent_active"
        session["consentId"] = status_data.get("consentId", handle)
        session["approvedAt"] = status_data.get("approvedAt", datetime.utcnow().isoformat())

    await set_session(app_id, "aa_session", session)

    return AAConsentStatusResponse(
        consentHandle=handle,
        consentId=status_data.get("consentId"),
        status=status_data["status"],
        provider=provider,
        approvedAt=status_data.get("approvedAt"),
        approvedBy=status_data.get("approvedBy"),
    )


@router.post("/{app_id}/aa/fi/fetch", response_model=AAFetchResponse)
async def fetch_aa_fi_data(app_id: str, db: AsyncSession = Depends(get_db)):
    """
    Step 3: Fetch Financial Information after consent is ACTIVE.
    Pulls bank statements (12 months) + GST returns automatically.
    Stores data in Redis session for pipeline ingestion.
    """
    session = await get_session(app_id, "aa_session")
    if not session:
        raise HTTPException(404, "No AA session found.")

    if session.get("consentStatus") not in ("ACTIVE", None):
        raise HTTPException(400, f"Consent not active. Current status: {session.get('consentStatus')}")

    consent_id = session.get("consentId", session.get("consentHandle", ""))
    provider = session.get("provider", "mock")

    # Fetch FI data
    fi_data = await fetch_financial_data(consent_id, provider)

    # Compute bank analytics
    bank_analytics = compute_bank_analytics_from_aa(fi_data)

    # Store in Redis for pipeline agents to consume
    await set_session(app_id, "aa_fi_data", fi_data)
    await set_session(app_id, "bank_analytics", bank_analytics)

    # Store GST raw data for GSTR reconciliation engine
    gst_data = fi_data.get("gst_data", {})
    if gst_data:
        await set_session(app_id, "gst_raw", {
            "gstr2a": gst_data.get("gstr2a", {}),
            "gstr3b": gst_data.get("gstr3b", {}),
            "gstr1":  gst_data.get("gstr1", {}),
            "gstin":  gst_data.get("gstin", ""),
            "source": "account_aggregator",
        })

    # Update session
    session["step"] = "data_fetched"
    session["dataFetched"] = True
    session["bankStatementsFetched"] = bool(fi_data.get("bank_statements"))
    session["gstDataFetched"] = bool(gst_data)
    session["fetchedAt"] = datetime.utcnow().isoformat()
    await set_session(app_id, "aa_session", session)

    bank_count = len(fi_data.get("bank_statements", []))
    has_gst = bool(gst_data)

    return AAFetchResponse(
        success=True,
        source="account_aggregator",
        provider=provider,
        accountsFetched=fi_data.get("accounts_fetched", bank_count),
        bankStatementsFetched=bool(bank_count),
        gstDataFetched=has_gst,
        fetchedAt=session["fetchedAt"],
        message=(
            f"Successfully fetched {bank_count} bank account(s) (12 months) "
            f"{'+ GST returns (GSTR-1, 2A, 3B) ' if has_gst else ''}"
            f"via Account Aggregator. No manual upload required."
        ),
    )


@router.get("/{app_id}/aa/status", response_model=AASessionStatus)
async def get_aa_session_status(app_id: str):
    """Get full AA session status for the frontend wizard."""
    session = await get_session(app_id, "aa_session")
    if not session:
        return AASessionStatus(appId=app_id, step="not_started", dataFetched=False)

    return AASessionStatus(
        appId=app_id,
        step=session.get("step", "not_started"),
        consentHandle=session.get("consentHandle"),
        consentStatus=session.get("consentStatus"),
        provider=session.get("provider"),
        dataFetched=session.get("dataFetched", False),
        bankStatements=session.get("bankStatementsFetched", False),
        gstData=session.get("gstDataFetched", False),
        fetchedAt=session.get("fetchedAt"),
    )
