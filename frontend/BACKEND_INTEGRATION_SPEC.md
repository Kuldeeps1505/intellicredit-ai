# IntelliCredit AI — Frontend Specification for Backend Integration

> **Purpose**: This document provides everything a backend engineer or AI code generator needs to build APIs that integrate seamlessly with the existing React frontend. All TypeScript interfaces, data shapes, routes, and functional requirements are documented below.

---

## 1. TECHNOLOGY STACK

| Layer | Tech |
|-------|------|
| Framework | React 18 + TypeScript |
| Routing | react-router-dom v6 (BrowserRouter) |
| State | React Context (DatasetContext, ThemeContext) |
| Data Fetching | @tanstack/react-query v5 (installed, not yet wired to APIs) |
| Styling | Tailwind CSS + shadcn/ui |
| Charts | Recharts |
| PDF Export | jspdf (client-side generation) |
| Animations | framer-motion |

---

## 2. APPLICATION ROUTES & PAGES

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/` | Dashboard | Executive summary — score, decision, financial health, risk flags, module status cards |
| `/upload` | DocumentUpload | Credit application form + document upload (manual or Account Aggregator) |
| `/agents` | AgentProgress | Real-time AI agent pipeline visualization with log stream |
| `/risk` | RiskAnalytics | Risk gauge, Five-Cs radar, GSTR reconciliation, buyer concentration, risk flags table |
| `/spreads` | FinancialSpreads | P&L, Balance Sheet, Cash Flow (3-year spreads) + 17 financial ratio cards |
| `/bank-analytics` | BankStatementAnalytics | Bank cash flow charts, ABB trend, credit/debit categories, red flags, counterparties |
| `/promoter` | PromoterIntel | Director profiles, entity network graph, litigation timeline, news sentiment |
| `/diligence` | DueDiligence | Verification checklist, field visit reports, compliance status |
| `/report` | CamReport | Credit Appraisal Memorandum — sections, recommendation, loan terms, counterfactual simulator, PDF export |
| `/audit` | AuditTrail | Decision timeline, approval workflow, human overrides, compliance badges |

---

## 3. CURRENT DATA FLOW (DEMO MODE — TO BE REPLACED)

Currently, ALL data is hardcoded in `src/lib/` files with 3 demo datasets selected via `DatasetContext`:

```typescript
type DatasetId = "approve" | "fraud" | "conditional";
```

**The context provides:**
```typescript
interface DatasetContextValue {
  activeDataset: DatasetId;       // → will become applicationId: string
  setActiveDataset: (id) => void; // → will become setApplicationId
  dataset: Dataset;               // → fetched from API
}
```

### What needs to change:
- Replace `DatasetId` with a dynamic `applicationId: string`
- Each `getXxxData(datasetId)` function → API call via react-query
- The `DatasetContext` should fetch the base `Dataset` from API on applicationId change

---

## 4. ALL DATA INTERFACES (TypeScript — exact shapes the frontend consumes)

### 4.1 Base Application / Company Info

```typescript
// File: src/lib/demoData.ts
interface Dataset {
  id: string;              // application ID
  label: string;           // display label
  emoji: string;           // status emoji (optional)
  score: number;           // overall risk score 0-100
  companyName: string;     // "Reliance Textiles Pvt Ltd"
  cin: string;             // "U17291MH2019PTC123456"
  pan: string;             // "AABCR1234F"
  gstin: string;           // "27AABCR1234F1Z5"
  loanAmount: string;      // "45,00,00,000" (formatted INR)
  purpose: string;         // "Working Capital"
  sector: string;          // "Textiles & Apparel"
}
```

**API Endpoint needed**: `GET /api/applications/:id` → returns `Dataset`
**List endpoint**: `GET /api/applications` → returns `Dataset[]`

---

### 4.2 Document Upload

```typescript
// Frontend form fields submitted:
interface CreditApplication {
  companyName: string;
  cin: string;
  pan: string;
  gstin: string;
  loanAmount: string;
  purpose: string;
  sector: string;
}

// Document types expected:
type RequiredDocument =
  | "Annual Report (3 years)"
  | "Bank Statements (12 months)"
  | "GST Returns (GSTR-1, 2A, 3B)"
  | "Income Tax Returns (3 years)"
  | "Audited Financials"
  | "Memorandum of Association";

