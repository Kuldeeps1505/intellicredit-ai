import { useDataset } from "@/contexts/DatasetContext";
import { getRiskData } from "@/lib/riskData";
import { RiskGauge } from "@/components/risk/RiskGauge";
import { CitationBadge } from "@/components/risk/CitationBadge";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { motion } from "framer-motion";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, Cell, PieChart, Pie,
} from "recharts";
import { AlertTriangle, TrendingUp, DollarSign, Clock, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

const severityConfig = {
  critical: { color: "bg-destructive text-destructive-foreground", dot: "bg-destructive" },
  high: { color: "bg-warning/20 text-warning border border-warning/30", dot: "bg-warning" },
  medium: { color: "bg-caution/20 text-caution border border-caution/30", dot: "bg-caution" },
  low: { color: "bg-safe/20 text-safe border border-safe/30", dot: "bg-safe" },
};

const RiskAnalytics = () => {
  const { activeDataset, dataset } = useDataset();
  const data = getRiskData(activeDataset);
  const navigate = useNavigate();

  const getBuyerColor = (risk: string, idx: number) => {
    if (risk === "high") return "hsl(var(--destructive))";
    if (risk === "medium") return "hsl(var(--warning))";
    const fallback = ["hsl(var(--info))", "hsl(var(--safe))", "hsl(var(--caution))", "hsl(var(--muted-foreground))", "hsl(var(--muted-foreground))"];
    return fallback[Math.min(idx, fallback.length - 1)];
  };

  return (
    <ScrollArea className="h-[calc(100vh-120px)]">
      <div className="space-y-4 pr-2">
        {/* Top Row: Quick Stats + Gauge + Radar */}
        <div className="grid grid-cols-[1fr_280px_1fr] gap-4">
          {/* Quick Stats */}
          <Card className="p-4 flex flex-col justify-center gap-3">
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">Quick Stats</h3>
            {[
              { label: "Loan Amount", value: `₹${dataset.loanAmount}`, icon: DollarSign },
              { label: "Sector", value: dataset.sector, icon: TrendingUp },
              { label: "Pipeline", value: "Complete", icon: Clock },
            ].map((stat) => (
              <div key={stat.label} className="flex items-center gap-3 px-3 py-2 bg-secondary/50 rounded-lg">
                <stat.icon className="h-4 w-4 text-primary shrink-0" />
                <div>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                  <p className="text-sm font-mono-numbers text-foreground">{stat.value}</p>
                </div>
              </div>
            ))}
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
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={data.fiveCs}>
                <PolarGrid stroke="hsl(var(--border))" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10, fontFamily: "IBM Plex Mono" }}
                />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
                <Radar
                  dataKey="value"
                  stroke="hsl(var(--primary))"
                  fill="hsl(var(--primary))"
                  fillOpacity={0.25}
                  strokeWidth={2}
                />
              </RadarChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Middle Row: GSTR Waterfall + Buyer Concentration */}
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
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.gstrReconciliation} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="quarter"
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10, fontFamily: "IBM Plex Mono" }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                />
                <YAxis
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10, fontFamily: "Roboto Mono" }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                  tickFormatter={(v) => `₹${v}Cr`}
                />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                    fontSize: "12px",
                    fontFamily: "Roboto Mono",
                  }}
                  formatter={(value: number) => [`₹${value}Cr`]}
                />
                <Bar dataKey="gstr2a" name="GSTR-2A (Actual)" fill="hsl(var(--info))" radius={[2, 2, 0, 0]} />
                <Bar dataKey="gstr3b" name="GSTR-3B (Claimed)" radius={[2, 2, 0, 0]}>
                  {data.gstrReconciliation.map((entry, i) => (
                    <Cell key={i} fill={entry.flagged ? "hsl(var(--destructive))" : "hsl(var(--warning))"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            {data.suspectITC !== "₹0" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 bg-destructive/15 border border-destructive/30 rounded-full"
              >
                <AlertTriangle className="h-3 w-3 text-destructive" />
                <span className="text-xs font-display text-destructive font-bold">
                  Total Suspect ITC: {data.suspectITC}
                </span>
              </motion.div>
            )}
          </Card>

          {/* Buyer Concentration Donut */}
          <Card data-tour="risk-buyer" className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
                Buyer Concentration
              </h3>
              <Badge className="text-[10px] bg-primary/20 text-primary border-primary/30 px-1.5 py-0">
                ⚡ Concentration Engine
              </Badge>
            </div>
            <div className="grid grid-cols-[1fr_1fr] gap-2">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={data.buyerConcentration}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    dataKey="percentage"
                    nameKey="name"
                    strokeWidth={2}
                    stroke="hsl(var(--card))"
                  >
                    {data.buyerConcentration.map((entry, i) => (
                      <Cell key={i} fill={getBuyerColor(entry.risk, i)} />
                    ))}
                  </Pie>
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    formatter={(value: number) => [`${value}%`]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-col justify-center gap-1.5">
                <div className="text-center mb-2">
                  <p className="text-xs text-muted-foreground">Top 3 Concentration</p>
                  <p className={`text-lg font-mono-numbers font-bold ${
                    data.topThreeConcentration > 50 ? "text-destructive" : data.topThreeConcentration > 35 ? "text-warning" : "text-safe"
                  }`}>
                    {data.topThreeConcentration}%
                  </p>
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
          </Card>
        </div>

        {/* Link to Financial Spreads */}
        <Card
          className="p-4 cursor-pointer hover:border-primary/50 transition-colors group"
          onClick={() => navigate("/spreads")}
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">Financial Ratios</h3>
              <p className="text-xs text-muted-foreground mt-1">
                17 ratios with benchmarks, anomaly detection & 3-year trends
              </p>
            </div>
            <div className="flex items-center gap-2 text-primary group-hover:translate-x-1 transition-transform">
              <span className="text-xs font-display">View in Financial Spreads</span>
              <ArrowRight className="h-4 w-4" />
            </div>
          </div>
        </Card>

        {/* Risk Flags Table */}
        <Card data-tour="risk-flags" className="p-4">
          <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-3">
            Risk Flags ({data.riskFlags.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border">
                  {["Flag Type", "Severity", "Description", "Detected By", "Status"].map((h) => (
                    <th key={h} className="text-left py-2 px-2 text-muted-foreground font-display font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.riskFlags
                  .sort((a, b) => {
                    const order = { critical: 0, high: 1, medium: 2, low: 3 };
                    return order[a.severity] - order[b.severity];
                  })
                  .map((flag, i) => (
                    <motion.tr
                      key={i}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.05 }}
                      className={`border-b border-border/50 ${flag.severity === "critical" ? "bg-destructive/10" : ""}`}
                    >
                      <td className="py-2.5 px-2 font-display text-foreground">{flag.type}</td>
                      <td className="py-2.5 px-2">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-display font-medium ${severityConfig[flag.severity].color}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${severityConfig[flag.severity].dot} ${flag.severity === "critical" ? "animate-pulse" : ""}`} />
                          {flag.severity.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-2.5 px-2 text-muted-foreground max-w-[300px]">{flag.description}</td>
                      <td className="py-2.5 px-2 text-muted-foreground font-mono-numbers text-xs">{flag.detectedBy}</td>
                      <td className="py-2.5 px-2">
                        <span className={`text-xs font-display ${
                          flag.status === "active" ? "text-destructive" : flag.status === "monitoring" ? "text-warning" : "text-safe"
                        }`}>
                          {flag.status.toUpperCase()}
                        </span>
                      </td>
                    </motion.tr>
                  ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </ScrollArea>
  );
};

export default RiskAnalytics;
