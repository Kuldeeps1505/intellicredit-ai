"""
Agent 1 — Document Intelligence Agent
Day 2 deliverable.

Pipeline per document:
  1. Classify document type
  2. Extract text (pdfplumber for native, Tesseract for scanned)
  3. Extract tables (Camelot)
  4. FinBERT NER on text → financial entities
  5. Rule-based regex fallback for structured financial tables
  6. Record Chain of Evidence (provenance) for every extracted field
  7. GST-specific parsing via Sandbox.co.in API
  8. Bank statement parsing
  9. Embed chunks → ChromaDB
  10. Write financials + provenance to DB
  11. Publish WebSocket events throughout
"""
from __future__ import annotations
import re
import uuid
import time
import asyncio
from datetime import datetime
from pathlib import Path
import tempfile

import pdfplumber
from PIL import Image

# ── MVP: heavy ML libs removed ────────────────────────────────────────────
# pytesseract / pdf2image  → OCR skipped; pdfplumber handles text PDFs
# camelot / pandas         → pdfplumber table extraction used instead
# transformers / torch     → Claude API handles NLP (see run_finbert_ner stub)

from app.services.redis_service import publish_event, set_session
from app.services.minio_service import download_document
from app.services.chroma_service import upsert_chunks
from app.services.db_helper import log_agent, save_provenance, save_risk_flag
from app.config import settings

# ── MVP: FinBERT replaced by Claude API ──────────────────────────────────
# Full FinBERT NER (ProsusAI/finbert) removed — too heavy for hackathon.
# run_finbert_ner() now returns [] and regex extraction carries the full load.
# Post-hackathon: restore transformers + torch for production accuracy.
def get_finbert():
    return None


# ── Document type detection ───────────────────────────────
DOC_TYPE_KEYWORDS = {
    "GST_RETURN": ["gstr", "gstin", "gst return", "gstr-3b", "gstr-1", "input tax credit"],
    "ITR": ["income tax return", "itr", "assessment year", "schedule bp", "pan"],
    "ANNUAL_REPORT": ["annual report", "directors report", "balance sheet", "profit and loss"],
    "BANK_STATEMENT": ["account statement", "debit", "credit", "balance", "transaction date", "ifsc"],
    "LEGAL_NOTICE": ["legal notice", "nclt", "drt", "winding up", "insolvency", "petition"],
    "CREDIT_RATING": ["credit rating", "crisil", "icra", "care ratings", "rating rationale"],
    "BOARD_MINUTES": ["board of directors", "minutes of meeting", "resolution passed", "agenda"],
    "SHAREHOLDING_PATTERN": ["shareholding pattern", "promoter", "public shareholding", "din"],
}


def classify_document(filename: str, text_sample: str) -> str:
    fname = filename.lower()
    text_lower = text_sample.lower()[:2000]

    scores = {}
    for doc_type, keywords in DOC_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower or kw in fname)
        scores[doc_type] = score

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "UNKNOWN"


# ── PDF text extraction ───────────────────────────────────
def extract_text_native(pdf_bytes: bytes) -> list[dict]:
    """Extract text per page using pdfplumber. Returns [{page, text}]."""
    pages = []
    with pdfplumber.open(pdf_bytes if hasattr(pdf_bytes, 'read') else
                         __import__('io').BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"page": i, "text": text})
    return pages


def extract_text_ocr(pdf_bytes: bytes) -> list[dict]:
    """MVP stub: OCR removed. Returns empty — pdfplumber handles text PDFs."""
    return []


def is_scanned(pages: list[dict]) -> bool:
    """Heuristic: if average chars per page < 100, likely scanned."""
    if not pages:
        return True
    avg_chars = sum(len(p["text"]) for p in pages) / len(pages)
    return avg_chars < 100


# ── Table extraction (pdfplumber — replaces camelot for MVP) ─────────────
def extract_tables(pdf_path: str) -> list[dict]:
    """Extract tables using pdfplumber. No C deps, pure python."""
    results = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                for j, table in enumerate(page.extract_tables() or []):
                    if not table:
                        continue
                    # Convert to list-of-dicts using first row as header
                    headers = [str(h or f"col_{k}") for k, h in enumerate(table[0])]
                    rows = [dict(zip(headers, row)) for row in table[1:] if any(row)]
                    results.append({
                        "table_index": j,
                        "page": i,
                        "data": rows,
                        "accuracy": 90,  # pdfplumber doesn't report accuracy
                    })
    except Exception:
        pass
    return results


