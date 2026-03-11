import { DatasetId } from "./demoData";

export interface Director {
  name: string;
  din: string;
  designation: string;
  age: number;
  experience: string;
  linkedEntities: number;
  npaLinks: number;
  shellLinks: number;
  riskLevel: "clean" | "watchlist" | "flagged";
  cibilScore: number;
  netWorth: string;
}

export interface NetworkNode {
  id: string;
  label: string;
  type: "director" | "company" | "shell" | "npa" | "related";
  risk: "clean" | "warning" | "danger";
}

export interface NetworkEdge {
  from: string;
  to: string;
  label: string;
  suspicious: boolean;
}

export interface LitigationCase {
  date: string;
  court: string;
  caseType: string;
  status: "pending" | "disposed" | "settled";
  amount: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low";
}

export interface NewsItem {
  date: string;
  source: string;
  headline: string;
  sentiment: "positive" | "negative" | "neutral";
  relevance: number;
}

export interface PromoterDataset {
  directors: Director[];
  networkNodes: NetworkNode[];
  networkEdges: NetworkEdge[];
  litigation: LitigationCase[];
  news: NewsItem[];
  overallPromoterRisk: "low" | "medium" | "high" | "critical";
  mca21Flags: string[];
}

const approvePromoter: PromoterDataset = {
  overallPromoterRisk: "low",
  mca21Flags: [],
  directors: [
    { name: "Rajesh Mehta", din: "00123456", designation: "Managing Director", age: 52, experience: "28 years in textiles", linkedEntities: 3, npaLinks: 0, shellLinks: 0, riskLevel: "clean", cibilScore: 812, netWorth: "₹42Cr" },
    { name: "Priya Mehta", din: "00123457", designation: "Whole-Time Director", age: 48, experience: "22 years in operations", linkedEntities: 2, npaLinks: 0, shellLinks: 0, riskLevel: "clean", cibilScore: 798, netWorth: "₹28Cr" },
    { name: "Anand Sharma", din: "00234568", designation: "Independent Director", age: 61, experience: "35 years in banking", linkedEntities: 5, npaLinks: 0, shellLinks: 0, riskLevel: "clean", cibilScore: 835, netWorth: "₹18Cr" },
  ],
  networkNodes: [
    { id: "d1", label: "Rajesh Mehta", type: "director", risk: "clean" },
    { id: "d2", label: "Priya Mehta", type: "director", risk: "clean" },
    { id: "d3", label: "Anand Sharma", type: "director", risk: "clean" },
    { id: "c1", label: "Reliance Textiles", type: "company", risk: "clean" },
    { id: "c2", label: "Mehta Holdings", type: "related", risk: "clean" },
    { id: "c3", label: "RT Exports LLP", type: "related", risk: "clean" },
  ],
  networkEdges: [
    { from: "d1", to: "c1", label: "MD", suspicious: false },
    { from: "d2", to: "c1", label: "WTD", suspicious: false },
    { from: "d3", to: "c1", label: "ID", suspicious: false },
    { from: "d1", to: "c2", label: "Director", suspicious: false },
    { from: "d1", to: "c3", label: "Partner", suspicious: false },
  ],
  litigation: [
    { date: "2022-03", court: "NCLT Mumbai", caseType: "Commercial Dispute", status: "disposed", amount: "₹2.1Cr", description: "Payment dispute with supplier — settled amicably", severity: "low" },
  ],
  news: [
    { date: "2024-11", source: "Economic Times", headline: "Reliance Textiles wins ₹120Cr export order from H&M", sentiment: "positive", relevance: 95 },
    { date: "2024-09", source: "Business Standard", headline: "Gujarat textile sector sees 15% growth in H1 FY25", sentiment: "positive", relevance: 72 },
    { date: "2024-07", source: "Mint", headline: "Rajesh Mehta elected President of Gujarat Textile Association", sentiment: "positive", relevance: 88 },
    { date: "2024-04", source: "Financial Express", headline: "Textile exports rebound after two quarters of decline", sentiment: "neutral", relevance: 60 },
  ],
};

