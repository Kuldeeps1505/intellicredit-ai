import { PdfCtx, sectionHeader, drawTable, drawText, drawKeyValue, checkPage, colors } from "../pdfHelpers";
import { FacilityDataset } from "../../facilityData";

export function drawFacilityDetails(ctx: PdfCtx, sectionNum: number, facility: FacilityDataset) {
  sectionHeader(ctx, sectionNum, "Existing & Proposed Banking Facilities");

  // Existing Facilities
  checkPage(ctx, 30);
  drawText(ctx, "EXISTING BANKING FACILITIES", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;

  const colW = [ctx.contentW * 0.12, ctx.contentW * 0.10, ctx.contentW * 0.12, ctx.contentW * 0.12, ctx.contentW * 0.12, ctx.contentW * 0.18, ctx.contentW * 0.12, ctx.contentW * 0.12];
  const headers = ["Bank", "Type", "Nature", "Limit", "O/S", "Security", "Rate", "Status"];

  const existRows = facility.existingFacilities.map((f) => [
    f.bank, f.facilityType === "Fund Based" ? "FB" : "NFB", f.nature,
    f.sanctionedLimit, f.outstanding, f.security.substring(0, 22), f.rateOfInterest, f.repaymentStatus,
  ]);
  const existColors = facility.existingFacilities.map((f) =>
    f.repaymentStatus === "Regular" ? colors.safe :
    f.repaymentStatus === "Irregular" || f.repaymentStatus === "SMA-1" || f.repaymentStatus === "SMA-2" ? colors.danger :
    f.repaymentStatus === "NPA" ? colors.danger : colors.warning
  );
  drawTable(ctx, headers, existRows, { colWidths: colW, rowColors: existColors });

  drawKeyValue(ctx, [
    ["Total Existing Fund Based", facility.totalExistingFundBased],
    ["Total Existing Non-Fund Based", facility.totalExistingNonFundBased],
  ]);

  // Proposed Facilities
  checkPage(ctx, 30);
  drawText(ctx, "PROPOSED FACILITIES", ctx.margin + 4, ctx.y, { size: 7, color: colors.primary, style: "bold" });
  ctx.y += 5;

  const propRows = facility.proposedFacilities.map((f) => [
    f.bank, f.facilityType === "Fund Based" ? "FB" : "NFB", f.nature,
    f.sanctionedLimit, f.outstanding, f.security.substring(0, 22), f.rateOfInterest, "—",
  ]);
  drawTable(ctx, headers, propRows, { colWidths: colW });

  drawKeyValue(ctx, [
    ["Total Proposed Fund Based", facility.totalProposedFundBased],
    ["Total Proposed Non-Fund Based", facility.totalProposedNonFundBased],
  ]);
}
