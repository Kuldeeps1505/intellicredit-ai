import { DatasetId } from "./demoData";

export interface BankingFacility {
  bank: string;
  facilityType: "Fund Based" | "Non-Fund Based";
  nature: string;
  sanctionedLimit: string;
  outstanding: string;
  security: string;
  rateOfInterest: string;
  repaymentStatus: "Regular" | "Irregular" | "NPA" | "SMA-0" | "SMA-1" | "SMA-2";
}

export interface WorkingCapitalAssessment {
  currentAssets: { item: string; fy22: number; fy23: number; fy24: number; projected: number }[];
  currentLiabilities: { item: string; fy22: number; fy23: number; fy24: number; projected: number }[];
  netWorkingCapital: { fy22: number; fy23: number; fy24: number; projected: number };
  mpbf: { method: string; amount: string; details: string };
  drawingPower: string;
  assessedBankFinance: string;
}

export interface SensitivityScenario {
  parameter: string;
  change: string;
  revisedDSCR: number;
  revisedICR: number;
  impact: "Comfortable" | "Marginal" | "Stressed" | "Default";
}

export interface FacilityDataset {
  existingFacilities: BankingFacility[];
  proposedFacilities: BankingFacility[];
  totalExistingFundBased: string;
  totalExistingNonFundBased: string;
  totalProposedFundBased: string;
  totalProposedNonFundBased: string;
  workingCapital: WorkingCapitalAssessment;
  sensitivityAnalysis: SensitivityScenario[];
}

const approveFacility: FacilityDataset = {
  totalExistingFundBased: "₹32.00 Cr",
  totalExistingNonFundBased: "₹8.00 Cr",
  totalProposedFundBased: "₹45.00 Cr",
  totalProposedNonFundBased: "₹10.00 Cr",
  existingFacilities: [
    { bank: "HDFC Bank", facilityType: "Fund Based", nature: "Cash Credit", sanctionedLimit: "₹20.00 Cr", outstanding: "₹16.80 Cr", security: "Hypothecation of Stock & Debtors", rateOfInterest: "EBLR + 1.75%", repaymentStatus: "Regular" },
    { bank: "SBI", facilityType: "Fund Based", nature: "Term Loan", sanctionedLimit: "₹12.00 Cr", outstanding: "₹7.20 Cr", security: "EM of Factory Property", rateOfInterest: "EBLR + 1.50%", repaymentStatus: "Regular" },
    { bank: "HDFC Bank", facilityType: "Non-Fund Based", nature: "Letter of Credit", sanctionedLimit: "₹5.00 Cr", outstanding: "₹3.20 Cr", security: "Same as CC", rateOfInterest: "1.00% commission", repaymentStatus: "Regular" },
    { bank: "SBI", facilityType: "Non-Fund Based", nature: "Bank Guarantee", sanctionedLimit: "₹3.00 Cr", outstanding: "₹1.50 Cr", security: "Counter Guarantee + FD", rateOfInterest: "1.50% commission", repaymentStatus: "Regular" },
  ],
  proposedFacilities: [
    { bank: "Proposed Bank", facilityType: "Fund Based", nature: "Cash Credit (Enhanced)", sanctionedLimit: "₹30.00 Cr", outstanding: "—", security: "Hypothecation of Stock & Debtors + EM of Factory", rateOfInterest: "EBLR + 1.50%", repaymentStatus: "Regular" },
    { bank: "Proposed Bank", facilityType: "Fund Based", nature: "Term Loan", sanctionedLimit: "₹15.00 Cr", outstanding: "—", security: "EM of Factory Property at GIDC Sachin", rateOfInterest: "EBLR + 1.50%", repaymentStatus: "Regular" },
    { bank: "Proposed Bank", facilityType: "Non-Fund Based", nature: "Letter of Credit", sanctionedLimit: "₹7.00 Cr", outstanding: "—", security: "Same as CC limits", rateOfInterest: "0.80% commission", repaymentStatus: "Regular" },
    { bank: "Proposed Bank", facilityType: "Non-Fund Based", nature: "Bank Guarantee", sanctionedLimit: "₹3.00 Cr", outstanding: "—", security: "Counter Guarantee", rateOfInterest: "1.25% commission", repaymentStatus: "Regular" },
  ],
  workingCapital: {
    currentAssets: [
      { item: "Inventory / Stock", fy22: 5700, fy23: 5976, fy24: 5625, projected: 6200 },
      { item: "Sundry Debtors", fy22: 4275, fy23: 4648, fy24: 4875, projected: 5200 },
      { item: "Cash & Bank", fy22: 1850, fy23: 2400, fy24: 3200, projected: 3500 },
      { item: "Other Current Assets", fy22: 855, fy23: 996, fy24: 1125, projected: 1300 },
    ],
    currentLiabilities: [
      { item: "Sundry Creditors", fy22: 3420, fy23: 3652, fy24: 3750, projected: 4100 },
      { item: "Short-term Borrowings", fy22: 4275, fy23: 3984, fy24: 3375, projected: 3000 },
      { item: "Other Current Liabilities", fy22: 1140, fy23: 1162, fy24: 1125, projected: 1200 },
    ],
    netWorkingCapital: { fy22: 3845, fy23: 5222, fy24: 6575, projected: 7900 },
    mpbf: { method: "Turnover Method (Nayak Committee)", amount: "₹9,375 Lakhs", details: "25% of projected turnover of ₹37,500 Lakhs = ₹9,375 Lakhs. Borrower's margin @ 5% = ₹1,875 Lakhs. MPBF = ₹7,500 Lakhs." },
    drawingPower: "₹8,200 Lakhs (based on stock + debtors less margin)",
    assessedBankFinance: "₹7,500 Lakhs",
  },
  sensitivityAnalysis: [
    { parameter: "Revenue decline 10%", change: "-10% revenue", revisedDSCR: 1.62, revisedICR: 3.80, impact: "Comfortable" },
    { parameter: "Raw material cost +15%", change: "+15% COGS", revisedDSCR: 1.38, revisedICR: 3.10, impact: "Comfortable" },
    { parameter: "Interest rate +200bps", change: "+2% interest", revisedDSCR: 1.72, revisedICR: 3.50, impact: "Comfortable" },
    { parameter: "Combined stress", change: "All above", revisedDSCR: 1.12, revisedICR: 2.30, impact: "Marginal" },
  ],
};

