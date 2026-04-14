"""Agent 1 — Document Intelligence. pdfplumber+regex, no ChromaDB/MinIO."""
from __future__ import annotations
import re, uuid, time, io
from datetime import datetime
from pathlib import Path
import pdfplumber
from app.services.redis_service import publish_event, set_session
from app.services.db_helper import log_agent, save_provenance

AGENT = "document_intelligence"
LOCAL_STORE = Path(__file__).parent.parent / "local_uploads"

DOC_KEYWORDS = {
    "GST_RETURN":    ["gstr","gstin","gst return","gstr-3b","input tax credit"],
    "ITR":           ["income tax return","itr","assessment year"],
    "ANNUAL_REPORT": ["annual report","directors report","balance sheet","profit and loss"],
    "BANK_STATEMENT":["account statement","debit","credit","balance","transaction date"],
    "LEGAL_NOTICE":  ["legal notice","nclt","drt","winding up","insolvency"],
}

FIN_FIELDS = {
    "revenue":              ["revenue from operations","total revenue","net revenue","sales","turnover"],
    "ebitda":               ["ebitda","operating profit","earnings before interest"],
    "net_profit":           ["net profit","profit after tax","pat","profit for the year"],
    "total_debt":           ["total debt","total borrowings","long term borrowings"],
    "net_worth":            ["net worth","shareholders equity","total equity"],
    "cash_from_operations": ["cash from operations","operating cash flow","cfo"],
    "total_assets":         ["total assets"],
    "current_assets":       ["current assets","total current assets"],
    "current_liabilities":  ["current liabilities","total current liabilities"],
}

AMT_RE  = re.compile(
    r"(?:₹|rs\.?|inr)?\s*(\d[\d,]*\.?\d*)\s*(crore|cr|lakh|lac|lakhs|million|thousand)?",
    re.IGNORECASE
)
# Stricter pattern: requires a currency symbol OR a unit word, to avoid matching bare years
AMT_STRICT = re.compile(
    r"(?:(?:₹|rs\.?|inr)\s*(\d[\d,]*\.?\d*)\s*(crore|cr|lakh|lac|lakhs)?)"
    r"|(?:(\d[\d,]*\.?\d*)\s*(crore|cr|lakh|lac|lakhs))",
    re.IGNORECASE
)
YEAR_RE = re.compile(r"(20\d{2})")
RISK_KW = ["default","winding up","nclt","drt","wilful defaulter","insolvency","npa"]

# Minimum plausible value in Lakhs for each field (filters out year numbers etc.)
FIELD_MIN = {
    "revenue": 100, "ebitda": 10, "net_profit": -5000, "total_debt": 10,
    "net_worth": 10, "cash_from_operations": -5000, "total_assets": 100,
    "current_assets": 10, "current_liabilities": 10,
}


