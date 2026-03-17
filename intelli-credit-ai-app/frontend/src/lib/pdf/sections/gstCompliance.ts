import { PdfCtx, sectionHeader, drawTable, drawText, drawKeyValue, checkPage, colors } from "../pdfHelpers";
import { RiskDataset } from "../../riskData";

export function drawGstCompliance(ctx: PdfCtx, risk: RiskDataset, sectionNum: number = 4) {
  sectionHeader(ctx, sectionNum, "GST & Tax Compliance");

  drawKeyValue(ctx, [
    ["Suspect ITC Amount", risk.suspectITC],
    ["Flagged Quarters", `${risk.gstrReconciliation.filter((q) => q.flagged).length} of ${risk.gstrReconciliation.length}`],
  ], { valueColor: risk.suspectITC === "Rs.0" || risk.suspectITC === "\u20B90" ? colors.safe : colors.danger });

  checkPage(ctx, 30);
  drawText(ctx, "GSTR RECONCILIATION (Rs. Crores)", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;

  const colW = [ctx.contentW * 0.25, ctx.contentW * 0.2, ctx.contentW * 0.2, ctx.contentW * 0.15, ctx.contentW * 0.2];
  const rows = risk.gstrReconciliation.map((q) => {
    const variance = ((q.gstr3b - q.gstr2a) / q.gstr2a * 100).toFixed(1);
    return [q.quarter, q.gstr2a.toFixed(1), q.gstr3b.toFixed(1), `${variance}%`, q.flagged ? "! FLAGGED" : "[OK]"];
  });
  const rowColors = risk.gstrReconciliation.map((q) => q.flagged ? colors.danger : colors.safe);
  drawTable(ctx, ["Quarter", "GSTR-2A", "GSTR-3B", "Variance", "Status"], rows, { colWidths: colW, rowColors });
}
