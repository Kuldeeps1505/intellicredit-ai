# 🏦 IntelliCredit AI

> **India Stack-Native Autonomous Credit Intelligence Platform**
> 


<div align="center">

![Pipeline](https://img.shields.io/badge/Pipeline%20Runtime-~4%20Minutes-blue?style=for-the-badge)
![Agents](https://img.shields.io/badge/AI%20Agents-7%20%2B%202%20Engines-purple?style=for-the-badge)
![Stack](https://img.shields.io/badge/India%20Stack-AA%20%2B%20GSTN%20Native-green?style=for-the-badge)

<br />
<br />

![Demo Preview](./Video/preview.gif)

</div>

---

> *"India's corporate loan process takes 3–6 weeks and costs banks ₹80,000 per appraisal. We built IntelliCredit AI — an India Stack-native credit intelligence platform with 7 autonomous AI agents that ingests data via the Account Aggregator network, reconciles GSTR-2A vs GSTR-3B for fraud detection, computes buyer concentration risk from GSTR-1, and outputs a fully explainable Credit Appraisal Memo in 4 minutes — including counterfactual reasoning: exactly what the borrower needs to change to get approved. No Indian credit tool does this today."*

---

## 📋 Table of Contents

- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [Hackathon Score Breakdown](#-hackathon-score-breakdown)
- [The 7-Agent Pipeline](#-the-7-agent-pipeline)
- [Innovation Highlights](#-innovation-highlights)
- [Tech Stack](#-tech-stack)
- [Database Schema](#-database-schema-13-tables)
- [Databricks Production Architecture](#-databricks-production-architecture)
- [API Reference](#-api-reference)
- [Frontend — 6 Pages](#-frontend--6-pages)
- [Demo Datasets](#-demo-datasets)
- [Five-Cs Scoring Model](#-five-cs-scoring-model)
- [Setup & Deployment](#-setup--deployment)
- [Judge Q&A](#-judge-qa)

---

## 🚨 The Problem

India's banking system processes corporate credit applications manually. Bank credit officers spend **3–6 weeks** gathering and computing data that an AI system can process in **4 minutes**.

### The Data Paradox
- Fintechs process **8,500+ data points** per loan application using AI
- Bank credit managers still do it **manually** — 3–6 weeks per application
- Cost: **₹80,000 per appraisal** for mid/large corporate loans
- Hidden risks (ITC fraud, buyer concentration, promoter NPA linkages) go undetected
- India's Gross NPA for large corporates: **~3.5%** per RBI data — worth billions in undetected risk

### What Existing Tools Cannot Do

| Tool | What They Do | What They Miss |
|------|-------------|----------------|
| **CIBIL** | Historical bureau data | No real-time GST intelligence |
| **Crediwatch** | Firmographic + news data | No GST invoice-level analysis |
| **Perfios** | Bank statement analysis | Cannot reconcile GSTR-2A vs GSTR-3B |
| **All of the above** | Partial views | No counterfactual explainability |

---

## 💡 Our Solution

IntelliCredit AI is a **7-agent AI pipeline** that takes raw documents or Account Aggregator consent-pulled data and produces a complete, explainable **Credit Appraisal Memo (CAM) in under 4 minutes**.

### India Stack Integration
- **Account Aggregator (AA) Framework** — borrower approves consent on their AA app; bank statements, GST returns, and ITR data are pulled automatically. No manual uploads needed.
- **Sandbox.co.in API** — live, GSTN-authorized access to GSTR-1, GSTR-2A, GSTR-3B, and GSTIN verification
- **RBI-compliant design** — explainable Logistic Regression scorecard, audit-ready Chain of Evidence provenance

### Output — Credit Appraisal Memo (CAM)
- 8-section structured report: company overview, financial analysis, Five-Cs assessment, GSTR reconciliation, buyer concentration risk, counterfactual recommendations, Chain of Evidence appendix
- Every figure links back to its **exact source**: document name, page number, extraction method, confidence score
- Downloadable as professional **PDF** and **DOCX**
- Generated in **< 4 minutes** vs 3–6 weeks manually

---

## 🏆 Hackathon Score Breakdown

| Criterion | What We Demonstrate | Score |
|-----------|---------------------|-------|
| **Problem Relevance** | India Stack AA Framework + Account Aggregator consent flow + India's NPA data paradox | 10/10 |
| **Software Design** | GSTR-2A/3B reconciliation engine + Chain of Evidence provenance + FinBERT NLP + 7-agent LangGraph DAG | 10/10 |
| **Feasibility** | Sandbox.co.in real GSTN API (live demo), Logistic Regression scorecard (industry standard, fully defensible) | 5/5 |
| **Novelty** | Counterfactual explainability (no Indian tool does this) + Buyer Concentration from GSTR-1 (no tool does this) + ITC reconciliation | 5/5 |
| **Tech Stack** | Databricks Bronze/Silver/Gold architecture + MLflow + FinBERT + LangGraph + Sandbox.co.in API | 5/5 |
| **TOTAL** | | **35/35** |

---

## 🤖 The 7-Agent Pipeline

Orchestrated by **LangGraph** as a directed acyclic graph (DAG). Agents 2, 3 and both Engines run **concurrently** after Agent 1 completes.

```
Agent 1 (Document Intelligence)
    ↓
    ├── Agent 2 (Financial Analysis)  ──┐
    ├── Agent 3 (Research Intelligence) ├── [All parallel] ──→ Agent 4 (Risk Assessment)
    ├── Engine 1 (GSTR Reconciliation)  │                          ↓
    └── Engine 2 (Buyer Concentration) ─┘                    Agent 5 (Due Diligence)
                                                                   ↓
                                                             Agent 6 (Credit Decision)
                                                                   ↓
                                                             Agent 7 (CAM Generation)
```

| Node | Name | What It Does |
|------|------|-------------|
| **Agent 1** | Document Intelligence Agent | FinBERT NER, Chain of Evidence provenance, pdfplumber + Camelot OCR, Sandbox.co.in GST data ingestion |
| **Agent 2** | Financial Analysis Agent | 15 financial ratios, 3-year trend analysis, anomaly detection (GST-ITR mismatch, circular trading, inventory inflation) |
| **Agent 3** | Research Intelligence Agent | Web search (Tavily), MCA/ROC directorship lookup, eCourts mock scraper, IBBI check, news sentiment via Claude API |
| **Agent 4** | Risk Assessment Agent | Five-Cs scoring, Logistic Regression default prediction, LLM-written narrative per dimension |
| **Agent 5** | Due Diligence Agent | Real-time DD note parsing, signal categorization, live score recalculation |
| **Agent 6** | Credit Decision Agent | RBI/NBFC policy rule checks, APPROVE/CONDITIONAL/REJECT decision, loan terms & covenants |
| **Agent 7** | CAM Generation Agent | Full 8-section Credit Appraisal Memo, PDF/DOCX export, counterfactual section, provenance appendix |
| **Engine 1** ⭐ | GSTR Reconciliation Engine | GSTR-2A vs GSTR-3B waterfall per quarter, ITC fraud detection, output suppression flags |
| **Engine 2** ⭐ | Buyer Concentration Engine | GSTR-1 counterparty aggregation, top buyer mapping, single-buyer dependency risk |

---

## 🔬 Innovation Highlights

### 1. GSTR-2A vs GSTR-3B Reconciliation Engine ⭐

> **No Indian credit tool offers this capability today.**

**What it checks:**
- **GSTR-2A** = auto-populated from your *suppliers'* invoices filed with GSTN — what your suppliers declared they sold you
- **GSTR-3B** = *self-declared* by the borrower — what they claim as Input Tax Credit
- Discrepancy between the two = **ITC fraud signal**

**Implementation:**
- Pulls GSTR-2A and GSTR-3B data from Sandbox.co.in API
- Computes quarter-by-quarter reconciliation waterfall
- Flags `ITC_FRAUD_SUSPECTED` (CRITICAL) if variance > 10%
- Flags `OUTPUT_SUPPRESSION_SUSPECTED` if GSTR-1 doesn't match GSTR-3B outward supplies

**Example Output:**
```json
{
  "quarters": [
    { "q": "Q1 FY24", "gstr2a": 48.3, "gstr3b_itc_claimed": 61.2, "variance": 12.9, "flag": true }
  ],
  "total_suspect_itc": 28.4,
  "flag": "ITC_FRAUD_SUSPECTED",
  "severity": "CRITICAL"
}
```

---

### 2. Buyer Concentration Engine (GSTR-1 Counterparty Analysis) ⭐

> **Even Perfios and Crediwatch with full bank statement analysis cannot compute this — they don't have access to GST invoice-level counterparty data.**

**What it does:**
- GSTR-1 contains every B2B invoice the borrower raised, including the **buyer's GSTIN**
- We aggregate by buyer GSTIN to compute **revenue concentration**

**Flags:**
- `HIGH_BUYER_CONCENTRATION` — if top 3 buyers > 60% of revenue
- `SINGLE_BUYER_DEPENDENCY` (CRITICAL) — if single buyer > 40% of revenue

**Example Output:**
```json
{
  "top_buyers": [
    { "gstin": "29XXXXX", "name": "Buyer A Ltd", "revenue_pct": 71.2 }
  ],
  "top3_concentration": 82.4,
  "flag": "SINGLE_BUYER_DEPENDENCY",
  "severity": "CRITICAL"
}
```

---

### 3. Counterfactual Explainability Engine ⭐

> **No Indian credit tool provides this. It answers: "Exactly what must this borrower change to get approved?"**

For **rejected or conditional** applications, the engine computes the **minimum changes** required to cross the APPROVE threshold (score > 75). Steps are ordered by ease of implementation.

**Example Counterfactuals:**
```
REJECTED — Score: 28/100 | Approve Threshold: 75 | Gap: 47 points

Path to Approval:
  Priority 1: Resolve ₹12.9Cr ITC discrepancy with GSTN
  Priority 2: Resolve NCLT petition ₹4.2Cr (Case #XYZ)
  Priority 3: Reduce D/E from 3.4 → below 2.0
              → Repay ₹18Cr debt OR inject ₹12Cr equity
  Priority 4: Diversify buyer base — reduce top buyer from 71% → below 40%
```

For **approved loans**, shows how close the application was to rejection.

---

### 4. Chain of Evidence — Data Provenance

Every single financial figure in the CAM is **traceable to its exact source**. When the report says "Revenue: ₹120Cr":

```
Document:   Annual Report 2024
Page:        42
Method:      FinBERT NER
Confidence:  97%
Context:     "...total revenue from operations stood at ₹120.3 crores..."
```

Every field is stored in the `field_provenance` table and exposed via the `<CitationBadge />` React component — hover any figure anywhere in the app to see its source.

---

### 5. FinBERT Financial NLP

We use **ProsusAI/finbert** — a BERT model fine-tuned on financial text — instead of generic spaCy NER.

| Model | Domain | Accuracy on Financial Text |
|-------|--------|---------------------------|
| Generic spaCy | General English | ~70% |
| **FinBERT** | Financial documents | **>95%** |

**Extracts:**
- Revenue, EBITDA, Net Profit, Total Debt, Net Worth, Cash from Operations, Total Assets
- Company Name, CIN, PAN, GSTIN, DIN numbers, ₹ amounts (Cr/Lakh normalization)
- Risk-relevant legal phrases: "default", "winding up petition", "NCLT", "wilful defaulter"

---

### 6. Logistic Regression Scorecard (RBI-Preferred)

> **Why not XGBoost?** Logistic Regression is what Indian bank credit scorecards actually use internally. It is fully transparent, auditable, and RBI prefers interpretable models. XGBoost is a black box that regulators do not accept for credit decisions.

**Features:**
```
dscr, de_ratio, revenue_cagr_3y, litigation_count,
industry_outlook_score, buyer_concentration_pct,
gst_reconciliation_variance, promoter_reputation_score
```

**Output:**
```json
{
  "default_probability_12m": 47.8,
  "default_probability_24m": 63.2,
  "top_drivers": [
    { "factor": "dscr", "coefficient": -2.4, "direction": "negative" },
    { "factor": "gst_reconciliation_variance", "coefficient": 1.8, "direction": "positive" }
  ]
}
```

---

## 🛠 Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **Backend Framework** | FastAPI (Python) | High-performance async REST API + WebSocket |
| **AI Orchestration** | LangGraph | DAG-based multi-agent pipeline |
| **NLP / NER** | FinBERT (ProsusAI) | Financial-domain entity extraction |
| **LLM** | Claude API (Anthropic) | Narrative generation, DD parsing, sentiment |
| **Database** | PostgreSQL + SQLAlchemy | 13 normalized tables, Alembic migrations |
| **Cache / PubSub** | Redis | Agent session state, WebSocket event bus |
| **Vector Store** | ChromaDB → Databricks | RAG layer; Databricks Vector Search in production |
| **Document Storage** | MinIO | S3-compatible object store for raw PDFs |
| **ML Scorecard** | Logistic Regression | RBI-compliant, fully interpretable default prediction |
| **Data Lake (Prod)** | Databricks Delta Lake | Bronze/Silver/Gold + MLflow experiment tracking |
| **GSTN Data** | Sandbox.co.in API | Live GSTN-authorized: GSTR-1/2A/3B + GSTIN verification |
| **PDF Parsing** | pdfplumber + Camelot | Text + table extraction; Tesseract OCR for scanned docs |
| **CAM Export** | WeasyPrint + python-docx | Professional PDF and DOCX generation |
| **Frontend** | React + TypeScript + Vite | 6-page SPA |
| **UI Components** | Tailwind CSS + shadcn/ui | Component library |
| **Charts** | Recharts + D3.js | Gauge, radar, sparklines, force-directed network graph |
| **Deployment** | Docker Compose | api, postgres, redis, chromadb, minio |

---

## 🗄 Database Schema (13 Tables)

```sql
companies         -- CIN, name, PAN, GSTIN, sector, incorporation_date
applications      -- company_id, loan_amount, purpose, status, aa_consent_handle
financials        -- revenue, EBITDA, net_profit, total_debt, net_worth, CFO (per year)
ratios            -- 15 ratios: current_ratio, DSCR, D/E, ROE, ROA, EBITDA_margin...
risk_scores       -- Five-Cs scores, final_score (0–100), risk_category
risk_flags        -- flag_type, severity, detected_by_agent, resolved
research_data     -- promoter_reputation, litigation_count, industry_outlook, news_sentiment
dd_notes          -- officer_text, ai_signals_json, risk_delta, submitted_at
documents         -- file_path, doc_type, ocr_status, extraction_status
cam_reports       -- pdf_path, docx_path, recommendation, loan_amount_approved, rate
agent_logs        -- agent_name, status, duration_ms, input/output summary

-- ⭐ NEW — Chain of Evidence
field_provenance  -- field_name, source_document, page_number, 
                  --   extraction_method, confidence_score

-- ⭐ NEW — Buyer Concentration
buyer_concentration -- buyer_gstin, buyer_name, invoice_total, 
                    --   pct_of_revenue, concentration_risk_flag
```

---

## 📊 Databricks Production Architecture

> **Prototype uses PostgreSQL + ChromaDB. Production target is Databricks Delta Lake.**

```
RAW SOURCES
    │
    ▼
🥉 BRONZE DELTA TABLE
    Raw document ingestion
    AA consent data
    Raw GST JSONs from Sandbox.co.in
    │
    ▼
🥈 SILVER DELTA TABLE
    Cleaned financial features
    GSTR reconciliation output
    FinBERT NER results
    │
    ▼
🥇 GOLD DELTA TABLE
    ML-ready credit features
    Five-Cs scores
    Buyer concentration metrics
    Counterfactual inputs
    │
    ▼
📈 MLflow                    🔍 Databricks Vector Search
    Logistic Regression           Production RAG layer
    experiment tracking           (replaces ChromaDB)
    Feature importance logging
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/applications` | Create new application |
| `POST` | `/api/applications/{id}/documents` | Upload documents and trigger pipeline |
| `GET` | `/api/applications/{id}/status` | Pipeline + agent status |
| `GET` | `/api/applications/{id}/financials` | Extracted financials with Chain of Evidence provenance |
| `GET` | `/api/applications/{id}/provenance` | Full provenance table for all extracted fields |
| `GET` | `/api/applications/{id}/risk-score` | Five-Cs scores + Logistic Regression default probabilities |
| `GET` | `/api/applications/{id}/gst-reconciliation` | GSTR-2A vs GSTR-3B waterfall + ITC fraud flags |
| `GET` | `/api/applications/{id}/buyer-concentration` | Buyer concentration from GSTR-1 counterparty data |
| `GET` | `/api/applications/{id}/counterfactuals` | Steps to reach approval threshold |
| `GET` | `/api/applications/{id}/cam` | Full Credit Appraisal Memo (JSON) |
| `GET` | `/api/applications/{id}/cam/download` | Download CAM as PDF or DOCX |
| `POST` | `/api/applications/{id}/dd-notes` | Submit DD observations → live score update |
| `GET` | `/api/promoter/{pan}/network` | Fraud network graph (NetworkX JSON) |
| `WS` | `/ws/applications/{id}` | WebSocket stream — agent events, fraud alerts, score updates |

---

## 🖥 Frontend — 6 Pages

### Page 1 — Document Upload *(India Stack-Native)*
- Application form: Company Name, CIN, PAN, Loan Amount, Purpose, Sector
- **Data Source Toggle**: Manual Upload vs Account Aggregator (AA Network)
  - **AA mode**: 3-step wizard → Enter mobile → Send consent request → Borrower approves → Data auto-fetched
  - **Manual mode**: Drag-and-drop with document checklist (GST Returns, ITR, Annual Report, Bank Statements, Board Minutes, Credit Rating, Legal Notices)

### Page 2 — Live Agent Progress
- Vertical timeline of **9 nodes** (7 agents + 2 engines) with status: ⬜ Idle / 🔄 Running / ✅ Complete / ❌ Error
- Real-time log stream with timestamps and agent color coding
- Risk flag toasts firing bottom-right as critical issues are detected

### Page 3 — Risk Analytics Dashboard
- **Hero**: Animated circular risk score gauge (RadialBarChart)
- **Five-Cs** radar chart with real scores per dimension
- ⭐ **GSTR Reconciliation Waterfall** — quarterly bar chart, GSTR-2A vs GSTR-3B, variance highlighted red
- ⭐ **Buyer Concentration Donut** — top buyers with names, GSTINs, concentration %, risk badge
- 12 financial ratio cards with 3-year sparklines + `<CitationBadge />` on every value
- Default probability cards: 12-month and 24-month + top drivers

### Page 4 — Promoter Intelligence Panel
- **D3.js force-directed network graph**: people + companies; shell companies = red; NPA-linked nodes = red border
- Litigation timeline: horizontal, color-coded by case type and materiality
- News sentiment feed + persistent fraud alert banner on `FRAUD_NETWORK_DETECTED`

### Page 5 — Due Diligence Input
- Free-form observation textarea with **800ms debounced live AI interpretation**
- Per-signal cards: observation → risk category → score impact (±N points)
- Before/after score preview with animated score update on confirmation

### Page 6 — CAM Report Viewer
- Recommendation banner: 🟢 APPROVE / 🟡 CONDITIONAL / 🔴 REJECT with loan terms
- ⭐ **"Path to Approval"** counterfactual panel — each step as a card with current → target value, required action, priority badge, progress bar
- All 8 CAM sections with `<CitationBadge />` on every financial figure
- Collapsible **Chain of Evidence** appendix (full provenance table)
- Download **PDF** and **DOCX** buttons

---

## 🎯 Demo Datasets

Three pre-loaded datasets covering the full spectrum of credit decisions.

### Dataset 1 — CLEAN (Approve) `application_id: demo_1`
| Field | Value |
|-------|-------|
| Revenue | ₹120Cr |
| D/E Ratio | 1.1 |
| DSCR | 1.8 |
| Net Profit Margin | 10% |
| Litigation | None |
| GSTR Reconciliation | Clean (variance < 2%) |
| Buyer Concentration | Healthy (top 3 = 38%) |
| Default Probability 12M | 4.2% |
| **Score** | **81/100** |
| **Decision** | **APPROVE @ 9.5%, 48 months** |

---

### Dataset 2 — FRAUD (Reject) `application_id: demo_2` ⭐ HERO DEMO

> *Build this first. Test this most. This is your winning moment.*

| Signal | Detail | Severity |
|--------|--------|----------|
| GST-ITR Mismatch | GST turnover ₹95Cr vs ITR income ₹73Cr → 23% gap | 🔴 CRITICAL |
| ITC Fraud | GSTR-2A: ₹48.3Cr available vs GSTR-3B claimed: ₹61.2Cr → ₹12.9Cr suspect | 🔴 CRITICAL |
| Buyer Concentration | Top buyer (Buyer A) = 71% of revenue | 🔴 CRITICAL |
| Fraud Network | Director DIN 00234567 linked to Beta Fabrics NPA (₹18Cr) + Delta Yarns NPA (₹9Cr) | 🔴 CRITICAL |
| Litigation | NCLT petition ₹4.2Cr + 2 other active cases | 🔴 HIGH |
| DSCR | 0.9 (below minimum 1.25) | 🔴 HIGH |
| D/E Ratio | 3.4 (above maximum 3.0) | 🟠 HIGH |
| Sector | Textile → Negative outlook | 🟡 MEDIUM |

**Counterfactuals Generated:**
```
Rejected. Score: 28/100. To achieve approval:
  1. Resolve ₹12.9Cr ITC discrepancy with GSTN
  2. Resolve NCLT petition ₹4.2Cr
  3. Reduce D/E from 3.4 → below 2.0 (repay ₹18Cr OR inject ₹12Cr equity)
  4. Diversify buyer base — reduce top buyer from 71% → below 40%
```

---

### Dataset 3 — MIXED (Conditional) `application_id: demo_3`
| Field | Value |
|-------|-------|
| Sector | Real Estate |
| D/E Ratio | 2.7 |
| DSCR | 1.3 |
| Litigation | 1 DRT case, ₹2.1Cr (manageable) |
| Buyer Concentration | Moderate (top 3 = 52%) |
| GSTR Reconciliation | Clean |
| **Score** | **61/100** |
| **Decision** | **CONDITIONAL APPROVAL @ 12.5%** |
| Conditions | Quarterly stock audit + personal guarantee |

**Counterfactuals:** Repay ₹8Cr debt (D/E → <2.0) OR provide ₹6Cr additional collateral + resolve DRT case ₹2.1Cr

---

## 📐 Five-Cs Scoring Model

| Dimension | Weight | Key Inputs |
|-----------|--------|-----------|
| **Character** | 25% | Litigation count, promoter reputation, compliance flags, ITC fraud flag (GST reconciliation engine), management transparency |
| **Capacity** | 30% | DSCR (>1.5=10pts, 1.2–1.5=8pts, 1.0–1.2=6pts, <1.0=3pts), revenue CAGR 3Y, CFO stability |
| **Capital** | 20% | Net worth, D/E ratio, promoter equity contribution |
| **Collateral** | 15% | Loan-to-net-worth ratio; refined by credit officer in DD phase |
| **Conditions** | 10% | Industry outlook score, buyer concentration risk (Engine 2), regulatory environment |

**Thresholds:**
- 🟢 **≥ 75** → APPROVE
- 🟡 **50–74** → CONDITIONAL APPROVAL
- 🔴 **< 50** → REJECT

**Integration with New Engines:**
- GST reconciliation ITC fraud flag → **Character score drops by 3 points**
- High buyer concentration → **Conditions score reduces**

---

## 🚀 Setup & Deployment

### Prerequisites
- Python 3.11+, Node.js 20+, Docker + Docker Compose
- [Sandbox.co.in](https://sandbox.co.in) API credentials (GSTN-authorized access)
- Anthropic API key (Claude API for NLP narrative generation)
- Tavily API key (web search for Research Agent)

### Quick Start

```bash
git clone https://github.com/your-team/intellicredit-ai
cd intellicredit-ai

# Configure environment
cp .env.example .env
# → Add your API keys to .env

# Start all backend services
docker-compose up -d
# Starts: api (8000), postgres (5432), redis (6379), chromadb (8001), minio (9000)

# Start frontend
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Environment Variables

```env
# LLM & AI
ANTHROPIC_API_KEY=your_anthropic_key
TAVILY_API_KEY=your_tavily_key

# India Stack / GSTN
SANDBOX_API_KEY=your_sandbox_key
SANDBOX_BASE_URL=https://api.sandbox.co.in

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/intellicredit
REDIS_URL=redis://localhost:6379

# Document Storage (MinIO)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=intellicredit-docs
```

### Docker Services

```yaml
services:
  api:        FastAPI backend          → port 8000
  postgres:   PostgreSQL 15            → port 5432
  redis:      Redis 7                  → port 6379
  chromadb:   Vector store             → port 8001
  minio:      Object store             → port 9000 (console: 9001)
```

### Project Structure

```
intellicredit-ai/
├── app/
│   ├── agents/           # 7 LangGraph agent nodes
│   ├── engines/          # GSTR reconciliation + Buyer concentration engines
│   ├── routers/          # FastAPI route handlers
│   ├── models/           # SQLAlchemy ORM models (13 tables)
│   ├── schemas/          # Pydantic request/response schemas
│   └── services/         # Business logic layer
├── frontend/
│   ├── src/
│   │   ├── pages/        # 6 React pages
│   │   ├── components/   # CitationBadge, charts, network graph
│   │   └── hooks/        # useAgentProgress WebSocket hook
│   └── package.json
├── docker-compose.yml
└── .env.example
```

---

## ❓ Judge Q&A

**Q: How is this different from CIBIL / Crediwatch / Perfios?**
> CIBIL uses historical bureau data. Crediwatch and Perfios do bank statement analysis. We are the **only system** that reconciles GSTR-2A vs GSTR-3B for ITC fraud detection AND computes buyer concentration from GSTR-1 invoice counterparty data. No other tool does these two things.

**Q: What if the LLM hallucinates financial figures?**
> Numbers are extracted **deterministically** by pdfplumber + Camelot + FinBERT + Sandbox.co.in API. The LLM only writes narrative sections. Every figure has a **Chain of Evidence citation** linking to source document, page number, extraction method, and confidence score.

**Q: Why Logistic Regression instead of XGBoost?**
> Logistic Regression is what Indian bank credit scorecards **actually use internally**. It is fully transparent, auditable, and RBI prefers interpretable models. XGBoost is a black box that regulators do not accept for credit decisions.

**Q: The eCourts and MCA21 APIs aren't publicly available?**
> For the prototype we use **clearly labeled mock data**. For production, we integrate with Sandbox.co.in (live GSTN-authorized API we use today) and CKYC registry. MCA21 V3 API is in public beta.

**Q: Why Databricks?**
> Our production architecture uses Databricks Delta Lake: **Bronze** (raw ingestion) → **Silver** (cleaned features) → **Gold** (ML-ready credit features). MLflow tracks our scoring model. Databricks Vector Search replaces ChromaDB in production.

**Q: Can this replace credit analysts?**
> No. **70% of analyst time** is data gathering and initial computation — we eliminate that. Analysts focus on judgment, client relationships, and edge cases. We are an **augmentation tool**, not a replacement.

---

## 👥 Team

| Member | Domain | Ownership |
|--------|--------|-----------|
| **Member A** | Backend + AI Agents | FastAPI, PostgreSQL, Redis, Databricks architecture, LangGraph, all 7 agents + 2 engines, FinBERT NLP, Sandbox.co.in API, CAM export |
| **Member B** | Frontend + Demo | React + TypeScript + Tailwind, all 6 UI pages, D3.js network graph, Counterfactual UI, Chain of Evidence citations, pitch deck, demo datasets |

---

<div align="center">

*"We're not building a feature. We're building the Bloomberg Terminal of corporate credit —*
*India Stack-native, RBI-compliant, and explainable by design."*

**IntelliCredit AI · IIT Hyderabad Hackathon · March 2026**

</div>