const fraudFacility: FacilityDataset = {
  totalExistingFundBased: "₹18.75 Cr",
  totalExistingNonFundBased: "₹5.50 Cr",
  totalProposedFundBased: "₹22.50 Cr",
  totalProposedNonFundBased: "₹5.00 Cr",
  existingFacilities: [
    { bank: "PNB", facilityType: "Fund Based", nature: "Cash Credit", sanctionedLimit: "₹10.00 Cr", outstanding: "₹9.85 Cr", security: "Hypothecation of Stock & Debtors", rateOfInterest: "EBLR + 2.50%", repaymentStatus: "SMA-2" },
    { bank: "ICICI Bank", facilityType: "Fund Based", nature: "OD Facility", sanctionedLimit: "₹5.00 Cr", outstanding: "₹4.90 Cr", security: "FD Lien + Property EM", rateOfInterest: "EBLR + 2.25%", repaymentStatus: "SMA-1" },
    { bank: "Bajaj Finance", facilityType: "Fund Based", nature: "Term Loan", sanctionedLimit: "₹3.75 Cr", outstanding: "₹3.20 Cr", security: "Vehicle Hypothecation", rateOfInterest: "16.50% Fixed", repaymentStatus: "Irregular" },
    { bank: "PNB", facilityType: "Non-Fund Based", nature: "Letter of Credit", sanctionedLimit: "₹3.50 Cr", outstanding: "₹3.50 Cr", security: "Same as CC", rateOfInterest: "1.50% commission", repaymentStatus: "Irregular" },
    { bank: "ICICI Bank", facilityType: "Non-Fund Based", nature: "Bank Guarantee", sanctionedLimit: "₹2.00 Cr", outstanding: "₹2.00 Cr", security: "Counter Guarantee + FD", rateOfInterest: "2.00% commission", repaymentStatus: "Regular" },
  ],
  proposedFacilities: [
    { bank: "Proposed Bank", facilityType: "Fund Based", nature: "Term Loan", sanctionedLimit: "₹22.50 Cr", outstanding: "—", security: "Property at Karol Bagh (disputed)", rateOfInterest: "EBLR + 2.50%", repaymentStatus: "Regular" },
    { bank: "Proposed Bank", facilityType: "Non-Fund Based", nature: "Letter of Credit", sanctionedLimit: "₹5.00 Cr", outstanding: "—", security: "Same as Term Loan", rateOfInterest: "1.25% commission", repaymentStatus: "Regular" },
  ],
  workingCapital: {
    currentAssets: [
      { item: "Inventory / Stock", fy22: 2730, fy23: 8500, fy24: 10400, projected: 12000 },
      { item: "Sundry Debtors", fy22: 3640, fy23: 12750, fy24: 18200, projected: 22000 },
      { item: "Cash & Bank", fy22: 920, fy23: 425, fy24: 260, projected: 200 },
      { item: "Other Current Assets", fy22: 546, fy23: 2125, fy24: 3640, projected: 4500 },
    ],
    currentLiabilities: [
      { item: "Sundry Creditors", fy22: 2730, fy23: 8925, fy24: 12480, projected: 15000 },
      { item: "Short-term Borrowings", fy22: 2184, fy23: 7650, fy24: 11440, projected: 14000 },
      { item: "Other Current Liabilities", fy22: 364, fy23: 850, fy24: 1560, projected: 2000 },
    ],
    netWorkingCapital: { fy22: 2558, fy23: 6375, fy24: 7020, projected: 7700 },
    mpbf: { method: "Turnover Method (Nayak Committee)", amount: "NOT ASSESSABLE", details: "Revenue legitimacy under question due to circular trading. Projected turnover cannot be relied upon. MPBF assessment suspended." },
    drawingPower: "NOT ASSESSABLE — Stock & debtors unverifiable",
    assessedBankFinance: "NIL — Application rejected",
  },
  sensitivityAnalysis: [
    { parameter: "Base case (as reported)", change: "No change", revisedDSCR: 0.18, revisedICR: 0.14, impact: "Default" },
    { parameter: "Revenue increase 20%", change: "+20% revenue", revisedDSCR: 0.32, revisedICR: 0.25, impact: "Default" },
    { parameter: "Cost reduction 15%", change: "-15% opex", revisedDSCR: 0.45, revisedICR: 0.38, impact: "Default" },
    { parameter: "Debt restructuring", change: "50% haircut", revisedDSCR: 0.68, revisedICR: 0.52, impact: "Stressed" },
  ],
};

