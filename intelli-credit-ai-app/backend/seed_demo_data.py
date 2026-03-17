"""
Demo Dataset Seeder — Day 5 deliverable.
Pre-loads all 3 demo datasets directly into DB + Redis.
No document upload needed — data is injected directly.

Usage:
  python seed_demo_data.py

Creates:
  demo_1 — APPROVE (Score 81, IT sector, clean GST)
  demo_2 — REJECT HERO DEMO (Score 28, fraud, NCLT, ITC fraud, single buyer 71%)
  demo_3 — CONDITIONAL APPROVAL (Score 61, Real Estate, DRT case)
"""
import asyncio
import uuid
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, text

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.models import (
    Base, Company, Application, Financial, Ratio,
    RiskScore, RiskFlag, ResearchData, DDNote,
    CAMReport, AgentLog, FieldProvenance, BuyerConcentration
)

engine = create_async_engine(settings.database_url, echo=False)
Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# ── Fixed demo IDs ────────────────────────────────────────
DEMO_IDS = {
    "demo_1": "11111111-1111-1111-1111-111111111111",
    "demo_2": "22222222-2222-2222-2222-222222222222",
    "demo_3": "33333333-3333-3333-3333-333333333333",
}

COMPANY_IDS = {
    "demo_1": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "demo_2": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    "demo_3": "cccccccc-cccc-cccc-cccc-cccccccccccc",
}


async def clean_demo(session, app_id):
    """Remove existing demo records to allow re-seeding."""
    for table in ["field_provenance", "buyer_concentration", "risk_flags", "risk_scores",
                  "ratios", "financials", "research_data", "dd_notes", "cam_reports",
                  "agent_logs", "documents", "applications"]:
        await session.execute(
            text(f"DELETE FROM {table} WHERE application_id = :id"), {"id": app_id}
        )
    await session.commit()


