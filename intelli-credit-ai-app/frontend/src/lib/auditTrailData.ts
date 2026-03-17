import { DatasetId } from "./demoData";

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  actorType: "ai_agent" | "human" | "system";
  actionType: "data_extraction" | "analysis" | "decision" | "override" | "modification" | "initiation" | "verification";
  module: string;
  description: string;
  details?: string;
  confidence?: number;
  dataSources?: string[];
  previousValue?: string;
  newValue?: string;
}

export interface HumanOverride {
  id: string;
  timestamp: string;
  officer: string;
  originalRecommendation: string;
  overriddenTo: string;
  reason: string;
  approvedBy: string;
  flaggedForReview: boolean;
}

export interface WorkflowStage {
  stage: string;
  status: "completed" | "in_progress" | "pending" | "blocked";
  actor?: string;
  actorType?: "ai_agent" | "human" | "system";
  timestamp?: string;
  notes?: string;
}

export interface ComplianceBadge {
  regulation: string;
  status: "compliant" | "partial" | "non_compliant";
  details: string;
}

export interface AuditTrailDataset {
  events: AuditEvent[];
  overrides: HumanOverride[];
  workflow: WorkflowStage[];
  compliance: ComplianceBadge[];
}

const approveAudit: AuditTrailDataset = {
  events: [
    { id: "E001", timestamp: "2024-11-15 14:00:12", actor: "Amit Patel (CO)", actorType: "human", actionType: "initiation", module: "Document Upload", description: "Application initiated", details: "Loan: ₹45Cr Working Capital for Reliance Textiles Pvt Ltd", dataSources: ["Manual Entry"] },
    { id: "E002", timestamp: "2024-11-15 14:02:45", actor: "System", actorType: "system", actionType: "verification", module: "Document Upload", description: "AA consent received", details: "Borrower approved Account Aggregator consent via Sahamati network" },
    { id: "E003", timestamp: "2024-11-15 14:05:30", actor: "DocParser Agent", actorType: "ai_agent", actionType: "data_extraction", module: "Agent Progress", description: "Document parsing complete", details: "6/6 documents parsed. 312 data points extracted.", confidence: 97, dataSources: ["Annual Reports", "Bank Statements", "GST Returns", "ITR", "Audited Financials", "MoA"] },
    { id: "E004", timestamp: "2024-11-15 14:10:15", actor: "FinSpread Agent", actorType: "ai_agent", actionType: "analysis", module: "Financial Spreads", description: "Financial spreading complete", details: "3-year P&L, BS, CF spread. 17 ratios calculated. 0 anomalies detected.", confidence: 95, dataSources: ["Audited Financials FY22-24"] },
    { id: "E005", timestamp: "2024-11-15 14:12:42", actor: "GST Verify Agent", actorType: "ai_agent", actionType: "verification", module: "Risk Analytics", description: "GST verification complete", details: "GSTR-1 vs 2A vs 3B reconciled. Zero suspect ITC. All quarters clean.", confidence: 98, dataSources: ["GSTN Portal", "GSTR-1", "GSTR-2A", "GSTR-3B"] },
    { id: "E006", timestamp: "2024-11-15 14:18:20", actor: "GSTR Recon Engine", actorType: "ai_agent", actionType: "analysis", module: "Risk Analytics", description: "GSTR reconciliation engine complete", details: "8 quarters analyzed. Max mismatch: 1.2% (within threshold).", confidence: 96 },
    { id: "E007", timestamp: "2024-11-15 14:20:05", actor: "Buyer Conc Engine", actorType: "ai_agent", actionType: "analysis", module: "Risk Analytics", description: "Buyer concentration analysis", details: "Top-3 concentration: 34.7%. No single buyer >15%. Healthy diversification.", confidence: 94 },
    { id: "E008", timestamp: "2024-11-15 14:23:18", actor: "Bank Statement Agent", actorType: "ai_agent", actionType: "analysis", module: "Bank Analytics", description: "Bank statement analysis complete", details: "ABB ₹3.42Cr. Bounce ratio 0.8%. No circular transactions. Behavior score: 88/100.", confidence: 92, dataSources: ["12-month bank statements via AA"] },
    { id: "E009", timestamp: "2024-11-15 14:25:40", actor: "Promoter Intel Agent", actorType: "ai_agent", actionType: "analysis", module: "Promoter Intel", description: "Promoter intelligence complete", details: "3 directors verified. 0 NPA links. 0 shell links. MCA21 clean. CIBIL avg: 815.", confidence: 96, dataSources: ["MCA21", "CIBIL", "eCourts", "CERSAI", "News APIs"] },
    { id: "E010", timestamp: "2024-11-15 14:28:55", actor: "Risk Scoring Agent", actorType: "ai_agent", actionType: "decision", module: "Risk Analytics", description: "Risk score computed", details: "Overall Score: 81/100. Category: Low Risk. Default Prob 12M: 2.1%.", confidence: 94 },
    { id: "E011", timestamp: "2024-11-15 14:30:10", actor: "Due Diligence Agent", actorType: "ai_agent", actionType: "verification", module: "Due Diligence", description: "Due diligence checks complete", details: "15/15 checks completed. 96% completion. Status: CLEAR.", confidence: 97 },
    { id: "E012", timestamp: "2024-11-15 14:32:28", actor: "CAM Generator Agent", actorType: "ai_agent", actionType: "decision", module: "CAM Report", description: "CAM report generated", details: "Decision: APPROVE. 6 sections generated. Loan terms recommended.", confidence: 93 },
    { id: "E013", timestamp: "2024-11-15 14:33:50", actor: "Counterfactual Agent", actorType: "ai_agent", actionType: "analysis", module: "CAM Report", description: "Counterfactual analysis complete", details: "4 improvement scenarios generated. Max potential score: 89.", confidence: 90 },
    { id: "E014", timestamp: "2024-11-15 15:45:00", actor: "Amit Patel (CO)", actorType: "human", actionType: "verification", module: "CAM Report", description: "Credit Officer reviewed and approved", details: "Manual review completed. No overrides needed. Forwarded to sanctioning authority." },
    { id: "E015", timestamp: "2024-11-15 16:20:00", actor: "Ravi Sharma (VP Credit)", actorType: "human", actionType: "decision", module: "Approval Workflow", description: "Sanctioning authority approved", details: "Approved with standard conditions. Disbursement cleared." },
  ],
  overrides: [],
  workflow: [
    { stage: "Application Created", status: "completed", actor: "Amit Patel (CO)", actorType: "human", timestamp: "2024-11-15 14:00:12", notes: "All documents received" },
    { stage: "Documents Verified", status: "completed", actor: "DocParser Agent", actorType: "ai_agent", timestamp: "2024-11-15 14:05:30", notes: "6/6 documents parsed" },
    { stage: "Analysis Complete", status: "completed", actor: "Multiple Agents", actorType: "ai_agent", timestamp: "2024-11-15 14:28:55", notes: "All 9 agents completed successfully" },
    { stage: "Risk Scored", status: "completed", actor: "Risk Scoring Agent", actorType: "ai_agent", timestamp: "2024-11-15 14:28:55", notes: "Score: 81 — Low Risk" },
    { stage: "CAM Generated", status: "completed", actor: "CAM Generator Agent", actorType: "ai_agent", timestamp: "2024-11-15 14:32:28", notes: "Decision: APPROVE" },
    { stage: "Reviewer Approved", status: "completed", actor: "Amit Patel (CO)", actorType: "human", timestamp: "2024-11-15 15:45:00", notes: "No overrides" },
    { stage: "Sanctioning Authority", status: "completed", actor: "Ravi Sharma (VP Credit)", actorType: "human", timestamp: "2024-11-15 16:20:00", notes: "Approved with standard conditions" },
    { stage: "Disbursement", status: "pending", notes: "Pending documentation completion" },
  ],
  compliance: [
    { regulation: "RBI Digital Lending Directions 2025", status: "compliant", details: "Full audit trail maintained. Borrower consent recorded." },
    { regulation: "MCA Audit Trail Mandate (Apr 2023)", status: "compliant", details: "All modifications logged with timestamps and actor details." },
    { regulation: "RBI IT Governance Master Direction", status: "compliant", details: "System logs maintained. Access controls active." },
    { regulation: "KYC/AML Compliance", status: "compliant", details: "PAN, GSTIN, CIN verified. CRILC check clear." },
    { regulation: "CERSAI Registration", status: "compliant", details: "No existing charges on proposed collateral." },
  ],
};