const conditionalFacility: FacilityDataset = {
  totalExistingFundBased: "₹8.50 Cr",
  totalExistingNonFundBased: "₹2.00 Cr",
  totalProposedFundBased: "₹8.00 Cr",
  totalProposedNonFundBased: "₹2.00 Cr",
  existingFacilities: [
    { bank: "Canara Bank", facilityType: "Fund Based", nature: "Cash Credit", sanctionedLimit: "₹5.00 Cr", outstanding: "₹4.20 Cr", security: "Hypothecation of Stock & Debtors", rateOfInterest: "EBLR + 2.00%", repaymentStatus: "Regular" },
    { bank: "HDFC Bank", facilityType: "Fund Based", nature: "Term Loan", sanctionedLimit: "₹3.50 Cr", outstanding: "₹2.80 Cr", security: "EM of Warehouse Property", rateOfInterest: "EBLR + 2.25%", repaymentStatus: "Regular" },
    { bank: "Canara Bank", facilityType: "Non-Fund Based", nature: "Letter of Credit", sanctionedLimit: "₹2.00 Cr", outstanding: "₹1.20 Cr", security: "Same as CC", rateOfInterest: "1.25% commission", repaymentStatus: "Regular" },
  ],
  proposedFacilities: [
    { bank: "Proposed Bank", facilityType: "Fund Based", nature: "Term Loan (Capex)", sanctionedLimit: "₹8.00 Cr", outstanding: "—", security: "EM of Warehouse + Processing Unit at Hubli", rateOfInterest: "EBLR + 2.25%", repaymentStatus: "Regular" },
    { bank: "Proposed Bank", facilityType: "Non-Fund Based", nature: "Bank Guarantee", sanctionedLimit: "₹2.00 Cr", outstanding: "—", security: "Counter Guarantee + Margin Money", rateOfInterest: "1.50% commission", repaymentStatus: "Regular" },
  ],
  workingCapital: {
    currentAssets: [
      { item: "Inventory / Stock", fy22: 1700, fy23: 1960, fy24: 2244, projected: 2500 },
      { item: "Sundry Debtors", fy22: 1275, fy23: 1568, fy24: 1836, projected: 2100 },
      { item: "Cash & Bank", fy22: 680, fy23: 588, fy24: 408, projected: 500 },
      { item: "Other Current Assets", fy22: 340, fy23: 392, fy24: 408, projected: 450 },
    ],
    currentLiabilities: [
      { item: "Sundry Creditors", fy22: 1020, fy23: 1176, fy24: 1326, projected: 1500 },
      { item: "Short-term Borrowings", fy22: 1275, fy23: 1568, fy24: 2040, projected: 1800 },
      { item: "Other Current Liabilities", fy22: 340, fy23: 392, fy24: 510, projected: 550 },
    ],
    netWorkingCapital: { fy22: 1360, fy23: 1372, fy24: 1020, projected: 1700 },
    mpbf: { method: "Turnover Method (Nayak Committee)", amount: "₹2,550 Lakhs", details: "25% of projected turnover of ₹10,200 Lakhs = ₹2,550 Lakhs. Borrower's margin @ 5% = ₹510 Lakhs. MPBF = ₹2,040 Lakhs." },
    drawingPower: "₹2,200 Lakhs (based on stock + debtors less margin)",
    assessedBankFinance: "₹2,040 Lakhs",
  },
  sensitivityAnalysis: [
    { parameter: "Revenue decline 10%", change: "-10% revenue", revisedDSCR: 0.95, revisedICR: 1.90, impact: "Stressed" },
    { parameter: "Raw material cost +15%", change: "+15% COGS", revisedDSCR: 0.82, revisedICR: 1.55, impact: "Stressed" },
    { parameter: "Interest rate +200bps", change: "+2% interest", revisedDSCR: 1.05, revisedICR: 2.00, impact: "Marginal" },
    { parameter: "Combined stress", change: "All above", revisedDSCR: 0.52, revisedICR: 1.10, impact: "Default" },
  ],
};

export function getFacilityData(id: DatasetId): FacilityDataset {
  switch (id) {
    case "approve": return approveFacility;
    case "fraud": return fraudFacility;
    case "conditional": return conditionalFacility;
  }
}
