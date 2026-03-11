import { DatasetId } from "./demoData";

export interface CamSection {
  title: string;
  content: string;
}

export interface Recommendation {
  decision: "approve" | "reject" | "conditional";
  summary: string;
  conditions: string[];
  loanTerms: {
    amount: string;
    tenure: string;
    rate: string;
    security: string;
    disbursement: string;
  };
}

export interface CounterfactualAction {
  action: string;
  impact: string;
  newScore: number;
  scoreImpact: number; // additive points when toggled on
  difficulty: "easy" | "medium" | "hard";
  timeframe: string;
}

export interface CamDataset {
  generatedAt: string;
  sections: CamSection[];
  recommendation: Recommendation;
  counterfactuals: CounterfactualAction[];
  keyMetrics: { label: string; value: string; status: "good" | "warning" | "danger" }[];
}

const approveCam: CamDataset = {
  generatedAt: "2024-11-15 14:32 IST",
  keyMetrics: [
    { label: "Risk Score", value: "81 / 100", status: "good" },
    { label: "CIBIL Score", value: "812", status: "good" },
    { label: "D/E Ratio", value: "1.15x", status: "good" },
    { label: "DSCR", value: "1.95x", status: "good" },
    { label: "Current Ratio", value: "1.82x", status: "good" },
    { label: "Revenue Growth", value: "+12.9%", status: "good" },
  ],
  sections: [
    { title: "Executive Summary", content: "Reliance Textiles Pvt Ltd is a well-established textile manufacturing entity based in Surat, Gujarat, with 28+ years of operations under the leadership of Mr. Rajesh Mehta. The company has demonstrated consistent growth with revenue CAGR of 11.2% over the past 3 years and improving profitability metrics. The loan request of ₹45Cr for working capital is well within the company's servicing capacity (DSCR 1.95x) and is adequately secured by factory property valued at ₹62Cr." },
    { title: "Business Overview", content: "The company operates in the textiles & apparel sector with a diversified buyer base across domestic and international markets. Key customers include Arvind Mills, Raymond Ltd, and Welspun India. The top-3 buyer concentration at 34.7% is within acceptable limits. The company holds a strong position in the Gujarat textile ecosystem and was recently awarded a ₹120Cr export order from H&M." },
    { title: "Financial Analysis", content: "All key financial ratios are within healthy benchmarks. EBITDA margins have improved from 14.2% to 18.4% over three years, reflecting operational efficiency gains. The D/E ratio has reduced from 1.8x to 1.15x, indicating disciplined deleveraging. Net profit margin stands at 8.2%, and PAT grew 20.4% YoY to ₹9.87Cr. Working capital management has improved with working capital days reducing from 78 to 62." },
    { title: "Promoter Assessment", content: "The promoter group has clean backgrounds with no NPA linkages, no disqualifications, and excellent CIBIL scores (812 for MD). Mr. Rajesh Mehta's experience of 28 years in the textile industry and his position as President of the Gujarat Textile Association add credibility. No adverse litigation or news sentiments identified." },
    { title: "Collateral Assessment", content: "Primary security: Factory premises at Plot 42, GIDC Sachin, Surat, valued at ₹62Cr (market value) / ₹48Cr (forced sale value). Clear title confirmed with no existing encumbrances. Coverage ratio: 1.38x on market value, 1.07x on FSV. Additional security: Personal guarantee of directors with combined net worth of ₹88Cr." },
    { title: "Risk Mitigation", content: "Minor working capital fluctuation in Q3 was seasonal and within normal textile industry patterns. GST compliance is clean with zero suspect ITC. No circular trading patterns or related party concerns identified. The company maintains adequate insurance coverage and has a diversified supplier base." },
  ],
  recommendation: {
    decision: "approve",
    summary: "Recommended for APPROVAL. The borrower demonstrates strong financials, clean promoter background, adequate collateral coverage, and a robust business model. All due diligence checks have been satisfactorily completed.",
    conditions: [
      "Standard documentation and security creation",
      "Quarterly financial reporting",
      "Maintain D/E ratio below 1.5x",
      "Insurance endorsement in favor of lender",
    ],
    loanTerms: {
      amount: "₹45,00,00,000",
      tenure: "12 months (renewable)",
      rate: "EBLR + 1.50% (effective ~10.35%)",
      security: "Factory property at GIDC Sachin (₹62Cr market value) + Personal Guarantee",
      disbursement: "Full disbursement upon security creation",
    },
  },
  counterfactuals: [],
};

