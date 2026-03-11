import { PdfCtx, sectionHeader, drawKeyValue, drawTable, drawText, checkPage, colors, statusColor } from "../pdfHelpers";
import { Dataset } from "../../demoData";
import { PromoterDataset } from "../../promoterData";

export function drawBorrowerProfile(ctx: PdfCtx, dataset: Dataset, promoter: PromoterDataset) {
  sectionHeader(ctx, 1, "Borrower Profile & Company Information");

  drawKeyValue(ctx, [
    ["Company Name", dataset.companyName],
    ["CIN", dataset.cin],
    ["PAN", dataset.pan],
    ["GSTIN", dataset.gstin],
    ["Sector / Industry", dataset.sector],
    ["Loan Amount Requested", `₹${dataset.loanAmount}`],
    ["Purpose of Facility", dataset.purpose],
  ]);

  // Directors table
  checkPage(ctx, 30);
  drawText(ctx, "BOARD OF DIRECTORS", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;

  const headers = ["Name", "DIN", "Designation", "CIBIL", "Net Worth", "Risk"];
  const colWidths = [ctx.contentW * 0.22, ctx.contentW * 0.15, ctx.contentW * 0.2, ctx.contentW * 0.12, ctx.contentW * 0.15, ctx.contentW * 0.16];
  const rows = promoter.directors.map((d) => [d.name, d.din, d.designation, String(d.cibilScore), d.netWorth, d.riskLevel.toUpperCase()]);
  const rowColors = promoter.directors.map((d) => statusColor(d.riskLevel));

  drawTable(ctx, headers, rows, { colWidths, rowColors });

  // MCA flags
  if (promoter.mca21Flags.length > 0) {
    drawText(ctx, "MCA21 FLAGS", ctx.margin + 4, ctx.y, { size: 7, color: colors.danger, style: "bold" });
    ctx.y += 5;
    promoter.mca21Flags.forEach((flag) => {
      drawText(ctx, `⚠  ${flag}`, ctx.margin + 6, ctx.y, { size: 6.5, color: colors.danger });
      ctx.y += 4.5;
    });
    ctx.y += 3;
  }
}
