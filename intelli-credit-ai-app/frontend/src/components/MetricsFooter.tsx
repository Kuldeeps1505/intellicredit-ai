import { useState, useEffect } from "react";
import { usePipeline } from "@/contexts/PipelineContext";
import { getRiskData } from "@/lib/riskData";
import { getFinancialSpreadsData } from "@/lib/financialSpreadsData";
import { getBankStatementData } from "@/lib/bankStatementData";
import { getCamData } from "@/lib/camData";
import { api } from "@/lib/api";
import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import type { RiskDataset } from "@/lib/riskData";
import type { CamDataset } from "@/lib/camData";
import type { BankStatementDataset } from "@/lib/bankStatementData";
import type { FinancialSpreadsDataset } from "@/lib/financialSpreadsData";

const decConfig = {
  approve:     { label: "APPROVE",     color: "text-safe",        Icon: CheckCircle2 },
  reject:      { label: "REJECT",      color: "text-destructive", Icon: XCircle },
  conditional: { label: "CONDITIONAL", color: "text-warning",     Icon: AlertTriangle },
};

export function MetricsFooter() {
  const { applicationId } = usePipeline();

  const [risk, setRisk]       = useState<RiskDataset>(getRiskData("fraud"));
  const [spreads, setSpreads] = useState<FinancialSpreadsDataset>(getFinancialSpreadsData("fraud"));
  const [bank, setBank]       = useState<BankStatementDataset>(getBankStatementData("fraud"));
  const [cam, setCam]         = useState<CamDataset>(getCamData("fraud"));

  useEffect(() => {
    if (!applicationId) return;
    api.getRisk(applicationId).then(setRisk).catch(() => {});
    api.getFinancials(applicationId).then(setSpreads).catch(() => {});
    api.getBankAnalytics(applicationId).then(setBank).catch(() => {});
    api.getCam(applicationId).then(setCam).catch(() => {});
  }, [applicationId]);

  const dscr    = spreads?.ratios?.find(r => r.name === "DSCR")?.fy24 ?? "—";
  const deRatio = spreads?.ratios?.find(r => r.name === "D/E Ratio")?.fy24 ?? "—";
  const dec     = decConfig[cam?.recommendation?.decision as keyof typeof decConfig] ?? decConfig.conditional;
  const DecIcon = dec.Icon;

  const scoreColor =
    risk.score >= 70 ? "text-safe" :
    risk.score >= 50 ? "text-warning" : "text-destructive";

  return (
    <footer className="h-9 border-t border-border/50 bg-card backdrop-blur-sm shadow-footer flex items-center justify-between px-6 text-[10px] font-mono-numbers">
      <div className="flex items-center gap-5">
        <MetricPill label="Score"  value={`${risk.score}`}              color={scoreColor} />
        <MetricPill label="DSCR"   value={`${dscr}x`}                   color={Number(dscr) >= 1.5 ? "text-safe" : Number(dscr) >= 1.0 ? "text-warning" : "text-destructive"} />
        <MetricPill label="D/E"    value={`${deRatio}x`}                color={Number(deRatio) <= 1.5 ? "text-safe" : Number(deRatio) <= 2.5 ? "text-warning" : "text-destructive"} />
        <MetricPill label="ABB"    value={`₹${bank?.summary?.abb ?? "—"}L`} color="text-muted-foreground" />
        <MetricPill label="PD 12m" value={`${risk.defaultProb12m}%`}    color={risk.defaultProb12m <= 5 ? "text-safe" : risk.defaultProb12m <= 15 ? "text-warning" : "text-destructive"} />
      </div>
      <div className="flex items-center gap-1.5">
        <DecIcon className={`h-3 w-3 ${dec.color}`} />
        <span className={`font-display font-bold ${dec.color}`}>{dec.label}</span>
      </div>
    </footer>
  );
}

function MetricPill({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-muted-foreground/60 font-display uppercase">{label}</span>
      <span className={`font-bold ${color}`}>{value}</span>
    </div>
  );
}
