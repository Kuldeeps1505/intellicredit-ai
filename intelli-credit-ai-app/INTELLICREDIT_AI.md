# IntelliCredit AI — Technical Reference

> India Stack-native autonomous corporate credit intelligence platform.  
> Replaces 3–6 weeks of manual credit appraisal with a 4-minute AI pipeline.  
> **IIT Hyderabad Hackathon 2026**

---

## 1. Problem

Indian banks spend 3–6 weeks and ₹80,000 per corporate loan appraisal — manually.  
Hidden risks (ITC fraud, buyer concentration, promoter NPA links) go undetected.  
No existing tool reconciles GSTR-2A vs GSTR-3B or computes buyer concentration from GSTR-1.

---

## 2. Solution

7 AI agents + 2 engines running in parallel, producing a full **Credit Appraisal Memo (CAM)** in ~4 minutes with:
- Real financial extraction from uploaded PDFs
- Live GSTN data via Sandbox.co.in API
- Promoter intelligence via Zaubacorp + eCourts + Tavily
- Five-Cs scoring + Logistic Regression default probability
- Counterfactual explainability ("what must change to get approved")

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.109, Python 3.11, SQLite (aiosqlite) |
| Agent Orchestration | LangGraph 1.0.9, LangChain Core |
| LLM | Google Gemini 2.0 Flash (primary) → Ollama/Mistral (fallback) |
| PDF Extraction | pdfplumber 0.11, regex NER |
| Document Output | python-docx, reportlab, jsPDF (client-side) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Charts | Recharts (radar, bar, pie), custom SVG gauges |
| State | React Context (PipelineContext), 500ms polling |
| Real-time | WebSocket + in-memory event bus (asyncio.Queue) |
| File Storage | Local disk (MinIO-compatible interface) |
| Pipeline State | JSON files on disk (survives uvicorn --reload) |

---

## 4. Agent Pipeline

```
Agent 1: Document Intelligence
    ↓
    ├── Agent 2: Financial Analysis      ─┐
    ├── Agent 3: Research Intelligence   ├── parallel
    ├── Engine 1: GSTR Reconciliation    ├── parallel
    └── Engine 2: Buyer Concentration   ─┘
                    ↓
            Agent 4: Risk Assessment
                    ↓
            Agent 5: Due Diligence
                    ↓
            Agent 6: Credit Decision
                    ↓
            Agent 7: CAM Generation
```

### Agent Details

| Agent | File | What it does |
|---|---|---|
| Document Intelligence | `agents/document_intelligence.py` | pdfplumber text extraction, regex NER for financials (revenue, EBITDA, debt, net worth), GSTIN/PAN/CIN extraction, Sandbox.co.in GST fetch |
| Financial Analysis | `agents/financial_analysis.py` | 15 financial ratios (DSCR, D/E, current ratio, EBITDA margin, ROE, ROA, receivables days, inventory days, GST-ITR variance), 7 anomaly detection rules |
| Research Intelligence | `agents/research_intelligence.py` | Zaubacorp scraper (director data), eCourts API (litigation), Tavily search (NCLT/IBBI/news), news sentiment scoring |
| GSTR Reconciliation Engine | `engines/gst_reconciliation.py` | GSTR-2A vs GSTR-3B per-quarter reconciliation, ITC fraud detection (>10% variance = CRITICAL flag), output suppression check |
| Buyer Concentration Engine | `engines/buyer_concentration.py` | GSTR-1 B2B invoice aggregation by buyer GSTIN, single-buyer dependency (>40% = CRITICAL), top-3 concentration (>60% = HIGH) |
| Risk Assessment | `agents/risk_assessment.py` | Five-Cs scoring (Character 25%, Capacity 30%, Capital 20%, Collateral 15%, Conditions 10%), Logistic Regression default probability (12m/24m), Gemini LLM explanations per C |
| Due Diligence | `agents/due_diligence.py` | 18-item verification checklist, field visit report parsing, compliance status |
| Credit Decision | `agents/credit_decision.py` | RBI/NBFC policy rule checks, loan terms computation, covenants, monitoring triggers |
| CAM Generation | `agents/cam_generation.py` | 14-section HTML CAM report, Gemini LLM narrative (Section 11 only), DOCX export |

---

## 5. Five-Cs Scoring Model

| Dimension | Weight | Key Inputs | Thresholds |
|---|---|---|---|
| Character | 25% | Litigation count, promoter reputation, ITC fraud flag, NPA links | ITC fraud = -3 pts |
| Capacity | 30% | DSCR (≥1.5=10, ≥1.25=8, ≥1.0=6, <1.0=3), revenue CAGR, CFO | DSCR < 1.0 = critical |
| Capital | 20% | D/E ratio (<1.0=9, <2.0=7, <3.0=5, >3.0=3), net worth | D/E > 3.0 = penalty |
| Collateral | 15% | Loan-to-net-worth ratio | LTV > 1.0 = 2 pts |
| Conditions | 10% | Industry outlook, buyer concentration | >60% conc = -2 pts |

