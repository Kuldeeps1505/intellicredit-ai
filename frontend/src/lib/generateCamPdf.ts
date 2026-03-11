import { CamDataset } from "./camData";
import { Dataset } from "./demoData";
import { RiskDataset } from "./riskData";
import { PromoterDataset } from "./promoterData";
import { FinancialSpreadsDataset } from "./financialSpreadsData";
import { BankStatementDataset } from "./bankStatementData";
import { DiligenceDataset } from "./diligenceData";
import { FacilityDataset } from "./facilityData";

import { createCtx, fillPage, addFooters } from "./pdf/pdfHelpers";
import { drawCoverPage } from "./pdf/sections/coverPage";
import { drawTocPage, updateToc } from "./pdf/sections/tocPage";
import { drawBorrowerProfile } from "./pdf/sections/borrowerProfile";
import { drawFacilityDetails } from "./pdf/sections/facilityDetails";
import { drawFinancialAnalysis } from "./pdf/sections/financialAnalysis";
import { drawWorkingCapital, drawSensitivityAnalysis } from "./pdf/sections/workingCapital";
import { drawBankStatement } from "./pdf/sections/bankStatement";
import { drawGstCompliance } from "./pdf/sections/gstCompliance";
import { drawRiskAssessment } from "./pdf/sections/riskAssessment";
import { drawDueDiligence } from "./pdf/sections/dueDiligence";
import { drawPromoterAssessment } from "./pdf/sections/promoterAssessment";
import { drawRecommendation } from "./pdf/sections/recommendation";
import { drawDisclaimer } from "./pdf/sections/disclaimer";

export interface CamPdfData {
  camData: CamDataset;
  dataset: Dataset;
  riskData: RiskDataset;
  promoterData: PromoterDataset;
  financialData: FinancialSpreadsDataset;
  bankData: BankStatementDataset;
  diligenceData: DiligenceDataset;
  facilityData: FacilityDataset;
}

function buildPdfDoc(data: CamPdfData) {
  const ctx = createCtx();
  fillPage(ctx);

  // Page 1: Cover Page
  drawCoverPage(ctx, data.dataset, data.camData);

  // Page 2: TOC placeholder
  drawTocPage(ctx);
  const tocPageNum = ctx.doc.getNumberOfPages();

  // Start content pages (y offset for page header)
  ctx.doc.addPage();
  fillPage(ctx);
  ctx.y = ctx.margin + 6; // Extra space for page header band

  // Standard CAM Section Ordering (per RBI/SBI format):
  // 1. Borrower Profile & Company Information
  drawBorrowerProfile(ctx, data.dataset, data.promoterData);

  // 2. Existing & Proposed Banking Facilities
  drawFacilityDetails(ctx, 2, data.facilityData);

  // 3. Promoter & Management Intelligence
  drawPromoterAssessment(ctx, data.promoterData, 3);

  // 4. Financial Analysis — 3-Year Spreads
  drawFinancialAnalysis(ctx, data.financialData, 4);

  // 5. Working Capital Assessment / MPBF
  drawWorkingCapital(ctx, 5, data.facilityData);

  // 6. Bank Statement Analysis
  drawBankStatement(ctx, data.bankData, 6);

  // 7. GST & Tax Compliance
  drawGstCompliance(ctx, data.riskData, 7);

  // 8. Risk Assessment (5Cs, PD, Flags, Buyer Concentration)
  drawRiskAssessment(ctx, data.riskData, 8);

  // 9. Due Diligence Summary
  drawDueDiligence(ctx, data.diligenceData, 9);

  // 10. Sensitivity / Stress Analysis
  drawSensitivityAnalysis(ctx, 10, data.facilityData);

  // 11-13. Narrative, Recommendation, Terms, Counterfactuals
  drawRecommendation(ctx, data.camData, 11);

  // Final section: Disclaimer & Signatures
  const disclaimerNum = data.camData.counterfactuals.length > 0 ? 15 : 14;
  drawDisclaimer(ctx, disclaimerNum);

  // Update TOC with real page numbers
  updateToc(ctx, tocPageNum);

  // Page headers + footers on all pages
  addFooters(ctx, data.dataset.companyName);

  return ctx.doc;
}

export function generateCamPdf(data: CamPdfData) {
  const doc = buildPdfDoc(data);
  const filename = `CAM_Report_${data.dataset.companyName.replace(/\s+/g, "_")}_${new Date().toISOString().split("T")[0]}.pdf`;
  doc.save(filename);
}

export function generateCamPdfBlobUrl(data: CamPdfData): string {
  const doc = buildPdfDoc(data);
  const blob = doc.output("blob");
  return URL.createObjectURL(blob);
}
