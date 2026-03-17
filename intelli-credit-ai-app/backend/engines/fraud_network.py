"""
Fraud Network Detection Engine — Day 4 deliverable.

Cross-references director DINs against:
  - Mock NPA database (200 director DINs pre-seeded)
  - Wilful Defaulters list (RBI mock data)

Pattern: same DIN in 2+ NPA companies → FRAUD_NETWORK_DETECTED (CRITICAL)

Also provides: GET /api/promoter/{pan}/network → NetworkX graph as JSON
"""
from __future__ import annotations
import re
from typing import Optional

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False

from app.services.db_helpers import save_risk_flag

AGENT = "fraud_network_detection"

# ── Mock NPA database — 200 director DINs ────────────────
# Format: {din: [{company, npa_year, amount_cr, bank}]}
MOCK_NPA_DB: dict[str, list[dict]] = {
    "00234567": [
        {"company": "Beta Fabrics Ltd", "npa_year": 2022, "amount_cr": 18.0,
         "bank": "Punjab National Bank", "status": "NPA"},
        {"company": "Delta Yarns Pvt Ltd", "npa_year": 2023, "amount_cr": 9.0,
         "bank": "Bank of Baroda", "status": "NPA"},
    ],
    "00987654": [
        {"company": "Sigma Steel Ltd", "npa_year": 2021, "amount_cr": 45.0,
         "bank": "SBI", "status": "WILFUL_DEFAULTER"},
    ],
    "00111222": [
        {"company": "Alpha Infra Corp", "npa_year": 2022, "amount_cr": 12.0,
         "bank": "HDFC Bank", "status": "NPA"},
        {"company": "Gamma Realty Pvt Ltd", "npa_year": 2023, "amount_cr": 6.5,
         "bank": "ICICI Bank", "status": "NPA"},
    ],
    "00333444": [
        {"company": "Omega Textiles Ltd", "npa_year": 2020, "amount_cr": 7.2,
         "bank": "Axis Bank", "status": "WILFUL_DEFAULTER"},
    ],
    "00555666": [
        {"company": "Zeta Chemicals Ltd", "npa_year": 2023, "amount_cr": 22.0,
         "bank": "Canara Bank", "status": "NPA"},
        {"company": "Eta Polymers Pvt Ltd", "npa_year": 2024, "amount_cr": 8.0,
         "bank": "Union Bank", "status": "NPA"},
    ],
    # 195 more DINs — clean (not in NPA list)
    **{f"009{i:05d}": [] for i in range(1, 196)},
}

WILFUL_DEFAULTERS = {"00987654", "00333444"}


def extract_dins_from_text(text: str) -> list[str]:
    """Extract 8-digit DIN numbers from text."""
    return re.findall(r"\b\d{8}\b", text)


def check_din(din: str) -> dict:
    """Check a single DIN against NPA + Wilful Defaulters database."""
    npa_records = MOCK_NPA_DB.get(din, [])
    is_wilful = din in WILFUL_DEFAULTERS
    return {
        "din": din,
        "npa_records": npa_records,
        "npa_count": len(npa_records),
        "is_wilful_defaulter": is_wilful,
        "total_npa_amount_cr": sum(r["amount_cr"] for r in npa_records),
        "is_flagged": len(npa_records) > 0 or is_wilful,
    }


def detect_fraud_network(dins: list[str]) -> dict:
    """
    Check all DINs. Detect multi-company NPA pattern.
    Returns full network analysis.
    """
    results = []
    flagged_dins = []
    total_npa_cr = 0.0

    for din in set(dins):
        check = check_din(din)
        results.append(check)
        if check["is_flagged"]:
            flagged_dins.append(din)
            total_npa_cr += check["total_npa_amount_cr"]

    # Fraud network: any DIN with 2+ NPA companies
    fraud_network_dins = [
        r for r in results
        if r["npa_count"] >= 2
    ]

    return {
        "dins_checked": len(set(dins)),
        "dins_flagged": len(flagged_dins),
        "fraud_network_detected": len(fraud_network_dins) > 0,
        "wilful_defaulters_found": len([r for r in results if r["is_wilful_defaulter"]]),
        "total_npa_exposure_cr": round(total_npa_cr, 2),
        "din_details": results,
        "fraud_network_details": fraud_network_dins,
    }


