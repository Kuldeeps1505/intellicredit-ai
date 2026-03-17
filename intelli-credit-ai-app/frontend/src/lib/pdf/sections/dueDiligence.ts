import { PdfCtx, sectionHeader, drawTable, drawText, drawKeyValue, checkPage, colors, statusColor } from "../pdfHelpers";
import { DiligenceDataset } from "../../diligenceData";

export function drawDueDiligence(ctx: PdfCtx, diligence: DiligenceDataset, sectionNum: number = 6) {
  sectionHeader(ctx, sectionNum, "Due Diligence Summary");

  const overallColor = statusColor(diligence.overallStatus);
  drawKeyValue(ctx, [
    ["Completion", `${diligence.completionPercent}%`],
    ["Overall Status", diligence.overallStatus.toUpperCase()],
  ], { valueColor: overallColor });

  // Verification checklist
  checkPage(ctx, 30);
  drawText(ctx, "VERIFICATION CHECKLIST", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  const colW = [ctx.contentW * 0.12, ctx.contentW * 0.18, ctx.contentW * 0.10, ctx.contentW * 0.12, ctx.contentW * 0.48];
  const rows = diligence.checks.map((c) => [
    c.category,
    c.item,
    c.status.toUpperCase(),
    c.source,
    c.notes.substring(0, 65) + (c.notes.length > 65 ? "..." : ""),
  ]);
  const rowColors = diligence.checks.map((c) => statusColor(c.status));
  drawTable(ctx, ["Category", "Item", "Status", "Source", "Notes"], rows, { colWidths: colW, rowColors });

  // Field visits
  if (diligence.fieldVisits.length > 0) {
    checkPage(ctx, 30);
    drawText(ctx, "FIELD VISIT REPORT", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
    ctx.y += 5;
    diligence.fieldVisits.forEach((fv) => {
      const fvColor = statusColor(fv.rating);
      drawKeyValue(ctx, [
        ["Date", fv.date],
        ["Officer", fv.officer],
        ["Location", fv.location],
        ["Rating", fv.rating.toUpperCase()],
        ["Photos Taken", String(fv.photoCount)],
      ], { valueColor: fvColor });

      drawText(ctx, "Observations:", ctx.margin + 4, ctx.y, { size: 6.5, color: colors.muted, style: "bold" });
      ctx.y += 4;
      fv.observations.forEach((obs) => {
        checkPage(ctx, 4);
        drawText(ctx, `- ${obs}`, ctx.margin + 6, ctx.y, { size: 6.5, color: colors.muted });
        ctx.y += 4;
      });
      ctx.y += 3;
    });
  }

  // Compliance
  checkPage(ctx, 30);
  drawText(ctx, "REGULATORY COMPLIANCE", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  const compColW = [ctx.contentW * 0.25, ctx.contentW * 0.15, ctx.contentW * 0.45, ctx.contentW * 0.15];
  drawTable(ctx, ["Regulation", "Status", "Details", "Last Checked"],
    diligence.compliance.map((c) => [c.regulation, c.status.toUpperCase().replace("_", " "), c.details.substring(0, 60), c.lastChecked]),
    { colWidths: compColW, rowColors: diligence.compliance.map((c) => statusColor(c.status)) }
  );
}