# ── FinBERT NER extraction ────────────────────────────────
FINANCIAL_FIELDS = {
    "revenue": ["revenue from operations", "total revenue", "net revenue", "sales", "turnover"],
    "ebitda": ["ebitda", "operating profit", "earnings before interest"],
    "net_profit": ["net profit", "profit after tax", "pat", "profit for the year"],
    "total_debt": ["total debt", "long term borrowings", "short term borrowings", "total borrowings"],
    "net_worth": ["net worth", "shareholders equity", "total equity"],
    "cash_from_operations": ["cash from operations", "operating cash flow", "cfo"],
    "total_assets": ["total assets"],
    "current_assets": ["current assets"],
    "current_liabilities": ["current liabilities"],
    "related_party_transactions": ["related party", "related party transactions"],
}

AMOUNT_PATTERN = re.compile(
    r"(?:₹|rs\.?|inr)?\s*(\d[\d,]*\.?\d*)\s*(crore|cr|lakh|lac|lakhs|million|thousand)?",
    re.IGNORECASE,
)

YEAR_PATTERN = re.compile(r"(20\d{2})", re.IGNORECASE)
RISK_KEYWORDS = ["default", "winding up", "nclt", "drt", "wilful defaulter", "insolvency", "npa"]


def normalize_amount_to_lakhs(value: str, unit: str) -> float | None:
    """Convert any amount string to ₹ Lakhs."""
    try:
        num = float(value.replace(",", ""))
        unit = (unit or "").lower()
        if unit in ("crore", "cr"):
            return num * 100
        elif unit in ("lakh", "lac", "lakhs"):
            return num
        elif unit == "million":
            return num * 10
        elif unit == "thousand":
            return num / 10
        return num  # assume lakhs if no unit
    except Exception:
        return None


def run_finbert_ner(text: str) -> list[dict]:
    """MVP stub: FinBERT removed. Regex extraction handles all fields.
    Post-hackathon: restore transformers pipeline here."""
    return []


