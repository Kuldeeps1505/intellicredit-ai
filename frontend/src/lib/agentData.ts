import { DatasetId } from "./demoData";

export type AgentStatus = "idle" | "running" | "complete" | "error";

export interface AgentNode {
  id: string;
  name: string;
  shortName: string;
  icon: string; // lucide icon name
  isEngine?: boolean;
  parallel?: boolean; // rendered side-by-side
  groupId?: string;   // agents in same group render in parallel
}

export interface AgentState extends AgentNode {
  status: AgentStatus;
  duration: number; // seconds
  startDelay: number; // ms before this agent starts
}

export interface LogEntry {
  timestamp: string;
  agent: string;
  message: string;
  level: "info" | "warning" | "critical";
}

export const agentNodes: AgentNode[] = [
  { id: "doc_parse", name: "Document Parser Agent", shortName: "DocParser", icon: "FileText" },
  { id: "fin_spread", name: "Financial Spreading Agent", shortName: "FinSpread", icon: "BarChart3", groupId: "parallel1" },
  { id: "gst_verify", name: "GST Verification Agent", shortName: "GSTVerify", icon: "ShieldCheck", groupId: "parallel1" },
  { id: "gstr_engine", name: "GSTR Reconciliation Engine", shortName: "GSTRRecon", icon: "Zap", isEngine: true, groupId: "parallel2" },
  { id: "buyer_engine", name: "Buyer Concentration Engine", shortName: "BuyerConc", icon: "Zap", isEngine: true, groupId: "parallel2" },
  { id: "promoter_intel", name: "Promoter Intelligence Agent", shortName: "PromoterIntel", icon: "Users" },
  { id: "risk_score", name: "Risk Scoring Agent", shortName: "RiskScore", icon: "Target" },
  { id: "cam_gen", name: "CAM Generator Agent", shortName: "CAMGen", icon: "FileOutput" },
  { id: "counter_fact", name: "Counterfactual Agent", shortName: "CounterFact", icon: "GitBranch" },
];

// Simulation timings per dataset (seconds)
const timings: Record<DatasetId, Record<string, number>> = {
  approve: {
    doc_parse: 3, fin_spread: 4, gst_verify: 3, gstr_engine: 5, buyer_engine: 4,
    promoter_intel: 3, risk_score: 2, cam_gen: 4, counter_fact: 2,
  },
  fraud: {
    doc_parse: 3, fin_spread: 4, gst_verify: 5, gstr_engine: 6, buyer_engine: 5,
    promoter_intel: 4, risk_score: 3, cam_gen: 4, counter_fact: 3,
  },
  conditional: {
    doc_parse: 3, fin_spread: 4, gst_verify: 4, gstr_engine: 5, buyer_engine: 4,
    promoter_intel: 3, risk_score: 2, cam_gen: 4, counter_fact: 2,
  },
};

export function getAgentTimings(datasetId: DatasetId) {
  return timings[datasetId];
}