// Upload modes:
type UploadMode = "manual" | "aa"; // manual file upload OR Account Aggregator

// Document status tracked per file:
interface DocItem {
  name: string;
  status: "pending" | "uploading" | "extracted" | "error";
  size?: string;
}
```

**API Endpoints needed**:
- `POST /api/applications` → create new application, returns `{ id: string }`
- `POST /api/applications/:id/documents` → upload document (multipart/form-data), body: `{ documentType: string, file: File }`
- `GET /api/applications/:id/documents` → returns `DocItem[]`
- `POST /api/applications/:id/aa-consent` → initiate Account Aggregator flow

---

### 4.3 Agent Progress / Pipeline

```typescript
// File: src/lib/agentData.ts

type AgentStatus = "idle" | "running" | "complete" | "error";

interface AgentNode {
  id: string;           // "doc_parse", "fin_spread", etc.
  name: string;         // "Document Parser Agent"
  shortName: string;    // "DocParser"
  icon: string;         // lucide icon name
  isEngine?: boolean;   // special "engine" badge
  groupId?: string;     // agents in same group run in parallel
}

interface AgentState extends AgentNode {
  status: AgentStatus;
  duration: number;     // seconds elapsed
  startDelay: number;   // ms before start
}

interface LogEntry {
  timestamp: string;    // "00:00:01" or ISO string
  agent: string;        // "DocParser"
  message: string;      // log message text
  level: "info" | "warning" | "critical";
}

// 9 agents in pipeline (sequential/parallel groups):
// Group 1: doc_parse (sequential)
// Group 2: fin_spread + gst_verify (parallel)
// Group 3: gstr_engine + buyer_engine (parallel)
// Group 4: promoter_intel (sequential)
// Group 5: risk_score (sequential)
// Group 6: cam_gen (sequential)
// Group 7: counter_fact (sequential)
```

**API Endpoints needed**:
- `POST /api/applications/:id/pipeline/start` → trigger pipeline
- `GET /api/applications/:id/pipeline/status` → returns `{ agents: AgentState[], progress: number, logs: LogEntry[] }`
- **OR WebSocket**: `ws://api/applications/:id/pipeline` → streams `AgentState` updates + `LogEntry` events in real-time

---

### 4.4 Risk Analytics

```typescript
// File: src/lib/riskData.ts

interface RiskDataset {
  score: number;                        // 0-100
  riskCategory: string;                 // "LOW", "MEDIUM", "HIGH", "VERY HIGH"
  defaultProb12m: number;               // e.g. 2.1 (percentage)
  defaultProb24m: number;               // e.g. 4.8
  fiveCs: FiveCsData[];                 // exactly 5 items
  gstrReconciliation: GSTRQuarter[];    // 8 quarters
  suspectITC: string;                   // "₹0" or "₹12.9Cr"
  buyerConcentration: BuyerConcentration[];
  topThreeConcentration: number;        // e.g. 34.7
  financialRatios: FinancialRatio[];    // 12 ratios
  riskFlags: RiskFlag[];
}

interface FiveCsData {
  subject: string;    // "Character" | "Capacity" | "Capital" | "Collateral" | "Conditions"
  value: number;      // 0-100
  fullMark: number;   // always 100
}

interface GSTRQuarter {
  quarter: string;    // "Q1 FY23"
  gstr2a: number;     // ₹ Crores
  gstr3b: number;     // ₹ Crores
  flagged: boolean;   // mismatch detected
}

interface BuyerConcentration {
  name: string;       // buyer company name
  gstin: string;      // partial GSTIN
  percentage: number; // revenue share %
  risk: "high" | "medium" | "low";
}

interface FinancialRatio {
  name: string;           // "Current Ratio"
  value: string;          // "1.82"
  numericValue: number;
  unit: string;           // "x", "%", "days", "Cr"
  sparkline: number[];    // 4 data points for mini trend
  yoyChange: number;      // YoY change percentage
  anomaly: boolean;       // flagged as anomalous
  citation: {
    document: string;     // source document name
    page: number;
    method: string;       // "FinBERT"
    confidence: number;   // 0-100
  };
}

interface RiskFlag {
  type: string;                                    // "GST Fraud", "Leverage"
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  detectedBy: string;                              // agent name
  status: "active" | "resolved" | "monitoring";
}
```

**API Endpoint**: `GET /api/applications/:id/risk` → returns `RiskDataset`

---