def extract_financials_from_text(
    pages: list[dict],
    source_filename: str,
) -> tuple[dict, list[dict]]:
    """
    Extract financial fields from page texts.
    Returns:
      financials: {field_name: value}
      provenance: [{field_name, field_value, source_document, page_number,
                    extraction_method, confidence_score, raw_text_snippet}]
    """
    financials: dict = {}
    provenance: list[dict] = []

    for page_info in pages:
        page_num = page_info["page"]
        text = page_info["text"]
        text_lower = text.lower()

        # ── Rule-based regex extraction ───────────────────
        for field, keywords in FINANCIAL_FIELDS.items():
            if field in financials:
                continue  # already found
            for kw in keywords:
                idx = text_lower.find(kw)
                if idx == -1:
                    continue
                # Look for amount in surrounding 200 chars
                snippet = text[max(0, idx - 50): idx + 200]
                match = AMOUNT_PATTERN.search(snippet)
                if match:
                    value = normalize_amount_to_lakhs(match.group(1), match.group(2))
                    if value is not None:
                        financials[field] = value
                        provenance.append({
                            "field_name": field,
                            "field_value": str(value),
                            "source_document": source_filename,
                            "page_number": page_num,
                            "extraction_method": "regex",
                            "confidence_score": 0.80,
                            "raw_text_snippet": snippet.strip()[:300],
                        })
                        break

        # ── FinBERT NER (for organization names, risk phrases) ──
        entities = run_finbert_ner(text[:3000])
        for ent in entities:
            word = ent.get("word", "")
            label = ent.get("entity_group", "")
            score = ent.get("score", 0.5)
            # Extract company/org names
            if label in ("ORG",) and "company_name" not in financials:
                financials["company_name"] = word
                provenance.append({
                    "field_name": "company_name",
                    "field_value": word,
                    "source_document": source_filename,
                    "page_number": page_num,
                    "extraction_method": "FinBERT",
                    "confidence_score": float(score),
                    "raw_text_snippet": text[max(0, text.find(word) - 30): text.find(word) + 60],
                })

        # ── Risk keyword detection ────────────────────────
        for kw in RISK_KEYWORDS:
            if kw in text_lower:
                idx = text_lower.find(kw)
                snippet = text[max(0, idx - 50): idx + 150]
                provenance.append({
                    "field_name": f"risk_phrase_{kw.replace(' ', '_')}",
                    "field_value": kw,
                    "source_document": source_filename,
                    "page_number": page_num,
                    "extraction_method": "regex",
                    "confidence_score": 0.95,
                    "raw_text_snippet": snippet.strip()[:300],
                })

        # ── Extract identifiers ───────────────────────────
        gstin_match = re.search(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b", text)
        if gstin_match and "gstin" not in financials:
            financials["gstin"] = gstin_match.group()
            provenance.append({
                "field_name": "gstin",
                "field_value": gstin_match.group(),
                "source_document": source_filename,
                "page_number": page_num,
                "extraction_method": "regex",
                "confidence_score": 0.99,
                "raw_text_snippet": text[max(0, gstin_match.start() - 20):gstin_match.end() + 20],
            })

        pan_match = re.search(r"\b[A-Z]{5}\d{4}[A-Z]{1}\b", text)
        if pan_match and "pan" not in financials:
            financials["pan"] = pan_match.group()
            provenance.append({
                "field_name": "pan",
                "field_value": pan_match.group(),
                "source_document": source_filename,
                "page_number": page_num,
                "extraction_method": "regex",
                "confidence_score": 0.99,
                "raw_text_snippet": text[max(0, pan_match.start() - 20):pan_match.end() + 20],
            })

        cin_match = re.search(r"\b[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b", text)
        if cin_match and "cin" not in financials:
            financials["cin"] = cin_match.group()
            provenance.append({
                "field_name": "cin",
                "field_value": cin_match.group(),
                "source_document": source_filename,
                "page_number": page_num,
                "extraction_method": "regex",
                "confidence_score": 0.99,
                "raw_text_snippet": text[max(0, cin_match.start() - 20):cin_match.end() + 20],
            })

        # ── Extract year ──────────────────────────────────
        if "year" not in financials:
            year_match = YEAR_PATTERN.search(text)
            if year_match:
                financials["year"] = int(year_match.group(1))

    return financials, provenance


# ── Bank statement parser ─────────────────────────────────
def parse_bank_statement(pages: list[dict]) -> dict:
    """Extract key bank statement metrics."""
    all_text = " ".join(p["text"] for p in pages).lower()
    result = {
        "monthly_credits": [],
        "monthly_debits": [],
        "avg_balance": None,
        "bounce_count": 0,
    }
    # Count bounces
    result["bounce_count"] = all_text.count("returned") + all_text.count("dishonoured") + all_text.count("bounced")
    return result


# ── Sandbox.co.in GST API ─────────────────────────────────
import httpx

async def fetch_gstin_verification(gstin: str) -> dict:
    """Verify GSTIN via Sandbox.co.in API."""
    if not settings.sandbox_api_key:
        return {"status": "MOCK", "gstin": gstin, "active": True}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.sandbox_base_url}/gstin/{gstin}",
                headers={"x-api-key": settings.sandbox_api_key},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return {"status": "ERROR", "gstin": gstin}


async def fetch_gstr3b(gstin: str, financial_year: str) -> dict:
    """Fetch GSTR-3B (self-declared turnover) from Sandbox.co.in."""
    if not settings.sandbox_api_key:
        # Return mock data for development
        return {
            "gstin": gstin,
            "financial_year": financial_year,
            "quarterly_turnover": [
                {"quarter": "Q1", "turnover": 2375.0, "itc_claimed": 153.0},
                {"quarter": "Q2", "turnover": 2500.0, "itc_claimed": 161.2},
                {"quarter": "Q3", "turnover": 2612.0, "itc_claimed": 168.0},
                {"quarter": "Q4", "turnover": 2513.0, "itc_claimed": 161.5},
            ],
            "source": "MOCK",
        }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.sandbox_base_url}/gsp/gstr3b",
                headers={"x-api-key": settings.sandbox_api_key},
                params={"gstin": gstin, "financial_year": financial_year},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return {"gstin": gstin, "source": "ERROR"}


