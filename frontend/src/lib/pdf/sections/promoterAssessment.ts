import { PdfCtx, sectionHeader, drawTable, drawText, checkPage, colors, severityColor, statusColor } from "../pdfHelpers";
import { PromoterDataset } from "../../promoterData";

export function drawPromoterAssessment(ctx: PdfCtx, promoter: PromoterDataset, sectionNum: number = 7) {
  sectionHeader(ctx, sectionNum, "Promoter & Management Intelligence");

  const riskColor = statusColor(promoter.overallPromoterRisk);
  drawText(ctx, `Overall Promoter Risk: ${promoter.overallPromoterRisk.toUpperCase()}`, ctx.margin + 4, ctx.y, {
    size: 8, color: riskColor, style: "bold",
  });
  ctx.y += 7;

  // Detailed director profiles
  checkPage(ctx, 30);
  drawText(ctx, "DIRECTOR PROFILES", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;
  const colW = [ctx.contentW * 0.17, ctx.contentW * 0.15, ctx.contentW * 0.10, ctx.contentW * 0.13, ctx.contentW * 0.10, ctx.contentW * 0.10, ctx.contentW * 0.10, ctx.contentW * 0.15];
  const rows = promoter.directors.map((d) => [
    d.name, d.designation, String(d.age) + " yrs", String(d.cibilScore), d.netWorth,
    String(d.linkedEntities), `${d.npaLinks} / ${d.shellLinks}`, d.riskLevel.toUpperCase(),
  ]);
  const rowColors = promoter.directors.map((d) => statusColor(d.riskLevel));
  drawTable(ctx, ["Name", "Designation", "Age", "CIBIL", "Net Worth", "Entities", "NPA/Shell", "Risk"],
    rows, { colWidths: colW, rowColors });

  // Litigation
  if (promoter.litigation.length > 0) {
    checkPage(ctx, 30);
    drawText(ctx, "LITIGATION HISTORY", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
    ctx.y += 5;
    const litColW = [ctx.contentW * 0.10, ctx.contentW * 0.15, ctx.contentW * 0.12, ctx.contentW * 0.10, ctx.contentW * 0.10, ctx.contentW * 0.43];
    drawTable(ctx, ["Date", "Court", "Type", "Status", "Amount", "Description"],
      promoter.litigation.map((l) => [l.date, l.court, l.caseType, l.status.toUpperCase(), l.amount, l.description.substring(0, 55)]),
      { colWidths: litColW, rowColors: promoter.litigation.map((l) => severityColor(l.severity)) }
    );
  }

  // News Sentiment
  if (promoter.news.length > 0) {
    checkPage(ctx, 30);
    drawText(ctx, "NEWS & MEDIA SENTIMENT", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
    ctx.y += 5;
    const newsColW = [ctx.contentW * 0.10, ctx.contentW * 0.15, ctx.contentW * 0.55, ctx.contentW * 0.12, ctx.contentW * 0.08];
    drawTable(ctx, ["Date", "Source", "Headline", "Sentiment", "Score"],
      promoter.news.map((n) => [n.date, n.source, n.headline.substring(0, 65), n.sentiment.toUpperCase(), `${n.relevance}%`]),
      { colWidths: newsColW, rowColors: promoter.news.map((n) => n.sentiment === "negative" ? colors.danger : n.sentiment === "positive" ? colors.safe : null) }
    );
  }

  // Network summary
  checkPage(ctx, 10);
  const shellNodes = promoter.networkNodes.filter((n) => n.type === "shell").length;
  const npaNodes = promoter.networkNodes.filter((n) => n.type === "npa").length;
  const suspiciousEdges = promoter.networkEdges.filter((e) => e.suspicious).length;
  drawText(ctx, `Network Analysis: ${promoter.networkNodes.length} entities, ${promoter.networkEdges.length} connections, ${suspiciousEdges} suspicious links, ${shellNodes} shell entities, ${npaNodes} NPA entities`,
    ctx.margin + 4, ctx.y, { size: 6.5, color: suspiciousEdges > 0 ? colors.danger : colors.muted });
  ctx.y += 6;
}