const fraudAudit: AuditTrailDataset = {
  events: [
    { id: "E001", timestamp: "2024-11-15 10:00:05", actor: "Priya Singh (CO)", actorType: "human", actionType: "initiation", module: "Document Upload", description: "Application initiated", details: "Loan: ₹22.5Cr Term Loan for Sunrise Exports International" },
    { id: "E002", timestamp: "2024-11-15 10:08:30", actor: "DocParser Agent", actorType: "ai_agent", actionType: "data_extraction", module: "Agent Progress", description: "Document parsing complete", details: "6/6 documents parsed. 287 data points extracted. ⚠️ 3 document quality warnings.", confidence: 82, dataSources: ["Annual Reports", "Bank Statements", "GST Returns", "ITR", "Audited Financials", "MoA"] },
    { id: "E003", timestamp: "2024-11-15 10:14:20", actor: "FinSpread Agent", actorType: "ai_agent", actionType: "analysis", module: "Financial Spreads", description: "Financial spreading complete", details: "🔴 CRITICAL: Revenue jumped 133% YoY with declining margins. 14 out of 17 ratios anomalous.", confidence: 88, dataSources: ["Audited Financials FY22-24"] },
    { id: "E004", timestamp: "2024-11-15 10:18:45", actor: "GST Verify Agent", actorType: "ai_agent", actionType: "verification", module: "Risk Analytics", description: "GST verification flagged", details: "🔴 GSTR-2A vs 3B mismatch: 42% in Q1 FY24. Suspect ITC: ₹4.2Cr. Circular trading pattern detected.", confidence: 91, dataSources: ["GSTN Portal"] },
    { id: "E005", timestamp: "2024-11-15 10:22:10", actor: "GSTR Recon Engine", actorType: "ai_agent", actionType: "analysis", module: "Risk Analytics", description: "GSTR reconciliation engine — CRITICAL ALERT", details: "🔴 5 out of 8 quarters show >15% mismatch. Fake ITC ring suspected involving 3 entities.", confidence: 93 },
    { id: "E006", timestamp: "2024-11-15 10:25:35", actor: "Bank Statement Agent", actorType: "ai_agent", actionType: "analysis", module: "Bank Analytics", description: "Bank statement analysis — MULTIPLE RED FLAGS", details: "🔴 Circular transactions: ₹8.4Cr. Window dressing detected. Bounce ratio: 14.2%. Cash: 28.5%. Score: 22/100.", confidence: 90, dataSources: ["12-month bank statements"] },
    { id: "E007", timestamp: "2024-11-15 10:30:50", actor: "Promoter Intel Agent", actorType: "ai_agent", actionType: "analysis", module: "Promoter Intel", description: "Promoter intelligence — CRITICAL RISK", details: "🔴 2 NPA links. Shell companies detected. Director disqualified under Sec 164(2). 5 MCA flags. 4 active litigations.", confidence: 95, dataSources: ["MCA21", "CIBIL", "eCourts", "ED/CBI records", "News APIs"] },
    { id: "E008", timestamp: "2024-11-15 10:35:15", actor: "Risk Scoring Agent", actorType: "ai_agent", actionType: "decision", module: "Risk Analytics", description: "Risk score computed", details: "🔴 Score: 28/100. Category: CRITICAL RISK. Default Prob 12M: 68.5%. RECOMMEND REJECT.", confidence: 96 },
    { id: "E009", timestamp: "2024-11-15 10:38:40", actor: "Due Diligence Agent", actorType: "ai_agent", actionType: "verification", module: "Due Diligence", description: "Due diligence — BLOCKED", details: "🔴 6 checks flagged. Wilful defaulter suspicion. CRILC SMA-2 classification. Completion: 72%.", confidence: 94 },
    { id: "E010", timestamp: "2024-11-15 10:42:05", actor: "CAM Generator Agent", actorType: "ai_agent", actionType: "decision", module: "CAM Report", description: "CAM report generated", details: "Decision: REJECT. Fraud indicators identified across multiple modules.", confidence: 97 },
    { id: "E011", timestamp: "2024-11-15 10:44:20", actor: "System", actorType: "system", actionType: "decision", module: "Compliance", description: "Auto-escalation triggered", details: "Application auto-escalated to Fraud Investigation Unit due to critical fraud indicators." },
    { id: "E012", timestamp: "2024-11-15 11:30:00", actor: "Priya Singh (CO)", actorType: "human", actionType: "verification", module: "CAM Report", description: "Credit Officer confirmed rejection", details: "Agreed with AI recommendation. Flagged for FIU investigation." },
    { id: "E013", timestamp: "2024-11-15 12:15:00", actor: "Sanjay Verma (Chief Risk)", actorType: "human", actionType: "decision", module: "Approval Workflow", description: "Chief Risk Officer reviewed", details: "Rejection confirmed. Suspicious Transaction Report (STR) to be filed with FIU-IND." },
  ],
  overrides: [],
  workflow: [
    { stage: "Application Created", status: "completed", actor: "Priya Singh (CO)", actorType: "human", timestamp: "2024-11-15 10:00:05" },
    { stage: "Documents Verified", status: "completed", actor: "DocParser Agent", actorType: "ai_agent", timestamp: "2024-11-15 10:08:30", notes: "3 quality warnings" },
    { stage: "Analysis Complete", status: "completed", actor: "Multiple Agents", actorType: "ai_agent", timestamp: "2024-11-15 10:35:15", notes: "Multiple critical flags" },
    { stage: "Risk Scored", status: "completed", actor: "Risk Scoring Agent", actorType: "ai_agent", timestamp: "2024-11-15 10:35:15", notes: "Score: 28 — Critical Risk" },
    { stage: "CAM Generated", status: "completed", actor: "CAM Generator Agent", actorType: "ai_agent", timestamp: "2024-11-15 10:42:05", notes: "Decision: REJECT" },
    { stage: "Reviewer Approved", status: "completed", actor: "Priya Singh (CO)", actorType: "human", timestamp: "2024-11-15 11:30:00", notes: "Rejection confirmed" },
    { stage: "Sanctioning Authority", status: "completed", actor: "Sanjay Verma (CRO)", actorType: "human", timestamp: "2024-11-15 12:15:00", notes: "STR to be filed" },
    { stage: "FIU Escalation", status: "in_progress", actor: "Compliance Team", actorType: "human", notes: "STR filing in progress" },
  ],
  compliance: [
    { regulation: "RBI Digital Lending Directions 2025", status: "compliant", details: "Full audit trail maintained for rejected application." },
    { regulation: "MCA Audit Trail Mandate (Apr 2023)", status: "compliant", details: "All AI decisions and human reviews logged." },
    { regulation: "RBI IT Governance Master Direction", status: "compliant", details: "Auto-escalation to FIU triggered per policy." },
    { regulation: "KYC/AML Compliance", status: "non_compliant", details: "🔴 Applicant flagged: Director disqualified, NPA links, shell entities." },
    { regulation: "CERSAI Registration", status: "partial", details: "Not applicable — application rejected." },
  ],
};

