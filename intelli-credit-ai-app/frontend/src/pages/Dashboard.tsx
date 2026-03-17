import { Link } from "react-router-dom";
import { useDataset } from "@/contexts/DatasetContext";
import { getRiskData } from "@/lib/riskData";
import { getPromoterData } from "@/lib/promoterData";
import { getDiligenceData } from "@/lib/diligenceData";
import { getCamData } from "@/lib/camData";
import { getFinancialSpreadsData } from "@/lib/financialSpreadsData";
import { getBankStatementData } from "@/lib/bankStatementData";
import { getAuditTrailData } from "@/lib/auditTrailData";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { motion } from "framer-motion";
import {
  Upload, Activity, BarChart3, Users, FileEdit, FileText,
  ArrowRight, AlertTriangle, CheckCircle2, XCircle, ShieldAlert,
  TrendingUp, TrendingDown, Zap, Landmark, ClipboardList, IndianRupee,
} from "lucide-react";

const scoreColor = (s: number) =>
  s >= 70 ? "text-safe" : s >= 50 ? "text-warning" : "text-destructive";

const scoreGlow = (s: number) =>
  s >= 70 ? "shadow-safe/20" : s >= 50 ? "shadow-warning/20" : "shadow-destructive/20";

const decLabel: Record<string, { text: string; color: string; icon: typeof CheckCircle2 }> = {
  approve: { text: "APPROVE", color: "text-safe", icon: CheckCircle2 },
  reject: { text: "REJECT", color: "text-destructive", icon: XCircle },
  conditional: { text: "CONDITIONAL", color: "text-warning", icon: AlertTriangle },
};