async def seed_dataset_1(session):
    """Demo 1 — APPROVE. Score 81. IT sector. Clean."""
    app_id = DEMO_IDS["demo_1"]
    comp_id = COMPANY_IDS["demo_1"]

    # Company
    existing = await session.execute(select(Company).where(Company.id == comp_id))
    if not existing.scalar_one_or_none():
        session.add(Company(
            id=comp_id, cin="U72200MH2012PTC123001",
            name="TechNova Solutions Pvt Ltd",
            pan="AABCT1234D", gstin="27AABCT1234D1Z5",
            sector="IT", registered_address="Pune, Maharashtra",
        ))

    await clean_demo(session, app_id)

    session.add(Application(
        id=app_id, company_id=comp_id,
        loan_amount_requested=300.0,
        purpose="Working capital for software project delivery",
        status="COMPLETED", aa_consent_handle="AA-CONSENT-DEMO-1",
    ))
    await session.flush()

    # Financials — 3 years
    for year, rev, ebitda, np_, debt, nw, cfo in [
        (2022, 8000, 1400, 780, 2200, 3800, 900),
        (2023, 9600, 1700, 960, 2000, 4600, 1100),
        (2024, 12000, 2160, 1200, 2300, 5700, 1400),
    ]:
        session.add(Financial(
            id=str(uuid.uuid4()), application_id=app_id, year=year,
            revenue=rev, ebitda=ebitda, net_profit=np_,
            total_debt=debt, net_worth=nw, cash_from_operations=cfo,
            total_assets=8000, current_assets=3200, current_liabilities=2100,
            related_party_transactions=200, source_doc_ref="TechNova_AR_FY24.pdf",
        ))

    # Ratios
    session.add(Ratio(
        id=str(uuid.uuid4()), application_id=app_id, year=2024,
        current_ratio=1.52, quick_ratio=1.31, cash_ratio=0.8,
        de_ratio=0.40, interest_coverage=8.2, net_profit_margin=0.10,
        roe=0.21, roa=0.15, ebitda_margin=0.18,
        asset_turnover=1.5, receivables_days=42, inventory_days=0,
        dscr=1.80, fixed_charge_coverage=2.1, gst_itr_variance=1.2,
    ))

    # Risk Score — APPROVE
    session.add(RiskScore(
        id=str(uuid.uuid4()), application_id=app_id,
        character=9.0, capacity=8.5, capital=8.5, collateral=7.5, conditions=8.0,
        character_explanation="Excellent track record — zero litigation, GSTN verified, clean audit history.",
        capacity_explanation="Strong DSCR of 1.80x comfortably above 1.25x threshold; 15% revenue CAGR.",
        capital_explanation="Low D/E of 0.40x with ₹57Cr net worth provides substantial equity cushion.",
        collateral_explanation="Loan-to-net-worth ratio of 0.05x — well within prudential limits.",
        conditions_explanation="IT sector Positive outlook; healthy buyer diversification (top 3 = 38%).",
        final_score=81.0, risk_category="LOW", decision="APPROVE",
        default_probability_12m=4.2, default_probability_24m=7.8,
        top_drivers=[
            {"factor": "dscr", "coefficient": 0.8, "direction": "decreases_risk"},
            {"factor": "de_ratio", "coefficient": 0.6, "direction": "decreases_risk"},
        ],
    ))

    # Research
    session.add(ResearchData(
        id=str(uuid.uuid4()), application_id=app_id,
        promoter_reputation="GOOD", litigation_count=0,
        industry_outlook="POSITIVE", news_sentiment_score=0.42,
        litigation_cases=[], news_articles=[],
        raw_json={"note": "Clean promoter history"},
    ))

    # GST recon — CLEAN
    gst_recon = {
        "quarters": [
            {"quarter": "Q1", "gstr2a_itc_available": 89.2, "gstr3b_itc_claimed": 90.1,
             "variance_pct": 1.0, "suspect_itc_amount": 0.0, "flagged": False},
            {"quarter": "Q2", "gstr2a_itc_available": 98.5, "gstr3b_itc_claimed": 99.0,
             "variance_pct": 0.5, "suspect_itc_amount": 0.0, "flagged": False},
            {"quarter": "Q3", "gstr2a_itc_available": 106.2, "gstr3b_itc_claimed": 107.0,
             "variance_pct": 0.8, "suspect_itc_amount": 0.0, "flagged": False},
            {"quarter": "Q4", "gstr2a_itc_available": 112.0, "gstr3b_itc_claimed": 112.8,
             "variance_pct": 0.7, "suspect_itc_amount": 0.0, "flagged": False},
        ],
        "total_suspect_itc_lakhs": 0.0, "itc_fraud_suspected": False,
        "output_suppression_suspected": False,
    }

    # Buyer concentration — HEALTHY
    buyer_conc_records = [
        ("29AAABC1001D1Z5", "Infosys Ltd", 1560, 13.0),
        ("27BBBCD2002E2Z6", "TCS Digital", 1440, 12.0),
        ("24CCCDE3003F3Z7", "Wipro Tech", 1320, 11.0),
        ("33DDDEF4004G4Z8", "HCL Services", 1200, 10.0),
        ("07EEEFG5005H5Z9", "Others", 6480, 54.0),
    ]
    for gstin, name, total, pct in buyer_conc_records:
        session.add(BuyerConcentration(
            id=str(uuid.uuid4()), application_id=app_id,
            buyer_gstin=gstin, buyer_name=name,
            invoice_total=total, pct_of_revenue=pct, concentration_risk_flag=False,
        ))

    # Counterfactuals — approved with buffer
    counterfactuals = {
        "current_score": 81.0, "approve_threshold": 75.0, "gap": 0.0,
        "decision": "APPROVE", "buffer_message":
            "This application was APPROVED with a buffer of 6.0 points above threshold. "
            "Score: 81/100. Approval threshold: 75. Risk category: LOW.",
        "total_achievable_improvement": 0.0, "would_achieve_approval": True,
        "counterfactuals": [],
    }

    # CAM
    session.add(CAMReport(
        id=str(uuid.uuid4()), application_id=app_id,
        recommendation="APPROVE", loan_amount_approved=300.0,
        interest_rate=9.5, tenor_months=48,
        covenants={"covenants": ["Annual audited financials", "Maintain DSCR > 1.25x"]},
        counterfactuals=counterfactuals["counterfactuals"],
    ))

    # Provenance records
    for field, value, source, page, method, conf in [
        ("revenue_2024", "12000.0", "TechNova_AR_FY24.pdf", 42, "Camelot", 0.97),
        ("net_profit_2024", "1200.0", "TechNova_AR_FY24.pdf", 44, "regex", 0.95),
        ("de_ratio_2024", "0.40", "TechNova_AR_FY24.pdf", 48, "FinBERT", 0.93),
        ("gstin", "27AABCT1234D1Z5", "TechNova_GST_Return.pdf", 1, "regex", 0.99),
    ]:
        session.add(FieldProvenance(
            id=str(uuid.uuid4()), application_id=app_id,
            field_name=field, field_value=value, source_document=source,
            page_number=page, extraction_method=method, confidence_score=conf,
        ))

    # Agent logs
    for agent_name, summary in [
        ("document_intelligence", "4 documents processed. 12 fields extracted."),
        ("financial_analysis", "15 ratios computed. 0 anomaly flags."),
        ("research_intelligence", "Reputation: GOOD. Litigation: 0. Sector: POSITIVE."),
        ("gst_reconciliation_engine", "GST reconciliation CLEAN. Variance < 2%."),
        ("buyer_concentration_engine", "Top buyer 13%. Top 3: 36%. Healthy."),
        ("risk_assessment", "Five-Cs: 9+8.5+8.5+7.5+8=81. APPROVE."),
        ("credit_decision", "APPROVE. ₹300L @ 9.5% for 48 months."),
        ("counterfactual_engine", "Approved with 6pt buffer. No counterfactuals needed."),
        ("cam_generation", "CAM generated. PDF + DOCX exported."),
    ]:
        session.add(AgentLog(
            id=str(uuid.uuid4()), application_id=app_id,
            agent_name=agent_name, status="COMPLETED",
            output_summary=summary, duration_ms=800,
        ))

    await session.flush()

    # Write Redis session
    from app.services.redis_service import set_session
    await set_session(app_id, "gst_reconciliation", gst_recon)
    await set_session(app_id, "counterfactuals", counterfactuals)
    await set_session(app_id, "risk_scores", {
        "character": 9.0, "capacity": 8.5, "capital": 8.5,
        "collateral": 7.5, "conditions": 8.0, "final_score": 81.0,
        "risk_category": "LOW", "decision": "APPROVE",
        "default_probability_12m": 4.2,
    })
    buyer_top = [{"buyer_gstin": g, "buyer_name": n, "invoice_total": t,
                  "pct_of_revenue": p, "concentration_risk_flag": False}
                 for g, n, t, p in buyer_conc_records]
    await set_session(app_id, "buyer_concentration", {
        "top_buyers": buyer_top, "total_buyers": 5,
        "top3_concentration_pct": 36.0, "top_buyer_pct": 13.0,
        "single_buyer_dependency": False, "high_concentration": False,
        "grand_total_revenue_lakhs": 12000,
    })

    print(f"  ✅ Dataset 1 seeded — app_id: {app_id}")