const fraudCam: CamDataset = {
  generatedAt: "2024-11-15 14:32 IST",
  keyMetrics: [
    { label: "Risk Score", value: "28 / 100", status: "danger" },
    { label: "CIBIL Score", value: "542", status: "danger" },
    { label: "D/E Ratio", value: "2.80x", status: "danger" },
    { label: "DSCR", value: "0.65x", status: "danger" },
    { label: "Current Ratio", value: "0.78x", status: "danger" },
    { label: "Revenue Growth", value: "-8.4%", status: "danger" },
  ],
  sections: [
    { title: "Executive Summary", content: "Sunrise Exports International presents an extremely high-risk profile with multiple critical red flags across all assessment dimensions. The company shows signs of systematic fraud including circular trading patterns via shell entities, ITC overclaims of ₹12.9Cr, and promoter linkages to 2 NPA entities. The CBI has registered an FIR for diversion of bank funds. This application is recommended for IMMEDIATE REJECTION." },
    { title: "Business Overview", content: "The company claims to operate in import/export trading from a registered address in Karol Bagh, Delhi. However, field verification found no operational activity at the premises — the address is a shared office space housing 14 other registered entities. The declared inventory of ₹15Cr could not be verified. Top-3 buyer concentration at 68.4% is dangerously high, with the primary buyer (Zenith Trading Co at 32.1%) identified as a suspected shell entity." },
    { title: "Financial Analysis", content: "Financial performance has deteriorated sharply across all metrics. Revenue contracted 8.4% YoY, EBITDA margin collapsed from 12.1% to 6.2%, and the company reported a net loss of ₹4.73Cr. The D/E ratio at 2.8x far exceeds sector benchmarks, and DSCR at 0.65x indicates inability to service existing debt. Working capital days have ballooned from 68 to 142, suggesting fictitious receivables or inventory." },
    { title: "Promoter Assessment", content: "CRITICAL: MD Vikram Gupta (DIN 00234567) is linked to 2 prior NPA entities and 1 shell company. Director Sanjay Mittal is linked to 2 shell entities. A director has been disqualified under Section 164(2) but continues on the board illegally. ED raids were conducted in October 2024, and a CBI chargesheet has been filed. Promoter CIBIL scores are in the 498-610 range." },
    { title: "Fraud Indicators", content: "Multiple fraud indicators confirmed: (1) Circular trading pattern: Sunrise → Zenith → Golden → Sunrise. (2) GSTR-2A vs 3B variance exceeding 40% with ₹12.9Cr suspect ITC. (3) Shell company linkages with zero-employee entities reporting ₹500Cr turnover. (4) ED money laundering probe and CBI FIR for bank fraud. (5) Fictitious operational claims — no activity at registered address." },
    { title: "Collateral Assessment", content: "The proposed collateral property has existing charges by SBI and disputed ownership. Property access was denied for independent valuation. Title search revealed multiple encumbrances. The collateral is deemed INADEQUATE and UNRELIABLE." },
  ],
  recommendation: {
    decision: "reject",
    summary: "Recommended for IMMEDIATE REJECTION. Multiple confirmed fraud indicators, regulatory investigations, and promoter disqualifications make this application ineligible for any form of credit facility. A Suspicious Transaction Report (STR) should be filed with FIU-IND.",
    conditions: [
      "File STR with FIU-IND within 7 days",
      "Report to CRILC as 'Rejected on Credit Grounds'",
      "Add promoters to internal caution list",
      "Share intelligence with fraud investigation unit",
    ],
    loanTerms: {
      amount: "NOT APPLICABLE",
      tenure: "NOT APPLICABLE",
      rate: "NOT APPLICABLE",
      security: "NOT APPLICABLE",
      disbursement: "NOT APPLICABLE",
    },
  },
  counterfactuals: [],
};

