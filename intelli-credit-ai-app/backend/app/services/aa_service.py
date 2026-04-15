"""
Account Aggregator (AA) Service — India Stack
=============================================
Implements the ReBIT 2.0 AA consent + FI fetch flow.

Flow:
  1. FIU creates consent request → AA returns consentHandle
  2. AA sends OTP to borrower's mobile → borrower approves on AA app
  3. FIU polls consent status → ACTIVE
  4. FIU sends FI fetch request with consentId
  5. AA fetches data from FIP (bank/GST) → returns encrypted FI data
  6. FIU decrypts → structured bank statements + GST data

Providers tried in order:
  1. Setu AA sandbox (developer.setu.co) — real API, instant sandbox access
  2. Sahamati simulator (api.sandbox.sahamati.org.in) — reference implementation
  3. Mock fallback — realistic demo data for hackathon presentation

References:
  https://developer.setu.co/data/account-aggregator
  https://developer.sahamati.org.in
  https://specifications.rebit.org.in
"""
from __future__ import annotations

import uuid
import json
import base64
import hashlib
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

AA_PROVIDER = getattr(settings, "aa_provider", "mock")   # "setu" | "sahamati" | "mock"
SETU_CLIENT_ID = getattr(settings, "setu_client_id", "")
SETU_CLIENT_SECRET = getattr(settings, "setu_client_secret", "")
SETU_AA_BASE = "https://dg-sandbox.setu.co"

SAHAMATI_BASE = "https://api.sandbox.sahamati.org.in/router/v2"
SAHAMATI_TOKEN = getattr(settings, "sahamati_token", "")

FIU_ID = getattr(settings, "fiu_id", "IntelliCredit-FIU-UAT")
AA_ID  = getattr(settings, "aa_id", "ONEMONEY-AA")   # default AA for sandbox


# ── Step 1: Create Consent Request ───────────────────────────────────────────

async def create_consent_request(
    mobile: str,
    app_id: str,
    loan_amount: float,
    purpose: str = "Loan Appraisal",
) -> dict:
    """
    Send consent request to AA on behalf of the borrower.
    Returns: { consentHandle, redirectUrl, txnId, provider }
    """
    txn_id = str(uuid.uuid4())
    consent_start = datetime.utcnow().isoformat() + "Z"
    consent_expiry = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
    data_start = (datetime.utcnow() - timedelta(days=365)).isoformat() + "Z"
    data_end = datetime.utcnow().isoformat() + "Z"

    # Try Setu first
    if AA_PROVIDER == "setu" and SETU_CLIENT_ID:
        result = await _setu_create_consent(
            mobile, txn_id, consent_start, consent_expiry, data_start, data_end, app_id
        )
        if result:
            return result

    # Try Sahamati simulator
    if AA_PROVIDER == "sahamati" and SAHAMATI_TOKEN:
        result = await _sahamati_create_consent(
            mobile, txn_id, consent_start, consent_expiry, data_start, data_end
        )
        if result:
            return result

    # Mock fallback — realistic demo
    return _mock_consent_request(mobile, txn_id, app_id)


async def _setu_create_consent(
    mobile, txn_id, consent_start, consent_expiry, data_start, data_end, app_id
) -> Optional[dict]:
    """Setu AA sandbox consent creation."""
    try:
        # Get access token
        token_resp = await _setu_get_token()
        if not token_resp:
            return None

        payload = {
            "ver": "2.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "txnid": txn_id,
            "ConsentDetail": {
                "consentStart": consent_start,
                "consentExpiry": consent_expiry,
                "consentMode": "VIEW",
                "fetchType": "PERIODIC",
                "consentTypes": ["TRANSACTIONS", "SUMMARY", "PROFILE"],
                "fiTypes": ["DEPOSIT", "TERM_DEPOSIT", "RECURRING_DEPOSIT", "GST_GSTR1_3B"],
                "DataConsumer": {"id": FIU_ID, "type": "FIU"},
                "Customer": {"id": f"{mobile}@onemoney"},
                "FIDataRange": {"from": data_start, "to": data_end},
                "DataLife": {"unit": "MONTH", "value": 1},
                "Frequency": {"unit": "HOUR", "value": 1},
                "DataFilter": [{"type": "TRANSACTIONAMOUNT", "operator": ">=", "value": "0"}],
                "Purpose": {
                    "code": "101",
                    "refUri": "https://api.rebit.org.in/aa/purpose/101.xml",
                    "text": purpose,
                    "Category": {"type": "purposeCategoryType"}
                }
            }
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{SETU_AA_BASE}/v2/consents",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token_resp}",
                    "x-product-instance-id": SETU_CLIENT_ID,
                    "Content-Type": "application/json",
                }
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                handle = data.get("consentHandle") or data.get("id", txn_id)
                redirect = data.get("url") or f"https://finsense.setu.co/consent/{handle}"
                return {
                    "consentHandle": handle,
                    "redirectUrl": redirect,
                    "txnId": txn_id,
                    "provider": "setu",
                    "status": "PENDING",
                }
    except Exception as e:
        logger.warning("Setu consent creation failed: %s", e)
    return None


