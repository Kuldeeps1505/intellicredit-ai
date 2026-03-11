import { PdfCtx, sectionHeader, drawTable, drawText, checkPage, colors } from "../pdfHelpers";
import { FinancialSpreadsDataset, LineItem } from "../../financialSpreadsData";

function formatNum(n: number): string {
  if (n === 0) return "—";
  return n < 0 ? `(${Math.abs(n).toLocaleString("en-IN")})` : n.toLocaleString("en-IN");
}

function lineItemRows(items: LineItem[]): string[][] {
  return items.map((item) => [
    (item.indent ? "  " : "") + item.label,
    formatNum(item.fy22),
    formatNum(item.fy23),
    formatNum(item.fy24),
  ]);
}

function lineItemColors(items: LineItem[]): ([number, number, number] | null)[] {
  return items.map((item) => {
    if (item.isTotal) return colors.primary;
    if (item.isSubTotal) return colors.text;
    return null;
  });
}

export function drawFinancialAnalysis(ctx: PdfCtx, spreads: FinancialSpreadsDataset, sectionNum: number = 2) {
  sectionHeader(ctx, sectionNum, "Financial Analysis — 3-Year Spreads");

  const colWidths = [ctx.contentW * 0.46, ctx.contentW * 0.18, ctx.contentW * 0.18, ctx.contentW * 0.18];

  // P&L
  checkPage(ctx, 30);
  drawText(ctx, "PROFIT & LOSS STATEMENT (Rs. Lakhs)", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  drawTable(ctx, ["Particulars", "FY 2022", "FY 2023", "FY 2024"], lineItemRows(spreads.pnl), { colWidths, rowColors: lineItemColors(spreads.pnl) });

  // Balance Sheet
  checkPage(ctx, 30);
  drawText(ctx, "BALANCE SHEET SUMMARY (Rs. Lakhs)", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  drawTable(ctx, ["Particulars", "FY 2022", "FY 2023", "FY 2024"], lineItemRows(spreads.balanceSheet), { colWidths, rowColors: lineItemColors(spreads.balanceSheet) });

  // Cash Flow
  checkPage(ctx, 30);
  drawText(ctx, "CASH FLOW STATEMENT (Rs. Lakhs)", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  drawTable(ctx, ["Particulars", "FY 2022", "FY 2023", "FY 2024"], lineItemRows(spreads.cashFlow), { colWidths, rowColors: lineItemColors(spreads.cashFlow) });

  // Key Ratios
  checkPage(ctx, 30);
  drawText(ctx, "KEY FINANCIAL RATIOS", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;

  const ratioHeaders = ["Ratio", "FY 2022", "FY 2023", "FY 2024", "Benchmark", "Status"];
  const rColW = [ctx.contentW * 0.26, ctx.contentW * 0.13, ctx.contentW * 0.13, ctx.contentW * 0.13, ctx.contentW * 0.15, ctx.contentW * 0.20];
  const ratioRows = spreads.ratios.map((r) => [
    r.name,
    `${r.fy22}${r.unit}`,
    `${r.fy23}${r.unit}`,
    `${r.fy24}${r.unit}`,
    `${r.benchmark}${r.unit}`,
    r.anomaly ? "! ANOMALY" : "[OK] NORMAL",
  ]);
  const ratioColors = spreads.ratios.map((r) => r.anomaly ? colors.danger : colors.safe);

  drawTable(ctx, ratioHeaders, ratioRows, { colWidths: rColW, rowColors: ratioColors });
}
