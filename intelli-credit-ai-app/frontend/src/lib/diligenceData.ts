import { DatasetId } from "./demoData";

export interface DiligenceCheck {
  id: string;
  category: string;
  item: string;
  status: "verified" | "pending" | "flagged" | "waived" | "not_applicable";
  source: string;
  verifiedBy: string;
  notes: string;
  timestamp?: string;
}

export interface FieldVisitNote {
  date: string;
  officer: string;
  location: string;
  observations: string[];
  photoCount: number;
  rating: "satisfactory" | "concerns" | "unsatisfactory";
}

export interface ComplianceItem {
  regulation: string;
  status: "compliant" | "non_compliant" | "partial" | "pending_review";
  details: string;
  lastChecked: string;
}

export interface DiligenceDataset {
  checks: DiligenceCheck[];
  fieldVisits: FieldVisitNote[];
  compliance: ComplianceItem[];
  completionPercent: number;
  overallStatus: "clear" | "concerns" | "blocked";
}

const approveDiligence: DiligenceDataset = {
  completionPercent: 96,
  overallStatus: "clear",
  checks: [
    { id: "1", category: "Identity", item: "PAN Verification", status: "verified", source: "NSDL", verifiedBy: "KYC Agent", notes: "PAN active and matches company records", timestamp: "2024-11-15" },
    { id: "2", category: "Identity", item: "GSTIN Verification", status: "verified", source: "GSTN Portal", verifiedBy: "GST Agent", notes: "Active registration, regular filer", timestamp: "2024-11-15" },
    { id: "3", category: "Identity", item: "CIN / MCA Status", status: "verified", source: "MCA21", verifiedBy: "Corp Agent", notes: "Active company, all filings up to date", timestamp: "2024-11-14" },
    { id: "4", category: "Financial", item: "3-Year Audited Financials", status: "verified", source: "Uploaded", verifiedBy: "FinSpread Agent", notes: "FY22-24 audited statements verified", timestamp: "2024-11-14" },
    { id: "5", category: "Financial", item: "Bank Statement (12M)", status: "verified", source: "AA Fetch", verifiedBy: "Bank Agent", notes: "12-month statements via Account Aggregator", timestamp: "2024-11-15" },
    { id: "6", category: "Financial", item: "ITR (3 Years)", status: "verified", source: "IT Portal", verifiedBy: "Tax Agent", notes: "ITR filed on time, no discrepancies", timestamp: "2024-11-13" },
    { id: "7", category: "Legal", item: "CIBIL / Bureau Report", status: "verified", source: "CIBIL", verifiedBy: "Credit Agent", notes: "Score: 812 — Excellent", timestamp: "2024-11-15" },
    { id: "8", category: "Legal", item: "Litigation Search", status: "verified", source: "eCourts", verifiedBy: "Legal Agent", notes: "1 disposed case, no active litigation", timestamp: "2024-11-14" },
    { id: "9", category: "Legal", item: "CERSAI Search", status: "verified", source: "CERSAI", verifiedBy: "Collateral Agent", notes: "No existing charges on proposed collateral", timestamp: "2024-11-15" },
    { id: "10", category: "Collateral", item: "Property Valuation", status: "verified", source: "Panel Valuer", verifiedBy: "Valuation Agent", notes: "Market value ₹62Cr, forced sale ₹48Cr", timestamp: "2024-11-12" },
    { id: "11", category: "Collateral", item: "Title Search", status: "verified", source: "Sub-Registrar", verifiedBy: "Legal Agent", notes: "Clear title, no encumbrances", timestamp: "2024-11-13" },
    { id: "12", category: "Operational", item: "Site Visit Completed", status: "verified", source: "Field Team", verifiedBy: "Field Officer", notes: "Factory operational, inventory verified", timestamp: "2024-11-10" },
    { id: "13", category: "Operational", item: "Trade References", status: "verified", source: "Direct Calls", verifiedBy: "Due Diligence Team", notes: "3/3 references verified — positive feedback", timestamp: "2024-11-11" },
    { id: "14", category: "Regulatory", item: "RBI Defaulter List (CRILC)", status: "verified", source: "CRILC", verifiedBy: "Compliance Agent", notes: "Not listed as SMA/NPA anywhere", timestamp: "2024-11-15" },
    { id: "15", category: "Regulatory", item: "Wilful Defaulter Check", status: "verified", source: "RBI", verifiedBy: "Compliance Agent", notes: "Clean — not a wilful defaulter", timestamp: "2024-11-15" },
  ],
  fieldVisits: [
    { date: "2024-11-10", officer: "Amit Patel", location: "Surat Factory — Plot 42, GIDC Sachin", observations: ["Factory fully operational with 200+ workers", "Modern looms and finishing equipment installed", "Raw material inventory consistent with books", "Well-maintained premises with safety compliance"], photoCount: 24, rating: "satisfactory" },
  ],
  compliance: [
    { regulation: "RBI KYC Master Direction", status: "compliant", details: "All KYC documents verified and current", lastChecked: "2024-11-15" },
    { regulation: "PMLA Compliance", status: "compliant", details: "No STR/CTR triggers identified", lastChecked: "2024-11-15" },
    { regulation: "Companies Act 2013", status: "compliant", details: "All filings current, board composition compliant", lastChecked: "2024-11-14" },
    { regulation: "GST Compliance", status: "compliant", details: "Regular filer, no discrepancies", lastChecked: "2024-11-15" },
    { regulation: "Environmental Clearance", status: "compliant", details: "Valid consent to operate till 2027", lastChecked: "2024-11-12" },
  ],
};

