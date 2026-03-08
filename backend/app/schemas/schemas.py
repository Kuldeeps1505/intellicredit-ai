"""
Pydantic v2 schemas — request bodies and response models.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ── Company ───────────────────────────────────────────────
class CompanyCreate(BaseModel):
    cin: str
    name: str
    pan: Optional[str] = None
    gstin: Optional[str] = None
    sector: Optional[str] = None
    incorporation_date: Optional[datetime] = None
    registered_address: Optional[str] = None


class CompanyOut(CompanyCreate):
    id: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Application ───────────────────────────────────────────
class ApplicationCreate(BaseModel):
    company: CompanyCreate
    loan_amount_requested: float = Field(..., gt=0, description="In ₹ Lakhs")
    purpose: Optional[str] = None
    assigned_officer_id: Optional[str] = None
    aa_consent_handle: Optional[str] = None


class ApplicationOut(BaseModel):
    id: str
    company_id: str
    loan_amount_requested: float
    purpose: Optional[str]
    status: str
    aa_consent_handle: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Application Status ────────────────────────────────────
class AgentStatus(BaseModel):
    agent_name: str
    status: str                   # IDLE | RUNNING | COMPLETED | ERROR
    duration_ms: Optional[int] = None
    output_summary: Optional[str] = None


class ApplicationStatus(BaseModel):
    application_id: str
    pipeline_status: str          # PENDING | PROCESSING | COMPLETED | ERROR
    agents: List[AgentStatus]
    overall_progress_pct: int


# ── Field Provenance ──────────────────────────────────────
class FieldProvenanceOut(BaseModel):
    field_name: str
    field_value: Optional[str]
    source_document: Optional[str]
    page_number: Optional[int]
    extraction_method: Optional[str]
    confidence_score: Optional[float]
    raw_text_snippet: Optional[str]
    model_config = {"from_attributes": True}


# ── Financials ────────────────────────────────────────────
class FinancialOut(BaseModel):
    year: int
    revenue: Optional[float]
    ebitda: Optional[float]
    net_profit: Optional[float]
    total_debt: Optional[float]
    net_worth: Optional[float]
    cash_from_operations: Optional[float]
    source_doc_ref: Optional[str]
    provenance: Optional[List[FieldProvenanceOut]] = []
    model_config = {"from_attributes": True}


class FinancialsResponse(BaseModel):
    application_id: str
    financials: List[FinancialOut]
    provenance: List[FieldProvenanceOut]


# ── Document Upload ───────────────────────────────────────
class DocumentOut(BaseModel):
    id: str
    original_filename: Optional[str]
    doc_type: Optional[str]
    ocr_status: str
    extraction_status: str
    file_path: str
    model_config = {"from_attributes": True}


# ── WebSocket Event ───────────────────────────────────────
class WSEvent(BaseModel):
    event_type: str               # AGENT_STARTED | AGENT_COMPLETED | FLAG_DETECTED | FIELD_EXTRACTED | ERROR
    agent_name: Optional[str] = None
    payload: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)