### 4.5 Financial Spreads

```typescript
// File: src/lib/financialSpreadsData.ts

interface FinancialSpreadsDataset {
  pnl: LineItem[];           // 14 line items
  balanceSheet: LineItem[];  // 19 line items
  cashFlow: LineItem[];      // 5 line items
  ratios: RatioItem[];       // 17 ratios across 5 categories
}

interface LineItem {
  label: string;        // "Revenue / Net Sales"
  fy22: number;         // value in ₹ Lakhs
  fy23: number;
  fy24: number;
  isTotal?: boolean;    // bold total row styling
  isSubTotal?: boolean; // semi-bold subtotal styling
  indent?: number;      // indentation level (not currently used much)
}

interface RatioItem {
  name: string;
  category: "liquidity" | "leverage" | "profitability" | "efficiency" | "debt_service";
  fy22: number;
  fy23: number;
  fy24: number;
  unit: string;         // "x", "%", "days"
  benchmark: number;    // industry benchmark
  anomaly: boolean;     // flagged
  sparkline: number[];  // [fy22, fy23, fy24]
}
```

**API Endpoint**: `GET /api/applications/:id/financials` → returns `FinancialSpreadsDataset`

**Note**: All monetary values in the financial statements are in **₹ Lakhs** (1 Lakh = 100,000 INR). The frontend converts to Crores for display where appropriate.

---

### 4.6 Bank Statement Analytics

```typescript
// File: src/lib/bankStatementData.ts

interface BankStatementDataset {
  summary: {
    abb: number;                  // Average Bank Balance (₹ Lakhs)
    avgMonthlyCredits: number;    // ₹ Lakhs
    avgMonthlyDebits: number;
    creditDebitRatio: number;     // e.g. 1.08
    emiObligations: number;       // ₹ Lakhs
    emiCount: number;
    bounceRatio: number;          // percentage
    totalBounces: number;
    cashWithdrawalPercent: number; // percentage
    behaviorScore: number;        // 0-100
  };
  monthlyCashFlow: MonthlyCashFlow[];    // 12 months
  creditCategories: TransactionCategory[];
  debitCategories: TransactionCategory[];
  redFlags: RedFlag[];
  topCounterparties: Counterparty[];
}

interface MonthlyCashFlow {
  month: string;      // "Jan", "Feb", etc.
  credits: number;    // ₹ Lakhs
  debits: number;
  closing: number;    // closing balance
}

interface TransactionCategory {
  category: string;   // "Business Income", "Supplier Payments"
  amount: number;     // ₹ Lakhs
  percentage: number;
  txnCount: number;
}

interface RedFlag {
  type: string;                          // "Circular Transactions"
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  detected: boolean;                     // whether this flag was triggered
  details?: string;                      // detail text shown when detected=true
}

interface Counterparty {
  name: string;
  credits: number;    // ₹ Lakhs
  debits: number;
  net: number;
  frequency: number;  // transaction count
  risk: "low" | "medium" | "high";
}
```

**API Endpoint**: `GET /api/applications/:id/bank-analytics` → returns `BankStatementDataset`

---

### 4.7 Promoter Intelligence

```typescript
// File: src/lib/promoterData.ts

interface PromoterDataset {
  directors: Director[];
  networkNodes: NetworkNode[];
  networkEdges: NetworkEdge[];
  litigation: LitigationCase[];
  news: NewsItem[];
  overallPromoterRisk: "low" | "medium" | "high" | "critical";
  mca21Flags: string[];           // array of flag description strings
}

interface Director {
  name: string;
  din: string;                    // Director Identification Number
  designation: string;            // "Managing Director"
  age: number;
  experience: string;             // "28 years in textiles"
  linkedEntities: number;
  npaLinks: number;
  shellLinks: number;
  riskLevel: "clean" | "watchlist" | "flagged";
  cibilScore: number;             // 300-900
  netWorth: string;               // "₹42Cr"
}

interface NetworkNode {
  id: string;                     // unique node ID
  label: string;                  // display name
  type: "director" | "company" | "shell" | "npa" | "related";
  risk: "clean" | "warning" | "danger";
}

interface NetworkEdge {
  from: string;     // node ID
  to: string;       // node ID
  label: string;    // "MD", "Director", "Circular Trade"
  suspicious: boolean;
}

interface LitigationCase {
  date: string;                   // "2024-08" or ISO date
  court: string;                  // "NCLT Delhi"
  caseType: string;               // "Insolvency", "Fraud"
  status: "pending" | "disposed" | "settled";
  amount: string;                 // "₹18.5Cr"
  description: string;
  severity: "critical" | "high" | "medium" | "low";
}

interface NewsItem {
  date: string;                   // "2024-11"
  source: string;                 // "Economic Times"
  headline: string;
  sentiment: "positive" | "negative" | "neutral";
  relevance: number;              // 0-100
}
```

