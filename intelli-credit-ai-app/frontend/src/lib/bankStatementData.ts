import { DatasetId } from "./demoData";

export interface MonthlyCashFlow {
  month: string;
  credits: number;
  debits: number;
  closing: number;
}

export interface TransactionCategory {
  category: string;
  amount: number;
  percentage: number;
  txnCount: number;
}

export interface RedFlag {
  type: string;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  detected: boolean;
  details?: string;
}

export interface Counterparty {
  name: string;
  credits: number;
  debits: number;
  net: number;
  frequency: number;
  risk: "low" | "medium" | "high";
}

export interface BankStatementDataset {
  summary: {
    abb: number;
    avgMonthlyCredits: number;
    avgMonthlyDebits: number;
    creditDebitRatio: number;
    emiObligations: number;
    emiCount: number;
    bounceRatio: number;
    totalBounces: number;
    cashWithdrawalPercent: number;
    behaviorScore: number;
  };
  monthlyCashFlow: MonthlyCashFlow[];
  creditCategories: TransactionCategory[];
  debitCategories: TransactionCategory[];
  redFlags: RedFlag[];
  topCounterparties: Counterparty[];
}

const approveBankStatement: BankStatementDataset = {
  summary: {
    abb: 342,
    avgMonthlyCredits: 3125,
    avgMonthlyDebits: 2890,
    creditDebitRatio: 1.08,
    emiObligations: 112,
    emiCount: 2,
    bounceRatio: 0.8,
    totalBounces: 2,
    cashWithdrawalPercent: 4.2,
    behaviorScore: 88,
  },
  monthlyCashFlow: [
    { month: "Jan", credits: 2950, debits: 2780, closing: 312 },
    { month: "Feb", credits: 3100, debits: 2850, closing: 362 },
    { month: "Mar", credits: 3400, debits: 3200, closing: 342 },
    { month: "Apr", credits: 2800, debits: 2700, closing: 322 },
    { month: "May", credits: 3050, debits: 2880, closing: 352 },
    { month: "Jun", credits: 3200, debits: 2950, closing: 372 },
    { month: "Jul", credits: 3350, debits: 3100, closing: 382 },
    { month: "Aug", credits: 2900, debits: 2800, closing: 342 },
    { month: "Sep", credits: 3150, debits: 2900, closing: 352 },
    { month: "Oct", credits: 3400, debits: 3050, closing: 362 },
    { month: "Nov", credits: 3200, debits: 2950, closing: 348 },
    { month: "Dec", credits: 3000, debits: 2820, closing: 358 },
  ],
  creditCategories: [
    { category: "Business Income", amount: 32400, percentage: 86.4, txnCount: 145 },
    { category: "Export Receivables", amount: 3200, percentage: 8.5, txnCount: 12 },
    { category: "Interest/Dividends", amount: 850, percentage: 2.3, txnCount: 6 },
    { category: "Other Credits", amount: 1050, percentage: 2.8, txnCount: 18 },
  ],
  debitCategories: [
    { category: "Supplier Payments", amount: 22800, percentage: 65.8, txnCount: 210 },
    { category: "Employee Salaries", amount: 4200, percentage: 12.1, txnCount: 36 },
    { category: "EMI Payments", amount: 1344, percentage: 3.9, txnCount: 24 },
    { category: "Tax Payments", amount: 2800, percentage: 8.1, txnCount: 15 },
    { category: "Utilities & Rent", amount: 1800, percentage: 5.2, txnCount: 48 },
    { category: "Other Debits", amount: 1736, percentage: 4.9, txnCount: 65 },
  ],
  redFlags: [
    { type: "Circular Transactions", severity: "critical", description: "Same amount credited and debited within 48h between related accounts", detected: false },
    { type: "End-of-Month Window Dressing", severity: "high", description: "Large credits on 28th-30th reversed on 1st-3rd", detected: false },
    { type: "Cash Deposit Spikes", severity: "high", description: "Large cash deposits before statement date", detected: false },
    { type: "Irregular Income Pattern", severity: "medium", description: "High variance in monthly credits (>50% CoV)", detected: false },
    { type: "High Bounce Rate", severity: "medium", description: "Cheque/ECS returns > 5%", detected: false },
    { type: "Declining Balance Trend", severity: "medium", description: "ABB declining 3+ consecutive months", detected: false },
    { type: "Loan Stacking", severity: "high", description: "Multiple new EMI debits in recent months", detected: false },
  ],
  topCounterparties: [
    { name: "Arvind Mills Ltd", credits: 8400, debits: 0, net: 8400, frequency: 36, risk: "low" },
    { name: "Raymond Ltd", credits: 6200, debits: 0, net: 6200, frequency: 24, risk: "low" },
    { name: "Welspun India", credits: 4800, debits: 0, net: 4800, frequency: 18, risk: "low" },
    { name: "Gujarat Cotton Suppliers", credits: 0, debits: 9600, net: -9600, frequency: 48, risk: "low" },
    { name: "HDFC Bank — Term Loan EMI", credits: 0, debits: 840, net: -840, frequency: 12, risk: "low" },
    { name: "SBI — CC Interest", credits: 0, debits: 504, net: -504, frequency: 12, risk: "low" },
  ],
};