def _classify(fname: str, sample: str) -> str:
    fl = fname.lower(); sl = sample.lower()[:2000]
    scores = {dt: sum(1 for kw in kws if kw in sl or kw in fl) for dt, kws in DOC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "UNKNOWN"


def _to_lakhs(val: str, unit: str):
    try:
        n = float(val.replace(",",""))
        u = (unit or "").lower()
        if u in ("crore","cr"):          return round(n*100, 2)
        if u in ("lakh","lac","lakhs"):  return round(n, 2)
        if u == "million":               return round(n*10, 2)
        return round(n, 2)
    except Exception:
        return None


def _extract(pages: list[dict], source: str):
    fins: dict = {}
    prov: list = []
    for pg in pages:
        pnum = pg["page"]; text = pg["text"]; tl = text.lower()
        for field, kws in FIN_FIELDS.items():
            if field in fins:
                continue
            for kw in kws:
                idx = tl.find(kw)
                if idx == -1:
                    continue
                # Look for amount AFTER the keyword (within 200 chars)
                snip = text[idx:idx+200]
                # Try strict pattern first (requires ₹ or unit word)
                m = AMT_STRICT.search(snip)
                if m:
                    val_str = m.group(1) or m.group(3) or ""
                    unit_str = m.group(2) or m.group(4) or ""
                else:
                    # Fall back to loose pattern but only if unit word present
                    m = AMT_RE.search(snip)
                    if not m or not m.group(2):  # require unit word
                        continue
                    val_str = m.group(1)
                    unit_str = m.group(2) or ""
                if not val_str:
                    continue
                v = _to_lakhs(val_str, unit_str)
                min_val = FIELD_MIN.get(field, 0)
                if v is not None and v >= min_val:
                    fins[field] = v
                    context = text[max(0,idx-20):idx+200].strip()[:250]
                    prov.append({"field_name":field,"field_value":str(v),
                        "source_document":source,"page_number":pnum,
                        "extraction_method":"regex","confidence_score":0.85,
                        "raw_text_snippet":context})
                    break
        for kw in RISK_KW:
            if kw in tl:
                idx = tl.find(kw)
                prov.append({"field_name":f"risk_{kw.replace(' ','_')}","field_value":kw,
                    "source_document":source,"page_number":pnum,
                    "extraction_method":"regex","confidence_score":0.95,
                    "raw_text_snippet":text[max(0,idx-40):idx+120].strip()[:200]})
        for pat, field in [
            (r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b","gstin"),
            (r"\b[A-Z]{5}\d{4}[A-Z]\b","pan"),
            (r"\b[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b","cin"),
        ]:
            if field not in fins:
                m = re.search(pat, text)
                if m:
                    fins[field] = m.group()
                    prov.append({"field_name":field,"field_value":m.group(),
                        "source_document":source,"page_number":pnum,
                        "extraction_method":"regex","confidence_score":0.99,
                        "raw_text_snippet":text[max(0,m.start()-15):m.end()+15]})
        if "year" not in fins:
            # Find the most recent year mentioned (not just the first)
            years = [int(y) for y in YEAR_RE.findall(text) if 2018 <= int(y) <= 2030]
            if years:
                fins["year"] = max(years)
    return fins, prov


async def run(app_id: str) -> dict:
    t = time.time()
    await log_agent(app_id, AGENT, "RUNNING")
    await publish_event(app_id, {"event_type":"AGENT_STARTED","agent_name":AGENT,
                                  "payload":{},"timestamp":datetime.utcnow().isoformat()})

    from sqlalchemy import select
    from app.models import Document, Financial
    from app.services.db_helper import _AgentSession

    all_fins: dict = {}
    all_prov: list = []

    async with _AgentSession() as session:
        docs = (await session.execute(
            select(Document).where(Document.application_id == app_id)
        )).scalars().all()
        doc_list = [{"id":d.id,"file_path":d.file_path,
                     "filename":d.original_filename or "document.pdf"} for d in docs]

    for doc in doc_list:
        fname = doc["filename"]; fpath = doc["file_path"]
        await publish_event(app_id, {"event_type":"AGENT_PROGRESS","agent_name":AGENT,
                                      "payload":{"message":f"Processing: {fname}"},
                                      "timestamp":datetime.utcnow().isoformat()})
        pdf_bytes = b""
        for candidate in [
            LOCAL_STORE / fpath.replace("/","_").replace("local://",""),
            Path(fpath.replace("local://","")),
            LOCAL_STORE / Path(fpath).name,
        ]:
            if candidate.exists():
                pdf_bytes = candidate.read_bytes(); break

        if not pdf_bytes:
            continue

        pages = []
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    pages.append({"page":i,"text":page.extract_text() or ""})
        except Exception:
            continue

        doc_type = _classify(fname, " ".join(p["text"] for p in pages[:3]))
        fins, prov = _extract(pages, fname)
        all_fins.update(fins); all_prov.extend(prov)

        async with _AgentSession() as session:
            d = (await session.execute(select(Document).where(Document.id == doc["id"]))).scalar_one_or_none()
            if d:
                d.doc_type = doc_type; d.ocr_status = "DONE"; d.extraction_status = "DONE"
                await session.commit()

    if all_fins:
        async with _AgentSession() as session:
            from sqlalchemy import select as sel
            existing = (await session.execute(
                sel(Financial).where(Financial.application_id == app_id)
            )).scalars().first()
            if not existing:
                session.add(Financial(id=str(uuid.uuid4()), application_id=app_id,
                    year=all_fins.get("year",2024),
                    revenue=all_fins.get("revenue"), ebitda=all_fins.get("ebitda"),
                    net_profit=all_fins.get("net_profit"), total_debt=all_fins.get("total_debt"),
                    net_worth=all_fins.get("net_worth"),
                    cash_from_operations=all_fins.get("cash_from_operations"),
                    total_assets=all_fins.get("total_assets"),
                    current_assets=all_fins.get("current_assets"),
                    current_liabilities=all_fins.get("current_liabilities")))
                await session.commit()

    if all_prov:
        await save_provenance(app_id, all_prov)

    await set_session(app_id, "extracted_financials", all_fins)

    duration_ms = int((time.time()-t)*1000)
    summary = f"Processed {len(doc_list)} doc(s). Extracted {len(all_fins)} fields."
    await log_agent(app_id, AGENT, "COMPLETED", output_summary=summary, duration_ms=duration_ms)
    await publish_event(app_id, {"event_type":"AGENT_COMPLETED","agent_name":AGENT,
                                  "payload":{"summary":summary},"timestamp":datetime.utcnow().isoformat()})
    return all_fins