async def seed_dataset_2(session):
    """Demo 2 — REJECT HERO. Score 28. Fraud. ITC fraud. NCLT. Single buyer 71%."""
    app_id = DEMO_IDS["demo_2"]
    comp_id = COMPANY_IDS["demo_2"]

    existing = await session.execute(select(Company).where(Company.id == comp_id))
    if not existing.scalar_one_or_none():
        session.add(Company(
            id=comp_id, cin="L17100MH2008PLC200002",
            name="Shree Textiles & Fabrics Ltd",
            pan="AABCS2345E", gstin="27AABCS2345E1Z6",
            sector="TEXTILE", registered_address="Mumbai, Maharashtra",
        ))

    await clean_demo(session, app_id)

    session.add(Application(
        id=app_id, company_id=comp_id,
        loan_amount_requested=500.0,
        purpose="Machinery upgrade and working capital",
        status="COMPLETED", aa_consent_handle="AA-CONSENT-DEMO-2",
    ))
    await session.flush()

    # Financials
    for year, rev, ebitda, np_, debt, nw, cfo in [
        (2022, 7500, 480, 210, 2800, 1800, -80),
        (2023, 8200, 520, 180, 3100, 1950, -120),
        (2024, 9500, 570, 150, 3900, 2100, -180),
    ]:
        session.add(Financial(
            id=str(uuid.uuid4()), application_id=app_id, year=year,
            revenue=rev, ebitda=ebitda, net_profit=np_,
            total_debt=debt, net_worth=nw, cash_from_operations=cfo,
            total_assets=6500, current_assets=2800, current_liabilities=3100,
            related_party_transactions=890, source_doc_ref="ShreeTextiles_AR_FY24.pdf",
        ))

    # Ratios
    session.add(Ratio(
        id=str(uuid.uuid4()), application_id=app_id, year=2024,
        current_ratio=0.90, quick_ratio=0.71, cash_ratio=0.12,
        de_ratio=1.86, interest_coverage=1.2, net_profit_margin=0.016,
        roe=0.07, roa=0.02, ebitda_margin=0.06,
        asset_turnover=1.46, receivables_days=198, inventory_days=82,
        dscr=0.90, fixed_charge_coverage=0.95, gst_itr_variance=23.0,
    ))

    # CRITICAL Risk Flags
    flags = [
        ("ITC_FRAUD_SUSPECTED", "CRITICAL",
         "GSTR-2A vs GSTR-3B reconciliation detected ₹12.9L in excess ITC claims. "
         "Borrower claimed Input Tax Credit not matched by supplier filings.",
         "gst_reconciliation_engine"),
        ("SINGLE_BUYER_DEPENDENCY", "CRITICAL",
         "Single buyer 'Alpha Trading Co' (GSTIN: 29AAAAB9876C1Z5) accounts for 71.0% "
         "of total revenue (₹6745L). Critical single-customer dependency.",
         "buyer_concentration_engine"),
        ("FRAUD_NETWORK_DETECTED", "CRITICAL",
         "Director DIN 00234567 linked to 2 NPA companies: "
         "Beta Fabrics Ltd (NPA 2022 ₹18Cr, PNB) and Delta Yarns Pvt Ltd (NPA 2023 ₹9Cr, BoB). "
         "Fraud network pattern detected.",
         "fraud_network_detection"),
        ("NCLT_LITIGATION", "CRITICAL",
         "1 active NCLT insolvency petition IB/374/2023. Claim amount: ₹4.2Cr.",
         "research_intelligence"),
        ("PROFIT_CASH_DIVERGENCE", "CRITICAL",
         "Cash from operations (₹-180L) is negative while net profit (₹150L) is positive. "
         "Classic earnings manipulation signal.",
         "financial_analysis"),
        ("GST_ITR_MISMATCH", "HIGH",
         "GST turnover ₹95Cr vs ITR income ₹73Cr — 23.0% variance (threshold: 15%). "
         "Revenue underreporting suspected.",
         "financial_analysis"),
        ("HIGH_LEVERAGE", "HIGH",
         "D/E ratio = 1.86 (rising trend). Note: combined with negative CFO signals distress.",
         "financial_analysis"),
        ("NEGATIVE_SECTOR_OUTLOOK", "MEDIUM",
         "Sector 'TEXTILE' has NEGATIVE outlook. China import surge; GST rate uncertainty; weak exports.",
         "research_intelligence"),
    ]
    for ft, sev, desc, agent in flags:
        session.add(RiskFlag(
            id=str(uuid.uuid4()), application_id=app_id,
            flag_type=ft, severity=sev, description=desc, detected_by_agent=agent,
        ))

    # Risk Score — REJECT
    session.add(RiskScore(
        id=str(uuid.uuid4()), application_id=app_id,
        character=2.5, capacity=2.0, capital=3.5, collateral=4.0, conditions=2.5,
        character_explanation="Critical character risk — ITC fraud suspected, DIN linked to 2 NPA companies, NCLT petition active.",
        capacity_explanation="DSCR of 0.90x is well below 1.25x minimum; negative CFO for 3 consecutive years.",
        capital_explanation="D/E of 1.86x rising with shrinking margins; net worth growth insufficient.",
        collateral_explanation="Loan-to-net-worth 0.24x but negative cash flow undermines collateral quality.",
        conditions_explanation="Textile sector Negative outlook; 71% single-buyer dependency — extreme concentration risk.",
        final_score=28.0, risk_category="VERY_HIGH", decision="REJECT",
        default_probability_12m=47.8, default_probability_24m=72.3,
        top_drivers=[
            {"factor": "dscr", "coefficient": 0.9, "direction": "increases_risk"},
            {"factor": "buyer_conc_pct", "coefficient": 0.7, "direction": "increases_risk"},
            {"factor": "itc_variance", "coefficient": 0.8, "direction": "increases_risk"},
        ],
    ))

    # Research
    session.add(ResearchData(
        id=str(uuid.uuid4()), application_id=app_id,
        promoter_reputation="HIGH_RISK", litigation_count=3,
        industry_outlook="NEGATIVE", news_sentiment_score=-0.38,
        litigation_cases=[
            {"case_id": "IB/374/2023", "court": "NCLT Mumbai Bench",
             "type": "INSOLVENCY", "claim_amount_cr": 4.2,
             "filed_date": "2023-02-14", "status": "PENDING", "material": True},
            {"case_id": "DRT/892/2022", "court": "DRT Mumbai",
             "type": "RECOVERY", "claim_amount_cr": 2.1,
             "filed_date": "2022-08-10", "status": "PENDING", "material": True},
            {"case_id": "CC/1043/2024", "court": "City Civil Court",
             "type": "COMMERCIAL_DISPUTE", "claim_amount_cr": 0.3,
             "filed_date": "2024-01-05", "status": "ACTIVE", "material": False},
        ],
        raw_json={"director_dins": ["00234567"]},
    ))

    # DD Notes — pre-seeded
    dd_signals = [
        {"signal_type": "LOW_CAPACITY_UTILIZATION", "description": "Plant at 35% capacity utilization",
         "risk_category": "OPERATIONAL_EFFICIENCY", "risk_points_delta": 10, "reasoning": "35% utilization indicates severe demand/operational stress."},
        {"signal_type": "MANAGEMENT_REFUSAL", "description": "Management refused to share auditor contact",
         "risk_category": "MANAGEMENT_TRANSPARENCY", "risk_points_delta": 8, "reasoning": "Refusal to share auditor details is a governance red flag."},
    ]
    session.add(DDNote(
        id=str(uuid.uuid4()), application_id=app_id,
        officer_text="Plant at 35% capacity. Management refused to share auditor contact. "
                     "Inventory appears inflated — stacks of unsold fabric visible.",
        ai_signals_json=dd_signals, risk_delta=18.0,
    ))

    # GST recon — FRAUD
    gst_recon = {
        "quarters": [
            {"quarter": "Q1 FY24", "gstr2a_itc_available": 48.3, "gstr3b_itc_claimed": 61.2,
             "variance_pct": 26.7, "suspect_itc_amount": 12.9, "flagged": True},
            {"quarter": "Q2 FY24", "gstr2a_itc_available": 52.1, "gstr3b_itc_claimed": 65.4,
             "variance_pct": 25.5, "suspect_itc_amount": 13.3, "flagged": True},
            {"quarter": "Q3 FY24", "gstr2a_itc_available": 61.0, "gstr3b_itc_claimed": 68.2,
             "variance_pct": 11.8, "suspect_itc_amount": 7.2, "flagged": True},
            {"quarter": "Q4 FY24", "gstr2a_itc_available": 71.5, "gstr3b_itc_claimed": 74.0,
             "variance_pct": 3.5, "suspect_itc_amount": 0.0, "flagged": False},
        ],
        "total_suspect_itc_lakhs": 129.0,
        "itc_fraud_suspected": True,
        "output_suppression_suspected": False,
        "gstin": "27AABCS2345E1Z6",
        "financial_year": "2023-24",
    }

    # Buyer concentration — CRITICAL
    buyer_records = [
        ("29AAAAB9876C1Z5", "Alpha Trading Co (Mumbai)", 6745.0, 71.0, True),
        ("27BBBBB1234D2Z6", "Beta Retail Ltd", 1124.0, 11.8, False),
        ("24CCCCC5678E3Z7", "Gamma Exports", 876.0, 9.2, False),
        ("33DDDDD9012F4Z8", "Delta Distributors", 542.0, 5.7, False),
        ("07EEEEE3456G5Z9", "Others", 213.0, 2.3, False),
    ]
    for gstin, name, total, pct, flag in buyer_records:
        session.add(BuyerConcentration(
            id=str(uuid.uuid4()), application_id=app_id,
            buyer_gstin=gstin, buyer_name=name,
            invoice_total=total, pct_of_revenue=pct, concentration_risk_flag=flag,
        ))

    # Counterfactuals
    counterfactuals = {
        "current_score": 28.0, "approve_threshold": 75.0, "gap": 47.0,
        "decision": "REJECT", "buffer_message": None,
        "total_achievable_improvement": 44.5, "would_achieve_approval": False,
        "counterfactuals": [
            {"factor": "collateral", "label": "Collateral Coverage",
             "current_value": "₹5.0Cr loan vs net worth ₹21L",
             "target_value": "Additional ₹8.0Cr collateral", "delta": 8.0,
             "score_impact": 12.0,
             "estimated_action": "Provide additional collateral of ₹8.0Cr (property/FD/securities)",
             "priority_rank": 1, "feasibility": "HIGH", "implementation_timeline": "1–2 weeks"},
            {"factor": "itc_fraud", "label": "ITC Reconciliation Discrepancy",
             "current_value": "₹12.9Cr suspect ITC", "target_value": "₹0 discrepancy",
             "delta": 12.9, "score_impact": 10.0,
             "estimated_action": "Resolve ₹12.9Cr ITC discrepancy — file revised GSTR-3B with GSTN, reconcile with supplier invoices",
             "priority_rank": 2, "feasibility": "MEDIUM", "implementation_timeline": "1–3 months"},
            {"factor": "de_ratio", "label": "Debt/Equity Ratio",
             "current_value": 1.86, "target_value": 1.5, "delta": 0.36,
             "score_impact": 8.0,
             "estimated_action": "Reduce D/E from 1.86 to below 1.5 — repay ₹7.6Cr debt OR infuse ₹4.6Cr equity",
             "priority_rank": 3, "feasibility": "MEDIUM", "implementation_timeline": "3–6 months"},
            {"factor": "litigation", "label": "Material Litigation",
             "current_value": "2 material cases totalling ₹6.3Cr",
             "target_value": "0 material cases", "delta": 2,
             "score_impact": 8.0,
             "estimated_action": "Resolve NCLT petition IB/374/2023 ₹4.2Cr + DRT case DRT/892/2022 ₹2.1Cr — obtain court clearance certificates",
             "priority_rank": 4, "feasibility": "LOW", "implementation_timeline": "12–24 months"},
            {"factor": "buyer_concentration", "label": "Buyer Revenue Concentration",
             "current_value": "71% revenue from top buyer",
             "target_value": "Below 40%", "delta": 31.0, "score_impact": 6.5,
             "estimated_action": "Diversify revenue — reduce top buyer from 71% to below 40% by onboarding 5+ new customers of comparable size",
             "priority_rank": 5, "feasibility": "LOW", "implementation_timeline": "12–24 months"},
        ],
    }

    # CAM
    session.add(CAMReport(
        id=str(uuid.uuid4()), application_id=app_id,
        recommendation="REJECT", loan_amount_approved=0.0,
        interest_rate=0.0, tenor_months=0,
        covenants={"covenants": [], "monitoring_triggers": []},
        counterfactuals=counterfactuals["counterfactuals"],
    ))

    # Provenance
    for field, value, source, page, method, conf in [
        ("revenue_2024", "9500.0", "ShreeTextiles_AR_FY24.pdf", 38, "Camelot", 0.96),
        ("gst_turnover", "9500.0", "ShreeTextiles_GST_Return.pdf", 2, "Sandbox_API", 0.99),
        ("itr_income", "7300.0", "ShreeTextiles_ITR.pdf", 5, "pdfplumber", 0.94),
        ("dscr_2024", "0.90", "ShreeTextiles_AR_FY24.pdf", 52, "regex", 0.92),
        ("gstin", "27AABCS2345E1Z6", "ShreeTextiles_GST_Return.pdf", 1, "regex", 0.99),
        ("risk_phrase_nclt", "NCLT", "LegalNotice_NCLT.pdf", 1, "regex", 0.99),
    ]:
        session.add(FieldProvenance(
            id=str(uuid.uuid4()), application_id=app_id,
            field_name=field, field_value=value, source_document=source,
            page_number=page, extraction_method=method, confidence_score=conf,
        ))

    # Agent logs
    for agent_name, summary in [
        ("document_intelligence", "5 documents processed. 18 fields extracted. Chain of Evidence recorded."),
        ("financial_analysis", "15 ratios computed. 5 anomaly flags: GST_ITR_MISMATCH, PROFIT_CASH_DIVERGENCE, HIGH_LEVERAGE."),
        ("gst_reconciliation_engine", "ITC FRAUD SUSPECTED. Suspect ITC: ₹129L across 3 quarters."),
        ("buyer_concentration_engine", "SINGLE_BUYER_DEPENDENCY CRITICAL. Top buyer: 71%. GSTIN: 29AAAAB9876C1Z5."),
        ("research_intelligence", "Reputation: HIGH_RISK. 3 litigation cases (1 NCLT). Textile sector NEGATIVE."),
        ("risk_assessment", "Five-Cs: 2.5+2+3.5+4+2.5=28. REJECT. Default 12m: 47.8%."),
        ("credit_decision", "REJECT. 5 critical flags. Policy violations: DSCR<1.25, fraud flags."),
        ("counterfactual_engine", "Gap: 47pts. 5 counterfactuals. Would not achieve approval without major restructuring."),
        ("cam_generation", "CAM generated. All 8 sections + Chain of Evidence appendix."),
    ]:
        session.add(AgentLog(
            id=str(uuid.uuid4()), application_id=app_id,
            agent_name=agent_name, status="COMPLETED",
            output_summary=summary, duration_ms=1200,
        ))

    await session.flush()

    from app.services.redis_service import set_session
    await set_session(app_id, "gst_reconciliation", gst_recon)
    await set_session(app_id, "counterfactuals", counterfactuals)
    await set_session(app_id, "risk_scores", {
        "character": 2.5, "capacity": 2.0, "capital": 3.5,
        "collateral": 4.0, "conditions": 2.5, "final_score": 28.0,
        "risk_category": "VERY_HIGH", "decision": "REJECT",
        "default_probability_12m": 47.8,
    })
    buyer_top = [{"buyer_gstin": g, "buyer_name": n, "invoice_total": t,
                  "pct_of_revenue": p, "concentration_risk_flag": f}
                 for g, n, t, p, f in buyer_records]
    await set_session(app_id, "buyer_concentration", {
        "top_buyers": buyer_top, "total_buyers": 5,
        "top3_concentration_pct": 92.0, "top_buyer_pct": 71.0,
        "single_buyer_dependency": True, "high_concentration": True,
        "grand_total_revenue_lakhs": 9500,
    })
    print(f"  ✅ Dataset 2 (HERO DEMO) seeded — app_id: {app_id}")