**API Endpoint**: `GET /api/applications/:id/promoter` → returns `PromoterDataset`

---

### 4.8 Due Diligence

```typescript
// File: src/lib/diligenceData.ts

interface DiligenceDataset {
  checks: DiligenceCheck[];
  fieldVisits: FieldVisitNote[];
  compliance: ComplianceItem[];
  completionPercent: number;      // 0-100
  overallStatus: "clear" | "concerns" | "blocked";
}

interface DiligenceCheck {
  id: string;
  category: string;               // "Identity", "Financial", "Legal", "Collateral", "Operational", "Regulatory"
  item: string;                   // "PAN Verification"
  status: "verified" | "pending" | "flagged" | "waived" | "not_applicable";
  source: string;                 // "NSDL", "GSTN Portal"
  verifiedBy: string;             // agent or officer name
  notes: string;
  timestamp?: string;             // ISO date or undefined
}

interface FieldVisitNote {
  date: string;
  officer: string;
  location: string;
  observations: string[];         // array of observation strings
  photoCount: number;
  rating: "satisfactory" | "concerns" | "unsatisfactory";
}

interface ComplianceItem {
  regulation: string;             // "RBI KYC Master Direction"
  status: "compliant" | "non_compliant" | "partial" | "pending_review";
  details: string;
  lastChecked: string;
}
```

**API Endpoint**: `GET /api/applications/:id/diligence` → returns `DiligenceDataset`

---

### 4.9 CAM Report (Credit Appraisal Memorandum)

```typescript
// File: src/lib/camData.ts

interface CamDataset {
  generatedAt: string;            // "2024-11-15 14:32 IST"
  sections: CamSection[];         // 5-6 narrative sections
  recommendation: Recommendation;
  counterfactuals: CounterfactualAction[];  // 0 for approve/reject, 4 for conditional
  keyMetrics: { label: string; value: string; status: "good" | "warning" | "danger" }[];
}

interface CamSection {
  title: string;      // "Executive Summary", "Business Overview", etc.
  content: string;    // narrative text paragraph
}

interface Recommendation {
  decision: "approve" | "reject" | "conditional";
  summary: string;    // recommendation explanation
  conditions: string[];  // list of conditions/requirements
  loanTerms: {
    amount: string;        // "₹45,00,00,000" or "NOT APPLICABLE"
    tenure: string;        // "12 months (renewable)"
    rate: string;          // "EBLR + 1.50%"
    security: string;      // collateral description
    disbursement: string;  // disbursement conditions
  };
}

interface CounterfactualAction {
  action: string;       // "Reduce D/E from 1.85x to 1.5x..."
  impact: string;       // "Risk score improves by ~8 points..."
  newScore: number;     // projected new score
  scoreImpact: number;  // additive points when toggled
  difficulty: "easy" | "medium" | "hard";
  timeframe: string;    // "6 months"
}
```

**API Endpoints**:
- `GET /api/applications/:id/cam` → returns `CamDataset`
- `POST /api/applications/:id/cam/generate` → trigger CAM generation

**PDF Export**: Currently client-side via jspdf. The PDF generator (`src/lib/generateCamPdf.ts`) aggregates data from ALL modules. If server-side PDF generation is desired, the endpoint would need to return a PDF blob.

---

### 4.10 Banking Facility Details (used in PDF export)

