import { PdfCtx, sectionHeader, drawTable, drawText, drawKeyValue, checkPage, colors, severityColor, statusColor } from "../pdfHelpers";
import { RiskDataset } from "../../riskData";

export function drawRiskAssessment(ctx: PdfCtx, risk: RiskDataset, sectionNum: number = 5) {
  sectionHeader(ctx, sectionNum, "Risk Assessment");

  const scoreColor = risk.score >= 70 ? colors.safe : risk.score >= 50 ? colors.warning : colors.danger;
  drawKeyValue(ctx, [
    ["Risk Score", `${risk.score} / 100`],
    ["Risk Category", risk.riskCategory],
    ["Probability of Default (12M)", `${risk.defaultProb12m}%`],
    ["Probability of Default (24M)", `${risk.defaultProb24m}%`],
  ], { valueColor: scoreColor });

  // 5Cs Assessment
  checkPage(ctx, 30);
  drawText(ctx, "5Cs CREDIT ASSESSMENT", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  const fiveColW = [ctx.contentW * 0.35, ctx.contentW * 0.25, ctx.contentW * 0.40];
  const fiveRows = risk.fiveCs.map((c) => {
    const rating = c.value >= 75 ? "STRONG" : c.value >= 50 ? "ADEQUATE" : "WEAK";
    return [c.subject, `${c.value} / ${c.fullMark}`, rating];
  });
  const fiveColors = risk.fiveCs.map((c) => c.value >= 75 ? colors.safe : c.value >= 50 ? colors.warning : colors.danger);
  drawTable(ctx, ["Dimension", "Score", "Rating"], fiveRows, { colWidths: fiveColW, rowColors: fiveColors });

  // Risk Flags
  if (risk.riskFlags.length > 0) {
    checkPage(ctx, 30);
    drawText(ctx, "RISK FLAGS", ctx.margin + 4, ctx.y, { size: 7, color: colors.danger, style: "bold" });
    ctx.y += 5;
    const rfColW = [ctx.contentW * 0.14, ctx.contentW * 0.10, ctx.contentW * 0.50, ctx.contentW * 0.14, ctx.contentW * 0.12];
    const rfRows = risk.riskFlags.map((f) => [f.type, f.severity.toUpperCase(), f.description.substring(0, 70) + (f.description.length > 70 ? "..." : ""), f.detectedBy.substring(0, 18), f.status.toUpperCase()]);
    const rfColors = risk.riskFlags.map((f) => severityColor(f.severity));
    drawTable(ctx, ["Type", "Severity", "Description", "Detected By", "Status"], rfRows, { colWidths: rfColW, rowColors: rfColors });
  }

  // Buyer Concentration
  checkPage(ctx, 30);
  drawText(ctx, "BUYER CONCENTRATION ANALYSIS", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  drawKeyValue(ctx, [["Top 3 Concentration", `${risk.topThreeConcentration}%`]], {
    valueColor: risk.topThreeConcentration > 60 ? colors.danger : risk.topThreeConcentration > 40 ? colors.warning : colors.safe,
  });
  const bcColW = [ctx.contentW * 0.30, ctx.contentW * 0.25, ctx.contentW * 0.20, ctx.contentW * 0.25];
  drawTable(ctx, ["Buyer", "GSTIN", "Share %", "Risk"],
    risk.buyerConcentration.map((b) => [b.name, b.gstin, `${b.percentage}%`, b.risk.toUpperCase()]),
    { colWidths: bcColW, rowColors: risk.buyerConcentration.map((b) => b.risk === "high" ? colors.danger : b.risk === "medium" ? colors.warning : null) }
  );
}