const fraudPromoter: PromoterDataset = {
  overallPromoterRisk: "critical",
  mca21Flags: [
    "DIN 00234567 linked to 2 NPA entities (loan defaults > ₹50Cr)",
    "Shell company Starline Impex (incorporated 2019, zero employees, ₹500Cr turnover)",
    "Director disqualified under Section 164(2) in 2021 — still active on board",
    "Common registered address with 14 other entities at same premises",
    "Circular trading pattern detected between Sunrise → Zenith → Golden → Sunrise",
  ],
  directors: [
    { name: "Vikram Gupta", din: "00234567", designation: "Managing Director", age: 44, experience: "15 years in trading", linkedEntities: 12, npaLinks: 2, shellLinks: 1, riskLevel: "flagged", cibilScore: 542, netWorth: "₹3.2Cr" },
    { name: "Sanjay Mittal", din: "00345678", designation: "Director", age: 39, experience: "10 years", linkedEntities: 8, npaLinks: 1, shellLinks: 2, riskLevel: "flagged", cibilScore: 498, netWorth: "₹1.8Cr" },
    { name: "Rekha Devi", din: "00456789", designation: "Director", age: 65, experience: "Unknown", linkedEntities: 4, npaLinks: 0, shellLinks: 1, riskLevel: "watchlist", cibilScore: 610, netWorth: "₹0.4Cr" },
  ],
  networkNodes: [
    { id: "d1", label: "Vikram Gupta", type: "director", risk: "danger" },
    { id: "d2", label: "Sanjay Mittal", type: "director", risk: "danger" },
    { id: "d3", label: "Rekha Devi", type: "director", risk: "warning" },
    { id: "c1", label: "Sunrise Exports", type: "company", risk: "danger" },
    { id: "c2", label: "Zenith Trading Co", type: "shell", risk: "danger" },
    { id: "c3", label: "Golden Exports Ltd", type: "shell", risk: "danger" },
    { id: "c4", label: "Starline Impex", type: "shell", risk: "danger" },
    { id: "c5", label: "NPA Entity 1", type: "npa", risk: "danger" },
    { id: "c6", label: "NPA Entity 2", type: "npa", risk: "danger" },
    { id: "c7", label: "Mittal Infra Pvt", type: "related", risk: "warning" },
  ],
  networkEdges: [
    { from: "d1", to: "c1", label: "MD", suspicious: false },
    { from: "d2", to: "c1", label: "Dir", suspicious: false },
    { from: "d3", to: "c1", label: "Dir", suspicious: false },
    { from: "d1", to: "c2", label: "Beneficial Owner", suspicious: true },
    { from: "d2", to: "c3", label: "Director", suspicious: true },
    { from: "d2", to: "c4", label: "Director", suspicious: true },
    { from: "d1", to: "c5", label: "Ex-Director", suspicious: true },
    { from: "d1", to: "c6", label: "Guarantor", suspicious: true },
    { from: "d2", to: "c7", label: "Director", suspicious: false },
    { from: "c1", to: "c2", label: "Circular Trade", suspicious: true },
    { from: "c2", to: "c3", label: "Circular Trade", suspicious: true },
    { from: "c3", to: "c1", label: "Circular Trade", suspicious: true },
  ],
  litigation: [
    { date: "2024-08", court: "NCLT Delhi", caseType: "Insolvency", status: "pending", amount: "₹18.5Cr", description: "Insolvency petition filed by Punjab National Bank for loan default", severity: "critical" },
    { date: "2024-03", court: "Delhi High Court", caseType: "Fraud", status: "pending", amount: "₹12Cr", description: "GST fraud investigation — Directorate General of GST Intelligence", severity: "critical" },
    { date: "2023-11", court: "SAT Mumbai", caseType: "SEBI Violation", status: "pending", amount: "₹5.2Cr", description: "Insider trading allegations in related listed entity", severity: "high" },
    { date: "2023-06", court: "CBI Special Court", caseType: "Bank Fraud", status: "pending", amount: "₹32Cr", description: "FIR registered for diversion of bank funds via shell entities", severity: "critical" },
    { date: "2022-09", court: "NCLT Delhi", caseType: "Oppression", status: "disposed", amount: "₹3.8Cr", description: "Minority shareholder oppression case — disposed", severity: "medium" },
  ],
  news: [
    { date: "2024-10", source: "NDTV", headline: "ED raids premises of Sunrise Exports in ₹200Cr money laundering probe", sentiment: "negative", relevance: 98 },
    { date: "2024-08", source: "Economic Times", headline: "Vikram Gupta named in CBI chargesheet for bank fraud", sentiment: "negative", relevance: 97 },
    { date: "2024-06", source: "Business Standard", headline: "GST dept detects ₹50Cr fake ITC network involving Delhi traders", sentiment: "negative", relevance: 90 },
    { date: "2024-04", source: "Mint", headline: "Shell company crackdown: MCA strikes off 14,000 entities", sentiment: "negative", relevance: 75 },
    { date: "2024-01", source: "Hindustan Times", headline: "Banking fraud cases surge 40% in FY24: RBI data", sentiment: "neutral", relevance: 55 },
  ],
};