```typescript
// File: src/lib/facilityData.ts

interface FacilityDataset {
  existingFacilities: BankingFacility[];
  proposedFacilities: BankingFacility[];
  totalExistingFundBased: string;      // "₹32.00 Cr"
  totalExistingNonFundBased: string;
  totalProposedFundBased: string;
  totalProposedNonFundBased: string;
  workingCapital: WorkingCapitalAssessment;
  sensitivityAnalysis: SensitivityScenario[];
}

interface BankingFacility {
  bank: string;
  facilityType: "Fund Based" | "Non-Fund Based";
  nature: string;                      // "Cash Credit", "Term Loan"
  sanctionedLimit: string;             // "₹20.00 Cr"
  outstanding: string;
  security: string;
  rateOfInterest: string;
  repaymentStatus: "Regular" | "Irregular" | "NPA" | "SMA-0" | "SMA-1" | "SMA-2";
}

interface WorkingCapitalAssessment {
  currentAssets: { item: string; fy22: number; fy23: number; fy24: number; projected: number }[];
  currentLiabilities: { item: string; fy22: number; fy23: number; fy24: number; projected: number }[];
  netWorkingCapital: { fy22: number; fy23: number; fy24: number; projected: number };
  mpbf: { method: string; amount: string; details: string };
  drawingPower: string;
  assessedBankFinance: string;
}

interface SensitivityScenario {
  parameter: string;
  change: string;
  revisedDSCR: number;
  revisedICR: number;
  impact: "Comfortable" | "Marginal" | "Stressed" | "Default";
}
```

**API Endpoint**: `GET /api/applications/:id/facilities` → returns `FacilityDataset`

---

### 4.11 Audit Trail

```typescript
// File: src/lib/auditTrailData.ts

interface AuditTrailDataset {
  events: AuditEvent[];
  overrides: HumanOverride[];
  workflow: WorkflowStage[];
  compliance: ComplianceBadge[];
}

interface AuditEvent {
  id: string;
  timestamp: string;                    // "2024-11-15 14:00:12"
  actor: string;                        // "Amit Patel (CO)" or "DocParser Agent"
  actorType: "ai_agent" | "human" | "system";
  actionType: "data_extraction" | "analysis" | "decision" | "override" | "modification" | "initiation" | "verification";
  module: string;                       // "Document Upload", "Risk Analytics", etc.
  description: string;
  details?: string;
  confidence?: number;                  // 0-100 (for AI decisions)
  dataSources?: string[];
  previousValue?: string;               // for overrides/modifications
  newValue?: string;
}

interface HumanOverride {
  id: string;
  timestamp: string;
  officer: string;
  originalRecommendation: string;
  overriddenTo: string;
  reason: string;
  approvedBy: string;
  flaggedForReview: boolean;
}

interface WorkflowStage {
  stage: string;                        // "Application Created", "Risk Scored"
  status: "completed" | "in_progress" | "pending" | "blocked";
  actor?: string;
  actorType?: "ai_agent" | "human" | "system";
  timestamp?: string;
  notes?: string;
}

interface ComplianceBadge {
  regulation: string;                   // "RBI Digital Lending Directions 2025"
  status: "compliant" | "partial" | "non_compliant";
  details: string;
}
```

**API Endpoints**:
- `GET /api/applications/:id/audit` → returns `AuditTrailDataset`
- `POST /api/applications/:id/audit/override` → create human override
  - Body: `{ originalRecommendation, overriddenTo, reason }`

---

## 5. AI CHAT WIDGET

The floating chat widget (`AiChatWidget.tsx`) currently uses client-side keyword matching. For production:

```typescript
interface ChatMessage {
  role: "user" | "assistant";
  content: string;  // supports **bold** markdown
}

// API Endpoint:
// POST /api/applications/:id/chat
// Body: { message: string, history: ChatMessage[] }
// Response: { reply: string }
```

The widget needs access to the current application context (company name, risk score) for contextual responses.

---

## 6. COMPLETE API SURFACE SUMMARY

