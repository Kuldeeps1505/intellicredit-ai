import { useDataset } from "@/contexts/DatasetContext";
import { getBankStatementData } from "@/lib/bankStatementData";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, LineChart, Line, Cell,
} from "recharts";
import {
  Landmark, AlertTriangle, CheckCircle2, XCircle, TrendingDown, TrendingUp,
  ArrowUpRight, ArrowDownRight, ShieldAlert, Eye,
} from "lucide-react";

const formatCr = (val: number) => `₹${(val / 100).toFixed(1)}Cr`;
const formatL = (val: number) => `₹${val}L`;

const SummaryCard = ({ label, value, suffix, status }: { label: string; value: string; suffix?: string; status: "good" | "warning" | "danger" }) => {
  const colors = {
    good: "text-safe",
    warning: "text-warning",
    danger: "text-destructive",
  };
  return (
    <div className="bg-card border border-border rounded-lg p-3">
      <p className="text-[10px] font-display text-muted-foreground uppercase tracking-wider">{label}</p>
      <p className={`text-lg font-mono-numbers font-bold ${colors[status]}`}>
        {value}
        {suffix && <span className="text-xs font-normal text-muted-foreground ml-1">{suffix}</span>}
      </p>
    </div>
  );
};

const BankStatementAnalytics = () => {
  const { activeDataset } = useDataset();
  const data = getBankStatementData(activeDataset);
  const { summary } = data;

  const detectedFlags = data.redFlags.filter((f) => f.detected);

  const abbStatus = summary.behaviorScore >= 70 ? "good" : summary.behaviorScore >= 50 ? "warning" : "danger";
  const bounceStatus = summary.bounceRatio <= 2 ? "good" : summary.bounceRatio <= 5 ? "warning" : "danger";
  const cashStatus = summary.cashWithdrawalPercent <= 10 ? "good" : summary.cashWithdrawalPercent <= 20 ? "warning" : "danger";
  const scoreStatus = summary.behaviorScore >= 70 ? "good" : summary.behaviorScore >= 50 ? "warning" : "danger";

  return (
    <ScrollArea className="h-[calc(100vh-120px)]">
      <div className="space-y-4 pr-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Landmark className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-display text-foreground">Bank Statement Analytics</h2>
          </div>
          <div className="flex items-center gap-2">
            {detectedFlags.length > 0 && (
              <Badge className="bg-destructive/20 text-destructive border-destructive/30 text-xs">
                <AlertTriangle className="h-3 w-3 mr-1" />
                {detectedFlags.length} Red Flags
              </Badge>
            )}
            <Badge className="bg-secondary text-muted-foreground border-border text-xs">
              12-Month Analysis
            </Badge>
          </div>
        </div>

        {/* Summary Cards */}
        <div data-tour="bank-summary" className="grid grid-cols-2 lg:grid-cols-4 gap-2">
          <SummaryCard label="Avg Bank Balance" value={formatL(summary.abb)} status={abbStatus} />
          <SummaryCard label="Bounce Ratio" value={`${summary.bounceRatio}%`} suffix={`(${summary.totalBounces} bounces)`} status={bounceStatus} />
          <SummaryCard label="Cash Withdrawal %" value={`${summary.cashWithdrawalPercent}%`} status={cashStatus} />
          <SummaryCard label="Behavior Score" value={`${summary.behaviorScore}`} suffix="/100" status={scoreStatus} />
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
          <SummaryCard label="Avg Monthly Credits" value={formatL(summary.avgMonthlyCredits)} status="good" />
          <SummaryCard label="Avg Monthly Debits" value={formatL(summary.avgMonthlyDebits)} status="good" />
          <SummaryCard label="Credit:Debit Ratio" value={summary.creditDebitRatio.toFixed(2)} suffix="x" status={summary.creditDebitRatio >= 1.05 ? "good" : summary.creditDebitRatio >= 1.0 ? "warning" : "danger"} />
          <SummaryCard label="EMI Obligations" value={formatL(summary.emiObligations)} suffix={`(${summary.emiCount} EMIs)`} status={summary.emiCount <= 2 ? "good" : summary.emiCount <= 4 ? "warning" : "danger"} />
        </div>

        {/* Cash Flow Chart + ABB Trend */}
        <div data-tour="bank-cashflow" className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card className="p-4">
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-3">Monthly Cash Flow</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.monthlyCashFlow} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                <RechartsTooltip
                  contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="credits" fill="hsl(var(--safe))" radius={[2, 2, 0, 0]} name="Credits" />
                <Bar dataKey="debits" fill="hsl(var(--destructive))" radius={[2, 2, 0, 0]} opacity={0.7} name="Debits" />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card className="p-4">
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-3">ABB Trend (Closing Balance)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data.monthlyCashFlow}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                <RechartsTooltip
                  contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
                />
                <Line type="monotone" dataKey="closing" stroke="hsl(var(--primary))" strokeWidth={2} dot={{ r: 3, fill: "hsl(var(--primary))" }} name="Closing Balance" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Transaction Categories */}
        <div data-tour="bank-categories" className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card className="p-4">
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-3">
              <ArrowUpRight className="h-3 w-3 inline text-safe mr-1" />
              Credit Categories
            </h3>
            <div className="space-y-2">
              {data.creditCategories.map((cat, i) => (
                <motion.div key={cat.category} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex justify-between text-xs mb-0.5">
                      <span className="text-foreground font-body">{cat.category}</span>
                      <span className="font-mono-numbers text-muted-foreground">{cat.percentage}% · {cat.txnCount} txns</span>
                    </div>
                    <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div className="h-full bg-safe rounded-full" style={{ width: `${cat.percentage}%` }} />
                    </div>
                  </div>
                  <span className="text-xs font-mono-numbers text-foreground w-16 text-right">{formatL(cat.amount)}</span>
                </motion.div>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-3">
              <ArrowDownRight className="h-3 w-3 inline text-destructive mr-1" />
              Debit Categories
            </h3>
            <div className="space-y-2">
              {data.debitCategories.map((cat, i) => (
                <motion.div key={cat.category} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex justify-between text-xs mb-0.5">
                      <span className="text-foreground font-body">{cat.category}</span>
                      <span className="font-mono-numbers text-muted-foreground">{cat.percentage}% · {cat.txnCount} txns</span>
                    </div>
                    <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div className="h-full bg-destructive/60 rounded-full" style={{ width: `${cat.percentage}%` }} />
                    </div>
                  </div>
                  <span className="text-xs font-mono-numbers text-foreground w-16 text-right">{formatL(cat.amount)}</span>
                </motion.div>
              ))}
            </div>
          </Card>
        </div>

        {/* Red Flags */}
        <Card data-tour="bank-redflags" className={`p-4 ${detectedFlags.length > 0 ? "border-destructive/30" : ""}`}>
          <div className="flex items-center gap-2 mb-3">
            <ShieldAlert className="h-4 w-4 text-primary" />
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
              Fraud & Red Flag Detection ({detectedFlags.length}/{data.redFlags.length})
            </h3>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
            {data.redFlags.map((flag, i) => (
              <motion.div
                key={flag.type}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className={`p-3 rounded-lg border ${
                  flag.detected
                    ? flag.severity === "critical"
                      ? "border-destructive/40 bg-destructive/10"
                      : flag.severity === "high"
                      ? "border-warning/40 bg-warning/10"
                      : "border-warning/20 bg-warning/10"
                    : "border-border bg-secondary/20"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  {flag.detected ? (
                    <XCircle className={`h-3.5 w-3.5 ${flag.severity === "critical" ? "text-destructive" : "text-warning"}`} />
                  ) : (
                    <CheckCircle2 className="h-3.5 w-3.5 text-safe" />
                  )}
                  <span className={`text-xs font-display font-medium ${flag.detected ? "text-foreground" : "text-muted-foreground"}`}>
                    {flag.type}
                  </span>
                  <Badge className={`ml-auto text-[9px] px-1.5 py-0 ${
                    flag.severity === "critical" ? "bg-destructive/20 text-destructive border-destructive/30" :
                    flag.severity === "high" ? "bg-warning/20 text-warning border-warning/30" :
                    "bg-muted text-muted-foreground border-border"
                  }`}>
                    {flag.severity.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground font-body">{flag.description}</p>
                {flag.detected && flag.details && (
                  <p className="text-xs text-foreground font-body mt-1.5 bg-background/50 rounded px-2 py-1.5 border border-border/50">
                    {flag.details}
                  </p>
                )}
              </motion.div>
            ))}
          </div>
        </Card>

        {/* Top Counterparties */}
        <Card className="overflow-hidden">
          <div className="px-4 py-2.5 border-b border-border bg-secondary/30 flex items-center gap-2">
            <Eye className="h-3.5 w-3.5 text-primary" />
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">Top Counterparties</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border bg-secondary/20">
                  <th className="text-left px-4 py-2 font-display text-muted-foreground">Counterparty</th>
                  <th className="text-right px-3 py-2 font-display text-muted-foreground">Credits</th>
                  <th className="text-right px-3 py-2 font-display text-muted-foreground">Debits</th>
                  <th className="text-right px-3 py-2 font-display text-muted-foreground">Net</th>
                  <th className="text-right px-3 py-2 font-display text-muted-foreground">Freq</th>
                  <th className="text-right px-3 py-2 font-display text-muted-foreground">Risk</th>
                </tr>
              </thead>
              <tbody>
                {data.topCounterparties.map((cp, i) => (
                  <motion.tr
                    key={cp.name}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.04 }}
                    className={`border-b border-border/50 ${cp.risk === "high" ? "bg-destructive/10" : ""}`}
                  >
                    <td className="px-4 py-2.5 font-body text-foreground">{cp.name}</td>
                    <td className="text-right px-3 py-2.5 font-mono-numbers text-safe">{cp.credits > 0 ? formatL(cp.credits) : "—"}</td>
                    <td className="text-right px-3 py-2.5 font-mono-numbers text-destructive">{cp.debits > 0 ? formatL(cp.debits) : "—"}</td>
                    <td className={`text-right px-3 py-2.5 font-mono-numbers font-medium ${cp.net >= 0 ? "text-safe" : "text-destructive"}`}>
                      {cp.net >= 0 ? "+" : ""}{formatL(Math.abs(cp.net))}
                    </td>
                    <td className="text-right px-3 py-2.5 font-mono-numbers text-muted-foreground">{cp.frequency} txns</td>
                    <td className="text-right px-3 py-2.5">
                      <Badge className={`text-[9px] px-1.5 py-0 ${
                        cp.risk === "high" ? "bg-destructive/20 text-destructive border-destructive/30" :
                        cp.risk === "medium" ? "bg-warning/20 text-warning border-warning/30" :
                        "bg-safe/20 text-safe border-safe/30"
                      }`}>
                        {cp.risk.toUpperCase()}
                      </Badge>
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

export default BankStatementAnalytics;