const fraudDiligence: DiligenceDataset = {
  completionPercent: 72,
  overallStatus: "blocked",
  checks: [
    { id: "1", category: "Identity", item: "PAN Verification", status: "verified", source: "NSDL", verifiedBy: "KYC Agent", notes: "PAN active", timestamp: "2024-11-15" },
    { id: "2", category: "Identity", item: "GSTIN Verification", status: "flagged", source: "GSTN Portal", verifiedBy: "GST Agent", notes: "⚠️ GST registration under investigation by DGGI", timestamp: "2024-11-15" },
    { id: "3", category: "Identity", item: "CIN / MCA Status", status: "flagged", source: "MCA21", verifiedBy: "Corp Agent", notes: "⚠️ Director disqualified under S.164(2), annual filings delayed", timestamp: "2024-11-14" },
    { id: "4", category: "Financial", item: "3-Year Audited Financials", status: "flagged", source: "Uploaded", verifiedBy: "FinSpread Agent", notes: "⚠️ Auditor qualified opinion on revenue recognition", timestamp: "2024-11-14" },
    { id: "5", category: "Financial", item: "Bank Statement (12M)", status: "flagged", source: "AA Fetch", verifiedBy: "Bank Agent", notes: "⚠️ Circular transactions detected between related accounts", timestamp: "2024-11-15" },
    { id: "6", category: "Financial", item: "ITR (3 Years)", status: "flagged", source: "IT Portal", verifiedBy: "Tax Agent", notes: "⚠️ Significant variance between ITR and audited financials", timestamp: "2024-11-13" },
    { id: "7", category: "Legal", item: "CIBIL / Bureau Report", status: "flagged", source: "CIBIL", verifiedBy: "Credit Agent", notes: "⚠️ Score: 542 — Poor. Multiple overdue accounts", timestamp: "2024-11-15" },
    { id: "8", category: "Legal", item: "Litigation Search", status: "flagged", source: "eCourts", verifiedBy: "Legal Agent", notes: "⚠️ 5 active cases including CBI FIR and insolvency petition", timestamp: "2024-11-14" },
    { id: "9", category: "Legal", item: "CERSAI Search", status: "flagged", source: "CERSAI", verifiedBy: "Collateral Agent", notes: "⚠️ Existing charge by SBI on proposed collateral", timestamp: "2024-11-15" },
    { id: "10", category: "Collateral", item: "Property Valuation", status: "pending", source: "Panel Valuer", verifiedBy: "—", notes: "Awaiting — property access denied by occupant", timestamp: undefined },
    { id: "11", category: "Collateral", item: "Title Search", status: "flagged", source: "Sub-Registrar", verifiedBy: "Legal Agent", notes: "⚠️ Multiple encumbrances and disputed ownership", timestamp: "2024-11-13" },
    { id: "12", category: "Operational", item: "Site Visit Completed", status: "flagged", source: "Field Team", verifiedBy: "Field Officer", notes: "⚠️ Registered address is shared office — no operations visible", timestamp: "2024-11-10" },
    { id: "13", category: "Operational", item: "Trade References", status: "flagged", source: "Direct Calls", verifiedBy: "Due Diligence Team", notes: "⚠️ 2/3 references unreachable, 1 denied relationship", timestamp: "2024-11-11" },
    { id: "14", category: "Regulatory", item: "RBI Defaulter List (CRILC)", status: "flagged", source: "CRILC", verifiedBy: "Compliance Agent", notes: "⚠️ Listed as SMA-2 with PNB, NPA with SBI", timestamp: "2024-11-15" },
    { id: "15", category: "Regulatory", item: "Wilful Defaulter Check", status: "flagged", source: "RBI", verifiedBy: "Compliance Agent", notes: "⚠️ Proceedings initiated by PNB for wilful default classification", timestamp: "2024-11-15" },
  ],
  fieldVisits: [
    { date: "2024-11-10", officer: "Suresh Kumar", location: "Registered Office — 3rd Floor, Karol Bagh, Delhi", observations: ["Shared office space with 14 other registered entities", "No signage, no employees, no operational activity", "Adjacent units confirmed no knowledge of Sunrise Exports", "Inventory claim of ₹15Cr could not be verified — no warehouse"], photoCount: 8, rating: "unsatisfactory" },
  ],
  compliance: [
    { regulation: "RBI KYC Master Direction", status: "non_compliant", details: "Director disqualification not disclosed in application", lastChecked: "2024-11-15" },
    { regulation: "PMLA Compliance", status: "non_compliant", details: "Shell company linkages trigger STR requirements", lastChecked: "2024-11-15" },
    { regulation: "Companies Act 2013", status: "non_compliant", details: "Annual filings pending, disqualified director on board", lastChecked: "2024-11-14" },
    { regulation: "GST Compliance", status: "non_compliant", details: "Under DGGI investigation for fake ITC", lastChecked: "2024-11-15" },
    { regulation: "Environmental Clearance", status: "pending_review", details: "No manufacturing operations found to assess", lastChecked: "2024-11-10" },
  ],
};