const fraudBankStatement: BankStatementDataset = {
  summary: {
    abb: 85,
    avgMonthlyCredits: 4375,
    avgMonthlyDebits: 4290,
    creditDebitRatio: 1.02,
    emiObligations: 285,
    emiCount: 5,
    bounceRatio: 14.2,
    totalBounces: 34,
    cashWithdrawalPercent: 28.5,
    behaviorScore: 22,
  },
  monthlyCashFlow: [
    { month: "Jan", credits: 3800, debits: 3900, closing: 120 },
    { month: "Feb", credits: 4200, debits: 4350, closing: 85 },
    { month: "Mar", credits: 5500, debits: 5200, closing: 180 },
    { month: "Apr", credits: 3200, debits: 3400, closing: 65 },
    { month: "May", credits: 4800, debits: 4700, closing: 95 },
    { month: "Jun", credits: 5200, debits: 5300, closing: 48 },
    { month: "Jul", credits: 3900, debits: 3850, closing: 72 },
    { month: "Aug", credits: 4600, debits: 4550, closing: 88 },
    { month: "Sep", credits: 5800, debits: 5700, closing: 112 },
    { month: "Oct", credits: 3500, debits: 3600, closing: 65 },
    { month: "Nov", credits: 4100, debits: 4200, closing: 42 },
    { month: "Dec", credits: 3900, debits: 3730, closing: 52 },
  ],
  creditCategories: [
    { category: "Business Income", amount: 28500, percentage: 54.3, txnCount: 85 },
    { category: "Inter-Company Transfers", amount: 14200, percentage: 27.0, txnCount: 42 },
    { category: "Cash Deposits", amount: 6800, percentage: 13.0, txnCount: 28 },
    { category: "Other Credits", amount: 3000, percentage: 5.7, txnCount: 15 },
  ],
  debitCategories: [
    { category: "Supplier Payments", amount: 18400, percentage: 35.7, txnCount: 120 },
    { category: "Inter-Company Transfers", amount: 12800, percentage: 24.9, txnCount: 38 },
    { category: "Cash Withdrawals", amount: 8200, percentage: 15.9, txnCount: 65 },
    { category: "EMI Payments", amount: 3420, percentage: 6.6, txnCount: 60 },
    { category: "Employee Salaries", amount: 520, percentage: 1.0, txnCount: 12 },
    { category: "Other Debits", amount: 8140, percentage: 15.9, txnCount: 95 },
  ],
  redFlags: [
    { type: "Circular Transactions", severity: "critical", description: "Same amount credited and debited within 48h between related accounts", detected: true, details: "₹8.4Cr circular flow detected: Sunrise → Zenith Trading → Golden Exports → Sunrise. Pattern repeats monthly." },
    { type: "End-of-Month Window Dressing", severity: "high", description: "Large credits on 28th-30th reversed on 1st-3rd", detected: true, details: "₹2.1Cr credited on 29th Mar, ₹1.9Cr debited on 2nd Apr. Similar pattern in Jun, Sep." },
    { type: "Cash Deposit Spikes", severity: "high", description: "Large cash deposits before statement date", detected: true, details: "Cash deposits of ₹45L-₹80L on 25th-28th of month, 6 out of 12 months." },
    { type: "Irregular Income Pattern", severity: "medium", description: "High variance in monthly credits (>50% CoV)", detected: true, details: "Coefficient of variation: 68.2%. Monthly credits range from ₹32L to ₹58L." },
    { type: "High Bounce Rate", severity: "medium", description: "Cheque/ECS returns > 5%", detected: true, details: "34 bounces out of 240 transactions (14.2%). Includes 5 EMI bounces." },
    { type: "Declining Balance Trend", severity: "medium", description: "ABB declining 3+ consecutive months", detected: true, details: "ABB declined from ₹1.8Cr (Jan) to ₹0.52Cr (Dec) — 71% decline over 12 months." },
    { type: "Loan Stacking", severity: "high", description: "Multiple new EMI debits in recent months", detected: true, details: "3 new EMI obligations appeared in last 4 months totaling ₹1.8Cr/month." },
  ],
  topCounterparties: [
    { name: "Zenith Trading Co", credits: 9200, debits: 8400, net: 800, frequency: 42, risk: "high" },
    { name: "Golden Exports Ltd", credits: 5800, debits: 5200, net: 600, frequency: 28, risk: "high" },
    { name: "Starline Impex Pvt Ltd", credits: 3200, debits: 2800, net: 400, frequency: 18, risk: "high" },
    { name: "Cash Deposits (ATM/Branch)", credits: 6800, debits: 0, net: 6800, frequency: 28, risk: "high" },
    { name: "PNB — Term Loan EMI", credits: 0, debits: 1440, net: -1440, frequency: 12, risk: "medium" },
    { name: "ICICI — OD Interest", credits: 0, debits: 960, net: -960, frequency: 12, risk: "medium" },
    { name: "Bajaj Finance — EMI", credits: 0, debits: 720, net: -720, frequency: 8, risk: "medium" },
  ],
};