async def seed_dataset_3(session):
    """Demo 3 — CONDITIONAL. Score 61. Real Estate. DRT case. D/E 2.7."""
    app_id = DEMO_IDS["demo_3"]
    comp_id = COMPANY_IDS["demo_3"]

    existing = await session.execute(select(Company).where(Company.id == comp_id))
    if not existing.scalar_one_or_none():
        session.add(Company(
            id=comp_id, cin="U45200DL2010PLC300003",
            name="Prestige Realty Developers Ltd",
            pan="AABCP3456F", gstin="07AABCP3456F1Z7",
            sector="REAL_ESTATE", registered_address="New Delhi",
        ))

    await clean_demo(session, app_id)

    session.add(Application(
        id=app_id, company_id=comp_id,
        loan_amount_requested=800.0,
        purpose="Construction finance for residential project Phase 2",
        status="COMPLETED", aa_consent_handle="AA-CONSENT-DEMO-3",
    ))
    await session.flush()

    for year, rev, ebitda, np_, debt, nw, cfo in [
        (2022, 14000, 2800, 980, 9200, 5800, 620),
        (2023, 16500, 3300, 1140, 10100, 6800, 780),
        (2024, 18000, 3780, 1260, 12800, 7200, 900),
    ]:
        session.add(Financial(
            id=str(uuid.uuid4()), application_id=app_id, year=year,
            revenue=rev, ebitda=ebitda, net_profit=np_,
            total_debt=debt, net_worth=nw, cash_from_operations=cfo,
            total_assets=22000, current_assets=8200, current_liabilities=6100,
            related_party_transactions=1400, source_doc_ref="Prestige_AR_FY24.pdf",
        ))

    session.add(Ratio(
        id=str(uuid.uuid4()), application_id=app_id, year=2024,
        current_ratio=1.34, quick_ratio=0.98, cash_ratio=0.42,
        de_ratio=1.78, interest_coverage=2.1, net_profit_margin=0.07,
        roe=0.175, roa=0.057, ebitda_margin=0.21,
        asset_turnover=0.82, receivables_days=88, inventory_days=210,
        dscr=1.30, fixed_charge_coverage=1.4, gst_itr_variance=3.8,
    ))

    # Flags
    session.add(RiskFlag(
        id=str(uuid.uuid4()), application_id=app_id,
        flag_type="MATERIAL_LITIGATION", severity="MEDIUM",
        description="1 DRT case DRT/445/2022 (₹2.1Cr) — manageable, not NCLT.",
        detected_by_agent="research_intelligence",
    ))

    session.add(RiskScore(
        id=str(uuid.uuid4()), application_id=app_id,
        character=7.0, capacity=6.5, capital=5.5, collateral=6.5, conditions=5.0,
        character_explanation="Moderate character risk — 1 DRT litigation (₹2.1Cr), promoter reputation MEDIUM.",
        capacity_explanation="DSCR of 1.30x marginally above 1.25x threshold; improving revenue trend.",
        capital_explanation="D/E of 1.78x is within limit but elevated for Real Estate sector.",
        collateral_explanation="Underlying real estate assets provide adequate cover at current LTV.",
        conditions_explanation="Real Estate sector NEUTRAL outlook; moderate buyer concentration (top 3 = 52%).",
        final_score=61.0, risk_category="MEDIUM", decision="CONDITIONAL_APPROVAL",
        default_probability_12m=18.4, default_probability_24m=31.6,
        top_drivers=[
            {"factor": "de_ratio", "coefficient": 0.5, "direction": "increases_risk"},
            {"factor": "dscr", "coefficient": -0.3, "direction": "decreases_risk"},
        ],
    ))

    session.add(ResearchData(
        id=str(uuid.uuid4()), application_id=app_id,
        promoter_reputation="MEDIUM", litigation_count=1,
        industry_outlook="NEUTRAL", news_sentiment_score=0.08,
        litigation_cases=[
            {"case_id": "DRT/445/2022", "court": "DRT Delhi",
             "type": "RECOVERY", "claim_amount_cr": 2.1,
             "filed_date": "2022-03-20", "status": "PENDING", "material": False},
        ],
        raw_json={},
    ))

    gst_recon = {
        "quarters": [
            {"quarter": "Q1 FY24", "gstr2a_itc_available": 142.0, "gstr3b_itc_claimed": 144.8,
             "variance_pct": 2.0, "suspect_itc_amount": 0.0, "flagged": False},
            {"quarter": "Q2 FY24", "gstr2a_itc_available": 168.0, "gstr3b_itc_claimed": 169.6,
             "variance_pct": 1.0, "suspect_itc_amount": 0.0, "flagged": False},
            {"quarter": "Q3 FY24", "gstr2a_itc_available": 188.0, "gstr3b_itc_claimed": 192.2,
             "variance_pct": 2.2, "suspect_itc_amount": 0.0, "flagged": False},
            {"quarter": "Q4 FY24", "gstr2a_itc_available": 198.0, "gstr3b_itc_claimed": 201.0,
             "variance_pct": 1.5, "suspect_itc_amount": 0.0, "flagged": False},
        ],
        "total_suspect_itc_lakhs": 0.0, "itc_fraud_suspected": False,
        "output_suppression_suspected": False,
    }

    buyer_records = [
        ("07AAAAC1001H1Z5", "Metro Construction Ltd", 4860, 27.0, False),
        ("27BBBBC2002I2Z6", "Urban Infra Pvt Ltd", 3240, 18.0, False),
        ("24CCCCC3003J3Z7", "Skyline Developers", 1260, 7.0, False),
        ("33DDDDC4004K4Z8", "Others", 8640, 48.0, False),
    ]
    for gstin, name, total, pct, flag in buyer_records:
        session.add(BuyerConcentration(
            id=str(uuid.uuid4()), application_id=app_id,
            buyer_gstin=gstin, buyer_name=name,
            invoice_total=total, pct_of_revenue=pct, concentration_risk_flag=flag,
        ))

    counterfactuals = {
        "current_score": 61.0, "approve_threshold": 75.0, "gap": 14.0,
        "decision": "CONDITIONAL_APPROVAL", "buffer_message": None,
        "total_achievable_improvement": 22.0, "would_achieve_approval": True,
        "counterfactuals": [
            {"factor": "collateral", "label": "Collateral Coverage",
             "current_value": "₹8.0Cr loan vs net worth ₹72Cr",
             "target_value": "Additional ₹6.0Cr collateral", "delta": 6.0,
             "score_impact": 9.0,
             "estimated_action": "Provide additional collateral of ₹6.0Cr — property/FD/developer guarantee",
             "priority_rank": 1, "feasibility": "HIGH", "implementation_timeline": "1–2 weeks"},
            {"factor": "de_ratio", "label": "Debt/Equity Ratio",
             "current_value": 1.78, "target_value": 1.5, "delta": 0.28,
             "score_impact": 7.0,
             "estimated_action": "Reduce D/E from 1.78 to below 1.5 — repay ₹20Cr debt OR infuse ₹12Cr equity",
             "priority_rank": 2, "feasibility": "MEDIUM", "implementation_timeline": "3–6 months"},
            {"factor": "litigation", "label": "DRT Litigation",
             "current_value": "1 DRT case ₹2.1Cr", "target_value": "0 cases",
             "delta": 1, "score_impact": 4.0,
             "estimated_action": "Resolve DRT/445/2022 ₹2.1Cr — settle with claimant and obtain NOC from DRT",
             "priority_rank": 3, "feasibility": "MEDIUM", "implementation_timeline": "3–9 months"},
        ],
    }

    session.add(CAMReport(
        id=str(uuid.uuid4()), application_id=app_id,
        recommendation="CONDITIONAL_APPROVAL", loan_amount_approved=680.0,
        interest_rate=12.5, tenor_months=36,
        covenants={
            "covenants": ["Quarterly audited financials", "Personal guarantee of promoter",
                          "Quarterly stock audit", "Maintain DSCR above 1.25x"],
            "monitoring_triggers": ["DSCR below 1.25 for 1 quarter", "Revenue decline > 15%"]
        },
        counterfactuals=counterfactuals["counterfactuals"],
    ))

    for field, value, source, page, method, conf in [
        ("revenue_2024", "18000.0", "Prestige_AR_FY24.pdf", 40, "Camelot", 0.97),
        ("dscr_2024", "1.30", "Prestige_AR_FY24.pdf", 55, "regex", 0.93),
        ("de_ratio_2024", "1.78", "Prestige_AR_FY24.pdf", 52, "FinBERT", 0.91),
    ]:
        session.add(FieldProvenance(
            id=str(uuid.uuid4()), application_id=app_id,
            field_name=field, field_value=value, source_document=source,
            page_number=page, extraction_method=method, confidence_score=conf,
        ))

    for agent_name, summary in [
        ("document_intelligence", "3 documents. 14 fields extracted."),
        ("financial_analysis", "15 ratios. 1 flag: INVENTORY_INFLATION (RE sector normal)."),
        ("gst_reconciliation_engine", "GST CLEAN. Max variance 2.2%."),
        ("buyer_concentration_engine", "Top buyer 27%. Top 3: 52%. Moderate."),
        ("research_intelligence", "Reputation: MEDIUM. 1 DRT case. RE sector NEUTRAL."),
        ("risk_assessment", "Five-Cs: 7+6.5+5.5+6.5+5=61. CONDITIONAL_APPROVAL."),
        ("credit_decision", "CONDITIONAL. ₹680L @ 12.5% for 36m. Personal guarantee required."),
        ("counterfactual_engine", "Gap: 14pts. Collateral provision alone achieves approval."),
        ("cam_generation", "CAM generated. PDF + DOCX."),
    ]:
        session.add(AgentLog(
            id=str(uuid.uuid4()), application_id=app_id,
            agent_name=agent_name, status="COMPLETED",
            output_summary=summary, duration_ms=900,
        ))

    await session.flush()

    from app.services.redis_service import set_session
    await set_session(app_id, "gst_reconciliation", gst_recon)
    await set_session(app_id, "counterfactuals", counterfactuals)
    await set_session(app_id, "risk_scores", {
        "character": 7.0, "capacity": 6.5, "capital": 5.5,
        "collateral": 6.5, "conditions": 5.0, "final_score": 61.0,
        "risk_category": "MEDIUM", "decision": "CONDITIONAL_APPROVAL",
        "default_probability_12m": 18.4,
    })
    buyer_top = [{"buyer_gstin": g, "buyer_name": n, "invoice_total": t,
                  "pct_of_revenue": p, "concentration_risk_flag": f}
                 for g, n, t, p, f in buyer_records]
    await set_session(app_id, "buyer_concentration", {
        "top_buyers": buyer_top, "total_buyers": 4,
        "top3_concentration_pct": 52.0, "top_buyer_pct": 27.0,
        "single_buyer_dependency": False, "high_concentration": False,
        "grand_total_revenue_lakhs": 18000,
    })
    print(f"  ✅ Dataset 3 (CONDITIONAL) seeded — app_id: {app_id}")


