import jsPDF from "jspdf";

export const colors = {
  primary: [26, 58, 108] as [number, number, number],
  dark: [30, 35, 50] as [number, number, number],
  text: [40, 45, 60] as [number, number, number],
  muted: [110, 115, 130] as [number, number, number],
  safe: [22, 130, 65] as [number, number, number],
  warning: [180, 130, 20] as [number, number, number],
  danger: [190, 40, 40] as [number, number, number],
  white: [255, 255, 255] as [number, number, number],
  cardBg: [245, 246, 250] as [number, number, number],
  tableBg1: [255, 255, 255] as [number, number, number],
  tableBg2: [245, 247, 252] as [number, number, number],
  tableHeader: [26, 58, 108] as [number, number, number],
  border: [210, 215, 225] as [number, number, number],
};

export const decisionColor = {
  approve: colors.safe,
  reject: colors.danger,
  conditional: colors.warning,
};

export interface PdfCtx {
  doc: jsPDF;
  y: number;
  margin: number;
  pageW: number;
  contentW: number;
  sectionPages: { title: string; page: number }[];
}

export function createCtx(): PdfCtx {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const pageW = doc.internal.pageSize.getWidth();
  const margin = 16;
  return { doc, y: margin, margin, pageW, contentW: pageW - margin * 2, sectionPages: [] };
}

export function fillPage(_ctx: PdfCtx) {
  // White background — no fill needed (PDF default is white)
}

/** Sanitize text for jsPDF Helvetica (no Unicode symbols) */
function sanitize(text: string): string {
  return text
    .replace(/₹/g, "Rs.")
    .replace(/⚠/g, "!")
    .replace(/→/g, "->")
    .replace(/✓/g, "[OK]")
    .replace(/•/g, "-");
}

export function checkPage(ctx: PdfCtx, needed: number) {
  if (ctx.y + needed > ctx.doc.internal.pageSize.getHeight() - ctx.margin - 10) {
    ctx.doc.addPage();
    fillPage(ctx);
    ctx.y = ctx.margin + 6;
  }
}

export function newPage(ctx: PdfCtx) {
  ctx.doc.addPage();
  fillPage(ctx);
  ctx.y = ctx.margin + 6;
}

export function drawText(
  ctx: PdfCtx,
  text: string,
  x: number,
  yPos: number,
  opts: {
    size?: number;
    color?: [number, number, number];
    style?: string;
    maxWidth?: number;
    align?: "left" | "center" | "right";
  } = {}
) {
  const safeText = sanitize(text);
  ctx.doc.setFontSize(opts.size || 10);
  ctx.doc.setTextColor(...(opts.color || colors.text));
  ctx.doc.setFont("helvetica", opts.style || "normal");
  if (opts.maxWidth) {
    return ctx.doc.text(safeText, x, yPos, { maxWidth: opts.maxWidth, align: opts.align });
  }
  return ctx.doc.text(safeText, x, yPos, { align: opts.align });
}

export function sectionHeader(ctx: PdfCtx, num: number, title: string) {
  checkPage(ctx, 45);
  ctx.sectionPages.push({ title: `${num}. ${title}`, page: ctx.doc.getNumberOfPages() });
  ctx.doc.setFillColor(...colors.primary);
  ctx.doc.rect(ctx.margin, ctx.y, 1.5, 6, "F");
  drawText(ctx, `${num}. ${title.toUpperCase()}`, ctx.margin + 5, ctx.y + 4.5, {
    size: 10,
    color: colors.primary,
    style: "bold",
  });
  ctx.y += 10;
}

export function drawWrappedText(ctx: PdfCtx, text: string, opts?: { color?: [number, number, number]; size?: number }) {
  const size = opts?.size || 7.5;
  const safeText = sanitize(text);
  ctx.doc.setFontSize(size);
  ctx.doc.setTextColor(...(opts?.color || colors.muted));
  ctx.doc.setFont("helvetica", "normal");
  const lines = ctx.doc.splitTextToSize(safeText, ctx.contentW - 8);
  lines.forEach((line: string) => {
    checkPage(ctx, 4);
    ctx.doc.text(line, ctx.margin + 4, ctx.y);
    ctx.y += 3.5;
  });
  ctx.y += 2;
}