async def fetch_gstr2a(gstin: str, financial_year: str) -> dict:
    """Fetch GSTR-2A (auto-populated from supplier filings) from Sandbox.co.in."""
    if not settings.sandbox_api_key:
        return {
            "gstin": gstin,
            "financial_year": financial_year,
            "quarterly_itc_available": [
                {"quarter": "Q1", "itc_available": 120.5},
                {"quarter": "Q2", "itc_available": 148.3},
                {"quarter": "Q3", "itc_available": 155.7},
                {"quarter": "Q4", "itc_available": 140.2},
            ],
            "source": "MOCK",
        }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.sandbox_base_url}/gsp/gstr2a",
                headers={"x-api-key": settings.sandbox_api_key},
                params={"gstin": gstin, "financial_year": financial_year},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return {"gstin": gstin, "source": "ERROR"}


# ── ChromaDB embedding (MVP: use chromadb's built-in embedder) ───────────
# sentence-transformers removed — too heavy. ChromaDB's default
# embedding function (chromadb.utils.embedding_functions.DefaultEmbeddingFunction)
# handles this with a lightweight onnx model automatically.

def embed_and_store(app_id: str, doc_type: str, source: str, pages: list[dict]):
    """Chunk pages and store in ChromaDB using its built-in embedder."""
    try:
        all_chunks = []
        for page_info in pages:
            chunks = chunk_text(page_info["text"])
            for j, chunk in enumerate(chunks):
                all_chunks.append({
                    "text": chunk,
                    "page_number": page_info["page"],
                    "chunk_id": f"p{page_info['page']}_c{j}",
                })

        if not all_chunks:
            return

        # Pass None for embeddings — chroma_service uses its default embedder
        upsert_chunks(app_id, doc_type, source, all_chunks, embeddings=None)
    except Exception as e:
        print(f"[ChromaDB] Embedding error: {e}")


# ── DB write helpers ──────────────────────────────────────
async def save_financials_to_db(app_id: str, financials: dict, doc_id: str):
    """Write extracted financials to the financials table."""
    from app.models import Financial
    from app.services.db_helpers import _AgentSession
    import uuid as _uuid
    async with _AgentSession() as session:
        fin = Financial(
            id=str(_uuid.uuid4()),
            application_id=app_id,
            year=financials.get("year", datetime.utcnow().year),
            revenue=financials.get("revenue"),
            ebitda=financials.get("ebitda"),
            net_profit=financials.get("net_profit"),
            total_debt=financials.get("total_debt"),
            net_worth=financials.get("net_worth"),
            cash_from_operations=financials.get("cash_from_operations"),
            total_assets=financials.get("total_assets"),
            current_assets=financials.get("current_assets"),
            current_liabilities=financials.get("current_liabilities"),
            related_party_transactions=financials.get("related_party_transactions"),
            source_doc_ref=doc_id,
        )
        session.add(fin)
        await session.commit()


async def update_doc_status(doc_id: str, ocr_status: str, extraction_status: str, doc_type: str):
    from app.models import Document
    from sqlalchemy import select
    from app.services.db_helpers import _AgentSession
    async with _AgentSession() as session:
        result = await session.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc.ocr_status = ocr_status
            doc.extraction_status = extraction_status
            doc.doc_type = doc_type
            await session.commit()


