import { useState, useEffect, useRef } from "react";
import { usePipeline } from "@/contexts/PipelineContext";
import { RiskGauge } from "@/components/risk/RiskGauge";
import { ScoreWaterfall } from "@/components/ScoreWaterfall";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { motion, AnimatePresence } from "framer-motion";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, Cell, PieChart, Pie,
} from "recharts";
import {
  AlertTriangle, TrendingUp, DollarSign, Clock, ArrowRight,
  RefreshCw, CheckCircle2, XCircle, Loader2, Info,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";

// ── Types (extended to match new backend fields) ──────────────────────────────
interface FiveCsExplanation {
  character?: string;
  capacity?: string;
  capital?: string;
  collateral?: string;
  conditions?: string;
}

interface RiskDataLive {
  score: number;
  riskCategory: string;
  defaultProb12m: number;
  defaultProb24m: number;
  decision: string;
  fiveCs: { subject: string; value: number; fullMark: number }[];
  fiveCsExplanations: FiveCsExplanation;
  topDrivers: { factor: string; coefficient: number; direction: string }[];
  gstrReconciliation: { quarter: string; gstr2a: number; gstr3b: number; flagged: boolean }[];
  suspectITC: string;
  buyerConcentration: { name: string; gstin: string; percentage: number; risk: string }[];
  topThreeConcentration: number;
  financialRatios: {
    name: string; value: string; numericValue: number; unit: string;
    sparkline: number[]; yoyChange: number; anomaly: boolean;
    citation: { document: string; page: number; method: string; confidence: number };
  }[];
  riskFlags: { type: string; severity: string; description: string; detectedBy: string; status: string }[];
  dataSource: "live" | "fallback" | "pending";
}

const EMPTY_DATA: RiskDataLive = {
  score: 0, riskCategory: "PENDING", defaultProb12m: 0, defaultProb24m: 0, decision: "PENDING",
  fiveCs: ["Character","Capacity","Capital","Collateral","Conditions"].map(s => ({ subject: s, value: 0, fullMark: 100 })),
  fiveCsExplanations: {}, topDrivers: [], gstrReconciliation: [], suspectITC: "₹0",
  buyerConcentration: [], topThreeConcentration: 0, financialRatios: [], riskFlags: [],
  dataSource: "pending",
};

const severityConfig: Record<string, { color: string; dot: string }> = {
  critical: { color: "bg-destructive text-destructive-foreground",       dot: "bg-destructive" },
  high:     { color: "bg-warning/20 text-warning border border-warning/30", dot: "bg-warning" },
  medium:   { color: "bg-caution/20 text-caution border border-caution/30", dot: "bg-caution" },
  low:      { color: "bg-safe/20 text-safe border border-safe/30",          dot: "bg-safe" },
};

const decisionConfig: Record<string, { color: string; icon: typeof CheckCircle2; label: string }> = {
  APPROVE:      { color: "text-safe",        icon: CheckCircle2, label: "APPROVE" },
  CONDITIONAL:  { color: "text-warning",     icon: AlertTriangle, label: "CONDITIONAL" },
  REJECT:       { color: "text-destructive", icon: XCircle,      label: "REJECT" },
  PENDING:      { color: "text-muted-foreground", icon: Clock,   label: "PENDING" },
};

const RiskAnalytics = () => {
  const { applicationId, application, pipelineStatus } = usePipeline();
  const navigate = useNavigate();

  const [data, setData] = useState<RiskDataLive>(EMPTY_DATA);
  const [loading, setLoading] = useState(false);
  const [lastFetched, setLastFetched] = useState<Date | null>(null);
  const [expandedC, setExpandedC] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchRisk = async (showLoader = false) => {
    if (!applicationId) return;
    if (showLoader) setLoading(true);
    try {
      const result = await api.getRisk(applicationId) as unknown as RiskDataLive;
      setData(result);
      setLastFetched(new Date());
    } catch {
      // keep existing data on error
    } finally {
      if (showLoader) setLoading(false);
    }
  };

  // Initial fetch + auto-poll while pipeline is running
  useEffect(() => {
    if (!applicationId) { setData(EMPTY_DATA); return; }
    fetchRisk(true);

    // Poll every 3s while pipeline is running, stop when complete
    if (pipelineStatus === "running") {
      pollRef.current = setInterval(() => fetchRisk(false), 3000);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [applicationId, pipelineStatus]);

  // Stop polling when pipeline completes
  useEffect(() => {
    if (pipelineStatus === "completed" || pipelineStatus === "idle") {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
      if (applicationId) fetchRisk(false);
    }
  }, [pipelineStatus]);

  const getBuyerColor = (risk: string, idx: number) => {
    if (risk === "high")   return "hsl(var(--destructive))";
    if (risk === "medium") return "hsl(var(--warning))";
    const fallback = ["hsl(var(--info))","hsl(var(--safe))","hsl(var(--caution))","hsl(var(--muted-foreground))"];
    return fallback[Math.min(idx, fallback.length - 1)];
  };

  const isPending = data.dataSource === "pending";
  const dec = decisionConfig[data.decision] ?? decisionConfig.PENDING;
  const DecIcon = dec.icon;

  if (!applicationId) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <Info className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">No application loaded. Upload documents first.</p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-[calc(100vh-120px)]">
      <div className="space-y-4 pr-2">

        {/* Status bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {pipelineStatus === "running" && (
              <Badge className="bg-info/20 text-info border-info/30 text-[10px] flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" /> Pipeline running — auto-refreshing
              </Badge>
            )}
            {data.dataSource === "live" && (
              <Badge className="bg-safe/20 text-safe border-safe/30 text-[10px]">
                ✓ Live data from pipeline
              </Badge>
            )}
            {isPending && (
              <Badge className="bg-secondary text-muted-foreground border-border text-[10px]">
                Run pipeline to see results
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {lastFetched && (
              <span className="text-[10px] text-muted-foreground font-mono-numbers">
                Updated {lastFetched.toLocaleTimeString()}
              </span>
            )}
            <button onClick={() => fetchRisk(true)}
              className="p-1.5 rounded-md hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground">
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {loading && (
          <div className="space-y-4">
            <div className="grid grid-cols-[1fr_280px_1fr] gap-4">
              <Skeleton className="h-48 rounded-xl" /><Skeleton className="h-48 rounded-xl" /><Skeleton className="h-48 rounded-xl" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-64 rounded-xl" /><Skeleton className="h-64 rounded-xl" />
            </div>
          </div>
        )}

        {!loading && (<>

        {/* Row 1: Quick Stats + Gauge + Radar */}
        <div className="grid grid-cols-[1fr_280px_1fr] gap-4">

          {/* Quick Stats + Decision */}
          <Card className="p-4 flex flex-col justify-center gap-3">
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">Application</h3>
            {[
              { label: "Loan Amount", value: application ? `₹${application.loanAmount}` : "—", icon: DollarSign },
              { label: "Sector",      value: application?.sector ?? "—",                        icon: TrendingUp },
              { label: "Status",      value: application?.status ?? "—",                        icon: Clock },
            ].map((stat) => (
              <div key={stat.label} className="flex items-center gap-3 px-3 py-2 bg-secondary/50 rounded-lg">
                <stat.icon className="h-4 w-4 text-primary shrink-0" />
                <div>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                  <p className="text-sm font-mono-numbers text-foreground">{stat.value}</p>
                </div>
              </div>
            ))}
            {/* Decision badge */}
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
              data.decision === "APPROVE" ? "bg-safe/10 border-safe/30" :
              data.decision === "REJECT"  ? "bg-destructive/10 border-destructive/30" :
              data.decision === "CONDITIONAL" ? "bg-warning/10 border-warning/30" :
              "bg-secondary border-border"
            }`}>
              <DecIcon className={`h-4 w-4 ${dec.color}`} />
              <span className={`text-sm font-display font-bold ${dec.color}`}>{dec.label}</span>
            </div>
          </Card>

          {/* Risk Gauge */}
          <Card data-tour="risk-gauge" className="p-4 flex items-center justify-center">
            <RiskGauge
              score={data.score}
              category={data.riskCategory}
              defaultProb12m={data.defaultProb12m}
              defaultProb24m={data.defaultProb24m}
            />
          </Card>

          {/* Five-Cs Radar */}
          <Card data-tour="risk-radar" className="p-4">
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-2">Five-Cs Analysis</h3>
            <ResponsiveContainer width="100%" height={180}>
              <RadarChart data={data.fiveCs}>
                <PolarGrid stroke="hsl(var(--border))" />
                <PolarAngleAxis dataKey="subject"
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10, fontFamily: "IBM Plex Mono" }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
                <Radar dataKey="value" stroke="hsl(var(--primary))" fill="hsl(var(--primary))"
                  fillOpacity={0.25} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
            {/* Clickable C scores */}
            <div className="grid grid-cols-5 gap-1 mt-1">
              {data.fiveCs.map((c) => (
                <button key={c.subject}
                  onClick={() => setExpandedC(expandedC === c.subject ? null : c.subject)}
                  className={`text-center p-1 rounded transition-colors ${expandedC === c.subject ? "bg-primary/10" : "hover:bg-secondary/50"}`}>
                  <p className={`text-sm font-mono-numbers font-bold ${
                    c.value >= 70 ? "text-safe" : c.value >= 50 ? "text-warning" : c.value > 0 ? "text-destructive" : "text-muted-foreground"
                  }`}>{c.value > 0 ? c.value : "—"}</p>
                  <p className="text-[9px] text-muted-foreground">{c.subject.slice(0, 4)}</p>
                </button>
              ))}
            </div>
          </Card>
        </div>

        {/* Five-Cs Explanation Panel (expandable) */}
        <AnimatePresence>
          {expandedC && data.fiveCsExplanations[expandedC.toLowerCase() as keyof FiveCsExplanation] && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.2 }}>
              <Card className="p-4 border-primary/30 bg-primary/5">
                <div className="flex items-start gap-3">
                  <Info className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-display text-primary uppercase tracking-wider mb-1">{expandedC} — AI Explanation</p>
                    <p className="text-sm text-foreground font-body">
                      {data.fiveCsExplanations[expandedC.toLowerCase() as keyof FiveCsExplanation]}
                    </p>
                  </div>
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Score Waterfall — SHAP-style explainability */}
        {applicationId && (
          <Card className="p-4 border-primary/20">
            <div className="flex items-center gap-2 mb-4">
              <h3 className="text-xs font-display text-primary uppercase tracking-wider font-bold">
                Score Decomposition — Explainable AI
              </h3>
              <Badge className="text-[9px] bg-primary/20 text-primary border-primary/30 px-1.5 py-0">
                SHAP-style · RBI Grade
              </Badge>
            </div>
            <ScoreWaterfall applicationId={applicationId} />
          </Card>
        )}

        {/* Row 2: GSTR Waterfall + Buyer Concentration */}
        <div className="grid grid-cols-2 gap-4">

          {/* GSTR Reconciliation */}
          <Card data-tour="risk-gstr" className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
                GSTR-2A vs GSTR-3B Reconciliation
              </h3>
              <Badge className="text-[10px] bg-primary/20 text-primary border-primary/30 px-1.5 py-0">
                ⚡ Fraud Detection Engine
              </Badge>
            </div>
            {data.gstrReconciliation.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={data.gstrReconciliation} barGap={2}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="quarter"
                      tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 9, fontFamily: "IBM Plex Mono" }}
                      axisLine={{ stroke: "hsl(var(--border))" }} />
                    <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 9 }}
                      axisLine={{ stroke: "hsl(var(--border))" }}
                      tickFormatter={(v) => `₹${v}Cr`} />
                    <RechartsTooltip
                      contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: "11px" }}
                      formatter={(value: number) => [`₹${value}Cr`]} />
                    <Bar dataKey="gstr2a" name="GSTR-2A (Available)" fill="hsl(var(--info))" radius={[2,2,0,0]} />
                    <Bar dataKey="gstr3b" name="GSTR-3B (Claimed)" radius={[2,2,0,0]}>
                      {data.gstrReconciliation.map((entry, i) => (
                        <Cell key={i} fill={entry.flagged ? "hsl(var(--destructive))" : "hsl(var(--warning))"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                {data.suspectITC !== "₹0" && (
                  <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                    className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 bg-destructive/15 border border-destructive/30 rounded-full">
                    <AlertTriangle className="h-3 w-3 text-destructive" />
                    <span className="text-xs font-display text-destructive font-bold">
                      Total Suspect ITC: {data.suspectITC}
                    </span>
                  </motion.div>
                )}
              </>
            ) : (
              <div className="h-48 flex items-center justify-center text-muted-foreground text-xs">
                {isPending ? "Run pipeline to see GSTR reconciliation" : "No GSTR data available"}
              </div>
            )}
          </Card>

          {/* Buyer Concentration */}
          <Card data-tour="risk-buyer" className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
                Buyer Concentration
              </h3>
              <Badge className="text-[10px] bg-primary/20 text-primary border-primary/30 px-1.5 py-0">
                ⚡ Concentration Engine
              </Badge>
            </div>
            {data.buyerConcentration.length > 0 ? (
              <div className="grid grid-cols-[1fr_1fr] gap-2">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={data.buyerConcentration} cx="50%" cy="50%"
                      innerRadius={50} outerRadius={75} dataKey="percentage" nameKey="name"
                      strokeWidth={2} stroke="hsl(var(--card))">
                      {data.buyerConcentration.map((entry, i) => (
                        <Cell key={i} fill={getBuyerColor(entry.risk, i)} />
                      ))}
                    </Pie>
                    <RechartsTooltip
                      contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: "11px" }}
                      formatter={(value: number) => [`${value}%`]} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-col justify-center gap-1.5">
                  <div className="text-center mb-2">
                    <p className="text-xs text-muted-foreground">Top 3 Concentration</p>
                    <p className={`text-lg font-mono-numbers font-bold ${
                      data.topThreeConcentration > 50 ? "text-destructive" : data.topThreeConcentration > 35 ? "text-warning" : "text-safe"
                    }`}>{data.topThreeConcentration}%</p>
                  </div>
                  {data.buyerConcentration.slice(0, 4).map((buyer, i) => (
                    <div key={i} className="flex items-center justify-between text-xs px-2 py-1 bg-secondary/30 rounded">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: getBuyerColor(buyer.risk, i) }} />
                        <span className="text-foreground truncate">{buyer.name}</span>
                      </div>
                      <span className="font-mono-numbers text-muted-foreground ml-1">{buyer.percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-muted-foreground text-xs">
                {isPending ? "Run pipeline to see buyer concentration" : "No buyer data available"}
              </div>
            )}
          </Card>
        </div>

        {/* Top Drivers (Logistic Regression) */}
        {data.topDrivers.length > 0 && (
          <Card className="p-4">
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-3">
              Default Probability Drivers — Logistic Regression
            </h3>
            <div className="grid grid-cols-5 gap-2">
              {data.topDrivers.slice(0, 5).map((d, i) => (
                <div key={i} className={`p-3 rounded-lg border text-center ${
                  d.direction === "increases_risk" ? "border-destructive/30 bg-destructive/5" : "border-safe/30 bg-safe/5"
                }`}>
                  <p className="text-[10px] text-muted-foreground font-display uppercase mb-1">
                    {d.factor.replace(/_/g, " ")}
                  </p>
                  <p className={`text-sm font-mono-numbers font-bold ${
                    d.direction === "increases_risk" ? "text-destructive" : "text-safe"
                  }`}>
                    {d.direction === "increases_risk" ? "▲" : "▼"} {Math.abs(d.coefficient).toFixed(2)}
                  </p>
                  <p className="text-[9px] text-muted-foreground mt-0.5">
                    {d.direction === "increases_risk" ? "Risk ↑" : "Risk ↓"}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Financial Ratios → link to spreads */}
        {data.financialRatios.length > 0 ? (
          <Card className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
                Key Financial Ratios ({data.financialRatios.filter(r => r.anomaly).length} anomalies)
              </h3>
              <button onClick={() => navigate("/spreads")}
                className="flex items-center gap-1 text-xs text-primary font-display hover:underline">
                Full Spreads <ArrowRight className="h-3 w-3" />
              </button>
            </div>
            <div className="grid grid-cols-4 gap-2">
              {data.financialRatios.slice(0, 8).map((r, i) => (
                <div key={i} className={`p-2.5 rounded-lg border ${r.anomaly ? "border-destructive/40 bg-destructive/5" : "border-border bg-secondary/20"}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-muted-foreground font-display">{r.name}</span>
                    {r.anomaly && <AlertTriangle className="h-3 w-3 text-destructive" />}
                  </div>
                  <p className={`text-base font-mono-numbers font-bold ${r.anomaly ? "text-destructive" : "text-foreground"}`}>
                    {r.value}{r.unit === "%" ? "%" : r.unit === "x" ? "x" : ""}
                  </p>
                  <p className={`text-[9px] font-mono-numbers mt-0.5 ${r.yoyChange >= 0 ? "text-safe" : "text-destructive"}`}>
                    {r.yoyChange >= 0 ? "▲" : "▼"} {Math.abs(r.yoyChange).toFixed(1)}% YoY
                  </p>
                </div>
              ))}
            </div>
          </Card>
        ) : (
          <Card className="p-4 cursor-pointer hover:border-primary/50 transition-colors group" onClick={() => navigate("/spreads")}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">Financial Ratios</h3>
                <p className="text-xs text-muted-foreground mt-1">17 ratios with benchmarks, anomaly detection & 3-year trends</p>
              </div>
              <div className="flex items-center gap-2 text-primary group-hover:translate-x-1 transition-transform">
                <span className="text-xs font-display">View in Financial Spreads</span>
                <ArrowRight className="h-4 w-4" />
              </div>
            </div>
          </Card>
        )}

        {/* Risk Flags Table */}
        <Card data-tour="risk-flags" className="p-4">
          <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-3">
            Risk Flags ({data.riskFlags.length})
          </h3>
          {data.riskFlags.length === 0 ? (
            <p className="text-xs text-muted-foreground py-4 text-center">
              {isPending ? "Run pipeline to detect risk flags" : "No risk flags detected"}
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border">
                    {["Flag Type","Severity","Description","Detected By","Status"].map(h => (
                      <th key={h} className="text-left py-2 px-2 text-muted-foreground font-display font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[...data.riskFlags]
                    .sort((a, b) => ({ critical:0, high:1, medium:2, low:3 }[a.severity] ?? 4) - ({ critical:0, high:1, medium:2, low:3 }[b.severity] ?? 4))
                    .map((flag, i) => (
                      <motion.tr key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.04 }}
                        className={`border-b border-border/50 ${flag.severity === "critical" ? "bg-destructive/10" : ""}`}>
                        <td className="py-2.5 px-2 font-display text-foreground">{flag.type}</td>
                        <td className="py-2.5 px-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-display font-medium ${(severityConfig[flag.severity] ?? severityConfig.low).color}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${(severityConfig[flag.severity] ?? severityConfig.low).dot} ${flag.severity === "critical" ? "animate-pulse" : ""}`} />
                            {flag.severity.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-2.5 px-2 text-muted-foreground max-w-[300px]">{flag.description}</td>
                        <td className="py-2.5 px-2 text-muted-foreground font-mono-numbers text-xs">{flag.detectedBy}</td>
                        <td className="py-2.5 px-2">
                          <span className={`text-xs font-display ${flag.status === "active" ? "text-destructive" : flag.status === "monitoring" ? "text-warning" : "text-safe"}`}>
                            {flag.status.toUpperCase()}
                          </span>
                        </td>
                      </motion.tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        </>)}
      </div>
    </ScrollArea>
  );
};

export default RiskAnalytics;
