import { DatasetId } from "./demoData";

export interface FiveCsData {
  subject: string;
  value: number;
  fullMark: number;
}

export interface GSTRQuarter {
  quarter: string;
  gstr2a: number;
  gstr3b: number;
  flagged: boolean;
}

export interface BuyerConcentration {
  name: string;
  gstin: string;
  percentage: number;
  risk: "high" | "medium" | "low";
}

export interface FinancialRatio {
  name: string;
  value: string;
  numericValue: number;
  unit: string;
  sparkline: number[];
  yoyChange: number; // percentage
  anomaly: boolean;
  citation: {
    document: string;
    page: number;
    method: string;
    confidence: number;
  };
}

export interface RiskFlag {
  type: string;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  detectedBy: string;
  status: "active" | "resolved" | "monitoring";
}

export interface RiskDataset {
  score: number;
  riskCategory: string;
  defaultProb12m: number;
  defaultProb24m: number;
  fiveCs: FiveCsData[];
  gstrReconciliation: GSTRQuarter[];
  suspectITC: string;
  buyerConcentration: BuyerConcentration[];
  topThreeConcentration: number;
  financialRatios: FinancialRatio[];
  riskFlags: RiskFlag[];
}

const approveData: RiskDataset = {
  score: 81,
  riskCategory: "LOW",
  defaultProb12m: 2.1,
  defaultProb24m: 4.8,
  fiveCs: [
    { subject: "Character", value: 85, fullMark: 100 },
    { subject: "Capacity", value: 78, fullMark: 100 },
    { subject: "Capital", value: 82, fullMark: 100 },
    { subject: "Collateral", value: 88, fullMark: 100 },
    { subject: "Conditions", value: 75, fullMark: 100 },
  ],
  gstrReconciliation: [
    { quarter: "Q1 FY23", gstr2a: 18.2, gstr3b: 18.5, flagged: false },
    { quarter: "Q2 FY23", gstr2a: 21.4, gstr3b: 21.8, flagged: false },
    { quarter: "Q3 FY23", gstr2a: 19.8, gstr3b: 20.1, flagged: false },
    { quarter: "Q4 FY23", gstr2a: 24.1, gstr3b: 24.3, flagged: false },
    { quarter: "Q1 FY24", gstr2a: 22.5, gstr3b: 22.9, flagged: false },
    { quarter: "Q2 FY24", gstr2a: 25.3, gstr3b: 25.6, flagged: false },
    { quarter: "Q3 FY24", gstr2a: 23.7, gstr3b: 24.0, flagged: false },
    { quarter: "Q4 FY24", gstr2a: 27.8, gstr3b: 28.1, flagged: false },
  ],
  suspectITC: "₹0",
  buyerConcentration: [
    { name: "Arvind Mills Ltd", gstin: "24AAB...1Z5", percentage: 14.2, risk: "low" },
    { name: "Raymond Ltd", gstin: "27AAC...2Z8", percentage: 11.8, risk: "low" },
    { name: "Welspun India", gstin: "24AAD...3Z1", percentage: 8.7, risk: "low" },
    { name: "Vardhman Textiles", gstin: "03AAE...4Z4", percentage: 7.1, risk: "low" },
    { name: "Others", gstin: "—", percentage: 58.2, risk: "low" },
  ],
  topThreeConcentration: 34.7,
  financialRatios: [
    { name: "Current Ratio", value: "1.82", numericValue: 1.82, unit: "x", sparkline: [1.5, 1.6, 1.7, 1.82], yoyChange: 7.1, anomaly: false, citation: { document: "Annual Report 2024", page: 42, method: "FinBERT", confidence: 97 } },
    { name: "D/E Ratio", value: "1.15", numericValue: 1.15, unit: "x", sparkline: [1.8, 1.5, 1.3, 1.15], yoyChange: -11.5, anomaly: false, citation: { document: "Annual Report 2024", page: 44, method: "FinBERT", confidence: 96 } },
    { name: "EBITDA Margin", value: "18.4", numericValue: 18.4, unit: "%", sparkline: [14.2, 15.8, 17.1, 18.4], yoyChange: 7.6, anomaly: false, citation: { document: "Annual Report 2024", page: 38, method: "FinBERT", confidence: 98 } },
    { name: "Net Profit Margin", value: "8.2", numericValue: 8.2, unit: "%", sparkline: [5.1, 6.3, 7.5, 8.2], yoyChange: 9.3, anomaly: false, citation: { document: "Annual Report 2024", page: 38, method: "FinBERT", confidence: 97 } },
    { name: "DSCR", value: "1.95", numericValue: 1.95, unit: "x", sparkline: [1.4, 1.6, 1.8, 1.95], yoyChange: 8.3, anomaly: false, citation: { document: "Annual Report 2024", page: 46, method: "FinBERT", confidence: 95 } },
    { name: "Interest Coverage", value: "4.2", numericValue: 4.2, unit: "x", sparkline: [3.1, 3.5, 3.8, 4.2], yoyChange: 10.5, anomaly: false, citation: { document: "Annual Report 2024", page: 46, method: "FinBERT", confidence: 96 } },
    { name: "Revenue Growth", value: "12.9", numericValue: 12.9, unit: "%", sparkline: [8.2, 10.1, 11.5, 12.9], yoyChange: 12.2, anomaly: false, citation: { document: "Annual Report 2024", page: 32, method: "FinBERT", confidence: 99 } },
    { name: "Asset Turnover", value: "1.35", numericValue: 1.35, unit: "x", sparkline: [1.1, 1.2, 1.28, 1.35], yoyChange: 5.5, anomaly: false, citation: { document: "Annual Report 2024", page: 48, method: "FinBERT", confidence: 94 } },
    { name: "Working Cap Days", value: "62", numericValue: 62, unit: "days", sparkline: [78, 72, 68, 62], yoyChange: -8.8, anomaly: false, citation: { document: "Annual Report 2024", page: 50, method: "FinBERT", confidence: 93 } },
    { name: "PAT", value: "9.87", numericValue: 9.87, unit: "Cr", sparkline: [5.4, 6.8, 8.2, 9.87], yoyChange: 20.4, anomaly: false, citation: { document: "Annual Report 2024", page: 36, method: "FinBERT", confidence: 98 } },
    { name: "Inventory Days", value: "45", numericValue: 45, unit: "days", sparkline: [52, 50, 48, 45], yoyChange: -6.3, anomaly: false, citation: { document: "Annual Report 2024", page: 52, method: "FinBERT", confidence: 92 } },
    { name: "ROE", value: "16.8", numericValue: 16.8, unit: "%", sparkline: [11.2, 13.5, 15.1, 16.8], yoyChange: 11.3, anomaly: false, citation: { document: "Annual Report 2024", page: 40, method: "FinBERT", confidence: 97 } },
  ],
  riskFlags: [
    { type: "Financial", severity: "low", description: "Minor working capital fluctuation in Q3", detectedBy: "FinSpread Agent", status: "monitoring" },
  ],
};

