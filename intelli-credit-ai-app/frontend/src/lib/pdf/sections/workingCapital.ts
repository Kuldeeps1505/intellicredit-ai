import { PdfCtx, sectionHeader, drawTable, drawText, drawKeyValue, drawWrappedText, checkPage, colors } from "../pdfHelpers";
import { FacilityDataset } from "../../facilityData";

function fmt(n: number): string {
  return n < 0 ? `(${Math.abs(n).toLocaleString("en-IN")})` : n.toLocaleString("en-IN");
}

export function drawWorkingCapital(ctx: PdfCtx, sectionNum: number, facility: FacilityDataset) {
  sectionHeader(ctx, sectionNum, "Working Capital Assessment");

  const wc = facility.workingCapital;
  const colW = [ctx.contentW * 0.36, ctx.contentW * 0.16, ctx.contentW * 0.16, ctx.contentW * 0.16, ctx.contentW * 0.16];

  // Current Assets
  checkPage(ctx, 30);
  drawText(ctx, "CURRENT ASSETS (Rs. Lakhs)", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  const caRows = wc.currentAssets.map((a) => [a.item, fmt(a.fy22), fmt(a.fy23), fmt(a.fy24), fmt(a.projected)]);
  const caTotal = wc.currentAssets.reduce((s, a) => ({
    fy22: s.fy22 + a.fy22, fy23: s.fy23 + a.fy23, fy24: s.fy24 + a.fy24, projected: s.projected + a.projected,
  }), { fy22: 0, fy23: 0, fy24: 0, projected: 0 });
  caRows.push(["Total Current Assets", fmt(caTotal.fy22), fmt(caTotal.fy23), fmt(caTotal.fy24), fmt(caTotal.projected)]);
  const caColors = [...wc.currentAssets.map(() => null), colors.primary] as ([number, number, number] | null)[];
  drawTable(ctx, ["Particulars", "FY 2022", "FY 2023", "FY 2024", "Projected"], caRows, { colWidths: colW, rowColors: caColors });

  // Current Liabilities
  checkPage(ctx, 30);
  drawText(ctx, "CURRENT LIABILITIES (Rs. Lakhs)", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  const clRows = wc.currentLiabilities.map((l) => [l.item, fmt(l.fy22), fmt(l.fy23), fmt(l.fy24), fmt(l.projected)]);
  const clTotal = wc.currentLiabilities.reduce((s, l) => ({
    fy22: s.fy22 + l.fy22, fy23: s.fy23 + l.fy23, fy24: s.fy24 + l.fy24, projected: s.projected + l.projected,
  }), { fy22: 0, fy23: 0, fy24: 0, projected: 0 });
  clRows.push(["Total Current Liabilities", fmt(clTotal.fy22), fmt(clTotal.fy23), fmt(clTotal.fy24), fmt(clTotal.projected)]);
  const clColors = [...wc.currentLiabilities.map(() => null), colors.primary] as ([number, number, number] | null)[];
  drawTable(ctx, ["Particulars", "FY 2022", "FY 2023", "FY 2024", "Projected"], clRows, { colWidths: colW, rowColors: clColors });

  // Net Working Capital
  checkPage(ctx, 30);
  drawKeyValue(ctx, [
    ["Net Working Capital FY22", `Rs.${fmt(wc.netWorkingCapital.fy22)} Lakhs`],
    ["Net Working Capital FY23", `Rs.${fmt(wc.netWorkingCapital.fy23)} Lakhs`],
    ["Net Working Capital FY24", `Rs.${fmt(wc.netWorkingCapital.fy24)} Lakhs`],
    ["Projected NWC", `Rs.${fmt(wc.netWorkingCapital.projected)} Lakhs`],
  ]);

  // MPBF Assessment
  checkPage(ctx, 30);
  drawText(ctx, "MAXIMUM PERMISSIBLE BANK FINANCE (MPBF)", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  drawKeyValue(ctx, [
    ["Method", wc.mpbf.method],
    ["MPBF Amount", wc.mpbf.amount],
    ["Drawing Power", wc.drawingPower],
    ["Assessed Bank Finance", wc.assessedBankFinance],
  ], { valueColor: wc.mpbf.amount === "NOT ASSESSABLE" ? colors.danger : colors.text });
  drawWrappedText(ctx, wc.mpbf.details);
}

export function drawSensitivityAnalysis(ctx: PdfCtx, sectionNum: number, facility: FacilityDataset) {
  sectionHeader(ctx, sectionNum, "Sensitivity / Stress Analysis");

  checkPage(ctx, 30);
  drawText(ctx, "DSCR & ICR UNDER STRESS SCENARIOS", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;

  const colW = [ctx.contentW * 0.30, ctx.contentW * 0.20, ctx.contentW * 0.15, ctx.contentW * 0.15, ctx.contentW * 0.20];
  const rows = facility.sensitivityAnalysis.map((s) => [
    s.parameter, s.change, s.revisedDSCR.toFixed(2) + "x", s.revisedICR.toFixed(2) + "x", s.impact,
  ]);
  const rowColors = facility.sensitivityAnalysis.map((s) =>
    s.impact === "Comfortable" ? colors.safe :
    s.impact === "Marginal" ? colors.warning :
    s.impact === "Stressed" ? [200, 90, 30] as [number, number, number] :
    colors.danger
  );
  drawTable(ctx, ["Scenario", "Change", "Revised DSCR", "Revised ICR", "Impact"], rows, { colWidths: colW, rowColors });
}