| Method | Endpoint | Returns | Priority |
|--------|----------|---------|----------|
| `GET` | `/api/applications` | `Dataset[]` | HIGH |
| `POST` | `/api/applications` | `{ id: string }` | HIGH |
| `GET` | `/api/applications/:id` | `Dataset` | HIGH |
| `POST` | `/api/applications/:id/documents` | `DocItem` | HIGH |
| `GET` | `/api/applications/:id/documents` | `DocItem[]` | HIGH |
| `POST` | `/api/applications/:id/aa-consent` | `{ status }` | MEDIUM |
| `POST` | `/api/applications/:id/pipeline/start` | `{ jobId }` | HIGH |
| `GET` | `/api/applications/:id/pipeline/status` | `{ agents, progress, logs }` | HIGH |
| `GET` | `/api/applications/:id/risk` | `RiskDataset` | HIGH |
| `GET` | `/api/applications/:id/financials` | `FinancialSpreadsDataset` | HIGH |
| `GET` | `/api/applications/:id/bank-analytics` | `BankStatementDataset` | HIGH |
| `GET` | `/api/applications/:id/promoter` | `PromoterDataset` | HIGH |
| `GET` | `/api/applications/:id/diligence` | `DiligenceDataset` | HIGH |
| `GET` | `/api/applications/:id/cam` | `CamDataset` | HIGH |
| `POST` | `/api/applications/:id/cam/generate` | `{ status }` | MEDIUM |
| `GET` | `/api/applications/:id/facilities` | `FacilityDataset` | MEDIUM |
| `GET` | `/api/applications/:id/audit` | `AuditTrailDataset` | HIGH |
| `POST` | `/api/applications/:id/audit/override` | `HumanOverride` | MEDIUM |
| `POST` | `/api/applications/:id/chat` | `{ reply }` | LOW |

---

## 7. FRONTEND INTEGRATION PATTERN (How to wire APIs)

### Step 1: Create API service layer
```typescript
// src/lib/api.ts
const API_BASE = import.meta.env.VITE_API_URL || "/api";

export async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

### Step 2: Create react-query hooks
```typescript
// src/hooks/useRiskData.ts
import { useQuery } from "@tanstack/react-query";

export function useRiskData(applicationId: string) {
  return useQuery({
    queryKey: ["risk", applicationId],
    queryFn: () => fetchJSON<RiskDataset>(`/applications/${applicationId}/risk`),
    enabled: !!applicationId,
  });
}
```

### Step 3: Replace static data calls in pages
```typescript
// Before:
const data = getRiskData(activeDataset);

// After:
const { data, isLoading, error } = useRiskData(applicationId);
```

### Step 4: Update DatasetContext
```typescript
// Replace DatasetId with applicationId
interface DatasetContextValue {
  applicationId: string;
  setApplicationId: (id: string) => void;
  dataset: Dataset | undefined;
  isLoading: boolean;
}
```

---

## 8. REAL-TIME FEATURES (WebSocket/SSE)

### Agent Pipeline (priority: HIGH)
The agent progress page shows real-time updates as agents process. Recommended: **Server-Sent Events (SSE)** or WebSocket.

```typescript
// SSE event types:
type PipelineEvent =
  | { type: "agent_status"; agentId: string; status: AgentStatus; elapsed: number }
  | { type: "log"; entry: LogEntry }
  | { type: "progress"; percent: number }
  | { type: "complete"; result: "success" | "error" }
