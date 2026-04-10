"""
All 13 SQLAlchemy ORM models for IntelliCredit AI.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean,
    DateTime, Text, ForeignKey, JSON, BigInteger
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


# ─── 1. companies ─────────────────────────────────────────────────────────────
class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    cin = Column(String(21), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    pan = Column(String(10), nullable=True, index=True)
    gstin = Column(String(15), nullable=True, index=True)
    sector = Column(String(100), nullable=True)
    incorporation_date = Column(DateTime, nullable=True)
    registered_address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("Application", back_populates="company")


# ─── 2. applications ──────────────────────────────────────────────────────────
class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    loan_amount_requested = Column(Float, nullable=False)          # in ₹ Lakhs
    purpose = Column(String(500), nullable=True)
    status = Column(String(50), default="PENDING")                 # PENDING | PROCESSING | COMPLETED | ERROR
    assigned_officer_id = Column(String(100), nullable=True)
    aa_consent_handle = Column(String(255), nullable=True)         # India Stack AA consent handle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="applications")
    financials = relationship("Financial", back_populates="application")
    ratios = relationship("Ratio", back_populates="application")
    risk_scores = relationship("RiskScore", back_populates="application")
    risk_flags = relationship("RiskFlag", back_populates="application")
    research_data = relationship("ResearchData", back_populates="application", uselist=False)
    dd_notes = relationship("DDNote", back_populates="application")
    documents = relationship("Document", back_populates="application")
    cam_reports = relationship("CAMReport", back_populates="application", uselist=False)
    agent_logs = relationship("AgentLog", back_populates="application")
    field_provenance = relationship("FieldProvenance", back_populates="application")
    buyer_concentration = relationship("BuyerConcentration", back_populates="application")


# ─── 3. financials ────────────────────────────────────────────────────────────
class Financial(Base):
    __tablename__ = "financials"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    year = Column(Integer, nullable=False)                          # e.g. 2024
    revenue = Column(Float, nullable=True)                         # ₹ Lakhs
    ebitda = Column(Float, nullable=True)
    net_profit = Column(Float, nullable=True)
    total_debt = Column(Float, nullable=True)
    net_worth = Column(Float, nullable=True)
    cash_from_operations = Column(Float, nullable=True)
    total_assets = Column(Float, nullable=True)
    current_assets = Column(Float, nullable=True)
    current_liabilities = Column(Float, nullable=True)
    related_party_transactions = Column(Float, nullable=True)
    source_doc_ref = Column(String(255), nullable=True)            # filename reference
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="financials")


# ─── 4. ratios ────────────────────────────────────────────────────────────────
class Ratio(Base):
    __tablename__ = "ratios"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    year = Column(Integer, nullable=False)
    current_ratio = Column(Float, nullable=True)
    quick_ratio = Column(Float, nullable=True)
    cash_ratio = Column(Float, nullable=True)
    de_ratio = Column(Float, nullable=True)
    debt_to_assets = Column(Float, nullable=True)
    interest_coverage = Column(Float, nullable=True)
    net_profit_margin = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    roa = Column(Float, nullable=True)
    ebitda_margin = Column(Float, nullable=True)
    asset_turnover = Column(Float, nullable=True)
    receivables_days = Column(Float, nullable=True)
    inventory_days = Column(Float, nullable=True)
    dscr = Column(Float, nullable=True)
    fixed_charge_coverage = Column(Float, nullable=True)
    gst_itr_variance = Column(Float, nullable=True)                # %
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="ratios")


# ─── 5. risk_scores ───────────────────────────────────────────────────────────
class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    character = Column(Float, nullable=True)                       # 0–10
    capacity = Column(Float, nullable=True)
    capital = Column(Float, nullable=True)
    collateral = Column(Float, nullable=True)
    conditions = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)                     # 0–100
    risk_category = Column(String(50), nullable=True)              # LOW | MEDIUM | HIGH | VERY_HIGH
    decision = Column(String(50), nullable=True)                   # APPROVE | CONDITIONAL | REJECT
    character_explanation = Column(Text, nullable=True)
    capacity_explanation = Column(Text, nullable=True)
    capital_explanation = Column(Text, nullable=True)
    collateral_explanation = Column(Text, nullable=True)
    conditions_explanation = Column(Text, nullable=True)
    default_probability_12m = Column(Float, nullable=True)
    default_probability_24m = Column(Float, nullable=True)
    top_drivers = Column(JSON, nullable=True)                      # [{factor, coefficient, direction}]
    computed_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="risk_scores")


# ─── 6. risk_flags ────────────────────────────────────────────────────────────
class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    flag_type = Column(String(100), nullable=False)                # e.g. GST_ITR_MISMATCH
    severity = Column(String(20), nullable=False)                  # CRITICAL | HIGH | MEDIUM | LOW
    description = Column(Text, nullable=False)
    detected_by_agent = Column(String(100), nullable=True)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="risk_flags")


# ─── 7. research_data ─────────────────────────────────────────────────────────
class ResearchData(Base):
    __tablename__ = "research_data"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, unique=True)
    promoter_reputation = Column(String(50), nullable=True)        # GOOD | MEDIUM | HIGH_RISK
    litigation_count = Column(Integer, default=0)
    industry_outlook = Column(String(20), nullable=True)           # POSITIVE | NEUTRAL | NEGATIVE
    news_sentiment_score = Column(Float, nullable=True)            # -1 to +1
    litigation_cases = Column(JSON, nullable=True)
    news_articles = Column(JSON, nullable=True)
    directorship_history = Column(JSON, nullable=True)
    raw_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="research_data")


# ─── 8. dd_notes ──────────────────────────────────────────────────────────────
class DDNote(Base):
    __tablename__ = "dd_notes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    officer_text = Column(Text, nullable=False)
    ai_signals_json = Column(JSON, nullable=True)                  # [{signal_type, description, risk_category, delta, reasoning}]
    risk_delta = Column(Float, default=0.0)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="dd_notes")


# ─── 9. documents ─────────────────────────────────────────────────────────────
class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    file_path = Column(String(500), nullable=False)                # MinIO object path
    original_filename = Column(String(255), nullable=True)
    doc_type = Column(String(50), nullable=True)                   # GST_RETURN | ITR | ANNUAL_REPORT | etc.
    ocr_status = Column(String(20), default="PENDING")             # PENDING | DONE | FAILED
    extraction_status = Column(String(20), default="PENDING")
    file_size_bytes = Column(BigInteger, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="documents")


# ─── 10. cam_reports ──────────────────────────────────────────────────────────
class CAMReport(Base):
    __tablename__ = "cam_reports"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, unique=True)
    pdf_path = Column(String(500), nullable=True)
    docx_path = Column(String(500), nullable=True)
    recommendation = Column(String(50), nullable=True)             # APPROVE | CONDITIONAL | REJECT
    loan_amount_approved = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)
    tenor_months = Column(Integer, nullable=True)
    covenants = Column(JSON, nullable=True)
    counterfactuals = Column(JSON, nullable=True)                  # [{factor, current, target, action, priority}]
    generated_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="cam_reports")


# ─── 11. agent_logs ───────────────────────────────────────────────────────────
class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)                    # STARTED | RUNNING | COMPLETED | ERROR
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="agent_logs")


# ─── 12. field_provenance (Chain of Evidence) ─────────────────────────────────
class FieldProvenance(Base):
    __tablename__ = "field_provenance"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    field_name = Column(String(100), nullable=False)               # e.g. "revenue_2024"
    field_value = Column(String(500), nullable=True)               # e.g. "12000.0"
    source_document = Column(String(255), nullable=True)           # filename
    page_number = Column(Integer, nullable=True)
    extraction_method = Column(String(50), nullable=True)          # FinBERT | regex | Camelot | Sandbox_API
    confidence_score = Column(Float, nullable=True)                # 0.0 – 1.0
    raw_text_snippet = Column(Text, nullable=True)                 # surrounding context
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="field_provenance")


# ─── 13. buyer_concentration ──────────────────────────────────────────────────
class BuyerConcentration(Base):
    __tablename__ = "buyer_concentration"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    buyer_gstin = Column(String(15), nullable=False)
    buyer_name = Column(String(255), nullable=True)
    invoice_total = Column(Float, nullable=True)                   # ₹ Lakhs
    pct_of_revenue = Column(Float, nullable=True)                  # e.g. 42.3
    concentration_risk_flag = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="buyer_concentration")
