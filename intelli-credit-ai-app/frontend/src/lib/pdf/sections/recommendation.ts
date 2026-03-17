import { PdfCtx, sectionHeader, drawText, drawKeyValue, drawWrappedText, checkPage, colors, decisionColor } from "../pdfHelpers";
import { CamDataset } from "../../camData";

export function drawRecommendation(ctx: PdfCtx, cam: CamDataset, sectionNum: number = 8) {
  // Narrative sections
  sectionHeader(ctx, sectionNum, "Credit Assessment Narrative");
  cam.sections.forEach((section, i) => {
    checkPage(ctx, 20);
    drawText(ctx, `${i + 1}. ${section.title}`, ctx.margin + 4, ctx.y, { size: 7.5, color: colors.text, style: "bold" });
    ctx.y += 5;
    drawWrappedText(ctx, section.content);
    ctx.y += 2;
  });

  // Recommendation
  sectionHeader(ctx, sectionNum + 1, "Recommendation & Decision");
  const dColor = decisionColor[cam.recommendation.decision];
  ctx.doc.setFillColor(...dColor);
  ctx.doc.roundedRect(ctx.margin, ctx.y - 2, ctx.contentW, 8, 1.5, 1.5, "F");
  drawText(ctx, cam.recommendation.decision.toUpperCase() === "REJECT" ? "REJECTED" : cam.recommendation.decision.toUpperCase() === "APPROVE" ? "APPROVED" : "CONDITIONAL APPROVAL",
    ctx.pageW / 2, ctx.y + 3.5, { size: 10, color: colors.white, style: "bold", align: "center" });
  ctx.y += 12;

  drawWrappedText(ctx, cam.recommendation.summary, { color: colors.text, size: 8 });

  // Conditions
  checkPage(ctx, 30);
  const condTitle = cam.recommendation.decision === "reject" ? "REQUIRED ACTIONS" : "CONDITIONS & COVENANTS";
  drawText(ctx, condTitle, ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  cam.recommendation.conditions.forEach((cond) => {
    checkPage(ctx, 5);
    drawText(ctx, `-> ${cond}`, ctx.margin + 6, ctx.y, { size: 6.5, color: colors.muted });
    ctx.y += 4.5;
  });
  ctx.y += 4;

  // Loan Terms
  sectionHeader(ctx, sectionNum + 2, "Proposed Loan Terms");
  const terms = cam.recommendation.loanTerms;
  drawKeyValue(ctx, [
    ["Facility Amount", terms.amount],
    ["Tenure", terms.tenure],
    ["Interest Rate", terms.rate],
    ["Security / Collateral", terms.security],
    ["Disbursement", terms.disbursement],
  ], { valueColor: terms.amount === "NOT APPLICABLE" ? colors.danger : colors.text });

  // Counterfactuals
  if (cam.counterfactuals.length > 0) {
    sectionHeader(ctx, sectionNum + 3, "Path to Approval — What-If Analysis");
    cam.counterfactuals.forEach((cf) => {
      checkPage(ctx, 18);
      ctx.doc.setFillColor(...colors.cardBg);
      ctx.doc.roundedRect(ctx.margin, ctx.y - 2, ctx.contentW, 12, 1, 1, "F");
      drawText(ctx, cf.action, ctx.margin + 4, ctx.y + 2, { size: 7, color: colors.text });
      drawText(ctx, cf.impact, ctx.margin + 4, ctx.y + 7, { size: 6, color: colors.muted });
      const sc = cf.newScore >= 75 ? colors.safe : cf.newScore >= 60 ? colors.warning : colors.danger;
      drawText(ctx, `New Score: ${cf.newScore}`, ctx.pageW - ctx.margin - 40, ctx.y + 2, { size: 7.5, color: sc, style: "bold" });
      drawText(ctx, `${cf.difficulty.toUpperCase()} - ${cf.timeframe}`, ctx.pageW - ctx.margin - 40, ctx.y + 7, { size: 6, color: colors.muted });
      ctx.y += 15;
    });
  }
}