# ── Main Agent Entry Point ────────────────────────────────
async def run(app_id: str) -> dict:
    """
    Called by the LangGraph DAG node_document_intelligence.
    Processes all documents for an application.
    Returns merged extracted_financials dict.
    """
    from app.models import Document, Application, Company
    from sqlalchemy import select
    from app.services.db_helpers import _AgentSession

    t_start = time.time()
    await log_agent(app_id, "document_intelligence", "RUNNING")

    # Fetch all uploaded documents
    async with _AgentSession() as session:
        docs_result = await session.execute(
            select(Document).where(Document.application_id == app_id)
        )
        documents = docs_result.scalars().all()
        doc_list = [{"id": d.id, "file_path": d.file_path, "filename": d.original_filename} for d in documents]

    all_financials = {}
    all_provenance = []
    gst_raw = {}

    for doc_info in doc_list:
        doc_id = doc_info["id"]
        file_path = doc_info["file_path"]
        filename = doc_info["filename"] or file_path.split("/")[-1]

        await publish_event(app_id, {
            "event_type": "AGENT_PROGRESS",
            "agent_name": "document_intelligence",
            "payload": {"message": f"Processing: {filename}"},
            "timestamp": datetime.utcnow().isoformat(),
        })

        try:
            pdf_bytes = download_document(file_path)
        except Exception as e:
            await update_doc_status(doc_id, "FAILED", "FAILED", "UNKNOWN")
            continue

        # ── Extract text ──────────────────────────────────
        pages = extract_text_native(pdf_bytes)
        if is_scanned(pages):
            pages = extract_text_ocr(pdf_bytes)

        await update_doc_status(doc_id, "DONE", "PENDING", "UNKNOWN")

        # ── Classify ──────────────────────────────────────
        sample_text = " ".join(p["text"] for p in pages[:3])
        doc_type = classify_document(filename, sample_text)

        await publish_event(app_id, {
            "event_type": "FIELD_EXTRACTED",
            "agent_name": "document_intelligence",
            "payload": {"doc_type": doc_type, "filename": filename},
            "timestamp": datetime.utcnow().isoformat(),
        })

        # ── Extract financials + provenance ───────────────
        financials, provenance = extract_financials_from_text(pages, filename)
        all_financials.update(financials)
        all_provenance.extend(provenance)

        # ── Emit field events ─────────────────────────────
        for field, value in financials.items():
            await publish_event(app_id, {
                "event_type": "FIELD_EXTRACTED",
                "agent_name": "document_intelligence",
                "payload": {"field": field, "value": value, "source": filename},
                "timestamp": datetime.utcnow().isoformat(),
            })

        # ── Bank statement special handling ───────────────
        if doc_type == "BANK_STATEMENT":
            bank_data = parse_bank_statement(pages)
            all_financials["bank_data"] = bank_data

        # ── GST: fetch from Sandbox.co.in ─────────────────
        if doc_type == "GST_RETURN" and "gstin" in all_financials:
            gstin = all_financials["gstin"]
            fy = str(all_financials.get("year", datetime.utcnow().year))
            gstr3b = await fetch_gstr3b(gstin, fy)
            gstr2a = await fetch_gstr2a(gstin, fy)
            gst_raw = {"gstr3b": gstr3b, "gstr2a": gstr2a}
            all_financials["gst_raw"] = gst_raw

        # ── Camelot table extraction ──────────────────────
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        tables = extract_tables(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)

        # ── Embed and store in ChromaDB ───────────────────
        embed_and_store(app_id, doc_type, filename, pages)

        await update_doc_status(doc_id, "DONE", "DONE", doc_type)

    # ── Save provenance to DB ─────────────────────────────
    if all_provenance:
        await save_provenance(app_id, all_provenance)

    # ── Save financials to DB ─────────────────────────────
    if all_financials:
        await save_financials_to_db(app_id, all_financials, "merged")

    # ── Write to Redis session ────────────────────────────
    from app.services.redis_service import set_session
    await set_session(app_id, "extracted_financials", all_financials)
    if gst_raw:
        await set_session(app_id, "gst_raw", gst_raw)

    duration_ms = int((time.time() - t_start) * 1000)
    summary = (
        f"Processed {len(doc_list)} documents. "
        f"Extracted {len(all_financials)} fields. "
        f"{len(all_provenance)} provenance records."
    )
    await log_agent(app_id, "document_intelligence", "COMPLETED",
                    output_summary=summary, duration_ms=duration_ms)

    await publish_event(app_id, {
        "event_type": "AGENT_COMPLETED",
        "agent_name": "document_intelligence",
        "payload": {"summary": summary, "duration_ms": duration_ms},
        "timestamp": datetime.utcnow().isoformat(),
    })

    return all_financials