const conditionalDiligence: DiligenceDataset = {
  completionPercent: 85,
  overallStatus: "concerns",
  checks: [
    { id: "1", category: "Identity", item: "PAN Verification", status: "verified", source: "NSDL", verifiedBy: "KYC Agent", notes: "PAN active and matches", timestamp: "2024-11-15" },
    { id: "2", category: "Identity", item: "GSTIN Verification", status: "verified", source: "GSTN Portal", verifiedBy: "GST Agent", notes: "Active registration", timestamp: "2024-11-15" },
    { id: "3", category: "Identity", item: "CIN / MCA Status", status: "flagged", source: "MCA21", verifiedBy: "Corp Agent", notes: "⚠️ Annual filing delayed for 2 consecutive years", timestamp: "2024-11-14" },
    { id: "4", category: "Financial", item: "3-Year Audited Financials", status: "verified", source: "Uploaded", verifiedBy: "FinSpread Agent", notes: "FY22-24 statements received, declining margins noted", timestamp: "2024-11-14" },
    { id: "5", category: "Financial", item: "Bank Statement (12M)", status: "verified", source: "AA Fetch", verifiedBy: "Bank Agent", notes: "Statements verified, some irregular cash flows in Q3", timestamp: "2024-11-15" },
    { id: "6", category: "Financial", item: "ITR (3 Years)", status: "verified", source: "IT Portal", verifiedBy: "Tax Agent", notes: "Filed on time, minor adjustments noted", timestamp: "2024-11-13" },
    { id: "7", category: "Legal", item: "CIBIL / Bureau Report", status: "verified", source: "CIBIL", verifiedBy: "Credit Agent", notes: "Score: 698 — Fair. One restructured account", timestamp: "2024-11-15" },
    { id: "8", category: "Legal", item: "Litigation Search", status: "verified", source: "eCourts", verifiedBy: "Legal Agent", notes: "1 pending appeal, 1 settled civil case", timestamp: "2024-11-14" },
    { id: "9", category: "Legal", item: "CERSAI Search", status: "verified", source: "CERSAI", verifiedBy: "Collateral Agent", notes: "Existing charge by HDFC Bank — will be NOC'd", timestamp: "2024-11-15" },
    { id: "10", category: "Collateral", item: "Property Valuation", status: "verified", source: "Panel Valuer", verifiedBy: "Valuation Agent", notes: "Market value ₹18Cr, forced sale ₹14Cr", timestamp: "2024-11-12" },
    { id: "11", category: "Collateral", item: "Title Search", status: "pending", source: "Sub-Registrar", verifiedBy: "—", notes: "Awaiting — title opinion expected in 3 days", timestamp: undefined },
    { id: "12", category: "Operational", item: "Site Visit Completed", status: "verified", source: "Field Team", verifiedBy: "Field Officer", notes: "Operations confirmed, some underutilization observed", timestamp: "2024-11-10" },
    { id: "13", category: "Operational", item: "Trade References", status: "pending", source: "Direct Calls", verifiedBy: "—", notes: "1/3 verified — awaiting 2 more callbacks", timestamp: undefined },
    { id: "14", category: "Regulatory", item: "RBI Defaulter List (CRILC)", status: "verified", source: "CRILC", verifiedBy: "Compliance Agent", notes: "Not listed as defaulter", timestamp: "2024-11-15" },
    { id: "15", category: "Regulatory", item: "Wilful Defaulter Check", status: "verified", source: "RBI", verifiedBy: "Compliance Agent", notes: "Clean", timestamp: "2024-11-15" },
  ],
  fieldVisits: [
    { date: "2024-11-10", officer: "Deepa Nair", location: "Warehouse & Processing Unit — Hubli, Karnataka", observations: ["Processing unit operational but running at ~60% capacity", "Cold storage facility recently commissioned", "Employee count (45) lower than declared (70)", "Raw material procurement records available"], photoCount: 16, rating: "concerns" },
  ],
  compliance: [
    { regulation: "RBI KYC Master Direction", status: "compliant", details: "KYC current", lastChecked: "2024-11-15" },
    { regulation: "PMLA Compliance", status: "compliant", details: "No triggers identified", lastChecked: "2024-11-15" },
    { regulation: "Companies Act 2013", status: "partial", details: "Annual filings delayed — rectification in progress", lastChecked: "2024-11-14" },
    { regulation: "GST Compliance", status: "compliant", details: "Regular filer, minor Q3 discrepancy resolved", lastChecked: "2024-11-15" },
    { regulation: "Environmental Clearance", status: "compliant", details: "Consent to operate valid till 2026", lastChecked: "2024-11-12" },
  ],
};

export function getDiligenceData(id: DatasetId): DiligenceDataset {
  switch (id) {
    case "approve": return approveDiligence;
    case "fraud": return fraudDiligence;
    case "conditional": return conditionalDiligence;
  }
}