async def main():
    print("\n🌱 IntelliCredit AI — Demo Data Seeder")
    print("=" * 50)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as session:
        print("\nSeeding Dataset 1 — APPROVE (IT sector, clean) ...")
        await seed_dataset_1(session)

        print("\nSeeding Dataset 2 — REJECT HERO (fraud, ITC, NCLT) ...")
        await seed_dataset_2(session)

        print("\nSeeding Dataset 3 — CONDITIONAL (Real Estate, DRT) ...")
        await seed_dataset_3(session)

        await session.commit()

    print("\n" + "=" * 50)
    print("✅ All 3 demo datasets seeded successfully!")
    print(f"\nDemo Application IDs:")
    for k, v in DEMO_IDS.items():
        print(f"  {k}: {v}")
    print("\nTest commands:")
    print(f"  curl http://localhost:8000/api/applications/{DEMO_IDS['demo_2']}/risk-score")
    print(f"  curl http://localhost:8000/api/applications/{DEMO_IDS['demo_2']}/gst-reconciliation")
    print(f"  curl http://localhost:8000/api/applications/{DEMO_IDS['demo_2']}/counterfactuals")
    print(f"  curl http://localhost:8000/api/applications/{DEMO_IDS['demo_2']}/buyer-concentration")
    print()


if __name__ == "__main__":
    asyncio.run(main())