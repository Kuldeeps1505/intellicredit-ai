export type DatasetId = "approve" | "fraud" | "conditional";

export interface Dataset {
  id: DatasetId;
  label: string;
  emoji: string;
  score: number;
  companyName: string;
  cin: string;
  pan: string;
  gstin: string;
  loanAmount: string;
  purpose: string;
  sector: string;
}

export const datasets: Dataset[] = [
  {
    id: "approve",
    label: "Approve",
    emoji: "✅",
    score: 81,
    companyName: "Reliance Textiles Pvt Ltd",
    cin: "U17291MH2019PTC123456",
    pan: "AABCR1234F",
    gstin: "27AABCR1234F1Z5",
    loanAmount: "45,00,00,000",
    purpose: "Working Capital",
    sector: "Textiles & Apparel",
  },
  {
    id: "fraud",
    label: "Fraud / Reject",
    emoji: "🚨",
    score: 28,
    companyName: "Sunrise Exports International",
    cin: "U51909DL2017PTC456789",
    pan: "AADCS5678G",
    gstin: "07AADCS5678G1Z2",
    loanAmount: "22,50,00,000",
    purpose: "Term Loan",
    sector: "Import/Export Trading",
  },
  {
    id: "conditional",
    label: "Conditional",
    emoji: "⚠️",
    score: 61,
    companyName: "GreenField Agro Solutions Ltd",
    cin: "L01100KA2015PLC098765",
    pan: "AABCG9876H",
    gstin: "29AABCG9876H1Z8",
    loanAmount: "12,00,00,000",
    purpose: "Capex Expansion",
    sector: "Agri-Processing",
  },
];

export const getDataset = (id: DatasetId) => datasets.find((d) => d.id === id)!;