const conditionalCam: CamDataset = {
  generatedAt: "2024-11-15 14:32 IST",
  keyMetrics: [
    { label: "Risk Score", value: "61 / 100", status: "warning" },
    { label: "CIBIL Score", value: "698", status: "warning" },
    { label: "D/E Ratio", value: "1.85x", status: "warning" },
    { label: "DSCR", value: "1.25x", status: "warning" },
    { label: "Current Ratio", value: "1.25x", status: "good" },
    { label: "Revenue Growth", value: "+5.2%", status: "warning" },
  ],
  sections: [
    { title: "Executive Summary", content: "GreenField Agro Solutions Ltd is a medium-risk borrower in the agri-processing sector with a viable business but several areas requiring strengthening. The company has demonstrated operational capability but faces margin pressure, rising leverage, and decelerating growth. With appropriate conditions and enhanced monitoring, the exposure can be considered within a reduced facility amount." },
    { title: "Business Overview", content: "The company operates in agri-processing with a focus on cold chain infrastructure in Karnataka. Recent expansion of cold storage facilities is positive but has contributed to increased leverage. The top-3 buyer concentration at 42.1% is moderate but the primary buyer AgriCorp India at 18.5% warrants monitoring. The sector faces margin pressure from rising raw material costs." },
    { title: "Financial Analysis", content: "Financial metrics show a declining trend but remain within serviceable range. EBITDA margin has dropped from 14.5% to 12.1% over three years. D/E ratio at 1.85x is approaching the sector threshold of 2.0x. DSCR at 1.25x provides thin but adequate coverage. Revenue growth has decelerated from 12.1% to 5.2%. Working capital days have increased from 65 to 85, requiring attention." },
    { title: "Promoter Assessment", content: "MD Karthik Reddy has 20 years of experience in agri-business with no NPA linkages. However, annual filings have been delayed for 2 consecutive years, indicating governance concerns. CIBIL score of 698 is fair but below preferred threshold. No criminal litigation or regulatory issues identified." },
    { title: "Collateral Assessment", content: "Proposed security: Warehouse and processing unit at Hubli, Karnataka, valued at ₹18Cr (market) / ₹14Cr (forced sale). Existing charge by HDFC Bank to be cleared with NOC. Coverage ratio on FSV: 1.17x — marginal. Additional personal guarantee of directors with combined net worth of ₹20Cr." },
    { title: "Conditions for Approval", content: "The credit facility can be approved subject to: (1) Reduction of facility from ₹12Cr to ₹8Cr to improve coverage ratios. (2) Additional collateral or top-up margin to achieve 1.5x FSV coverage. (3) Completion of pending due diligence items (title search, trade references). (4) Rectification of delayed MCA filings. (5) Quarterly monitoring with financial covenants." },
  ],
  recommendation: {
    decision: "conditional",
    summary: "Recommended for CONDITIONAL APPROVAL with reduced facility of ₹8Cr (from requested ₹12Cr) subject to completion of pending verifications and adherence to enhanced covenants. The borrower shows potential but requires closer monitoring.",
    conditions: [
      "Reduce facility to ₹8Cr (from ₹12Cr requested)",
      "Obtain HDFC Bank NOC and clear existing charge",
      "Complete pending title search and trade reference verification",
      "Rectify delayed MCA annual filings within 60 days",
      "Quarterly financial reporting with covenant monitoring",
      "Maintain D/E ratio below 2.0x at all times",
      "DSCR covenant: minimum 1.2x, tested quarterly",
      "Additional collateral or margin money of ₹2Cr",
    ],
    loanTerms: {
      amount: "₹8,00,00,000 (reduced from ₹12,00,00,000)",
      tenure: "12 months (renewable subject to review)",
      rate: "EBLR + 2.25% (effective ~11.10%)",
      security: "Warehouse at Hubli (₹18Cr MV) + PG of Directors + ₹2Cr margin money",
      disbursement: "Phased — 50% on security creation, 50% after covenant compliance review",
    },
  },
  counterfactuals: [
    { action: "Reduce D/E from 1.85x to 1.5x by repaying ₹3Cr term debt", impact: "Risk score improves by ~8 points, removes leverage flag", newScore: 69, scoreImpact: 8, difficulty: "medium", timeframe: "6 months" },
    { action: "Improve DSCR from 1.25x to 1.5x through cost optimization", impact: "Moves from marginal to comfortable servicing capacity", newScore: 72, scoreImpact: 11, difficulty: "hard", timeframe: "9 months" },
    { action: "Diversify buyer base — reduce top-3 concentration below 35%", impact: "Removes concentration risk flag, improves stability", newScore: 67, scoreImpact: 6, difficulty: "medium", timeframe: "12 months" },
    { action: "Rectify delayed MCA filings and improve governance", impact: "Removes compliance flag, improves Character score", newScore: 65, scoreImpact: 4, difficulty: "easy", timeframe: "2 months" },
  ],
};

export function getCamData(id: DatasetId): CamDataset {
  switch (id) {
    case "approve": return approveCam;
    case "fraud": return fraudCam;
    case "conditional": return conditionalCam;
  }
}