const conditionalPromoter: PromoterDataset = {
  overallPromoterRisk: "medium",
  mca21Flags: [
    "Director DIN 00567890 has delayed annual filing for 2 consecutive years",
  ],
  directors: [
    { name: "Karthik Reddy", din: "00567890", designation: "Managing Director", age: 46, experience: "20 years in agri-business", linkedEntities: 5, npaLinks: 0, shellLinks: 0, riskLevel: "watchlist", cibilScore: 698, netWorth: "₹12Cr" },
    { name: "Lakshmi Reddy", din: "00567891", designation: "Director", age: 42, experience: "15 years in finance", linkedEntities: 3, npaLinks: 0, shellLinks: 0, riskLevel: "clean", cibilScore: 745, netWorth: "₹8Cr" },
  ],
  networkNodes: [
    { id: "d1", label: "Karthik Reddy", type: "director", risk: "warning" },
    { id: "d2", label: "Lakshmi Reddy", type: "director", risk: "clean" },
    { id: "c1", label: "GreenField Agro", type: "company", risk: "warning" },
    { id: "c2", label: "Reddy Farms LLP", type: "related", risk: "clean" },
    { id: "c3", label: "KR Agri Exports", type: "related", risk: "clean" },
    { id: "c4", label: "AgriCorp India", type: "related", risk: "warning" },
  ],
  networkEdges: [
    { from: "d1", to: "c1", label: "MD", suspicious: false },
    { from: "d2", to: "c1", label: "Dir", suspicious: false },
    { from: "d1", to: "c2", label: "Partner", suspicious: false },
    { from: "d1", to: "c3", label: "Director", suspicious: false },
    { from: "c1", to: "c4", label: "Major Buyer (18.5%)", suspicious: false },
  ],
  litigation: [
    { date: "2023-12", court: "NCLAT Chennai", caseType: "Appeal", status: "pending", amount: "₹4.5Cr", description: "Appeal against supplier arbitration award", severity: "medium" },
    { date: "2023-05", court: "District Court Bangalore", caseType: "Civil", status: "settled", amount: "₹1.2Cr", description: "Land dispute for proposed factory site — settled", severity: "low" },
  ],
  news: [
    { date: "2024-10", source: "The Hindu", headline: "GreenField Agro expands cold chain infrastructure in Karnataka", sentiment: "positive", relevance: 85 },
    { date: "2024-07", source: "Economic Times", headline: "Agri-processing sector faces margin pressure from raw material costs", sentiment: "negative", relevance: 78 },
    { date: "2024-05", source: "Business Line", headline: "Karnataka agri exports grow 8% but profitability concerns linger", sentiment: "neutral", relevance: 70 },
  ],
};

export function getPromoterData(id: DatasetId): PromoterDataset {
  switch (id) {
    case "approve": return approvePromoter;
    case "fraud": return fraudPromoter;
    case "conditional": return conditionalPromoter;
  }
}