**Decision thresholds:** ≥75 = APPROVE | 60–74 = CONDITIONAL | 45–59 = CONDITIONAL | <45 = REJECT

**Default probability:** Pure-Python logistic regression (no sklearn). Features: DSCR, D/E, revenue CAGR, litigation count, industry score, buyer concentration %, ITC variance %, promoter reputation score.

---

## 6. Third-Party APIs Integrated

| API | Purpose | Key Used |
|---|---|---|
| **Sandbox.co.in** | GSTN-authorized: GSTR-1, GSTR-2A, GSTR-3B, GSTIN verification | `SANDBOX_API_KEY` + `SANDBOX_SECRET_KEY` |
| **Google Gemini 2.0 Flash** | LLM for Five-Cs explanations, CAM narrative, news sentiment | `GEMINI_API_KEY` |
| **Tavily** | Web search: NCLT/IBBI cases, news sentiment, NPA mentions | `TAVILY_API_KEY` |
| **Zaubacorp** | Free public scraper: director names, DINs, company status | No key needed |
| **eCourts API** | Litigation search by party name | No key needed |
| **Ollama** | Local LLM fallback (Mistral) when Gemini unavailable | Local only |

---

## 7. Database Schema (SQLite — 13 tables)

| Table | Key Columns |
|---|---|
| `companies` | id, cin, name, pan, gstin, sector |
| `applications` | id, company_id, loan_amount_requested, purpose, status |
| `financials` | id, application_id, year, revenue, ebitda, net_profit, total_debt, net_worth, cash_from_operations, total_assets, current_assets, current_liabilities |
| `ratios` | id, application_id, year, current_ratio, quick_ratio, de_ratio, dscr, ebitda_margin, net_profit_margin, roe, roa, receivables_days, inventory_days, gst_itr_variance |
| `risk_scores` | id, application_id, character, capacity, capital, collateral, conditions, final_score, risk_category, decision, default_probability_12m, default_probability_24m, top_drivers (JSON), explanations |
| `risk_flags` | id, application_id, flag_type, severity (CRITICAL/HIGH/MEDIUM/LOW), description, detected_by_agent, resolved |
| `research_data` | id, application_id, promoter_reputation, litigation_count, industry_outlook, news_sentiment_score, litigation_cases (JSON), news_articles (JSON), directorship_history (JSON) |
| `dd_notes` | id, application_id, officer_text, ai_signals_json, risk_delta |
| `documents` | id, application_id, file_path, original_filename, doc_type, ocr_status, extraction_status |
| `cam_reports` | id, application_id, pdf_path, docx_path, recommendation, loan_amount_approved, interest_rate, tenor_months, counterfactuals (JSON) |
| `agent_logs` | id, application_id, agent_name, status, output_summary, error_message, duration_ms |
| `field_provenance` | id, application_id, field_name, field_value, source_document, page_number, extraction_method, confidence_score |
| `buyer_concentration` | id, application_id, buyer_gstin, buyer_name, invoice_total, pct_of_revenue, concentration_risk_flag |

---

## 8. REST API Endpoints

