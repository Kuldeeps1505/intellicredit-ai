import { DatasetId } from "./demoData";

export interface LineItem {
  label: string;
  fy22: number;
  fy23: number;
  fy24: number;
  isTotal?: boolean;
  isSubTotal?: boolean;
  indent?: number;
}

export interface RatioItem {
  name: string;
  category: "liquidity" | "leverage" | "profitability" | "efficiency" | "debt_service";
  fy22: number;
  fy23: number;
  fy24: number;
  unit: string;
  benchmark: number;
  anomaly: boolean;
  sparkline: number[];
}

export interface FinancialSpreadsDataset {
  pnl: LineItem[];
  balanceSheet: LineItem[];
  cashFlow: LineItem[];
  ratios: RatioItem[];
}

const approveSpreads: FinancialSpreadsDataset = {
  pnl: [
    { label: "Revenue / Net Sales", fy22: 28500, fy23: 33200, fy24: 37500 },
    { label: "COGS / Cost of Materials", fy22: 18525, fy23: 21248, fy24: 23250 },
    { label: "Gross Profit", fy22: 9975, fy23: 11952, fy24: 14250, isSubTotal: true },
    { label: "Employee Costs", fy22: 2850, fy23: 3154, fy24: 3450 },
    { label: "Other Operating Expenses", fy22: 3078, fy23: 3320, fy24: 3900 },
    { label: "EBITDA", fy22: 4047, fy23: 5478, fy24: 6900, isSubTotal: true },
    { label: "Depreciation & Amortization", fy22: 1140, fy23: 1262, fy24: 1350 },
    { label: "EBIT", fy22: 2907, fy23: 4216, fy24: 5550, isSubTotal: true },
    { label: "Interest Expense", fy22: 1425, fy23: 1328, fy24: 1200 },
    { label: "PBT (Profit Before Tax)", fy22: 1482, fy23: 2888, fy24: 4350, isSubTotal: true },
    { label: "Tax Provision", fy22: 445, fy23: 867, fy24: 1363 },
    { label: "PAT (Profit After Tax)", fy22: 1037, fy23: 2021, fy24: 2987, isTotal: true },
    { label: "Non-recurring Adjustments", fy22: 0, fy23: -120, fy24: 0 },
    { label: "Adjusted PAT", fy22: 1037, fy23: 2141, fy24: 2987, isTotal: true },
  ],
  balanceSheet: [
    { label: "Cash & Bank Balances", fy22: 1850, fy23: 2400, fy24: 3200 },
    { label: "Sundry Debtors / Receivables", fy22: 4275, fy23: 4648, fy24: 4875 },
    { label: "Inventory", fy22: 5700, fy23: 5976, fy24: 5625 },
    { label: "Other Current Assets", fy22: 855, fy23: 996, fy24: 1125 },
    { label: "Total Current Assets", fy22: 12680, fy23: 14020, fy24: 14825, isSubTotal: true },
    { label: "Fixed Assets (Net)", fy22: 14250, fy23: 15540, fy24: 16500 },
    { label: "Intangible Assets", fy22: 285, fy23: 332, fy24: 375 },
    { label: "Investments", fy22: 1425, fy23: 1660, fy24: 1875 },
    { label: "Total Assets", fy22: 28640, fy23: 31552, fy24: 33575, isTotal: true },
    { label: "Sundry Creditors", fy22: 3420, fy23: 3652, fy24: 3750 },
    { label: "Short-term Borrowings", fy22: 4275, fy23: 3984, fy24: 3375 },
    { label: "Current Portion of LTD", fy22: 1140, fy23: 1162, fy24: 1125 },
    { label: "Total Current Liabilities", fy22: 8835, fy23: 8798, fy24: 8250, isSubTotal: true },
    { label: "Long-term Debt", fy22: 7125, fy23: 6640, fy24: 5625 },
    { label: "Other Long-term Liabilities", fy22: 570, fy23: 498, fy24: 450 },
    { label: "Total Liabilities", fy22: 16530, fy23: 15936, fy24: 14325, isTotal: true },
    { label: "Share Capital", fy22: 2850, fy23: 2850, fy24: 2850 },
    { label: "Reserves & Surplus", fy22: 9260, fy23: 12766, fy24: 16400 },
    { label: "Net Worth", fy22: 12110, fy23: 15616, fy24: 19250, isTotal: true },
  ],
  cashFlow: [
    { label: "Operating Cash Flow (OCF)", fy22: 3200, fy23: 4800, fy24: 6100 },
    { label: "Investing Cash Flow", fy22: -2100, fy23: -2400, fy24: -2200 },
    { label: "Financing Cash Flow", fy22: -800, fy23: -1850, fy24: -3100 },
    { label: "Net Change in Cash", fy22: 300, fy23: 550, fy24: 800, isSubTotal: true },
    { label: "Free Cash Flow (OCF - Capex)", fy22: 1100, fy23: 2400, fy24: 3900, isTotal: true },
  ],
  ratios: [
    { name: "Current Ratio", category: "liquidity", fy22: 1.44, fy23: 1.59, fy24: 1.80, unit: "x", benchmark: 1.5, anomaly: false, sparkline: [1.44, 1.59, 1.80] },
    { name: "Quick Ratio", category: "liquidity", fy22: 0.79, fy23: 0.91, fy24: 1.11, unit: "x", benchmark: 1.0, anomaly: false, sparkline: [0.79, 0.91, 1.11] },
    { name: "Working Capital Days", category: "liquidity", fy22: 78, fy23: 70, fy24: 62, unit: "days", benchmark: 75, anomaly: false, sparkline: [78, 70, 62] },
    { name: "D/E Ratio", category: "leverage", fy22: 1.80, fy23: 1.35, fy24: 1.15, unit: "x", benchmark: 2.0, anomaly: false, sparkline: [1.80, 1.35, 1.15] },
    { name: "Total Debt/EBITDA", category: "leverage", fy22: 2.82, fy23: 1.94, fy24: 1.30, unit: "x", benchmark: 3.0, anomaly: false, sparkline: [2.82, 1.94, 1.30] },
    { name: "Interest Coverage (ICR)", category: "leverage", fy22: 2.04, fy23: 3.17, fy24: 4.63, unit: "x", benchmark: 2.5, anomaly: false, sparkline: [2.04, 3.17, 4.63] },
    { name: "Gross Margin", category: "profitability", fy22: 35.0, fy23: 36.0, fy24: 38.0, unit: "%", benchmark: 30, anomaly: false, sparkline: [35.0, 36.0, 38.0] },
    { name: "EBITDA Margin", category: "profitability", fy22: 14.2, fy23: 16.5, fy24: 18.4, unit: "%", benchmark: 15, anomaly: false, sparkline: [14.2, 16.5, 18.4] },
    { name: "Net Margin", category: "profitability", fy22: 3.6, fy23: 6.1, fy24: 8.0, unit: "%", benchmark: 5, anomaly: false, sparkline: [3.6, 6.1, 8.0] },
    { name: "ROE", category: "profitability", fy22: 8.6, fy23: 12.9, fy24: 15.5, unit: "%", benchmark: 12, anomaly: false, sparkline: [8.6, 12.9, 15.5] },
    { name: "ROA", category: "profitability", fy22: 3.6, fy23: 6.4, fy24: 8.9, unit: "%", benchmark: 5, anomaly: false, sparkline: [3.6, 6.4, 8.9] },
    { name: "DSO (Receivable Days)", category: "efficiency", fy22: 55, fy23: 51, fy24: 47, unit: "days", benchmark: 60, anomaly: false, sparkline: [55, 51, 47] },
    { name: "Inventory Days", category: "efficiency", fy22: 73, fy23: 66, fy24: 55, unit: "days", benchmark: 70, anomaly: false, sparkline: [73, 66, 55] },
    { name: "Payable Days", category: "efficiency", fy22: 44, fy23: 40, fy24: 37, unit: "days", benchmark: 45, anomaly: false, sparkline: [44, 40, 37] },
    { name: "Cash Conversion Cycle", category: "efficiency", fy22: 84, fy23: 77, fy24: 65, unit: "days", benchmark: 80, anomaly: false, sparkline: [84, 77, 65] },
    { name: "DSCR", category: "debt_service", fy22: 1.42, fy23: 1.72, fy24: 1.95, unit: "x", benchmark: 1.5, anomaly: false, sparkline: [1.42, 1.72, 1.95] },
    { name: "Fixed Charge Coverage", category: "debt_service", fy22: 1.28, fy23: 1.55, fy24: 1.82, unit: "x", benchmark: 1.25, anomaly: false, sparkline: [1.28, 1.55, 1.82] },
  ],
};

