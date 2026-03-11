import { PdfCtx, newPage, drawText, colors } from "../pdfHelpers";

export function drawTocPage(ctx: PdfCtx) {
  newPage(ctx);
  // Placeholder — content will be drawn by updateToc after all sections are rendered
}

export function updateToc(ctx: PdfCtx, tocPageNum: number) {
  ctx.doc.setPage(tocPageNum);
  const { doc, margin, pageW } = ctx;

  // White background is default — no fill needed

  let y = margin;
  drawText(ctx, "TABLE OF CONTENTS", margin, y + 4, { size: 12, color: colors.primary, style: "bold" });
  y += 12;

  doc.setDrawColor(...colors.primary);
  doc.setLineWidth(0.4);
  doc.line(margin, y, pageW - margin, y);
  y += 8;

  ctx.sectionPages.forEach((s) => {
    // Dot leader line
    doc.setDrawColor(...colors.border);
    doc.setLineWidth(0.1);
    doc.line(margin + 55, y - 1, pageW - margin - 20, y - 1);

    drawText(ctx, s.title, margin + 4, y, { size: 8, color: colors.text });
    drawText(ctx, `Page ${s.page}`, pageW - margin - 4, y, { size: 8, color: colors.muted, align: "right" });
    y += 7;
  });
}
