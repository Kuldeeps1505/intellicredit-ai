/**
 * CAM PDF Generator — 14-section format matching IntelliCredit reference PDF.
 * Uses jsPDF client-side. All data from live API responses.
 */
import jsPDF from "jspdf";

export interface CamPdfData {
  camData: any;
  dataset: any;
  riskData: any;
  promoterData?: any;
  financialData?: any;
  bankData?: any;
  diligenceData?: any;
  facilityData?: any;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const C = {
  navy:    [26,  58, 108] as [number,number,number],
  text:    [30,  35,  50] as [number,number,number],
  muted:   [100,105, 120] as [number,number,number],
  safe:    [22, 130,  65] as [number,number,number],
  warn:    [180,130,  20] as [number,number,number],
  danger:  [190, 40,  40] as [number,number,number],
  white:   [255,255, 255] as [number,number,number],
  bg:      [245,246, 250] as [number,number,number],
  border:  [210,215, 225] as [number,number,number],
  row1:    [255,255, 255] as [number,number,number],
  row2:    [245,247, 252] as [number,number,number],
};

function san(t: string): string {
  return (t || "")
    .replace(/₹/g, "Rs.")
    .replace(/⚠/g, "!")
    .replace(/→/g, "->")
    .replace(/✓/g, "[OK]")
    .replace(/•/g, "-")
    .replace(/[^\x00-\x7F]/g, "?");
}

interface Ctx { doc: jsPDF; y: number; m: number; w: number; cw: number; }

function mk(): Ctx {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const m = 16;
  return { doc, y: m, m, w: doc.internal.pageSize.getWidth(), cw: doc.internal.pageSize.getWidth() - m * 2 };
}

function ph(ctx: Ctx) { return ctx.doc.internal.pageSize.getHeight(); }

function chk(ctx: Ctx, need: number) {
  if (ctx.y + need > ph(ctx) - ctx.m - 10) {
    ctx.doc.addPage();
    ctx.y = ctx.m + 8;
  }
}

function txt(ctx: Ctx, t: string, x: number, y: number, sz = 9, col = C.text, bold = false, align: "left"|"center"|"right" = "left") {
  ctx.doc.setFontSize(sz);
  ctx.doc.setTextColor(...col);
  ctx.doc.setFont("helvetica", bold ? "bold" : "normal");
  ctx.doc.text(san(t), x, y, { align });
}

function wrap(ctx: Ctx, t: string, sz = 7.5, col = C.muted) {
  ctx.doc.setFontSize(sz); ctx.doc.setTextColor(...col); ctx.doc.setFont("helvetica","normal");
  const lines = ctx.doc.splitTextToSize(san(t), ctx.cw - 6);
  lines.forEach((l: string) => { chk(ctx, 4); ctx.doc.text(l, ctx.m + 3, ctx.y); ctx.y += 3.8; });
  ctx.y += 2;
}

function secHead(ctx: Ctx, n: number, title: string) {
  chk(ctx, 14);
  ctx.doc.setFillColor(...C.navy);
  ctx.doc.rect(ctx.m, ctx.y, 2, 7, "F");
  txt(ctx, `${n}. ${title.toUpperCase()}`, ctx.m + 6, ctx.y + 5, 10, C.navy, true);
  ctx.y += 12;
}

function kv(ctx: Ctx, pairs: [string,string][], valCol = C.text) {
  const h = pairs.length * 5.5 + 4;
  chk(ctx, h + 2);
  ctx.doc.setFillColor(...C.bg);
  ctx.doc.roundedRect(ctx.m, ctx.y - 2, ctx.cw, h, 1.5, 1.5, "F");
  pairs.forEach(([k, v]) => {
    txt(ctx, k, ctx.m + 4, ctx.y + 2, 6.5, C.muted);
    txt(ctx, v, ctx.m + 55, ctx.y + 2, 7, valCol);
    ctx.y += 5.5;
  });
  ctx.y += 4;
}

function tbl(ctx: Ctx, headers: string[], rows: string[][], colW?: number[], rowCols?: ([number,number,number]|null)[]) {
  const cw = colW || headers.map(() => ctx.cw / headers.length);
  chk(ctx, 8 + 5.5 * Math.min(rows.length, 3));
  ctx.doc.setFillColor(...C.navy);
  ctx.doc.rect(ctx.m, ctx.y - 1, ctx.cw, 6.5, "F");
  let x = ctx.m + 2;
  headers.forEach((h, i) => { txt(ctx, h, x, ctx.y + 3.5, 6, C.white, true); x += cw[i]; });
  ctx.y += 6.5;
  rows.forEach((row, ri) => {
    chk(ctx, 5.5);
    ctx.doc.setFillColor(...(ri % 2 === 0 ? C.row1 : C.row2));
    ctx.doc.rect(ctx.m, ctx.y - 1, ctx.cw, 5.5, "F");
    x = ctx.m + 2;
    row.forEach((cell, ci) => {
      const col = rowCols?.[ri] || (ci === 0 ? C.text : C.muted);
      txt(ctx, cell, x, ctx.y + 3, 6.5, col as [number,number,number]);
      x += cw[ci];
    });
    ctx.y += 5.5;
  });
  ctx.y += 3;
}

function decCol(d: string): [number,number,number] {
  if (d === "approve") return C.safe;
  if (d === "reject")  return C.danger;
  return C.warn;
}

function sevCol(s: string): [number,number,number] {
  if (s === "critical") return C.danger;
  if (s === "high")     return [200,90,30];
  if (s === "medium")   return C.warn;
  return C.safe;
}

// ── Cover Page ────────────────────────────────────────────────────────────────
function cover(ctx: Ctx, ds: any, cam: any) {
  const doc = ctx.doc;
  doc.setFillColor(...C.navy);
  doc.rect(0, 0, ctx.w, 60, "F");
  txt(ctx, "CREDIT APPRAISAL MEMORANDUM", ctx.w/2, 22, 16, C.white, true, "center");
  txt(ctx, "CONFIDENTIAL — FOR INTERNAL USE ONLY", ctx.w/2, 30, 7, [180,190,210], false, "center");
  doc.setDrawColor(255,255,255); doc.setLineWidth(0.3);
  doc.line(ctx.m, 36, ctx.w - ctx.m, 36);
  txt(ctx, san(ds.companyName), ctx.w/2, 46, 13, C.white, true, "center");
  txt(ctx, `CIN: ${ds.cin}  |  GSTIN: ${ds.gstin}`, ctx.w/2, 53, 7, [180,190,210], false, "center");

  ctx.y = 72;
  const dc = decCol(cam.recommendation.decision);
  doc.setFillColor(...dc);
  doc.roundedRect(ctx.m, ctx.y, ctx.cw, 14, 2, 2, "F");
  const label = cam.recommendation.decision === "approve" ? "APPROVED" :
                cam.recommendation.decision === "reject"  ? "REJECTED" : "CONDITIONAL APPROVAL";
  txt(ctx, label, ctx.w/2, ctx.y + 9, 14, C.white, true, "center");
  ctx.y += 20;

  kv(ctx, [
    ["Company",        san(ds.companyName)],
    ["Loan Amount",    `Rs.${ds.loanAmount}`],
    ["Purpose",        ds.purpose || "—"],
    ["Sector",         ds.sector || "—"],
    ["Generated",      cam.generatedAt],
    ["Prepared by",    "IntelliCredit AI — 7-Agent Pipeline"],
  ]);
}

// ── Build full PDF — 14 sections ─────────────────────────────────────────────
function build(data: CamPdfData): jsPDF {
  const ctx = mk();
  const { camData: cam, dataset: ds, riskData: risk } = data;
  const company = ds?.companyName || "—";
  const cin     = ds?.cin || "—";
  const gstin   = ds?.gstin || "—";
  const loan    = ds?.loanAmount || "—";
  const purpose = ds?.purpose || "—";
  const sector  = ds?.sector || "—";

  // ── COVER PAGE ─────────────────────────────────────────────────────────────
  cover(ctx, ds, cam);

  // ── TABLE OF CONTENTS ──────────────────────────────────────────────────────
  ctx.doc.addPage(); ctx.y = ctx.m + 4;
  ctx.doc.setFillColor(...C.navy);
  ctx.doc.rect(0, 0, ctx.w, 8, "F");
  txt(ctx, "TABLE OF CONTENTS", ctx.w/2, 5.5, 9, C.white, true, "center");
  ctx.y = 18;
  const toc = [
    "1. Borrower Profile & Company Information",
    "2. Existing & Proposed Banking Facilities",
    "3. Promoter & Management Intelligence",
    "4. Financial Analysis — 3-Year Spreads",
    "5. Working Capital Assessment",
    "6. Bank Statement Analysis (12 Months)",
    "7. GST & Tax Compliance",
    "8. Risk Assessment — Five-Cs",
    "9. Due Diligence Summary",
    "10. Sensitivity / Stress Analysis",
    "11. Credit Assessment Narrative",
    "12. Recommendation & Decision",
    "13. Proposed Loan Terms",
    "14. Disclaimer & Authorization",
  ];
  toc.forEach((item, i) => {
    ctx.doc.setFillColor(...(i % 2 === 0 ? C.row1 : C.row2));
    ctx.doc.rect(ctx.m, ctx.y - 3, ctx.cw, 6, "F");
    txt(ctx, item, ctx.m + 4, ctx.y + 1, 7.5, C.text);
    ctx.y += 6;
  });

  // ── SECTION 1: BORROWER PROFILE ────────────────────────────────────────────
  ctx.doc.addPage(); ctx.y = ctx.m + 4;
  secHead(ctx, 1, "Borrower Profile & Company Information");
  kv(ctx, [
    ["Company Name",        san(company)],
    ["CIN",                 san(cin)],
    ["PAN",                 san(ds?.pan || "—")],
    ["GSTIN",               san(gstin)],
    ["Sector / Industry",   san(sector)],
    ["Loan Amount Requested", `Rs.${loan}`],
    ["Purpose of Facility", san(purpose)],
  ]);

  // Directors from promoter data
  const directors = data.promoterData?.directors || [];
  if (directors.length) {
    txt(ctx, "BOARD OF DIRECTORS", ctx.m + 3, ctx.y, 7, C.navy, true); ctx.y += 5;
    tbl(ctx,
      ["Name", "DIN", "Designation", "CIBIL", "Net Worth", "Risk"],
      directors.map((d: any) => [
        san(d.name || "—"), san(d.din || "—"), san(d.designation || "—"),
        String(d.cibilScore || "—"), san(d.netWorth || "—"),
        d.riskLevel === "flagged" ? "FLAGGED" : d.riskLevel === "watchlist" ? "WATCHLIST" : "CLEAN",
      ]),
      [ctx.cw*0.28, ctx.cw*0.14, ctx.cw*0.20, ctx.cw*0.10, ctx.cw*0.14, ctx.cw*0.14],
      directors.map((d: any) => d.riskLevel === "flagged" ? C.danger : d.riskLevel === "watchlist" ? C.warn : C.safe),
    );
  }

  // ── SECTION 2: BANKING FACILITIES ─────────────────────────────────────────
  secHead(ctx, 2, "Existing & Proposed Banking Facilities");
  txt(ctx, "Note: Banking facility details to be provided by credit officer.", ctx.m + 3, ctx.y, 7, C.muted); ctx.y += 8;
  kv(ctx, [
    ["Proposed Facility Amount", `Rs.${loan}`],
    ["Purpose",                  san(purpose)],
    ["Security",                 san(cam?.recommendation?.loanTerms?.security || "Hypothecation of current assets + EM on fixed assets")],
    ["Interest Rate",            san(cam?.recommendation?.loanTerms?.rate || "—")],
    ["Tenure",                   san(cam?.recommendation?.loanTerms?.tenure || "—")],
  ]);

  // ── SECTION 3: PROMOTER INTELLIGENCE ──────────────────────────────────────
  secHead(ctx, 3, "Promoter & Management Intelligence");
  const overallRisk = data.promoterData?.overallPromoterRisk || "N/A";
  const riskCol = overallRisk === "low" ? C.safe : overallRisk === "medium" ? C.warn : C.danger;
  txt(ctx, `Overall Promoter Risk: ${overallRisk.toUpperCase()}`, ctx.m + 3, ctx.y, 8, riskCol, true); ctx.y += 7;

  const litigation = data.promoterData?.litigation || [];
  if (litigation.length) {
    txt(ctx, "LITIGATION HISTORY", ctx.m + 3, ctx.y, 7, C.navy, true); ctx.y += 5;
    tbl(ctx,
      ["Date", "Court", "Type", "Status", "Amount", "Description"],
      litigation.map((c: any) => [
        san(c.date || "—"), san(c.court || "—"), san(c.caseType || "—"),
        san(c.status || "—"), san(c.amount || "—"), san((c.description || "").slice(0, 40)),
      ]),
      [ctx.cw*0.10, ctx.cw*0.18, ctx.cw*0.14, ctx.cw*0.12, ctx.cw*0.12, ctx.cw*0.34],
    );
  }

  const news = data.promoterData?.news || [];
  if (news.length) {
    txt(ctx, "NEWS & MEDIA SENTIMENT", ctx.m + 3, ctx.y, 7, C.navy, true); ctx.y += 5;
    tbl(ctx,
      ["Date", "Source", "Headline", "Sentiment"],
      news.slice(0, 5).map((n: any) => [
        san(n.date || "—"), san(n.source || "—"),
        san((n.headline || "").slice(0, 55)), san(n.sentiment || "—"),
      ]),
      [ctx.cw*0.10, ctx.cw*0.16, ctx.cw*0.56, ctx.cw*0.18],
      news.slice(0, 5).map((n: any) => n.sentiment === "negative" ? C.danger : n.sentiment === "positive" ? C.safe : C.muted),
    );
  }

  // ── SECTION 4: FINANCIAL ANALYSIS ─────────────────────────────────────────
  ctx.doc.addPage(); ctx.y = ctx.m + 4;
  secHead(ctx, 4, "Financial Analysis — 3-Year Spreads");
  const fins = data.financialData;
  if (fins?.pnl?.length) {
    txt(ctx, "PROFIT & LOSS STATEMENT (Rs. Lakhs)", ctx.m + 3, ctx.y, 7, C.navy, true); ctx.y += 5;
    tbl(ctx,
      ["Particulars", "FY 2022", "FY 2023", "FY 2024"],
      fins.pnl.slice(0, 12).map((r: any) => [
        san(r.label), String(r.fy22?.toFixed(0) || "—"),
        String(r.fy23?.toFixed(0) || "—"), String(r.fy24?.toFixed(0) || "—"),
      ]),
      [ctx.cw*0.46, ctx.cw*0.18, ctx.cw*0.18, ctx.cw*0.18],
    );
  }
  if (fins?.ratios?.length) {
    txt(ctx, "KEY FINANCIAL RATIOS", ctx.m + 3, ctx.y, 7, C.navy, true); ctx.y += 5;
    tbl(ctx,
      ["Ratio", "FY 2022", "FY 2023", "FY 2024", "Benchmark", "Status"],
      fins.ratios.slice(0, 12).map((r: any) => [
        san(r.name),
        String(r.fy22?.toFixed(2) || "—"), String(r.fy23?.toFixed(2) || "—"),
        String(r.fy24?.toFixed(2) || "—"),
        String(r.benchmark || "—"),
        r.anomaly ? "WARN" : "OK",
      ]),
      [ctx.cw*0.28, ctx.cw*0.12, ctx.cw*0.12, ctx.cw*0.12, ctx.cw*0.18, ctx.cw*0.18],
      fins.ratios.slice(0, 12).map((r: any) => r.anomaly ? C.danger : C.safe),
    );
  } else {
    wrap(ctx, "Financial spread data not available. Run pipeline to extract financials.", 7.5, C.muted);
  }

  // ── SECTION 5: WORKING CAPITAL ─────────────────────────────────────────────
  secHead(ctx, 5, "Working Capital Assessment");
  if (fins?.pnl) {
    const rev24 = fins.pnl.find((r: any) => r.label?.includes("Revenue"))?.fy24 || 0;
    const mpbf = rev24 * 0.25;
    kv(ctx, [
      ["Projected Turnover (FY24)", `Rs.${rev24.toFixed(0)} Lakhs`],
      ["MPBF (25% of Turnover)",    `Rs.${mpbf.toFixed(0)} Lakhs`],
      ["Method",                    "Turnover Method (Nayak Committee)"],
      ["Assessed Bank Finance",     `Rs.${(mpbf * 0.8).toFixed(0)} Lakhs`],
    ]);
  } else {
    wrap(ctx, "Working capital data not available.", 7.5, C.muted);
  }

  // ── SECTION 6: BANK STATEMENT ──────────────────────────────────────────────
  secHead(ctx, 6, "Bank Statement Analysis (12 Months)");
  const bank = data.bankData;
  if (bank?.summary) {
    kv(ctx, [
      ["Average Bank Balance (ABB)", `Rs.${bank.summary.abb || "—"}L`],
      ["Avg Monthly Credits",        `Rs.${bank.summary.avgMonthlyCredits || "—"}L`],
      ["Avg Monthly Debits",         `Rs.${bank.summary.avgMonthlyDebits || "—"}L`],
      ["Credit:Debit Ratio",         `${bank.summary.creditDebitRatio || "—"}x`],
      ["Bounce Ratio",               `${bank.summary.bounceRatio || "—"}%`],
      ["Cash Withdrawal %",          `${bank.summary.cashWithdrawalPercent || "—"}%`],
      ["Behavior Score",             `${bank.summary.behaviorScore || "—"}/100`],
    ]);
    const redFlags = (bank.redFlags || []).filter((f: any) => f.detected);
    if (redFlags.length) {
      txt(ctx, `RED FLAGS DETECTED: ${redFlags.length}`, ctx.m + 3, ctx.y, 7, C.danger, true); ctx.y += 5;
      tbl(ctx,
        ["Flag Type", "Severity", "Details"],
        redFlags.map((f: any) => [san(f.type || "—"), san(f.severity || "—"), san((f.details || f.description || "").slice(0, 60))]),
        [ctx.cw*0.30, ctx.cw*0.15, ctx.cw*0.55],
        redFlags.map((f: any) => f.severity === "critical" ? C.danger : C.warn),
      );
    }
  } else {
    wrap(ctx, "Bank statement data not available. Upload 12-month bank statement.", 7.5, C.muted);
  }

  // ── SECTION 7: GST COMPLIANCE ──────────────────────────────────────────────
  ctx.doc.addPage(); ctx.y = ctx.m + 4;
  secHead(ctx, 7, "GST & Tax Compliance");
  const gstr = risk?.gstrReconciliation || [];
  const suspectItc = risk?.suspectITC || "Rs.0";
  const flaggedQ = gstr.filter((q: any) => q.flagged).length;
  kv(ctx, [
    ["Suspect ITC Amount", san(suspectItc)],
    ["Flagged Quarters",   `${flaggedQ} of ${gstr.length}`],
  ]);
  if (gstr.length) {
    tbl(ctx,
      ["Quarter", "GSTR-2A (Cr)", "GSTR-3B (Cr)", "Variance", "Status"],
      gstr.map((q: any) => [
        san(q.quarter), `Rs.${q.gstr2a?.toFixed(2) || "—"}Cr`,
        `Rs.${q.gstr3b?.toFixed(2) || "—"}Cr`,
        `${((q.gstr3b - q.gstr2a) / (q.gstr2a || 1) * 100).toFixed(1)}%`,
        q.flagged ? "FLAGGED" : "[OK]",
      ]),
      [ctx.cw*0.18, ctx.cw*0.18, ctx.cw*0.18, ctx.cw*0.18, ctx.cw*0.28],
      gstr.map((q: any) => q.flagged ? C.danger : C.safe),
    );
  }

  // ── SECTION 8: RISK ASSESSMENT ─────────────────────────────────────────────
  secHead(ctx, 8, "Risk Assessment — Five-Cs Framework");
  kv(ctx, [
    ["Risk Score",              `${risk?.score || 0}/100`],
    ["Risk Category",           san(risk?.riskCategory || "N/A")],
    ["Probability of Default (12M)", `${risk?.defaultProb12m || 0}%`],
    ["Probability of Default (24M)", `${risk?.defaultProb24m || 0}%`],
  ]);
  const fiveCs = risk?.fiveCs || [];
  if (fiveCs.length) {
    tbl(ctx,
      ["Dimension", "Score (/100)", "Rating"],
      fiveCs.map((c: any) => [
        san(c.subject), `${c.value}/100`,
        c.value >= 70 ? "STRONG" : c.value >= 50 ? "ADEQUATE" : "WEAK",
      ]),
      [ctx.cw*0.35, ctx.cw*0.25, ctx.cw*0.40],
      fiveCs.map((c: any) => c.value >= 70 ? C.safe : c.value >= 50 ? C.warn : C.danger),
    );
  }
  if (risk?.riskFlags?.length) {
    txt(ctx, "RISK FLAGS", ctx.m + 3, ctx.y, 7, C.navy, true); ctx.y += 5;
    tbl(ctx,
      ["Type", "Severity", "Description", "Detected By", "Status"],
      risk.riskFlags.map((f: any) => [
        san(f.type || "—"), san(f.severity?.toUpperCase() || "—"),
        san((f.description || "").slice(0, 45)), san(f.detectedBy || "—"), san(f.status || "—"),
      ]),
      [ctx.cw*0.20, ctx.cw*0.12, ctx.cw*0.38, ctx.cw*0.18, ctx.cw*0.12],
      risk.riskFlags.map((f: any) => sevCol(f.severity)),
    );
  }
  if (risk?.buyerConcentration?.length) {
    txt(ctx, `BUYER CONCENTRATION — Top 3: ${risk.topThreeConcentration}%`, ctx.m + 3, ctx.y, 7, C.navy, true); ctx.y += 5;
    tbl(ctx,
      ["Buyer", "GSTIN", "Share %", "Risk"],
      risk.buyerConcentration.map((b: any) => [san(b.name), san(b.gstin), `${b.percentage}%`, b.risk.toUpperCase()]),
      [ctx.cw*0.35, ctx.cw*0.25, ctx.cw*0.20, ctx.cw*0.20],
      risk.buyerConcentration.map((b: any) => b.risk === "high" ? C.danger : b.risk === "medium" ? C.warn : C.safe),
    );
  }

  // ── SECTION 9: DUE DILIGENCE ───────────────────────────────────────────────
  ctx.doc.addPage(); ctx.y = ctx.m + 4;
  secHead(ctx, 9, "Due Diligence Summary");
  const dd = data.diligenceData;
  if (dd?.checks?.length) {
    kv(ctx, [
      ["Completion",     `${dd.completionPercent || 0}%`],
      ["Overall Status", san(dd.overallStatus || "N/A")],
    ]);
    tbl(ctx,
      ["Category", "Item", "Status", "Source", "Notes"],
      dd.checks.slice(0, 15).map((c: any) => [
        san(c.category || "—"), san(c.item || "—"),
        san(c.status?.toUpperCase() || "—"), san(c.source || "—"),
        san((c.notes || "").slice(0, 35)),
      ]),
      [ctx.cw*0.14, ctx.cw*0.26, ctx.cw*0.12, ctx.cw*0.16, ctx.cw*0.32],
      dd.checks.slice(0, 15).map((c: any) =>
        c.status === "verified" ? C.safe : c.status === "flagged" ? C.danger : C.muted),
    );
  } else {
    wrap(ctx, "Due diligence checklist not available.", 7.5, C.muted);
  }

  // ── SECTION 10: STRESS ANALYSIS ────────────────────────────────────────────
  secHead(ctx, 10, "Sensitivity / Stress Analysis");
  const baseDscr = risk?.financialRatios?.find((r: any) => r.name === "DSCR")?.numericValue || 0;
  const baseIcr  = risk?.financialRatios?.find((r: any) => r.name === "Interest Coverage")?.numericValue || 0;
  kv(ctx, [
    ["Base DSCR (FY24)", `${baseDscr.toFixed(2)}x`],
    ["Base ICR (FY24)",  `${baseIcr.toFixed(2)}x`],
  ]);
  tbl(ctx,
    ["Scenario", "Change", "Revised DSCR", "Revised ICR", "Impact"],
    [
      ["Revenue decline 10%",    "-10% revenue",  `${(baseDscr * 0.88).toFixed(2)}x`, `${(baseIcr * 0.85).toFixed(2)}x`, baseDscr * 0.88 >= 1.25 ? "Comfortable" : "Marginal"],
      ["Raw material cost +15%", "+15% COGS",     `${(baseDscr * 0.82).toFixed(2)}x`, `${(baseIcr * 0.78).toFixed(2)}x`, baseDscr * 0.82 >= 1.25 ? "Comfortable" : "Marginal"],
      ["Interest rate +200bps",  "+2% interest",  `${(baseDscr * 0.90).toFixed(2)}x`, `${(baseIcr * 0.82).toFixed(2)}x`, baseDscr * 0.90 >= 1.25 ? "Comfortable" : "Marginal"],
      ["Combined stress",        "All above",     `${(baseDscr * 0.72).toFixed(2)}x`, `${(baseIcr * 0.65).toFixed(2)}x`, baseDscr * 0.72 >= 1.25 ? "Comfortable" : "Marginal"],
    ],
    [ctx.cw*0.26, ctx.cw*0.18, ctx.cw*0.16, ctx.cw*0.16, ctx.cw*0.24],
  );

  // ── SECTION 11: CREDIT NARRATIVE ───────────────────────────────────────────
  secHead(ctx, 11, "Credit Assessment Narrative");
  cam.sections?.forEach((s: any, i: number) => {
    chk(ctx, 16);
    txt(ctx, `${i+1}. ${san(s.title)}`, ctx.m + 3, ctx.y, 7.5, C.text, true); ctx.y += 5;
    wrap(ctx, s.content, 7.5, C.muted);
    ctx.y += 2;
  });

  // ── SECTION 12: RECOMMENDATION ─────────────────────────────────────────────
  ctx.doc.addPage(); ctx.y = ctx.m + 4;
  secHead(ctx, 12, "Recommendation & Decision");
  const dc = decCol(cam.recommendation?.decision || "conditional");
  ctx.doc.setFillColor(...dc);
  ctx.doc.roundedRect(ctx.m, ctx.y - 2, ctx.cw, 12, 2, 2, "F");
  const dlabel = cam.recommendation?.decision === "approve" ? "APPROVED" :
                 cam.recommendation?.decision === "reject"  ? "REJECTED" : "CONDITIONAL APPROVAL";
  txt(ctx, dlabel, ctx.w/2, ctx.y + 7, 14, C.white, true, "center");
  ctx.y += 16;
  wrap(ctx, cam.recommendation?.summary || "—", 8, C.text);
  if (cam.recommendation?.conditions?.length) {
    txt(ctx, "CONDITIONS & COVENANTS", ctx.m + 3, ctx.y, 7, C.navy, true); ctx.y += 5;
    cam.recommendation.conditions.forEach((c: string) => {
      chk(ctx, 5); txt(ctx, `-> ${san(c)}`, ctx.m + 6, ctx.y, 6.5, C.muted); ctx.y += 4.5;
    });
    ctx.y += 3;
  }

  // ── SECTION 13: LOAN TERMS ─────────────────────────────────────────────────
  secHead(ctx, 13, "Proposed Loan Terms");
  const lt = cam.recommendation?.loanTerms || {};
  kv(ctx, [
    ["Facility Amount",   san(lt.amount || "—")],
    ["Tenure",            san(lt.tenure || "—")],
    ["Interest Rate",     san(lt.rate || "—")],
    ["Security",          san(lt.security || "—")],
    ["Disbursement",      san(lt.disbursement || "—")],
  ], lt.amount === "NOT APPLICABLE" ? C.danger : C.text);

  // Counterfactuals
  if (cam.counterfactuals?.length) {
    txt(ctx, "PATH TO APPROVAL — COUNTERFACTUAL ANALYSIS", ctx.m + 3, ctx.y, 7, C.navy, true); ctx.y += 5;
    tbl(ctx,
      ["Action", "Score Impact", "Difficulty", "Timeline"],
      cam.counterfactuals.map((cf: any) => [
        san((cf.action || "").slice(0, 55)), `+${cf.scoreImpact} pts`,
        san(cf.difficulty?.toUpperCase() || "—"), san(cf.timeframe || "—"),
      ]),
      [ctx.cw*0.50, ctx.cw*0.15, ctx.cw*0.15, ctx.cw*0.20],
    );
  }

  // ── SECTION 14: DISCLAIMER ─────────────────────────────────────────────────
  secHead(ctx, 14, "Disclaimer & Authorization");
  wrap(ctx,
    "DISCLAIMER: This Credit Appraisal Memorandum has been generated by the IntelliCredit AI Engine " +
    "using data sourced from uploaded financial documents, government databases (MCA21, GSTN, CIBIL, " +
    "CERSAI, eCourts), and account aggregator feeds. While the AI system employs advanced natural " +
    "language processing (FinBERT) and machine learning models for analysis, the output should be " +
    "treated as a decision-support tool and not as a final credit decision. All findings, risk scores, " +
    "and recommendations should be independently verified by the credit officer and approved through " +
    "the appropriate sanctioning authority as per the institution's credit policy. " +
    "This report is strictly confidential and intended solely for internal credit assessment purposes. " +
    "Unauthorized distribution or reproduction is prohibited.",
    7.5, C.muted);
  ctx.y += 8;
  kv(ctx, [
    ["Prepared by",    "IntelliCredit AI Engine v2.0"],
    ["Date",           new Date().toLocaleDateString("en-IN", { day:"2-digit", month:"short", year:"numeric" })],
    ["Classification", "STRICTLY CONFIDENTIAL"],
    ["Review Authority", "Credit Committee"],
  ]);

  // Signature blocks
  ctx.y += 6;
  chk(ctx, 30);
  const sigW = (ctx.cw - 16) / 3;
  ["Prepared By", "Reviewed By", "Approved By"].forEach((label, i) => {
    const sx = ctx.m + i * (sigW + 8);
    ctx.doc.setDrawColor(...C.border);
    ctx.doc.line(sx, ctx.y + 20, sx + sigW, ctx.y + 20);
    txt(ctx, label, sx, ctx.y + 24, 6.5, C.navy, true);
    txt(ctx, "Name: _______________", sx, ctx.y + 29, 6, C.muted);
    txt(ctx, "Date: _______________", sx, ctx.y + 33, 6, C.muted);
    txt(ctx, "Designation: ________", sx, ctx.y + 37, 6, C.muted);
  });
  ctx.y += 42;

  // ── PAGE HEADERS + FOOTERS ─────────────────────────────────────────────────
  const total = ctx.doc.getNumberOfPages();
  for (let p = 1; p <= total; p++) {
    ctx.doc.setPage(p);
    const pageH = ctx.doc.internal.pageSize.getHeight();
    if (p > 1) {
      ctx.doc.setFillColor(...C.navy);
      ctx.doc.rect(0, 0, ctx.w, 8, "F");
      ctx.doc.setFontSize(5.5); ctx.doc.setTextColor(...C.white); ctx.doc.setFont("helvetica","normal");
      ctx.doc.text("INTELLICREDIT AI — CREDIT APPRAISAL MEMORANDUM", ctx.m, 5.5);
      ctx.doc.text(san(company), ctx.w - ctx.m, 5.5, { align: "right" });
    }
    ctx.doc.setFontSize(5.5); ctx.doc.setTextColor(...C.muted);
    ctx.doc.text(`CONFIDENTIAL - Page ${p} of ${total}`, ctx.w/2, pageH - 6, { align: "center" });
    ctx.doc.setDrawColor(...C.border);
    ctx.doc.line(ctx.m, pageH - 9, ctx.w - ctx.m, pageH - 9);
  }

  return ctx.doc;
}

// ── Public API ────────────────────────────────────────────────────────────────

export function generateCamPdf(data: CamPdfData) {
  const doc = build(data);
  const name = `CAM_${san(data.dataset?.companyName || "Report").replace(/\s+/g,"_")}_${new Date().toISOString().split("T")[0]}.pdf`;
  doc.save(name);
}

export function generateCamPdfBlobUrl(data: CamPdfData): string {
  const doc = build(data);
  return URL.createObjectURL(doc.output("blob"));
}