def build_network_graph(app_id: str, company_name: str, dins: list[str]) -> dict:
    """
    Build NetworkX graph:
      - Central node: borrower company
      - Director nodes linked to borrower
      - NPA company nodes linked to directors
    Returns JSON-serializable graph for frontend D3 visualization.
    """
    if not HAS_NX:
        return {"nodes": [], "edges": [], "error": "networkx not installed"}

    G = nx.Graph()

    # Central company node
    G.add_node(company_name, node_type="BORROWER", color="#3B82F6")

    for din in set(dins):
        check = check_din(din)
        din_label = f"DIR-{din}"
        node_color = "#EF4444" if check["is_flagged"] else "#10B981"
        G.add_node(din_label, node_type="DIRECTOR", din=din, color=node_color)
        G.add_edge(company_name, din_label, edge_type="DIRECTOR_OF")

        for npa in check["npa_records"]:
            npa_label = npa["company"]
            G.add_node(
                npa_label,
                node_type="NPA_COMPANY",
                amount_cr=npa["amount_cr"],
                year=npa["npa_year"],
                bank=npa["bank"],
                color="#DC2626",
            )
            G.add_edge(din_label, npa_label,
                       edge_type="DIRECTOR_NPA",
                       label=f"NPA {npa['npa_year']} ₹{npa['amount_cr']}Cr")

    nodes = [{"id": n, **G.nodes[n]} for n in G.nodes()]
    edges = [{"source": u, "target": v, **G.edges[u, v]} for u, v in G.edges()]

    return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}


async def run(app_id: str, extracted_text: str = "", company_name: str = "Unknown") -> dict:
    """
    Main entry point. Extracts DINs from documents, checks against NPA DB,
    saves risk flags, returns network analysis.
    """
    # Extract DINs from extracted text (document intelligence output)
    dins_from_text = extract_dins_from_text(extracted_text)

    # Also check demo Dataset 2 DIN if seeded
    from app.services.redis_service import get_session
    extracted = await get_session(app_id, "extracted_financials") or {}
    seeded_dins = extracted.get("director_dins", [])
    all_dins = list(set(dins_from_text + seeded_dins))

    if not all_dins:
        return {
            "dins_checked": 0,
            "fraud_network_detected": False,
            "note": "No DINs found in documents",
            "graph": {"nodes": [], "edges": []},
        }

    network = detect_fraud_network(all_dins)
    graph = build_network_graph(app_id, company_name, all_dins)

    # Save risk flags
    if network["fraud_network_detected"]:
        for detail in network["fraud_network_details"]:
            companies = ", ".join(r["company"] for r in detail["npa_records"])
            await save_risk_flag(
                app_id,
                "FRAUD_NETWORK_DETECTED",
                "CRITICAL",
                (
                    f"Director DIN {detail['din']} linked to {detail['npa_count']} NPA companies: "
                    f"{companies}. Total NPA exposure: ₹{detail['total_npa_amount_cr']:.1f}Cr. "
                    "Fraud network pattern detected."
                ),
                AGENT,
            )

    if network["wilful_defaulters_found"] > 0:
        await save_risk_flag(
            app_id,
            "WILFUL_DEFAULTER_LINKED",
            "CRITICAL",
            f"{network['wilful_defaulters_found']} director(s) classified as Wilful Defaulter by RBI.",
            AGENT,
        )

    result = {**network, "graph": graph}
    from app.services.redis_service import set_session
    await set_session(app_id, "fraud_network", result)
    return result