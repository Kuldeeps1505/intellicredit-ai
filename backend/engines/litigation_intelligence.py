"""
Litigation Intelligence Engine — Day 4 deliverable.

Pre-seeded mock court database: eCourts, NCLT, IBBI, DRT.
Classifies, scores materiality, tracks trajectory.

Output:
{
  active_cases: 3,
  material_cases: 1,
  nclt_count: 1,
  highest_claim: 4.2,
  risk_level: "HIGH",
  cases: [...]
}
"""
from __future__ import annotations

# ── Mock litigation database ──────────────────────────────
# Keyed by lowercase company name keywords for lookup
MOCK_LITIGATION_DB: dict[str, list[dict]] = {
    "demo_fraud": [
        {
            "case_id": "IB/374/2023",
            "court": "NCLT Mumbai Bench",
            "type": "INSOLVENCY",
            "classification": "FINANCIAL",
            "claim_amount_cr": 4.2,
            "filed_date": "2023-02-14",
            "status": "PENDING",
            "last_hearing": "2025-01-20",
            "next_hearing": "2025-04-15",
            "petitioner": "XYZ Bank Ltd",
            "material": True,
        },
        {
            "case_id": "DRT/892/2022",
            "court": "DRT Mumbai",
            "type": "RECOVERY",
            "classification": "FINANCIAL",
            "claim_amount_cr": 2.1,
            "filed_date": "2022-08-10",
            "status": "PENDING",
            "last_hearing": "2025-02-15",
            "next_hearing": "2025-05-20",
            "petitioner": "ABC Finance Ltd",
            "material": True,
        },
        {
            "case_id": "CC/1043/2024",
            "court": "City Civil Court Mumbai",
            "type": "COMMERCIAL_DISPUTE",
            "classification": "COMMERCIAL",
            "claim_amount_cr": 0.3,
            "filed_date": "2024-01-05",
            "status": "ACTIVE",
            "last_hearing": "2025-01-30",
            "next_hearing": "2025-04-10",
            "petitioner": "Supplier Co.",
            "material": False,
        },
    ],
    "demo_conditional": [
        {
            "case_id": "DRT/445/2022",
            "court": "DRT Delhi",
            "type": "RECOVERY",
            "classification": "FINANCIAL",
            "claim_amount_cr": 2.1,
            "filed_date": "2022-03-20",
            "status": "PENDING",
            "last_hearing": "2025-01-10",
            "next_hearing": "2025-04-20",
            "petitioner": "PQR Bank",
            "material": False,
        },
    ],
}

RISK_LEVELS = {
    (0, 0): "CLEAN",
    (1, 0): "LOW",
    (1, 1): "MEDIUM",
    (2, 1): "HIGH",
    (3, 1): "VERY_HIGH",
}


def assess_materiality(case: dict, revenue_lakhs: float) -> bool:
    """A case is material if claim > 10% of annual revenue."""
    claim_lakhs = case.get("claim_amount_cr", 0) * 100
    if revenue_lakhs and revenue_lakhs > 0:
        return (claim_lakhs / revenue_lakhs) > 0.10
    return case.get("claim_amount_cr", 0) > 1.0  # >₹1Cr always material if no revenue data


def analyze_litigation(company_name: str, cin: str, revenue_lakhs: float = None) -> dict:
    """
    Look up litigation for a company.
    Assesses materiality, classifies risk.
    """
    cases = []
    name_lower = company_name.lower()

    for key, db_cases in MOCK_LITIGATION_DB.items():
        if key in name_lower or name_lower in key:
            cases = db_cases.copy()
            break

    # Reassess materiality with revenue data if available
    for case in cases:
        if revenue_lakhs:
            case["material"] = assess_materiality(case, revenue_lakhs)

    active_cases = [c for c in cases if c["status"] in ("PENDING", "ACTIVE")]
    material_cases = [c for c in cases if c.get("material")]
    nclt_cases = [c for c in cases if "NCLT" in c.get("court", "")]
    highest_claim = max((c.get("claim_amount_cr", 0) for c in cases), default=0)
    total_claim = sum(c.get("claim_amount_cr", 0) for c in cases)

    # Risk level
    n_active = len(active_cases)
    n_material = len(material_cases)
    risk_key = min(
        RISK_LEVELS.keys(),
        key=lambda k: abs(k[0] - n_active) + abs(k[1] - n_material),
    )
    risk_level = RISK_LEVELS.get(risk_key, "HIGH")
    if nclt_cases:
        risk_level = "VERY_HIGH"

    return {
        "company_name": company_name,
        "active_cases": len(active_cases),
        "material_cases": len(material_cases),
        "nclt_count": len(nclt_cases),
        "drt_count": len([c for c in cases if "DRT" in c.get("court", "")]),
        "highest_claim_cr": highest_claim,
        "total_claim_cr": round(total_claim, 2),
        "risk_level": risk_level,
        "cases": cases,
    }