export default function Dashboard() {
  const { activeDataset, dataset } = useDataset();
  const risk = getRiskData(activeDataset);
  const promoter = getPromoterData(activeDataset);
  const diligence = getDiligenceData(activeDataset);
  const cam = getCamData(activeDataset);
  const spreads = getFinancialSpreadsData(activeDataset);
  const bank = getBankStatementData(activeDataset);
  const audit = getAuditTrailData(activeDataset);

  const dec = decLabel[cam.recommendation.decision];
  const DecIcon = dec.icon;

  // Key financial metrics from spreads
  const revenue = spreads.pnl.find(r => r.label.includes("Revenue"))?.fy24 ?? 0;
  const ebitdaRow = spreads.pnl.find(r => r.label === "EBITDA");
  const ebitda = ebitdaRow?.fy24 ?? 0;
  const ebitdaMargin = revenue > 0 ? ((ebitda / revenue) * 100).toFixed(1) : "0";
  const deRatio = spreads.ratios.find(r => r.name === "D/E Ratio")?.fy24 ?? "—";
  const dscr = spreads.ratios.find(r => r.name === "DSCR")?.fy24 ?? "—";
  const abb = bank.summary.abb;

  const flagsBySeverity = {
    critical: risk.riskFlags.filter((f) => f.severity === "critical").length,
    high: risk.riskFlags.filter((f) => f.severity === "high").length,
    medium: risk.riskFlags.filter((f) => f.severity === "medium").length,
  };

  const modules = [
    {
      title: "Document Upload",
      path: "/upload",
      icon: Upload,
      description: "Application data & document ingestion",
      status: "Complete",
      statusColor: "text-safe",
      detail: `${dataset.companyName} · ₹${dataset.loanAmount}`,
    },
    {
      title: "Agent Progress",
      path: "/agents",
      icon: Activity,
      description: "AI agent pipeline execution",
      status: "9/9 Agents",
      statusColor: "text-safe",
      detail: "All agents completed successfully",
    },
    {
      title: "Risk Analytics",
      path: "/risk",
      icon: BarChart3,
      description: "Credit risk scoring & financial analysis",
      status: risk.riskCategory,
      statusColor: scoreColor(risk.score),
      detail: `Score: ${risk.score}/100 · PD 12m: ${risk.defaultProb12m}%`,
    },
    {
      title: "Promoter Intel",
      path: "/promoter",
      icon: Users,
      description: "Director network & fraud detection",
      status: promoter.overallPromoterRisk.toUpperCase(),
      statusColor: promoter.overallPromoterRisk === "low" ? "text-safe" :
        promoter.overallPromoterRisk === "medium" ? "text-warning" : "text-destructive",
      detail: `${promoter.directors.length} directors · ${promoter.mca21Flags.length} flags`,
    },
    {
      title: "Due Diligence",
      path: "/diligence",
      icon: FileEdit,
      description: "Verification checklist & compliance",
      status: `${diligence.completionPercent}%`,
      statusColor: diligence.overallStatus === "clear" ? "text-safe" :
        diligence.overallStatus === "concerns" ? "text-warning" : "text-destructive",
      detail: `${diligence.checks.filter((c) => c.status === "flagged").length} flagged · ${diligence.checks.filter((c) => c.status === "pending").length} pending`,
    },
    {
      title: "Financial Spreads",
      path: "/spreads",
      icon: IndianRupee,
      description: "P&L, Balance Sheet, ratios & 3-year trends",
      status: `${spreads.ratios.filter(r => r.anomaly).length} Anomalies`,
      statusColor: spreads.ratios.filter(r => r.anomaly).length > 3 ? "text-destructive" :
        spreads.ratios.filter(r => r.anomaly).length > 0 ? "text-warning" : "text-safe",
      detail: `Revenue ₹${(revenue / 100).toFixed(0)}Cr · EBITDA ${ebitdaMargin}%`,
    },
    {
      title: "Bank Analytics",
      path: "/bank-analytics",
      icon: Landmark,
      description: "Cash flow analysis & banking behavior",
      status: `Score ${bank.summary.behaviorScore}`,
      statusColor: bank.summary.behaviorScore >= 70 ? "text-safe" :
        bank.summary.behaviorScore >= 50 ? "text-warning" : "text-destructive",
      detail: `ABB ₹${abb}L · Bounce ${bank.summary.bounceRatio}%`,
    },
    {
      title: "CAM Report",
      path: "/report",
      icon: FileText,
      description: "Credit appraisal memorandum & recommendation",
      status: dec.text,
      statusColor: dec.color,
      detail: cam.recommendation.summary.slice(0, 80) + "…",
    },
    {
      title: "Audit Trail",
      path: "/audit",
      icon: ClipboardList,
      description: "Decision log, overrides & compliance",
      status: `${audit.overrides.length} Overrides`,
      statusColor: audit.overrides.length > 2 ? "text-warning" : "text-safe",
      detail: `${audit.workflow.filter(s => s.status === "completed").length}/${audit.workflow.length} stages complete`,
    },
  ];

  return (
    <div className="animate-slide-up space-y-6">
      {/* Hero — Score + Decision */}
      <div className="grid grid-cols-[1fr_auto] gap-6">
        <Card data-tour="risk-score" className="p-6 flex items-center gap-8">
          {/* Big Score */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`relative flex items-center justify-center w-28 h-28 rounded-full border-4 shadow-lg ${
              risk.score >= 70 ? "border-safe" : risk.score >= 50 ? "border-warning" : "border-destructive"
            } ${scoreGlow(risk.score)}`}
          >
            <div className="text-center">
              <span className={`text-3xl font-mono-numbers font-bold ${scoreColor(risk.score)}`}>
                {risk.score}
              </span>
              <p className="text-[10px] text-muted-foreground font-display">/ 100</p>
            </div>
          </motion.div>

          {/* Company + Metrics */}
          <div className="flex-1 space-y-3">
            <div>
              <h2 className="text-lg font-display text-foreground font-bold">{dataset.companyName}</h2>
              <p className="text-xs text-muted-foreground font-mono-numbers">
                {dataset.cin} · {dataset.sector}
              </p>
            </div>
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: "Loan Amount", value: `₹${dataset.loanAmount}` },
                { label: "Purpose", value: dataset.purpose },
                { label: "Risk Category", value: risk.riskCategory },
                { label: "PD (12m)", value: `${risk.defaultProb12m}%` },
              ].map((m) => (
                <div key={m.label} className="bg-secondary/40 rounded-lg px-3 py-2">
                  <p className="text-[10px] text-muted-foreground font-display uppercase">{m.label}</p>
                  <p className="text-sm font-mono-numbers text-foreground mt-0.5">{m.value}</p>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Decision Card */}
        <Card className={`p-6 flex flex-col items-center justify-center min-w-[180px] ${
          cam.recommendation.decision === "approve" ? "border-safe/30" :
          cam.recommendation.decision === "reject" ? "border-destructive/30" : "border-warning/30"
        }`}>
          <DecIcon className={`h-8 w-8 mb-2 ${dec.color}`} />
          <p className={`text-lg font-display font-bold ${dec.color}`}>{dec.text}</p>
          <p className="text-[10px] text-muted-foreground mt-1 font-display">AI RECOMMENDATION</p>
          <Link
            to="/report"
            className="mt-3 text-xs text-primary font-display flex items-center gap-1 hover:underline"
          >
            View CAM Report <ArrowRight className="h-3 w-3" />
          </Link>
        </Card>
      </div>

      {/* Financial Health Strip */}
      <Card data-tour="financial-health" className="p-4">
        <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
          <TrendingUp className="h-3.5 w-3.5 text-primary" />
          Financial Health Summary
        </h3>
        <div className="grid grid-cols-5 gap-3">
          {[
            { label: "Revenue (FY24)", value: `₹${(revenue / 100).toFixed(0)} Cr`, trend: revenue > (spreads.pnl.find(r => r.label.includes("Revenue"))?.fy23 ?? 0) },
            { label: "EBITDA Margin", value: `${ebitdaMargin}%`, trend: Number(ebitdaMargin) >= 15 },
            { label: "D/E Ratio", value: `${deRatio}x`, trend: Number(deRatio) <= 1.5 },
            { label: "DSCR", value: `${dscr}x`, trend: Number(dscr) >= 1.5 },
            { label: "Avg Bank Balance", value: `₹${abb}L`, trend: bank.summary.behaviorScore >= 70 },
          ].map((m) => (
            <div key={m.label} className="bg-secondary/40 rounded-lg px-3 py-2.5">
              <p className="text-[10px] text-muted-foreground font-display uppercase">{m.label}</p>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="text-sm font-mono-numbers font-bold text-foreground">{m.value}</span>
                {m.trend ? (
                  <TrendingUp className="h-3 w-3 text-safe" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-destructive" />
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Risk Flags Summary */}
      {risk.riskFlags.length > 0 && (
        <Card className={`p-4 ${flagsBySeverity.critical > 0 ? "border-destructive/20 bg-destructive/10" : ""}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-primary" />
              <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
                Active Risk Flags
              </h3>
            </div>
            <div className="flex items-center gap-3">
              {flagsBySeverity.critical > 0 && (
                <Badge className="text-[10px] bg-destructive/20 text-destructive border-destructive/30">
                  {flagsBySeverity.critical} CRITICAL
                </Badge>
              )}
              {flagsBySeverity.high > 0 && (
                <Badge className="text-[10px] bg-warning/20 text-warning border-warning/30">
                  {flagsBySeverity.high} HIGH
                </Badge>
              )}
              {flagsBySeverity.medium > 0 && (
                <Badge className="text-[10px] bg-caution/20 text-caution border-caution/30">
                  {flagsBySeverity.medium} MEDIUM
                </Badge>
              )}
            </div>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {risk.riskFlags.slice(0, 4).map((flag, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-start gap-2 text-xs text-muted-foreground bg-secondary/30 rounded-lg px-3 py-2"
              >
                <AlertTriangle className={`h-3 w-3 mt-0.5 shrink-0 ${
                  flag.severity === "critical" ? "text-destructive" :
                  flag.severity === "high" ? "text-warning" : "text-caution"
                }`} />
                <span className="line-clamp-2">{flag.description}</span>
              </motion.div>
            ))}
          </div>
          {risk.riskFlags.length > 4 && (
            <Link to="/risk" className="mt-2 text-xs text-primary font-display flex items-center gap-1 hover:underline">
              View all {risk.riskFlags.length} flags <ArrowRight className="h-3 w-3" />
            </Link>
          )}
        </Card>
      )}

      {/* Module Navigation Cards */}
      <div data-tour="modules">
        <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
          <Zap className="h-3.5 w-3.5 text-primary" />
          Analysis Modules
        </h3>
        <div className="grid grid-cols-3 gap-3">
          {modules.map((mod, i) => (
            <motion.div
              key={mod.path}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
            >
              <Link to={mod.path}>
                <Card className="p-4 hover:border-primary/40 transition-all group cursor-pointer h-full">
                  <div className="flex items-start justify-between mb-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <mod.icon className="h-4 w-4 text-primary" />
                    </div>
                    <Badge className={`text-[9px] px-1.5 py-0 ${mod.statusColor} bg-transparent border-transparent font-display font-bold`}>
                      {mod.status}
                    </Badge>
                  </div>
                  <h4 className="text-sm font-display text-foreground font-medium mb-1 group-hover:text-primary transition-colors">
                    {mod.title}
                  </h4>
                  <p className="text-xs text-muted-foreground font-body mb-2">{mod.description}</p>
                  <p className="text-[10px] text-muted-foreground/70 font-mono-numbers line-clamp-1">{mod.detail}</p>
                  <div className="mt-3 flex items-center gap-1 text-xs text-primary font-display opacity-0 group-hover:opacity-100 transition-opacity">
                    Open <ArrowRight className="h-3 w-3" />
                  </div>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Five-Cs Quick Summary */}
      <Card className="p-4">
        <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-3">Five-Cs at a Glance</h3>
        <div className="grid grid-cols-5 gap-3">
          {risk.fiveCs.map((c) => (
            <div key={c.subject} className="text-center">
              <div className="relative mx-auto w-14 h-14 mb-2">
                <svg viewBox="0 0 36 36" className="w-full h-full">
                  <path
                    d="M18 2.0845a 15.9155 15.9155 0 0 1 0 31.831a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="hsl(var(--border))"
                    strokeWidth="3"
                  />
                  <path
                    d="M18 2.0845a 15.9155 15.9155 0 0 1 0 31.831a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke={c.value >= 70 ? "hsl(var(--safe))" : c.value >= 50 ? "hsl(var(--warning))" : "hsl(var(--destructive))"}
                    strokeWidth="3"
                    strokeDasharray={`${c.value}, 100`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className={`absolute inset-0 flex items-center justify-center text-sm font-mono-numbers font-bold ${
                  c.value >= 70 ? "text-safe" : c.value >= 50 ? "text-warning" : "text-destructive"
                }`}>
                  {c.value}
                </span>
              </div>
              <p className="text-xs font-display text-muted-foreground">{c.subject}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