const conditionalBankStatement: BankStatementDataset = {
  summary: {
    abb: 148,
    avgMonthlyCredits: 1020,
    avgMonthlyDebits: 985,
    creditDebitRatio: 1.04,
    emiObligations: 68,
    emiCount: 2,
    bounceRatio: 3.8,
    totalBounces: 9,
    cashWithdrawalPercent: 12.5,
    behaviorScore: 58,
  },
  monthlyCashFlow: [
    { month: "Jan", credits: 980, debits: 920, closing: 165 },
    { month: "Feb", credits: 850, debits: 880, closing: 148 },
    { month: "Mar", credits: 1100, debits: 1050, closing: 162 },
    { month: "Apr", credits: 920, debits: 950, closing: 138 },
    { month: "May", credits: 1050, debits: 980, closing: 155 },
    { month: "Jun", credits: 1200, debits: 1100, closing: 172 },
    { month: "Jul", credits: 880, debits: 920, closing: 142 },
    { month: "Aug", credits: 1080, debits: 1020, closing: 158 },
    { month: "Sep", credits: 1150, debits: 1080, closing: 148 },
    { month: "Oct", credits: 950, debits: 980, closing: 128 },
    { month: "Nov", credits: 1020, debits: 1050, closing: 118 },
    { month: "Dec", credits: 1060, debits: 890, closing: 142 },
  ],
  creditCategories: [
    { category: "Business Income", amount: 9800, percentage: 80.1, txnCount: 96 },
    { category: "Agri Subsidy Credits", amount: 1200, percentage: 9.8, txnCount: 4 },
    { category: "Inter-Company Transfers", amount: 680, percentage: 5.6, txnCount: 8 },
    { category: "Other Credits", amount: 560, percentage: 4.5, txnCount: 12 },
  ],
  debitCategories: [
    { category: "Supplier Payments", amount: 6200, percentage: 52.5, txnCount: 110 },
    { category: "Employee Salaries", amount: 1800, percentage: 15.2, txnCount: 24 },
    { category: "EMI Payments", amount: 816, percentage: 6.9, txnCount: 24 },
    { category: "Capex Payments", amount: 1400, percentage: 11.9, txnCount: 8 },
    { category: "Tax Payments", amount: 680, percentage: 5.8, txnCount: 10 },
    { category: "Other Debits", amount: 924, percentage: 7.7, txnCount: 42 },
  ],
  redFlags: [
    { type: "Circular Transactions", severity: "critical", description: "Same amount credited and debited within 48h between related accounts", detected: false },
    { type: "End-of-Month Window Dressing", severity: "high", description: "Large credits on 28th-30th reversed on 1st-3rd", detected: false },
    { type: "Cash Deposit Spikes", severity: "high", description: "Large cash deposits before statement date", detected: false },
    { type: "Irregular Income Pattern", severity: "medium", description: "High variance in monthly credits (>50% CoV)", detected: true, details: "Seasonal agri business — CoV of 42%. Credits drop 30% in Jul-Aug (monsoon)." },
    { type: "High Bounce Rate", severity: "medium", description: "Cheque/ECS returns > 5%", detected: false },
    { type: "Declining Balance Trend", severity: "medium", description: "ABB declining 3+ consecutive months", detected: true, details: "ABB declined from ₹1.72Cr (Jun) to ₹1.18Cr (Nov) — 5 consecutive months. Likely due to capex." },
    { type: "Loan Stacking", severity: "high", description: "Multiple new EMI debits in recent months", detected: false },
  ],
  topCounterparties: [
    { name: "AgriCorp India Pvt Ltd", credits: 3800, debits: 0, net: 3800, frequency: 18, risk: "medium" },
    { name: "Karnataka Agri Co-op", credits: 2400, debits: 0, net: 2400, frequency: 12, risk: "low" },
    { name: "Reddy Farms LLP", credits: 680, debits: 420, net: 260, frequency: 8, risk: "low" },
    { name: "Agri Input Suppliers", credits: 0, debits: 3600, net: -3600, frequency: 48, risk: "low" },
    { name: "Canara Bank — Term Loan EMI", credits: 0, debits: 540, net: -540, frequency: 12, risk: "low" },
    { name: "SBI — CC Interest", credits: 0, debits: 276, net: -276, frequency: 12, risk: "low" },
  ],
};

export function getBankStatementData(id: DatasetId): BankStatementDataset {
  switch (id) {
    case "approve": return approveBankStatement;
    case "fraud": return fraudBankStatement;
    case "conditional": return conditionalBankStatement;
  }
}
