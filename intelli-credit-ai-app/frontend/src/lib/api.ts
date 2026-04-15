/**
 * API service layer — all backend calls go through here.
 * Base URL reads from VITE_API_URL env var, falls back to localhost:8000.
 */

const BASE = (import.meta.env.VITE_API_URL as string) || "http://localhost:8000";
const WS_BASE = BASE.replace(/^http/, "ws");

// ── Types ──────────────────────────────────────────────────────────────────────

export interface CreateApplicationPayload {
  company: {
    cin: string;
    name: string;
    pan?: string;
    gstin?: string;
    sector?: string;
  };
  loan_amount_requested: number;
  purpose?: string;
}

export interface ApplicationSummary {
  id: string;
  label: string;
  emoji: string;
  score?: number;
  companyName: string;
  cin: string;
  pan?: string;
  gstin?: string;
  loanAmount: string;
  purpose?: string;
  sector?: string;
  decision?: string;
  status: string;
}

export interface DocItem {
  name: string;
  status: string;
  size?: string;
  doc_type?: string;
}

export interface AgentStateOut {
  id: string;
  name: string;
  shortName: string;
  icon: string;
  isEngine: boolean;
  groupId: string;
  status: string;
  duration: number;
  startDelay: number;
}

export interface LogEntryOut {
  timestamp: string;
  agent: string;
  message: string;
  level: "info" | "warning" | "critical";
}

export interface PipelineStatusResponse {
  agents: AgentStateOut[];
  progress: number;
  logs: LogEntryOut[];
}

// ── Helpers ────────────────────────────────────────────────────────────────────

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Applications ───────────────────────────────────────────────────────────────

export const api = {
  createApplication: (payload: CreateApplicationPayload) =>
    request<{ id: string }>("/api/applications", { method: "POST", body: JSON.stringify(payload) }),

  uploadDocument: (appId: string, file: File, documentType = "UNKNOWN") => {
    const form = new FormData();
    form.append("file", file);
    form.append("documentType", documentType);
    return fetch(`${BASE}/api/applications/${appId}/documents`, { method: "POST", body: form })
      .then(async (res) => { if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`); return res.json() as Promise<DocItem>; });
  },

  startPipeline: (appId: string) =>
    request<{ jobId: string; status: string }>(`/api/applications/${appId}/pipeline/start`, { method: "POST" }),

  getPipelineStatus: (appId: string) =>
    request<PipelineStatusResponse>(`/api/applications/${appId}/pipeline/status`),

  listApplications: () => request<ApplicationSummary[]>("/api/applications"),
  getApplication:   (appId: string) => request<ApplicationSummary>(`/api/applications/${appId}`),

  getRisk:          (appId: string) => request<unknown>(`/api/applications/${appId}/risk`),
  getScoreExplanation: (appId: string) => request<{
    baseScore: number; finalScore: number; decision: string;
    steps: { label: string; value: number; cumulative: number; category: string; detail: string; source: string }[];
    positiveTotal: number; negativeTotal: number; dataSource: string;
  }>(`/api/applications/${appId}/score-explanation`),
  getPromoter:      (appId: string) => request<import("@/lib/promoterData").PromoterDataset>(`/api/applications/${appId}/promoter`),
  getDiligence:     (appId: string) => request<import("@/lib/diligenceData").DiligenceDataset>(`/api/applications/${appId}/diligence`),
  getCam:           (appId: string) => request<import("@/lib/camData").CamDataset>(`/api/applications/${appId}/cam`),
  getFinancials:    (appId: string) => request<import("@/lib/financialSpreadsData").FinancialSpreadsDataset>(`/api/applications/${appId}/financials`),
  getBankAnalytics: (appId: string) => request<import("@/lib/bankStatementData").BankStatementDataset>(`/api/applications/${appId}/bank-analytics`),
  getAudit:         (appId: string) => request<import("@/lib/auditTrailData").AuditTrailDataset>(`/api/applications/${appId}/audit`),

  // Account Aggregator (India Stack)
  aaInitiateConsent: (appId: string, mobile: string, purpose?: string) =>
    request<{ consentHandle: string; redirectUrl: string; txnId: string; provider: string; status: string; message?: string; aaApp?: string; expiresIn?: string }>(
      `/api/applications/${appId}/aa/consent/initiate`,
      { method: "POST", body: JSON.stringify({ mobile, purpose: purpose || "Loan Appraisal" }) }
    ),
  aaConsentStatus: (appId: string) =>
    request<{ consentHandle: string; consentId?: string; status: string; provider: string; approvedAt?: string }>(
      `/api/applications/${appId}/aa/consent/status`
    ),
  aaFetchFI: (appId: string) =>
    request<{ success: boolean; accountsFetched: number; bankStatementsFetched: boolean; gstDataFetched: boolean; message: string }>(
      `/api/applications/${appId}/aa/fi/fetch`, { method: "POST" }
    ),
  aaSessionStatus: (appId: string) =>
    request<{ step: string; consentHandle?: string; consentStatus?: string; dataFetched: boolean; bankStatements: boolean; gstData: boolean }>(
      `/api/applications/${appId}/aa/status`
    ),
};

// ── WebSocket factory ──────────────────────────────────────────────────────────

export function createPipelineWebSocket(appId: string): WebSocket {
  return new WebSocket(`${WS_BASE}/ws/applications/${appId}`);
}