export function drawTable(
  ctx: PdfCtx,
  headers: string[],
  rows: string[][],
  opts?: {
    colWidths?: number[];
    headerColor?: [number, number, number];
    highlightCol?: number;
    rowColors?: ([number, number, number] | null)[];
  }
) {
  const colCount = headers.length;
  const defaultColW = ctx.contentW / colCount;
  const colWidths = opts?.colWidths || headers.map(() => defaultColW);
  const rowH = 5.5;
  const headerH = 6;

  checkPage(ctx, headerH + rowH * Math.min(rows.length, 3));
  ctx.doc.setFillColor(...colors.tableHeader);
  ctx.doc.rect(ctx.margin, ctx.y - 1, ctx.contentW, headerH, "F");
  let xOff = ctx.margin + 2;
  headers.forEach((h, i) => {
    drawText(ctx, h, xOff, ctx.y + 3, { size: 6, color: colors.white, style: "bold" });
    xOff += colWidths[i];
  });
  ctx.y += headerH;

  rows.forEach((row, ri) => {
    checkPage(ctx, rowH);
    const bg = ri % 2 === 0 ? colors.tableBg1 : colors.tableBg2;
    ctx.doc.setFillColor(...bg);
    ctx.doc.rect(ctx.margin, ctx.y - 1, ctx.contentW, rowH, "F");
    xOff = ctx.margin + 2;
    row.forEach((cell, ci) => {
      const cellColor = opts?.rowColors?.[ri] || (ci === (opts?.highlightCol ?? -1) ? colors.text : colors.muted);
      drawText(ctx, cell, xOff, ctx.y + 3, { size: 6.5, color: cellColor as [number, number, number] });
      xOff += colWidths[ci];
    });
    ctx.y += rowH;
  });
  ctx.y += 3;
}

export function drawKeyValue(ctx: PdfCtx, pairs: [string, string][], opts?: { valueColor?: [number, number, number] }) {
  const cardHeight = pairs.length * 5.5 + 4;
  checkPage(ctx, cardHeight + 2);
  ctx.doc.setFillColor(...colors.cardBg);
  ctx.doc.roundedRect(ctx.margin, ctx.y - 2, ctx.contentW, cardHeight, 1.5, 1.5, "F");
  pairs.forEach(([label, value]) => {
    drawText(ctx, label, ctx.margin + 4, ctx.y + 2, { size: 6.5, color: colors.muted });
    drawText(ctx, value, ctx.margin + 50, ctx.y + 2, { size: 7, color: opts?.valueColor || colors.text });
    ctx.y += 5.5;
  });
  ctx.y += 4;
}

export function statusColor(status: string): [number, number, number] {
  switch (status) {
    case "verified": case "compliant": case "clean": case "good": case "low": case "disposed": case "settled": case "satisfactory":
      return colors.safe;
    case "flagged": case "non_compliant": case "danger": case "critical": case "high": case "unsatisfactory": case "active":
      return colors.danger;
    case "pending": case "pending_review": case "partial": case "watchlist": case "warning": case "medium": case "concerns": case "monitoring":
      return colors.warning;
    default: return colors.muted;
  }
}

export function severityColor(severity: string): [number, number, number] {
  switch (severity) {
    case "critical": return colors.danger;
    case "high": return [200, 90, 30];
    case "medium": return colors.warning;
    case "low": return colors.safe;
    default: return colors.muted;
  }
}

export function addFooters(ctx: PdfCtx, companyName: string) {
  const pageCount = ctx.doc.getNumberOfPages();
  for (let p = 1; p <= pageCount; p++) {
    ctx.doc.setPage(p);
    const ph = ctx.doc.internal.pageSize.getHeight();

    if (p > 1) {
      ctx.doc.setFillColor(...colors.primary);
      ctx.doc.rect(0, 0, ctx.pageW, 8, "F");
      ctx.doc.setFontSize(5.5);
      ctx.doc.setTextColor(...colors.white);
      ctx.doc.text("INTELLICREDIT — CREDIT APPRAISAL MEMORANDUM", ctx.margin, 5.5);
      ctx.doc.text(companyName, ctx.pageW - ctx.margin, 5.5, { align: "right" });
    }

    ctx.doc.setFontSize(5.5);
    ctx.doc.setTextColor(...colors.muted);
    ctx.doc.text(
      `CONFIDENTIAL - Page ${p} of ${pageCount}`,
      ctx.pageW / 2, ph - 6, { align: "center" }
    );
    ctx.doc.setDrawColor(...colors.border);
    ctx.doc.line(ctx.margin, ph - 9, ctx.pageW - ctx.margin, ph - 9);
  }
}