const fraudSpreads: FinancialSpreadsDataset = {
  pnl: [
    { label: "Revenue / Net Sales", fy22: 18200, fy23: 42500, fy24: 52000 },
    { label: "COGS / Cost of Materials", fy22: 15470, fy23: 38250, fy24: 47320 },
    { label: "Gross Profit", fy22: 2730, fy23: 4250, fy24: 4680, isSubTotal: true },
    { label: "Employee Costs", fy22: 364, fy23: 425, fy24: 520 },
    { label: "Other Operating Expenses", fy22: 1456, fy23: 2975, fy24: 3640 },
    { label: "EBITDA", fy22: 910, fy23: 850, fy24: 520, isSubTotal: true },
    { label: "Depreciation & Amortization", fy22: 182, fy23: 212, fy24: 260 },
    { label: "EBIT", fy22: 728, fy23: 638, fy24: 260, isSubTotal: true },
    { label: "Interest Expense", fy22: 546, fy23: 1275, fy24: 1820 },
    { label: "PBT (Profit Before Tax)", fy22: 182, fy23: -637, fy24: -1560, isSubTotal: true },
    { label: "Tax Provision", fy22: 55, fy23: 0, fy24: 0 },
    { label: "PAT (Profit After Tax)", fy22: 127, fy23: -637, fy24: -1560, isTotal: true },
    { label: "Non-recurring Adjustments", fy22: 0, fy23: 420, fy24: 0 },
    { label: "Adjusted PAT", fy22: 127, fy23: -217, fy24: -1560, isTotal: true },
  ],
  balanceSheet: [
    { label: "Cash & Bank Balances", fy22: 920, fy23: 425, fy24: 260 },
    { label: "Sundry Debtors / Receivables", fy22: 3640, fy23: 12750, fy24: 18200 },
    { label: "Inventory", fy22: 2730, fy23: 8500, fy24: 10400 },
    { label: "Other Current Assets", fy22: 546, fy23: 2125, fy24: 3640 },
    { label: "Total Current Assets", fy22: 7836, fy23: 23800, fy24: 32500, isSubTotal: true },
    { label: "Fixed Assets (Net)", fy22: 2184, fy23: 2550, fy24: 2600 },
    { label: "Intangible Assets", fy22: 91, fy23: 85, fy24: 104 },
    { label: "Investments", fy22: 364, fy23: 425, fy24: 520 },
    { label: "Total Assets", fy22: 10475, fy23: 26860, fy24: 35724, isTotal: true },
    { label: "Sundry Creditors", fy22: 2730, fy23: 8925, fy24: 12480 },
    { label: "Short-term Borrowings", fy22: 2184, fy23: 7650, fy24: 11440 },
    { label: "Current Portion of LTD", fy22: 364, fy23: 850, fy24: 1560 },
    { label: "Total Current Liabilities", fy22: 5278, fy23: 17425, fy24: 25480, isSubTotal: true },
    { label: "Long-term Debt", fy22: 1820, fy23: 5100, fy24: 7280 },
    { label: "Other Long-term Liabilities", fy22: 182, fy23: 425, fy24: 520 },
    { label: "Total Liabilities", fy22: 7280, fy23: 22950, fy24: 33280, isTotal: true },
    { label: "Share Capital", fy22: 1000, fy23: 1000, fy24: 1000 },
    { label: "Reserves & Surplus", fy22: 2195, fy23: 2910, fy24: 1444 },
    { label: "Net Worth", fy22: 3195, fy23: 3910, fy24: 2444, isTotal: true },
  ],
  cashFlow: [
    { label: "Operating Cash Flow (OCF)", fy22: 650, fy23: -1200, fy24: -3800 },
    { label: "Investing Cash Flow", fy22: -300, fy23: -450, fy24: -200 },
    { label: "Financing Cash Flow", fy22: 200, fy23: 1150, fy24: 3840 },
    { label: "Net Change in Cash", fy22: 550, fy23: -500, fy24: -160, isSubTotal: true },
    { label: "Free Cash Flow (OCF - Capex)", fy22: 350, fy23: -1650, fy24: -4000, isTotal: true },
  ],
  ratios: [
    { name: "Current Ratio", category: "liquidity", fy22: 1.48, fy23: 1.37, fy24: 1.28, unit: "x", benchmark: 1.5, anomaly: true, sparkline: [1.48, 1.37, 1.28] },
    { name: "Quick Ratio", category: "liquidity", fy22: 0.97, fy23: 0.88, fy24: 0.87, unit: "x", benchmark: 1.0, anomaly: true, sparkline: [0.97, 0.88, 0.87] },
    { name: "Working Capital Days", category: "liquidity", fy22: 52, fy23: 55, fy24: 49, unit: "days", benchmark: 75, anomaly: false, sparkline: [52, 55, 49] },
    { name: "D/E Ratio", category: "leverage", fy22: 1.25, fy23: 3.26, fy24: 7.68, unit: "x", benchmark: 2.0, anomaly: true, sparkline: [1.25, 3.26, 7.68] },
    { name: "Total Debt/EBITDA", category: "leverage", fy22: 4.40, fy23: 15.00, fy24: 36.00, unit: "x", benchmark: 3.0, anomaly: true, sparkline: [4.40, 15.00, 36.00] },
    { name: "Interest Coverage (ICR)", category: "leverage", fy22: 1.33, fy23: 0.50, fy24: 0.14, unit: "x", benchmark: 2.5, anomaly: true, sparkline: [1.33, 0.50, 0.14] },
    { name: "Gross Margin", category: "profitability", fy22: 15.0, fy23: 10.0, fy24: 9.0, unit: "%", benchmark: 30, anomaly: true, sparkline: [15.0, 10.0, 9.0] },
    { name: "EBITDA Margin", category: "profitability", fy22: 5.0, fy23: 2.0, fy24: 1.0, unit: "%", benchmark: 15, anomaly: true, sparkline: [5.0, 2.0, 1.0] },
    { name: "Net Margin", category: "profitability", fy22: 0.7, fy23: -1.5, fy24: -3.0, unit: "%", benchmark: 5, anomaly: true, sparkline: [0.7, -1.5, -3.0] },
    { name: "ROE", category: "profitability", fy22: 4.0, fy23: -16.3, fy24: -63.8, unit: "%", benchmark: 12, anomaly: true, sparkline: [4.0, -16.3, -63.8] },
    { name: "ROA", category: "profitability", fy22: 1.2, fy23: -2.4, fy24: -4.4, unit: "%", benchmark: 5, anomaly: true, sparkline: [1.2, -2.4, -4.4] },
    { name: "DSO (Receivable Days)", category: "efficiency", fy22: 73, fy23: 110, fy24: 128, unit: "days", benchmark: 60, anomaly: true, sparkline: [73, 110, 128] },
    { name: "Inventory Days", category: "efficiency", fy22: 55, fy23: 73, fy24: 73, unit: "days", benchmark: 70, anomaly: true, sparkline: [55, 73, 73] },
    { name: "Payable Days", category: "efficiency", fy22: 55, fy23: 77, fy24: 88, unit: "days", benchmark: 45, anomaly: true, sparkline: [55, 77, 88] },
    { name: "Cash Conversion Cycle", category: "efficiency", fy22: 73, fy23: 106, fy24: 113, unit: "days", benchmark: 80, anomaly: true, sparkline: [73, 106, 113] },
    { name: "DSCR", category: "debt_service", fy22: 0.85, fy23: 0.42, fy24: 0.18, unit: "x", benchmark: 1.5, anomaly: true, sparkline: [0.85, 0.42, 0.18] },
    { name: "Fixed Charge Coverage", category: "debt_service", fy22: 0.72, fy23: 0.35, fy24: 0.12, unit: "x", benchmark: 1.25, anomaly: true, sparkline: [0.72, 0.35, 0.12] },
  ],
};