// Demo logs per dataset
export function getDemoLogs(datasetId: DatasetId): LogEntry[] {
  const base: LogEntry[] = [
    { timestamp: "00:00:01", agent: "DocParser", message: "Initializing document parsing pipeline...", level: "info" },
    { timestamp: "00:00:02", agent: "DocParser", message: "Extracting text from Annual Report 2024 (148 pages)", level: "info" },
    { timestamp: "00:00:03", agent: "DocParser", message: "OCR confidence: 97.2% — all documents parsed successfully", level: "info" },
    { timestamp: "00:00:04", agent: "FinSpread", message: "Starting financial statement spreading...", level: "info" },
    { timestamp: "00:00:04", agent: "GSTVerify", message: "Initiating GST return verification against GSTN...", level: "info" },
    { timestamp: "00:00:06", agent: "FinSpread", message: "Revenue trend: ₹120.3Cr → ₹135.8Cr (3Y CAGR: 12.9%)", level: "info" },
    { timestamp: "00:00:07", agent: "GSTVerify", message: "Verifying GSTR-1, GSTR-3B for 24 months...", level: "info" },
    { timestamp: "00:00:08", agent: "FinSpread", message: "D/E Ratio computed: 2.8x — exceeds threshold of 2.0x", level: "warning" },
  ];

  if (datasetId === "fraud") {
    return [
      ...base,
      { timestamp: "00:00:09", agent: "GSTRRecon", message: "⚡ GSTR-2A vs GSTR-3B reconciliation started...", level: "info" },
      { timestamp: "00:00:10", agent: "BuyerConc", message: "⚡ Analyzing buyer concentration patterns...", level: "info" },
      { timestamp: "00:00:12", agent: "GSTRRecon", message: "🚨 CRITICAL: ITC overclaim detected — ₹12.9Cr suspect across Q2-Q4 FY24", level: "critical" },
      { timestamp: "00:00:13", agent: "BuyerConc", message: "🚨 WARNING: Top 3 buyers = 68.4% revenue — HIGH concentration risk", level: "critical" },
      { timestamp: "00:00:15", agent: "PromoterIntel", message: "Director DIN 00234567 linked to 2 prior NPA entities", level: "critical" },
      { timestamp: "00:00:16", agent: "PromoterIntel", message: "🚨 FRAUD NETWORK DETECTED — shell company connections identified", level: "critical" },
      { timestamp: "00:00:18", agent: "RiskScore", message: "Composite risk score: 28/100 — VERY HIGH RISK", level: "critical" },
      { timestamp: "00:00:20", agent: "CAMGen", message: "CAM report generated — Recommendation: REJECT", level: "warning" },
      { timestamp: "00:00:22", agent: "CounterFact", message: "Path to approval requires: debt reduction ₹18Cr + equity infusion ₹12Cr + resolve NPA links", level: "info" },
    ];
  }

  if (datasetId === "conditional") {
    return [
      ...base,
      { timestamp: "00:00:09", agent: "GSTRRecon", message: "⚡ GSTR-2A vs GSTR-3B reconciliation started...", level: "info" },
      { timestamp: "00:00:10", agent: "BuyerConc", message: "⚡ Analyzing buyer concentration patterns...", level: "info" },
      { timestamp: "00:00:12", agent: "GSTRRecon", message: "Minor ITC discrepancy: ₹1.2Cr in Q3 FY24 — within tolerance", level: "warning" },
      { timestamp: "00:00:13", agent: "BuyerConc", message: "Top 3 buyers = 42.1% revenue — MODERATE concentration", level: "warning" },
      { timestamp: "00:00:15", agent: "PromoterIntel", message: "Promoter profile clean — no adverse findings", level: "info" },
      { timestamp: "00:00:17", agent: "RiskScore", message: "Composite risk score: 61/100 — MEDIUM RISK", level: "warning" },
      { timestamp: "00:00:19", agent: "CAMGen", message: "CAM report generated — Recommendation: CONDITIONAL APPROVE", level: "info" },
      { timestamp: "00:00:21", agent: "CounterFact", message: "Conditions: Additional collateral ₹5Cr + quarterly GST monitoring", level: "info" },
    ];
  }

  // approve
  return [
    ...base,
    { timestamp: "00:00:09", agent: "GSTRRecon", message: "⚡ GSTR-2A vs GSTR-3B reconciliation started...", level: "info" },
    { timestamp: "00:00:10", agent: "BuyerConc", message: "⚡ Analyzing buyer concentration patterns...", level: "info" },
    { timestamp: "00:00:11", agent: "GSTRRecon", message: "All quarters reconciled — no ITC discrepancies found", level: "info" },
    { timestamp: "00:00:12", agent: "BuyerConc", message: "Top 3 buyers = 31.2% revenue — healthy diversification", level: "info" },
    { timestamp: "00:00:14", agent: "PromoterIntel", message: "Promoter profile excellent — 15 years industry experience", level: "info" },
    { timestamp: "00:00:16", agent: "RiskScore", message: "Composite risk score: 81/100 — LOW RISK", level: "info" },
    { timestamp: "00:00:18", agent: "CAMGen", message: "CAM report generated — Recommendation: APPROVE", level: "info" },
    { timestamp: "00:00:19", agent: "CounterFact", message: "No counterfactual actions needed — all parameters within thresholds", level: "info" },
  ];
}