const fraudData: RiskDataset = {
  score: 28,
  riskCategory: "VERY HIGH",
  defaultProb12m: 34.2,
  defaultProb24m: 58.7,
  fiveCs: [
    { subject: "Character", value: 22, fullMark: 100 },
    { subject: "Capacity", value: 35, fullMark: 100 },
    { subject: "Capital", value: 28, fullMark: 100 },
    { subject: "Collateral", value: 40, fullMark: 100 },
    { subject: "Conditions", value: 30, fullMark: 100 },
  ],
  gstrReconciliation: [
    { quarter: "Q1 FY23", gstr2a: 8.2, gstr3b: 8.5, flagged: false },
    { quarter: "Q2 FY23", gstr2a: 9.1, gstr3b: 12.4, flagged: true },
    { quarter: "Q3 FY23", gstr2a: 7.8, gstr3b: 14.2, flagged: true },
    { quarter: "Q4 FY23", gstr2a: 10.5, gstr3b: 16.8, flagged: true },
    { quarter: "Q1 FY24", gstr2a: 11.2, gstr3b: 11.8, flagged: false },
    { quarter: "Q2 FY24", gstr2a: 9.8, gstr3b: 15.1, flagged: true },
    { quarter: "Q3 FY24", gstr2a: 8.4, gstr3b: 13.9, flagged: true },
    { quarter: "Q4 FY24", gstr2a: 12.1, gstr3b: 18.5, flagged: true },
  ],
  suspectITC: "₹12.9Cr",
  buyerConcentration: [
    { name: "Zenith Trading Co", gstin: "07ZEN...1Z2", percentage: 32.1, risk: "high" },
    { name: "Golden Exports Ltd", gstin: "07GOL...2Z5", percentage: 21.8, risk: "high" },
    { name: "Starline Impex", gstin: "07STA...3Z8", percentage: 14.5, risk: "medium" },
    { name: "Pacific Comm", gstin: "27PAC...4Z1", percentage: 8.2, risk: "low" },
    { name: "Others", gstin: "—", percentage: 23.4, risk: "low" },
  ],
  topThreeConcentration: 68.4,
  financialRatios: [
    { name: "Current Ratio", value: "0.78", numericValue: 0.78, unit: "x", sparkline: [1.2, 1.0, 0.9, 0.78], yoyChange: -13.3, anomaly: true, citation: { document: "Annual Report 2024", page: 42, method: "FinBERT", confidence: 94 } },
    { name: "D/E Ratio", value: "2.80", numericValue: 2.8, unit: "x", sparkline: [1.8, 2.1, 2.5, 2.8], yoyChange: 12.0, anomaly: true, citation: { document: "Annual Report 2024", page: 44, method: "FinBERT", confidence: 96 } },
    { name: "EBITDA Margin", value: "6.2", numericValue: 6.2, unit: "%", sparkline: [12.1, 10.4, 8.2, 6.2], yoyChange: -24.4, anomaly: true, citation: { document: "Annual Report 2024", page: 38, method: "FinBERT", confidence: 91 } },
    { name: "Net Profit Margin", value: "-2.1", numericValue: -2.1, unit: "%", sparkline: [3.2, 1.8, 0.2, -2.1], yoyChange: -1150, anomaly: true, citation: { document: "Annual Report 2024", page: 38, method: "FinBERT", confidence: 93 } },
    { name: "DSCR", value: "0.65", numericValue: 0.65, unit: "x", sparkline: [1.3, 1.1, 0.85, 0.65], yoyChange: -23.5, anomaly: true, citation: { document: "Annual Report 2024", page: 46, method: "FinBERT", confidence: 95 } },
    { name: "Interest Coverage", value: "1.1", numericValue: 1.1, unit: "x", sparkline: [2.8, 2.2, 1.6, 1.1], yoyChange: -31.3, anomaly: true, citation: { document: "Annual Report 2024", page: 46, method: "FinBERT", confidence: 94 } },
    { name: "Revenue Growth", value: "-8.4", numericValue: -8.4, unit: "%", sparkline: [15.2, 8.1, 2.3, -8.4], yoyChange: -465, anomaly: true, citation: { document: "Annual Report 2024", page: 32, method: "FinBERT", confidence: 97 } },
    { name: "Asset Turnover", value: "0.62", numericValue: 0.62, unit: "x", sparkline: [1.0, 0.85, 0.72, 0.62], yoyChange: -13.9, anomaly: true, citation: { document: "Annual Report 2024", page: 48, method: "FinBERT", confidence: 90 } },
    { name: "Working Cap Days", value: "142", numericValue: 142, unit: "days", sparkline: [68, 85, 110, 142], yoyChange: 29.1, anomaly: true, citation: { document: "Annual Report 2024", page: 50, method: "FinBERT", confidence: 88 } },
    { name: "PAT", value: "-4.73", numericValue: -4.73, unit: "Cr", sparkline: [2.1, 1.2, 0.1, -4.73], yoyChange: -4830, anomaly: true, citation: { document: "Annual Report 2024", page: 36, method: "FinBERT", confidence: 96 } },
    { name: "Inventory Days", value: "98", numericValue: 98, unit: "days", sparkline: [45, 58, 72, 98], yoyChange: 36.1, anomaly: true, citation: { document: "Annual Report 2024", page: 52, method: "FinBERT", confidence: 89 } },
    { name: "ROE", value: "-8.4", numericValue: -8.4, unit: "%", sparkline: [8.5, 4.2, 1.1, -8.4], yoyChange: -864, anomaly: true, citation: { document: "Annual Report 2024", page: 40, method: "FinBERT", confidence: 92 } },
  ],
  riskFlags: [
    { type: "GST Fraud", severity: "critical", description: "ITC overclaim of ₹12.9Cr detected across Q2-Q4 FY24. GSTR-2A vs 3B variance exceeds 40%.", detectedBy: "GSTR Reconciliation Engine", status: "active" },
    { type: "Buyer Concentration", severity: "critical", description: "Top 3 buyers constitute 68.4% of revenue. Zenith Trading Co alone is 32.1%.", detectedBy: "Buyer Concentration Engine", status: "active" },
    { type: "Fraud Network", severity: "critical", description: "Director DIN 00234567 linked to 2 prior NPA entities and 1 shell company.", detectedBy: "Promoter Intel Agent", status: "active" },
    { type: "Liquidity Crisis", severity: "high", description: "Current ratio below 1.0x indicates severe liquidity stress. Working capital days at 142.", detectedBy: "FinSpread Agent", status: "active" },
    { type: "Debt Overload", severity: "high", description: "D/E ratio at 2.8x far exceeds sector benchmark of 1.5x.", detectedBy: "FinSpread Agent", status: "active" },
    { type: "Revenue Decline", severity: "high", description: "Revenue contracted 8.4% YoY despite sector growing at 12%. Market share erosion evident.", detectedBy: "FinSpread Agent", status: "active" },
    { type: "Servicing Risk", severity: "high", description: "DSCR at 0.65x — borrower cannot service existing debt obligations.", detectedBy: "Risk Score Agent", status: "active" },
    { type: "Negative Profitability", severity: "medium", description: "Net loss of ₹4.73Cr in FY24. Three consecutive quarters of losses.", detectedBy: "FinSpread Agent", status: "monitoring" },
  ],
};

