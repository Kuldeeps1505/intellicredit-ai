import { PdfCtx, sectionHeader, drawKeyValue, drawTable, drawText, checkPage, colors, severityColor } from "../pdfHelpers";
import { BankStatementDataset } from "../../bankStatementData";

export function drawBankStatement(ctx: PdfCtx, bs: BankStatementDataset, sectionNum: number = 3) {
  sectionHeader(ctx, sectionNum, "Bank Statement Analysis (12 Months)");

  const s = bs.summary;
  drawKeyValue(ctx, [
    ["Average Bank Balance (ABB)", `Rs.${s.abb} Lakhs`],
    ["Avg Monthly Credits", `Rs.${s.avgMonthlyCredits} Lakhs`],
    ["Avg Monthly Debits", `Rs.${s.avgMonthlyDebits} Lakhs`],
    ["Credit/Debit Ratio", `${s.creditDebitRatio}x`],
    ["EMI Obligations", `Rs.${s.emiObligations} Lakhs/month (${s.emiCount} EMIs)`],
    ["Bounce Ratio", `${s.bounceRatio}% (${s.totalBounces} bounces)`],
    ["Cash Withdrawal %", `${s.cashWithdrawalPercent}%`],
    ["Behavior Score", `${s.behaviorScore} / 100`],
  ], { valueColor: s.behaviorScore >= 70 ? colors.safe : s.behaviorScore >= 50 ? colors.warning : colors.danger });

  // Monthly cash flow table
  checkPage(ctx, 30);
  drawText(ctx, "MONTHLY CASH FLOW (Rs. Lakhs)", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  const colW = [ctx.contentW * 0.2, ctx.contentW * 0.25, ctx.contentW * 0.25, ctx.contentW * 0.30];
  drawTable(ctx, ["Month", "Credits", "Debits", "Closing Balance"],
    bs.monthlyCashFlow.map((m) => [m.month, String(m.credits), String(m.debits), String(m.closing)]),
    { colWidths: colW }
  );

  // Red Flags
  checkPage(ctx, 30);
  drawText(ctx, "RED FLAG ANALYSIS", ctx.margin + 4, ctx.y, { size: 7, color: colors.danger, style: "bold" });
  ctx.y += 5;
  const flagHeaders = ["Red Flag", "Severity", "Status", "Details"];
  const fColW = [ctx.contentW * 0.22, ctx.contentW * 0.12, ctx.contentW * 0.10, ctx.contentW * 0.56];
  const flagRows = bs.redFlags.map((f) => [
    f.type,
    f.severity.toUpperCase(),
    f.detected ? "DETECTED" : "CLEAR",
    f.detected && f.details ? f.details.substring(0, 80) + (f.details.length > 80 ? "..." : "") : "—",
  ]);
  const flagRowColors = bs.redFlags.map((f) => f.detected ? severityColor(f.severity) : colors.safe);
  drawTable(ctx, flagHeaders, flagRows, { colWidths: fColW, rowColors: flagRowColors });

  // Top counterparties
  checkPage(ctx, 30);
  drawText(ctx, "TOP COUNTERPARTIES", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  const cpHeaders = ["Counterparty", "Credits (Rs.L)", "Debits (Rs.L)", "Net", "Frequency", "Risk"];
  const cpColW = [ctx.contentW * 0.28, ctx.contentW * 0.14, ctx.contentW * 0.14, ctx.contentW * 0.14, ctx.contentW * 0.12, ctx.contentW * 0.18];
  drawTable(ctx, cpHeaders,
    bs.topCounterparties.map((c) => [c.name, String(c.credits), String(c.debits), String(c.net), String(c.frequency), c.risk.toUpperCase()]),
    { colWidths: cpColW, rowColors: bs.topCounterparties.map((c) => c.risk === "high" ? colors.danger : c.risk === "medium" ? colors.warning : null) }
  );
}