**Base URL:** `http://localhost:8000`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/applications` | Create application |
| `GET` | `/api/applications` | List all applications |
| `GET` | `/api/applications/{id}` | Get application summary |
| `POST` | `/api/applications/{id}/documents` | Upload document |
| `POST` | `/api/applications/{id}/pipeline/start` | Trigger 7-agent pipeline |
| `GET` | `/api/applications/{id}/pipeline/status` | Live agent progress (reads from `pipeline_state/{id}.json`) |
| `GET` | `/api/applications/{id}/risk` | Five-Cs, GSTR, buyers, ratios, flags |
| `GET` | `/api/applications/{id}/financials` | P&L, Balance Sheet, Cash Flow, 17 ratios |
| `GET` | `/api/applications/{id}/promoter` | Directors, litigation, news, network graph |
| `GET` | `/api/applications/{id}/bank-analytics` | ABB, bounce ratio, monthly cash flow, red flags |
| `GET` | `/api/applications/{id}/diligence` | 18-item checklist, field visit, compliance |
| `GET` | `/api/applications/{id}/cam` | Full 14-section CAM JSON |
| `GET` | `/api/applications/{id}/cam/download` | Download HTML/DOCX |
| `GET` | `/api/applications/{id}/audit` | Full audit trail with timestamps |
| `POST` | `/api/applications/{id}/dd-notes` | Submit DD observations → live score update |
| `POST` | `/api/applications/{id}/chat` | AI chat with application context |
| `GET` | `/api/applications/{id}/counterfactuals` | Path-to-approval steps |
| `WS` | `/ws/applications/{id}` | Real-time agent events |
| `GET` | `/health` | Service health + all endpoint list |

---

## 9. Frontend Pages

| Page | Route | Data Source |
|---|---|---|
| Document Upload | `/upload` | User input → `POST /api/applications` + `POST /documents` |
| Agent Progress | `/agents` | `GET /pipeline/status` (500ms poll) + WebSocket |
| Risk Analytics | `/risk` | `GET /risk` — Five-Cs radar, GSTR waterfall, buyer donut, ratio cards |
| Financial Spreads | `/spreads` | `GET /financials` — P&L, BS, CF, 17 ratio cards |
| Bank Analytics | `/bank-analytics` | `GET /bank-analytics` — ABB, cash flow charts, red flags |
| Promoter Intel | `/promoter` | `GET /promoter` — D3 network graph, litigation timeline, news feed |
| Due Diligence | `/diligence` | `GET /diligence` — checklist, field visit |
| CAM Report | `/report` | `GET /cam` + `GET /risk` — 14 sections, counterfactual simulator, PDF export |
| Audit Trail | `/audit` | `GET /audit` — event timeline, overrides, compliance badges |
| Dashboard | `/` | Aggregates `/risk` + `/cam` |

---

## 10. CAM Report — 14 Sections

1. Borrower Profile & Company Information
2. Existing & Proposed Banking Facilities
3. Promoter & Management Intelligence
4. Financial Analysis — 3-Year Spreads (P&L, BS, CF, Ratios)
5. Working Capital Assessment (NWC, MPBF — Nayak Committee)
6. Bank Statement Analysis — 12 Months
7. GST & Tax Compliance (GSTR-2A vs GSTR-3B)
8. Risk Assessment — Five-Cs (scores, flags, buyer concentration)
9. Due Diligence Summary (checklist, field visit, regulatory)
10. Sensitivity / Stress Analysis (4 scenarios)
11. Credit Assessment Narrative (**Gemini LLM — only section using LLM**)
12. Recommendation & Decision
13. Proposed Loan Terms + Counterfactuals
14. Disclaimer & Authorization (3 signature blocks)

PDF generated client-side via **jsPDF** (browser). HTML version saved server-side.

---

## 11. Innovation Highlights

### GSTR-2A vs GSTR-3B Reconciliation ⭐
No Indian credit tool does this. GSTR-2A = auto-populated from supplier filings. GSTR-3B = self-declared. Variance > 10% = `ITC_FRAUD_SUSPECTED` (CRITICAL). Catches ₹Cr-scale ITC overclaims.

### Buyer Concentration from GSTR-1 ⭐
Even Perfios can't compute this — requires GST invoice-level counterparty data. Single buyer > 40% = CRITICAL. Top-3 > 60% = HIGH.

### Counterfactual Explainability ⭐
For rejected applications: "Resolve ₹12.9Cr ITC discrepancy → Reduce D/E from 3.4 to <2.0 → Diversify buyer base from 71% to <40%". Interactive simulator in the CAM Report page.

### Chain of Evidence
Every extracted figure links to: source document, page number, extraction method (regex/FinBERT), confidence score. Stored in `field_provenance` table.

### Logistic Regression Scorecard
RBI-preferred interpretable model. Not XGBoost (black box). Features: DSCR, D/E, revenue CAGR, litigation count, industry score, buyer concentration, ITC variance, promoter reputation. Outputs default probability at 12m and 24m.

---

## 12. Pipeline Execution Flow

1. User uploads annual report PDF → stored to `local_uploads/`
2. `POST /pipeline/start` → spawns daemon thread with own event loop
3. Thread writes progress to `pipeline_state/{app_id}.json` (survives reloads)
4. Frontend polls `/pipeline/status` every 500ms → reads JSON file
5. Agent 1 runs pdfplumber + regex on PDF → writes to `financials` DB table
6. Agents 2-5 run in parallel → write to `ratios`, `research_data`, Redis sessions
7. Agent 4 (Risk) runs Five-Cs math + Gemini LLM → writes to `risk_scores` DB
8. Agent 7 (CAM) builds 14-section HTML → saves to `cam_reports/` folder
9. `COMPLETE` event published → frontend stops polling, shows results

---

## 13. Running Locally

```bash
# Backend
cd intelli-credit-ai-app/backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd intelli-credit-ai-app/frontend
npm install
npm run dev
```

**Required `.env` keys:**
```
DATABASE_URL=sqlite+aiosqlite:///./intellicredit.db
SYNC_DATABASE_URL=sqlite:///./intellicredit.db
GEMINI_API_KEY=your_key
SANDBOX_API_KEY=your_key
SANDBOX_SECRET_KEY=your_key
TAVILY_API_KEY=your_key
```

**Test document:** `backend/test_documents/Annual_Report_Sunrise_Exports_FY2024.pdf`  
Generated via: `python generate_test_annual_report.py`

---

## 14. Key Numbers

| Metric | Value |
|---|---|
| Pipeline runtime | ~25–40 seconds (real agents) |
| Manual equivalent | 3–6 weeks |
| Cost saving | ₹80,000 per appraisal |
| DB tables | 13 |
| REST endpoints | 23 |
| Frontend pages | 10 |
| AI agents | 7 |
| Engines | 2 (GSTR Recon + Buyer Concentration) |
| CAM sections | 14 |
| Financial ratios computed | 15 |
| Anomaly detection rules | 7 |
| Five-Cs dimensions | 5 |