const conditionalData: RiskDataset = {
  score: 61,
  riskCategory: "MEDIUM",
  defaultProb12m: 8.4,
  defaultProb24m: 15.2,
  fiveCs: [
    { subject: "Character", value: 70, fullMark: 100 },
    { subject: "Capacity", value: 58, fullMark: 100 },
    { subject: "Capital", value: 55, fullMark: 100 },
    { subject: "Collateral", value: 65, fullMark: 100 },
    { subject: "Conditions", value: 62, fullMark: 100 },
  ],
  gstrReconciliation: [
    { quarter: "Q1 FY23", gstr2a: 5.2, gstr3b: 5.4, flagged: false },
    { quarter: "Q2 FY23", gstr2a: 6.1, gstr3b: 6.3, flagged: false },
    { quarter: "Q3 FY23", gstr2a: 5.8, gstr3b: 7.0, flagged: true },
    { quarter: "Q4 FY23", gstr2a: 7.2, gstr3b: 7.5, flagged: false },
    { quarter: "Q1 FY24", gstr2a: 6.8, gstr3b: 7.1, flagged: false },
    { quarter: "Q2 FY24", gstr2a: 7.5, gstr3b: 7.8, flagged: false },
    { quarter: "Q3 FY24", gstr2a: 6.9, gstr3b: 7.2, flagged: false },
    { quarter: "Q4 FY24", gstr2a: 8.1, gstr3b: 8.4, flagged: false },
  ],
  suspectITC: "₹1.2Cr",
  buyerConcentration: [
    { name: "AgriCorp India", gstin: "29AGR...1Z8", percentage: 18.5, risk: "medium" },
    { name: "FarmFresh Exports", gstin: "29FAR...2Z1", percentage: 14.2, risk: "low" },
    { name: "NaturePure Ltd", gstin: "29NAT...3Z4", percentage: 9.4, risk: "low" },
    { name: "Organic Valley", gstin: "29ORG...4Z7", percentage: 7.8, risk: "low" },
    { name: "Others", gstin: "—", percentage: 50.1, risk: "low" },
  ],
  topThreeConcentration: 42.1,
  financialRatios: [
    { name: "Current Ratio", value: "1.25", numericValue: 1.25, unit: "x", sparkline: [1.4, 1.35, 1.3, 1.25], yoyChange: -3.8, anomaly: false, citation: { document: "Annual Report 2024", page: 42, method: "FinBERT", confidence: 96 } },
    { name: "D/E Ratio", value: "1.85", numericValue: 1.85, unit: "x", sparkline: [1.4, 1.55, 1.7, 1.85], yoyChange: 8.8, anomaly: true, citation: { document: "Annual Report 2024", page: 44, method: "FinBERT", confidence: 95 } },
    { name: "EBITDA Margin", value: "12.1", numericValue: 12.1, unit: "%", sparkline: [14.5, 13.8, 12.8, 12.1], yoyChange: -5.5, anomaly: false, citation: { document: "Annual Report 2024", page: 38, method: "FinBERT", confidence: 97 } },
    { name: "Net Profit Margin", value: "4.8", numericValue: 4.8, unit: "%", sparkline: [6.2, 5.8, 5.2, 4.8], yoyChange: -7.7, anomaly: false, citation: { document: "Annual Report 2024", page: 38, method: "FinBERT", confidence: 96 } },
    { name: "DSCR", value: "1.25", numericValue: 1.25, unit: "x", sparkline: [1.5, 1.4, 1.32, 1.25], yoyChange: -5.3, anomaly: false, citation: { document: "Annual Report 2024", page: 46, method: "FinBERT", confidence: 94 } },
    { name: "Interest Coverage", value: "2.4", numericValue: 2.4, unit: "x", sparkline: [3.2, 2.9, 2.6, 2.4], yoyChange: -7.7, anomaly: false, citation: { document: "Annual Report 2024", page: 46, method: "FinBERT", confidence: 95 } },
    { name: "Revenue Growth", value: "5.2", numericValue: 5.2, unit: "%", sparkline: [12.1, 9.5, 7.2, 5.2], yoyChange: -27.8, anomaly: false, citation: { document: "Annual Report 2024", page: 32, method: "FinBERT", confidence: 98 } },
    { name: "Asset Turnover", value: "0.95", numericValue: 0.95, unit: "x", sparkline: [1.1, 1.05, 1.0, 0.95], yoyChange: -5.0, anomaly: false, citation: { document: "Annual Report 2024", page: 48, method: "FinBERT", confidence: 93 } },
    { name: "Working Cap Days", value: "85", numericValue: 85, unit: "days", sparkline: [65, 72, 78, 85], yoyChange: 9.0, anomaly: false, citation: { document: "Annual Report 2024", page: 50, method: "FinBERT", confidence: 91 } },
    { name: "PAT", value: "5.76", numericValue: 5.76, unit: "Cr", sparkline: [7.4, 6.8, 6.2, 5.76], yoyChange: -7.1, anomaly: false, citation: { document: "Annual Report 2024", page: 36, method: "FinBERT", confidence: 97 } },
    { name: "Inventory Days", value: "72", numericValue: 72, unit: "days", sparkline: [55, 60, 65, 72], yoyChange: 10.8, anomaly: false, citation: { document: "Annual Report 2024", page: 52, method: "FinBERT", confidence: 90 } },
    { name: "ROE", value: "10.2", numericValue: 10.2, unit: "%", sparkline: [14.5, 12.8, 11.5, 10.2], yoyChange: -11.3, anomaly: false, citation: { document: "Annual Report 2024", page: 40, method: "FinBERT", confidence: 96 } },
  ],
  riskFlags: [
    { type: "Leverage", severity: "high", description: "D/E ratio at 1.85x approaching sector threshold of 2.0x.", detectedBy: "FinSpread Agent", status: "active" },
    { type: "GST Discrepancy", severity: "medium", description: "Minor ITC discrepancy of ₹1.2Cr in Q3 FY23 — within tolerance but flagged.", detectedBy: "GSTR Reconciliation Engine", status: "monitoring" },
    { type: "Concentration", severity: "medium", description: "Top 3 buyers = 42.1% revenue — moderate concentration risk.", detectedBy: "Buyer Concentration Engine", status: "monitoring" },
    { type: "Growth Slowdown", severity: "medium", description: "Revenue growth decelerating from 12.1% to 5.2% over 3 years.", detectedBy: "FinSpread Agent", status: "monitoring" },
  ],
};

export function getRiskData(datasetId: DatasetId): RiskDataset {
  switch (datasetId) {
    case "approve": return approveData;
    case "fraud": return fraudData;
    case "conditional": return conditionalData;
  }
}