```

### Chat Widget (priority: LOW)
Can use regular REST POST for now. Stream responses later for LLM integration.

---

## 9. AUTHENTICATION & AUTHORIZATION

Currently NO authentication is implemented. For production:
- Add login/signup pages
- Protect all `/api/*` routes
- Add user roles: `credit_officer`, `reviewer`, `admin`
- The audit trail should capture the authenticated user as the actor
- Human overrides require `reviewer` or `admin` role

---

## 10. PDF EXPORT DATA REQUIREMENTS

The CAM PDF export (`generateCamPdf`) aggregates data from ALL modules in a single call:

```typescript
interface CamPdfData {
  camData: CamDataset;
  dataset: Dataset;
  riskData: RiskDataset;
  promoterData: PromoterDataset;
  financialData: FinancialSpreadsDataset;
  bankData: BankStatementDataset;
  diligenceData: DiligenceDataset;
  facilityData: FacilityDataset;
}
```

**Option A**: Keep client-side PDF generation (current) — frontend fetches all data independently.
**Option B**: Server-side PDF → `GET /api/applications/:id/cam/pdf` returns PDF blob.

---

## 11. KEY BUSINESS RULES & THRESHOLDS

### Risk Score Interpretation
| Score Range | Category | Color |
|------------|----------|-------|
| 70-100 | LOW RISK | Green (safe) |
| 50-69 | MEDIUM RISK | Yellow (warning) |
| 0-49 | HIGH/VERY HIGH RISK | Red (destructive) |

### Financial Ratio Benchmarks (used for anomaly detection)
| Ratio | Benchmark | Anomaly When |
|-------|-----------|-------------|
| Current Ratio | 1.5x | < benchmark |
| D/E Ratio | 2.0x | > benchmark |
| DSCR | 1.5x | < benchmark |
| Interest Coverage | 2.5x | < benchmark |
| EBITDA Margin | 15% | < benchmark |
| Net Margin | 5% | < benchmark |
| ROE | 12% | < benchmark |
| Working Cap Days | 75 days | > benchmark |

### Decision Logic
| Condition | Decision |
|-----------|----------|
| Score ≥ 70, no critical flags | APPROVE |
| Score < 50 OR critical fraud flags | REJECT |
| Score 50-69 OR moderate flags | CONDITIONAL |

### GSTR Fraud Detection
- Flag when GSTR-2A vs GSTR-3B variance > 15%
- Circular trading: same amount credited/debited within 48h between related entities

### Bank Statement Red Flags
- Circular transactions between related accounts
- End-of-month window dressing
- Cash deposit spikes before statement dates
- Bounce ratio > 5%
- Cash withdrawal > 20% of debits
- ABB declining 3+ consecutive months

---

## 12. INDIA-SPECIFIC REGULATORY CONTEXT

This platform operates in the **Indian banking/NBFC credit underwriting** domain:

- **GSTIN**: Goods and Services Tax Identification Number (15-digit)
- **CIN**: Corporate Identity Number (21-character, MCA-issued)
- **PAN**: Permanent Account Number (10-character, Income Tax)
- **DIN**: Director Identification Number (8-digit)
- **CIBIL**: Credit bureau score (300-900)
- **CRILC**: Central Repository of Information on Large Credits (RBI)
- **MCA21**: Ministry of Corporate Affairs portal
- **DSCR**: Debt Service Coverage Ratio
- **MPBF**: Maximum Permissible Bank Finance (Nayak Committee method)
- **Account Aggregator (AA)**: RBI-regulated data sharing framework (Sahamati network)
- **GSTR-1/2A/3B**: GST return types for sales, purchases, summary
- **SMA**: Special Mention Account (0/1/2 classification before NPA)
- **NPA**: Non-Performing Asset
- **STR**: Suspicious Transaction Report (filed with FIU-IND)
- **EBLR**: External Benchmark Lending Rate

**All monetary values use Indian numbering**: Lakhs (₹L = ₹100,000) and Crores (₹Cr = ₹10,000,000)

---

## 13. FILE STRUCTURE REFERENCE

```
src/
├── App.tsx                          # Router setup
├── components/
│   ├── AppLayout.tsx                # Layout wrapper (sidebar + header + footer)
│   ├── AppSidebar.tsx               # Navigation + dataset switcher
│   ├── AppHeader.tsx                # Breadcrumb + score badge
│   ├── MetricsFooter.tsx            # Bottom metrics bar
│   ├── AiChatWidget.tsx             # Floating AI chat
│   ├── DemoTourOverlay.tsx          # Guided tour overlay
│   └── risk/                        # Shared risk components
│       ├── RiskGauge.tsx
│       └── CitationBadge.tsx
├── contexts/
│   ├── DatasetContext.tsx            # ★ Primary data context (replace with API)
│   ├── ThemeContext.tsx              # Theme switching (gold/blue)
│   └── DemoTourContext.tsx
├── lib/
│   ├── demoData.ts                  # ★ Base dataset definitions
│   ├── riskData.ts                  # ★ Risk analytics data
│   ├── financialSpreadsData.ts      # ★ Financial statements & ratios
│   ├── bankStatementData.ts         # ★ Bank analytics data
│   ├── promoterData.ts              # ★ Promoter intelligence data
│   ├── diligenceData.ts             # ★ Due diligence checks
│   ├── camData.ts                   # ★ CAM report data
│   ├── facilityData.ts              # ★ Banking facilities data
│   ├── auditTrailData.ts            # ★ Audit trail events
│   ├── agentData.ts                 # ★ Agent pipeline config
│   ├── generateCamPdf.ts            # PDF generation orchestrator
│   └── pdf/                         # PDF section renderers
└── pages/                           # 10 page components (see routes above)
```

Files marked with ★ contain hardcoded demo data that needs to be replaced with API calls.

---

## 14. ENVIRONMENT VARIABLES NEEDED

```env
VITE_API_URL=https://api.intellicredit.example.com
VITE_WS_URL=wss://api.intellicredit.example.com/ws
```

---

*This spec is auto-generated from the IntelliCredit AI frontend codebase. All interfaces match the exact TypeScript types consumed by React components.*