const conditionalAudit: AuditTrailDataset = {
  events: [
    { id: "E001", timestamp: "2024-11-15 11:00:08", actor: "Deepak Kumar (CO)", actorType: "human", actionType: "initiation", module: "Document Upload", description: "Application initiated", details: "Loan: ₹12Cr Capex Expansion for GreenField Agro Solutions Ltd" },
    { id: "E002", timestamp: "2024-11-15 11:06:30", actor: "DocParser Agent", actorType: "ai_agent", actionType: "data_extraction", module: "Agent Progress", description: "Document parsing complete", details: "6/6 documents parsed. 298 data points extracted.", confidence: 94, dataSources: ["Annual Reports", "Bank Statements", "GST Returns", "ITR", "Audited Financials", "MoA"] },
    { id: "E003", timestamp: "2024-11-15 11:12:15", actor: "FinSpread Agent", actorType: "ai_agent", actionType: "analysis", module: "Financial Spreads", description: "Financial spreading complete", details: "⚠️ FY24 shows margin compression. EBITDA margin dropped from 12% to 8%. FCF negative due to capex.", confidence: 91, dataSources: ["Audited Financials FY22-24"] },
    { id: "E004", timestamp: "2024-11-15 11:16:40", actor: "GST Verify Agent", actorType: "ai_agent", actionType: "verification", module: "Risk Analytics", description: "GST verification — minor concerns", details: "⚠️ Filing delays in 2 quarters. No suspect ITC. GSTR mismatch within 5% tolerance.", confidence: 89 },
    { id: "E005", timestamp: "2024-11-15 11:20:55", actor: "Bank Statement Agent", actorType: "ai_agent", actionType: "analysis", module: "Bank Analytics", description: "Bank statement analysis — caution", details: "⚠️ ABB declining 5 months (₹1.72Cr → ₹1.18Cr). Seasonal pattern + capex drain. Bounce ratio 3.8%. Score: 58.", confidence: 87, dataSources: ["12-month bank statements via AA"] },
    { id: "E006", timestamp: "2024-11-15 11:25:10", actor: "Promoter Intel Agent", actorType: "ai_agent", actionType: "analysis", module: "Promoter Intel", description: "Promoter intelligence — medium risk", details: "⚠️ 1 MCA flag (delayed filings). CIBIL: 698 (below ideal). 0 NPA links. 1 watchlist director.", confidence: 90 },
    { id: "E007", timestamp: "2024-11-15 11:28:30", actor: "Risk Scoring Agent", actorType: "ai_agent", actionType: "decision", module: "Risk Analytics", description: "Risk score computed", details: "Score: 61/100. Category: MEDIUM RISK. Default Prob 12M: 8.4%. RECOMMEND CONDITIONAL.", confidence: 88 },
    { id: "E008", timestamp: "2024-11-15 11:32:00", actor: "CAM Generator Agent", actorType: "ai_agent", actionType: "decision", module: "CAM Report", description: "CAM report generated", details: "Decision: CONDITIONAL. 5 conditions recommended.", confidence: 86 },
    { id: "E009", timestamp: "2024-11-15 13:00:00", actor: "Deepak Kumar (CO)", actorType: "human", actionType: "modification", module: "CAM Report", description: "Credit Officer modified loan terms", previousValue: "Rate: 12.5%, Tenure: 5yr", newValue: "Rate: 13.0%, Tenure: 4yr", details: "Increased rate by 50bps and shortened tenure due to margin concerns." },
    { id: "E010", timestamp: "2024-11-15 13:30:00", actor: "Meera Iyer (AVP Credit)", actorType: "human", actionType: "decision", module: "Approval Workflow", description: "Sanctioning authority — conditional approval", details: "Approved with enhanced monitoring. Quarterly review mandated." },
  ],
  overrides: [
    {
      id: "OVR001",
      timestamp: "2024-11-15 13:00:00",
      officer: "Deepak Kumar (CO)",
      originalRecommendation: "Rate: 12.5%, Tenure: 5 years",
      overriddenTo: "Rate: 13.0%, Tenure: 4 years",
      reason: "FY24 margin compression and declining ABB warrant tighter terms. Shorter tenure reduces exposure window.",
      approvedBy: "Meera Iyer (AVP Credit)",
      flaggedForReview: false,
    },
  ],
  workflow: [
    { stage: "Application Created", status: "completed", actor: "Deepak Kumar (CO)", actorType: "human", timestamp: "2024-11-15 11:00:08" },
    { stage: "Documents Verified", status: "completed", actor: "DocParser Agent", actorType: "ai_agent", timestamp: "2024-11-15 11:06:30" },
    { stage: "Analysis Complete", status: "completed", actor: "Multiple Agents", actorType: "ai_agent", timestamp: "2024-11-15 11:28:30", notes: "Caution flags in financials and bank analytics" },
    { stage: "Risk Scored", status: "completed", actor: "Risk Scoring Agent", actorType: "ai_agent", timestamp: "2024-11-15 11:28:30", notes: "Score: 61 — Medium Risk" },
    { stage: "CAM Generated", status: "completed", actor: "CAM Generator Agent", actorType: "ai_agent", timestamp: "2024-11-15 11:32:00", notes: "Decision: CONDITIONAL" },
    { stage: "Reviewer Modified", status: "completed", actor: "Deepak Kumar (CO)", actorType: "human", timestamp: "2024-11-15 13:00:00", notes: "Loan terms modified (rate +50bps, tenure -1yr)" },
    { stage: "Sanctioning Authority", status: "completed", actor: "Meera Iyer (AVP Credit)", actorType: "human", timestamp: "2024-11-15 13:30:00", notes: "Conditional approval with quarterly review" },
    { stage: "Disbursement", status: "pending", notes: "Pending condition fulfillment" },
  ],
  compliance: [
    { regulation: "RBI Digital Lending Directions 2025", status: "compliant", details: "Full audit trail maintained. Human override logged." },
    { regulation: "MCA Audit Trail Mandate (Apr 2023)", status: "compliant", details: "Previous and new values captured for all modifications." },
    { regulation: "RBI IT Governance Master Direction", status: "compliant", details: "System logs maintained. Override reason documented." },
    { regulation: "KYC/AML Compliance", status: "partial", details: "⚠️ Director DIN annual filing delayed — pending verification." },
    { regulation: "CERSAI Registration", status: "compliant", details: "Proposed collateral clear of existing charges." },
  ],
};

export function getAuditTrailData(id: DatasetId): AuditTrailDataset {
  switch (id) {
    case "approve": return approveAudit;
    case "fraud": return fraudAudit;
    case "conditional": return conditionalAudit;
  }
}