async def _setu_get_token() -> Optional[str]:
    """Get Setu OAuth2 token."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{SETU_AA_BASE}/auth/token",
                json={
                    "clientID": SETU_CLIENT_ID,
                    "secret": SETU_CLIENT_SECRET,
                }
            )
            if resp.status_code == 200:
                return resp.json().get("access_token")
    except Exception:
        pass
    return None


async def _sahamati_create_consent(
    mobile, txn_id, consent_start, consent_expiry, data_start, data_end
) -> Optional[dict]:
    """Sahamati simulator consent creation."""
    try:
        payload = {
            "ver": "2.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "txnid": txn_id,
            "ConsentDetail": {
                "consentStart": consent_start,
                "consentExpiry": consent_expiry,
                "consentMode": "VIEW",
                "fetchType": "ONETIME",
                "consentTypes": ["TRANSACTIONS", "SUMMARY"],
                "fiTypes": ["DEPOSIT", "GST_GSTR1_3B"],
                "DataConsumer": {"id": FIU_ID, "type": "FIU"},
                "Customer": {"id": f"{mobile}@onemoney"},
                "FIDataRange": {"from": data_start, "to": data_end},
                "DataLife": {"unit": "MONTH", "value": 1},
                "Frequency": {"unit": "HOUR", "value": 1},
                "Purpose": {"code": "101", "text": "Loan Appraisal"}
            }
        }
        x_meta = base64.b64encode(json.dumps({"recipient-id": AA_ID}).encode()).decode()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{SAHAMATI_BASE}/Consent",
                json=payload,
                headers={
                    "Authorization": f"Bearer {SAHAMATI_TOKEN}",
                    "x-request-meta": x_meta,
                    "Content-Type": "application/json",
                }
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                handle = data.get("ConsentHandle", txn_id)
                return {
                    "consentHandle": handle,
                    "redirectUrl": f"https://sahamati.org.in/aa-simulator/consent/{handle}",
                    "txnId": txn_id,
                    "provider": "sahamati",
                    "status": "PENDING",
                }
    except Exception as e:
        logger.warning("Sahamati consent creation failed: %s", e)
    return None


def _mock_consent_request(mobile: str, txn_id: str, app_id: str) -> dict:
    """
    Mock consent — realistic demo for hackathon.
    Simulates the exact same UX as real AA.
    """
    handle = f"AA-CONSENT-{app_id[:8].upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    return {
        "consentHandle": handle,
        "redirectUrl": f"https://sahamati.org.in/demo-consent?handle={handle}&mobile={mobile}",
        "txnId": txn_id,
        "provider": "mock",
        "status": "PENDING",
        "message": "OTP sent to borrower's registered mobile. Borrower must approve on AA app.",
        "aaApp": "OneMoney / Finvu / CAMS Finserv",
        "expiresIn": "10 minutes",
    }


# ── Step 2: Poll Consent Status ───────────────────────────────────────────────

async def get_consent_status(consent_handle: str, provider: str = "mock") -> dict:
    """
    Poll AA for consent status.
    Returns: { status: "PENDING" | "ACTIVE" | "REJECTED" | "EXPIRED", consentId }
    """
    if provider == "setu" and SETU_CLIENT_ID:
        return await _setu_get_consent_status(consent_handle)
    if provider == "sahamati" and SAHAMATI_TOKEN:
        return await _sahamati_get_consent_status(consent_handle)
    return _mock_consent_status(consent_handle)


async def _setu_get_consent_status(handle: str) -> dict:
    try:
        token = await _setu_get_token()
        if not token:
            return _mock_consent_status(handle)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{SETU_AA_BASE}/v2/consents/{handle}",
                headers={"Authorization": f"Bearer {token}", "x-product-instance-id": SETU_CLIENT_ID}
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": data.get("status", "PENDING"),
                    "consentId": data.get("id", handle),
                    "provider": "setu",
                }
    except Exception:
        pass
    return _mock_consent_status(handle)


async def _sahamati_get_consent_status(handle: str) -> dict:
    try:
        x_meta = base64.b64encode(json.dumps({"recipient-id": AA_ID}).encode()).decode()
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{SAHAMATI_BASE}/Consent/handle/{handle}",
                headers={"Authorization": f"Bearer {SAHAMATI_TOKEN}", "x-request-meta": x_meta}
            )
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("ConsentStatus", {}).get("status", "PENDING")
                consent_id = data.get("ConsentStatus", {}).get("id", handle)
                return {"status": status, "consentId": consent_id, "provider": "sahamati"}
    except Exception:
        pass
    return _mock_consent_status(handle)


def _mock_consent_status(handle: str) -> dict:
    """
    Mock: auto-approve after first poll for demo purposes.
    In real demo, this would wait for borrower to approve on AA app.
    """
    return {
        "status": "ACTIVE",
        "consentId": f"CONSENT-{handle}",
        "provider": "mock",
        "approvedAt": datetime.utcnow().isoformat(),
        "approvedBy": f"Borrower via OneMoney AA App",
    }


# ── Step 3: Fetch Financial Information ───────────────────────────────────────

async def fetch_financial_data(consent_id: str, provider: str = "mock") -> dict:
    """
    Fetch bank statements + GST data using approved consent.
    Returns structured data ready for pipeline ingestion.
    """
    if provider == "setu" and SETU_CLIENT_ID:
        result = await _setu_fetch_fi(consent_id)
        if result:
            return result

    if provider == "sahamati" and SAHAMATI_TOKEN:
        result = await _sahamati_fetch_fi(consent_id)
        if result:
            return result

    return _mock_fi_data(consent_id)


async def _setu_fetch_fi(consent_id: str) -> Optional[dict]:
    """Setu FI data fetch."""
    try:
        token = await _setu_get_token()
        if not token:
            return None
        session_id = str(uuid.uuid4())
        payload = {
            "ver": "2.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "txnid": session_id,
            "FIDataRange": {
                "from": (datetime.utcnow() - timedelta(days=365)).isoformat() + "Z",
                "to": datetime.utcnow().isoformat() + "Z",
            },
            "Consent": {"id": consent_id, "digitalSignature": ""},
            "KeyMaterial": {"cryptoAlg": "ECDH", "curve": "Curve25519", "params": ""},
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{SETU_AA_BASE}/v2/sessions",
                json=payload,
                headers={"Authorization": f"Bearer {token}", "x-product-instance-id": SETU_CLIENT_ID}
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return _parse_setu_fi_response(data)
    except Exception as e:
        logger.warning("Setu FI fetch failed: %s", e)
    return None


async def _sahamati_fetch_fi(consent_id: str) -> Optional[dict]:
    """Sahamati FI data fetch."""
    try:
        session_id = str(uuid.uuid4())
        x_meta = base64.b64encode(json.dumps({"recipient-id": AA_ID}).encode()).decode()
        payload = {
            "ver": "2.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "txnid": session_id,
            "FIDataRange": {
                "from": (datetime.utcnow() - timedelta(days=365)).isoformat() + "Z",
                "to": datetime.utcnow().isoformat() + "Z",
            },
            "Consent": {"id": consent_id, "digitalSignature": "mock-sig"},
            "KeyMaterial": {"cryptoAlg": "ECDH", "curve": "Curve25519", "params": "mock"},
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{SAHAMATI_BASE}/FI/request",
                json=payload,
                headers={"Authorization": f"Bearer {SAHAMATI_TOKEN}", "x-request-meta": x_meta}
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return _parse_sahamati_fi_response(data)
    except Exception as e:
        logger.warning("Sahamati FI fetch failed: %s", e)
    return None


def _parse_setu_fi_response(data: dict) -> dict:
    """Parse Setu FI response into structured format."""
    accounts = data.get("FI", [])
    return _structure_fi_data(accounts, "setu")


def _parse_sahamati_fi_response(data: dict) -> dict:
    """Parse Sahamati FI response into structured format."""
    accounts = data.get("FI", [])
    return _structure_fi_data(accounts, "sahamati")


def _structure_fi_data(accounts: list, provider: str) -> dict:
    """Convert raw FI data to IntelliCredit pipeline format."""
    bank_statements = []
    gst_data = {}

    for account in accounts:
        fi_type = account.get("fiType", "")
        data = account.get("data", {})

        if fi_type == "DEPOSIT":
            transactions = data.get("Transactions", {}).get("Transaction", [])
            summary = data.get("Summary", {})
            bank_statements.append({
                "account_id": account.get("linkRefNumber", ""),
                "bank": summary.get("bankName", "Unknown Bank"),
                "account_type": summary.get("type", "SAVINGS"),
                "balance": float(summary.get("currentBalance", 0)),
                "transactions": [
                    {
                        "date": t.get("valueDate", ""),
                        "amount": float(t.get("amount", 0)),
                        "type": t.get("type", ""),
                        "narration": t.get("narration", ""),
                        "balance": float(t.get("currentBalance", 0)),
                    }
                    for t in transactions[:500]  # cap at 500 transactions
                ],
            })

        elif "GST" in fi_type:
            gst_data = {
                "gstin": data.get("gstin", ""),
                "gstr1": data.get("GSTR1", {}),
                "gstr3b": data.get("GSTR3B", {}),
                "gstr2a": data.get("GSTR2A", {}),
            }

    return {
        "source": "account_aggregator",
        "provider": provider,
        "fetched_at": datetime.utcnow().isoformat(),
        "bank_statements": bank_statements,
        "gst_data": gst_data,
        "accounts_fetched": len(accounts),
    }


def _mock_fi_data(consent_id: str) -> dict:
    """
    Realistic mock FI data — matches Sunrise Exports fraud scenario.
    Used when real AA is unavailable.
    """
    months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
    transactions = []
    balance = 28412.0
    for i, month in enumerate(months):
        # Credits (business income)
        credit = round(2800 + (i % 3) * 200 + (i * 50), 2)
        balance += credit
        transactions.append({
            "date": f"2024-{(i+4) % 12 + 1:02d}-05",
            "amount": credit,
            "type": "CREDIT",
            "narration": f"NEFT/Zenith Trading Co/{month} payment",
            "balance": round(balance, 2),
        })
        # Debits (supplier payments)
        debit = round(credit * 0.92, 2)
        balance -= debit
        transactions.append({
            "date": f"2024-{(i+4) % 12 + 1:02d}-15",
            "amount": debit,
            "type": "DEBIT",
            "narration": f"RTGS/Gujarat Cotton Suppliers/{month}",
            "balance": round(balance, 2),
        })

    return {
        "source": "account_aggregator",
        "provider": "mock",
        "fetched_at": datetime.utcnow().isoformat(),
        "consent_id": consent_id,
        "bank_statements": [
            {
                "account_id": "ACC-SUNRISE-001",
                "bank": "Punjab National Bank",
                "account_type": "CURRENT",
                "balance": round(balance, 2),
                "transactions": transactions,
                "summary": {
                    "avg_monthly_credits": 312500,
                    "avg_monthly_debits": 289000,
                    "bounce_count": 2,
                    "bounce_ratio_pct": 0.8,
                    "avg_balance": 34200,
                    "behavior_score": 72,
                }
            }
        ],
        "gst_data": {
            "gstin": "07AADCS5678G1Z2",
            "gstr3b": {
                "quarterly_turnover": [
                    {"quarter": "Q1", "turnover": 384800, "itc_claimed": 118200},
                    {"quarter": "Q2", "turnover": 384800, "itc_claimed": 151200},
                    {"quarter": "Q3", "turnover": 384800, "itc_claimed": 139400},
                    {"quarter": "Q4", "turnover": 384800, "itc_claimed": 185400},
                ]
            },
            "gstr2a": {
                "quarterly_itc_available": [
                    {"quarter": "Q1", "itc_available": 112400},
                    {"quarter": "Q2", "itc_available": 98300},
                    {"quarter": "Q3", "itc_available": 84500},
                    {"quarter": "Q4", "itc_available": 121800},
                ]
            }
        },
        "accounts_fetched": 1,
        "data_note": "AA consent approved. Bank statements (12 months) + GST returns fetched automatically.",
    }


# ── Compute bank analytics from AA data ───────────────────────────────────────

def compute_bank_analytics_from_aa(fi_data: dict) -> dict:
    """
    Compute bank analytics from AA-fetched data.
    Returns format compatible with bank_analytics router.
    """
    statements = fi_data.get("bank_statements", [])
    if not statements:
        return {}

    stmt = statements[0]
    summary = stmt.get("summary", {})
    transactions = stmt.get("transactions", [])

    credits = [t for t in transactions if t.get("type") == "CREDIT"]
    debits  = [t for t in transactions if t.get("type") == "DEBIT"]

    total_credits = sum(t.get("amount", 0) for t in credits)
    total_debits  = sum(t.get("amount", 0) for t in debits)
    avg_credits   = total_credits / 12 if total_credits else 0
    avg_debits    = total_debits / 12 if total_debits else 0

    # Bounce detection
    bounce_count = sum(1 for t in transactions
                       if any(w in t.get("narration", "").upper()
                              for w in ["RETURN", "BOUNCE", "DISHONOUR", "INSUFFICIENT"]))
    bounce_ratio = (bounce_count / max(len(transactions), 1)) * 100

    # Cash withdrawal %
    cash_debits = sum(t.get("amount", 0) for t in debits
                      if any(w in t.get("narration", "").upper()
                             for w in ["ATM", "CASH", "WITHDRAWAL"]))
    cash_pct = (cash_debits / max(total_debits, 1)) * 100

    # Behavior score (0-100)
    score = 100
    if bounce_ratio > 5:   score -= 30
    elif bounce_ratio > 2: score -= 15
    if cash_pct > 20:      score -= 20
    elif cash_pct > 10:    score -= 10
    cd_ratio = total_credits / max(total_debits, 1)
    if cd_ratio < 1.0:     score -= 20
    elif cd_ratio < 1.05:  score -= 10

    # Monthly cash flow
    monthly = {}
    for t in transactions:
        month = t.get("date", "")[:7]  # YYYY-MM
        if month not in monthly:
            monthly[month] = {"credits": 0, "debits": 0, "closing": 0}
        if t.get("type") == "CREDIT":
            monthly[month]["credits"] += t.get("amount", 0)
        else:
            monthly[month]["debits"] += t.get("amount", 0)
        monthly[month]["closing"] = t.get("balance", 0)

    monthly_list = [
        {"month": k, "credits_lakhs": round(v["credits"] / 100, 2),
         "debits_lakhs": round(v["debits"] / 100, 2),
         "closing_balance_lakhs": round(v["closing"] / 100, 2)}
        for k, v in sorted(monthly.items())[-12:]
    ]

    return {
        "source": "account_aggregator",
        "summary": {
            "abb": round(stmt.get("balance", 0) / 100, 2),
            "avgMonthlyCredits": round(avg_credits / 100, 2),
            "avgMonthlyDebits": round(avg_debits / 100, 2),
            "creditDebitRatio": round(cd_ratio, 2),
            "emiObligations": round(avg_debits * 0.05 / 100, 2),
            "emiCount": 2,
            "bounceRatio": round(bounce_ratio, 1),
            "totalBounces": bounce_count,
            "cashWithdrawalPercent": round(cash_pct, 1),
            "behaviorScore": max(0, min(100, score)),
        },
        "monthlyCashFlow": monthly_list,
        "redFlags": [
            {
                "type": "High Bounce Ratio",
                "severity": "high" if bounce_ratio > 5 else "low",
                "description": f"Bounce ratio: {bounce_ratio:.1f}%",
                "detected": bounce_ratio > 2,
            },
            {
                "type": "High Cash Withdrawals",
                "severity": "medium",
                "description": f"Cash withdrawal: {cash_pct:.1f}% of debits",
                "detected": cash_pct > 10,
            },
        ],
    }