const conditionalSpreads: FinancialSpreadsDataset = {
  pnl: [
    { label: "Revenue / Net Sales", fy22: 8500, fy23: 9800, fy24: 10200 },
    { label: "COGS / Cost of Materials", fy22: 5950, fy23: 6860, fy24: 7344 },
    { label: "Gross Profit", fy22: 2550, fy23: 2940, fy24: 2856, isSubTotal: true },
    { label: "Employee Costs", fy22: 680, fy23: 784, fy24: 918 },
    { label: "Other Operating Expenses", fy22: 850, fy23: 980, fy24: 1122 },
    { label: "EBITDA", fy22: 1020, fy23: 1176, fy24: 816, isSubTotal: true },
    { label: "Depreciation & Amortization", fy22: 340, fy23: 392, fy24: 408 },
    { label: "EBIT", fy22: 680, fy23: 784, fy24: 408, isSubTotal: true },
    { label: "Interest Expense", fy22: 382, fy23: 441, fy24: 510 },
    { label: "PBT (Profit Before Tax)", fy22: 298, fy23: 343, fy24: -102, isSubTotal: true },
    { label: "Tax Provision", fy22: 89, fy23: 103, fy24: 0 },
    { label: "PAT (Profit After Tax)", fy22: 209, fy23: 240, fy24: -102, isTotal: true },
    { label: "Non-recurring Adjustments", fy22: 0, fy23: 0, fy24: -180 },
    { label: "Adjusted PAT", fy22: 209, fy23: 240, fy24: 78, isTotal: true },
  ],
  balanceSheet: [
    { label: "Cash & Bank Balances", fy22: 680, fy23: 588, fy24: 408 },
    { label: "Sundry Debtors / Receivables", fy22: 1275, fy23: 1568, fy24: 1836 },
    { label: "Inventory", fy22: 1700, fy23: 1960, fy24: 2244 },
    { label: "Other Current Assets", fy22: 340, fy23: 392, fy24: 408 },
    { label: "Total Current Assets", fy22: 3995, fy23: 4508, fy24: 4896, isSubTotal: true },
    { label: "Fixed Assets (Net)", fy22: 4250, fy23: 5880, fy24: 7140 },
    { label: "Intangible Assets", fy22: 85, fy23: 98, fy24: 102 },
    { label: "Investments", fy22: 425, fy23: 490, fy24: 510 },
    { label: "Total Assets", fy22: 8755, fy23: 10976, fy24: 12648, isTotal: true },
    { label: "Sundry Creditors", fy22: 1020, fy23: 1176, fy24: 1326 },
    { label: "Short-term Borrowings", fy22: 1275, fy23: 1568, fy24: 2040 },
    { label: "Current Portion of LTD", fy22: 340, fy23: 392, fy24: 510 },
    { label: "Total Current Liabilities", fy22: 2635, fy23: 3136, fy24: 3876, isSubTotal: true },
    { label: "Long-term Debt", fy22: 2550, fy23: 3430, fy24: 4590 },
    { label: "Other Long-term Liabilities", fy22: 170, fy23: 196, fy24: 204 },
    { label: "Total Liabilities", fy22: 5355, fy23: 6762, fy24: 8670, isTotal: true },
    { label: "Share Capital", fy22: 1500, fy23: 1500, fy24: 1500 },
    { label: "Reserves & Surplus", fy22: 1900, fy23: 2714, fy24: 2478 },
    { label: "Net Worth", fy22: 3400, fy23: 4214, fy24: 3978, isTotal: true },
  ],
  cashFlow: [
    { label: "Operating Cash Flow (OCF)", fy22: 850, fy23: 920, fy24: 380 },
    { label: "Investing Cash Flow", fy22: -600, fy23: -1800, fy24: -1600 },
    { label: "Financing Cash Flow", fy22: -150, fy23: 800, fy24: 1040 },
    { label: "Net Change in Cash", fy22: 100, fy23: -80, fy24: -180, isSubTotal: true },
    { label: "Free Cash Flow (OCF - Capex)", fy22: 250, fy23: -880, fy24: -1220, isTotal: true },
  ],
  ratios: [
    { name: "Current Ratio", category: "liquidity", fy22: 1.52, fy23: 1.44, fy24: 1.26, unit: "x", benchmark: 1.5, anomaly: true, sparkline: [1.52, 1.44, 1.26] },
    { name: "Quick Ratio", category: "liquidity", fy22: 0.87, fy23: 0.81, fy24: 0.68, unit: "x", benchmark: 1.0, anomaly: true, sparkline: [0.87, 0.81, 0.68] },
    { name: "Working Capital Days", category: "liquidity", fy22: 58, fy23: 51, fy24: 36, unit: "days", benchmark: 75, anomaly: false, sparkline: [58, 51, 36] },
    { name: "D/E Ratio", category: "leverage", fy22: 1.13, fy23: 1.19, fy24: 1.67, unit: "x", benchmark: 2.0, anomaly: false, sparkline: [1.13, 1.19, 1.67] },
    { name: "Total Debt/EBITDA", category: "leverage", fy22: 3.75, fy23: 4.25, fy24: 8.12, unit: "x", benchmark: 3.0, anomaly: true, sparkline: [3.75, 4.25, 8.12] },
    { name: "Interest Coverage (ICR)", category: "leverage", fy22: 1.78, fy23: 1.78, fy24: 0.80, unit: "x", benchmark: 2.5, anomaly: true, sparkline: [1.78, 1.78, 0.80] },
    { name: "Gross Margin", category: "profitability", fy22: 30.0, fy23: 30.0, fy24: 28.0, unit: "%", benchmark: 30, anomaly: false, sparkline: [30.0, 30.0, 28.0] },
    { name: "EBITDA Margin", category: "profitability", fy22: 12.0, fy23: 12.0, fy24: 8.0, unit: "%", benchmark: 15, anomaly: true, sparkline: [12.0, 12.0, 8.0] },
    { name: "Net Margin", category: "profitability", fy22: 2.5, fy23: 2.4, fy24: -1.0, unit: "%", benchmark: 5, anomaly: true, sparkline: [2.5, 2.4, -1.0] },
    { name: "ROE", category: "profitability", fy22: 6.1, fy23: 5.7, fy24: -2.6, unit: "%", benchmark: 12, anomaly: true, sparkline: [6.1, 5.7, -2.6] },
    { name: "ROA", category: "profitability", fy22: 2.4, fy23: 2.2, fy24: -0.8, unit: "%", benchmark: 5, anomaly: true, sparkline: [2.4, 2.2, -0.8] },
    { name: "DSO (Receivable Days)", category: "efficiency", fy22: 55, fy23: 58, fy24: 66, unit: "days", benchmark: 60, anomaly: true, sparkline: [55, 58, 66] },
    { name: "Inventory Days", category: "efficiency", fy22: 73, fy23: 73, fy24: 80, unit: "days", benchmark: 70, anomaly: true, sparkline: [73, 73, 80] },
    { name: "Payable Days", category: "efficiency", fy22: 44, fy23: 44, fy24: 47, unit: "days", benchmark: 45, anomaly: false, sparkline: [44, 44, 47] },
    { name: "Cash Conversion Cycle", category: "efficiency", fy22: 84, fy23: 87, fy24: 99, unit: "days", benchmark: 80, anomaly: true, sparkline: [84, 87, 99] },
    { name: "DSCR", category: "debt_service", fy22: 1.35, fy23: 1.28, fy24: 0.72, unit: "x", benchmark: 1.5, anomaly: true, sparkline: [1.35, 1.28, 0.72] },
    { name: "Fixed Charge Coverage", category: "debt_service", fy22: 1.18, fy23: 1.12, fy24: 0.58, unit: "x", benchmark: 1.25, anomaly: true, sparkline: [1.18, 1.12, 0.58] },
  ],
};

export function getFinancialSpreadsData(id: DatasetId): FinancialSpreadsDataset {
  switch (id) {
    case "approve": return approveSpreads;
    case "fraud": return fraudSpreads;
    case "conditional": return conditionalSpreads;
  }
}
