import { useState, useEffect } from "react";
import { usePipeline } from "@/contexts/PipelineContext";
import { getFinancialSpreadsData, LineItem, RatioItem } from "@/lib/financialSpreadsData";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, AlertTriangle, BarChart3, ArrowUp, ArrowDown } from "lucide-react";

const formatLakh = (val: number) => {
  if (val === 0) return "—";
  const abs = Math.abs(val);
  if (abs >= 100) return `${val < 0 ? "-" : ""}₹${(abs / 100).toFixed(1)}Cr`;
  return `${val < 0 ? "-" : ""}₹${abs.toFixed(0)}L`;
};

const yoyChange = (prev: number, curr: number) => {
  if (prev === 0) return curr > 0 ? 999 : curr < 0 ? -999 : 0;
  return ((curr - prev) / Math.abs(prev)) * 100;
};

const ChangeIndicator = ({ value }: { value: number }) => {
  if (Math.abs(value) > 500) return <span className="text-[10px] text-muted-foreground">New</span>;
  const isPositive = value > 0;
  const color = isPositive ? "text-safe" : "text-destructive";
  return (
    <span className={`text-[10px] font-mono-numbers ${color} flex items-center gap-0.5`}>
      {isPositive ? <ArrowUp className="h-2.5 w-2.5" /> : <ArrowDown className="h-2.5 w-2.5" />}
      {Math.abs(value).toFixed(1)}%
    </span>
  );
};

const SpreadTable = ({ items, title }: { items: LineItem[]; title: string }) => (
  <Card className="overflow-hidden">
    <div className="px-4 py-2.5 border-b border-border bg-secondary/30">
      <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">{title}</h3>
    </div>
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-border bg-secondary/20">
            <th className="text-left px-4 py-2 font-display text-muted-foreground w-[40%]">Line Item</th>
            <th className="text-right px-3 py-2 font-display text-muted-foreground">FY22</th>
            <th className="text-right px-3 py-2 font-display text-muted-foreground">FY23</th>
            <th className="text-right px-1 py-2 font-display text-muted-foreground w-[48px]">YoY</th>
            <th className="text-right px-3 py-2 font-display text-muted-foreground">FY24</th>
            <th className="text-right px-3 py-2 font-display text-muted-foreground w-[48px]">YoY</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, i) => {
            const yoy23 = yoyChange(item.fy22, item.fy23);
            const yoy24 = yoyChange(item.fy23, item.fy24);
            return (
              <motion.tr
                key={item.label}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.02 }}
                className={`border-b border-border/50 ${
                  item.isTotal ? "bg-primary/10 font-semibold" : item.isSubTotal ? "bg-secondary/20 font-medium" : ""
                }`}
              >
                <td className={`px-4 py-2 font-body ${item.isTotal || item.isSubTotal ? "text-foreground" : "text-muted-foreground"}`}>
                  {item.label}
                </td>
                <td className="text-right px-3 py-2 font-mono-numbers text-foreground">{formatLakh(item.fy22)}</td>
                <td className="text-right px-3 py-2 font-mono-numbers text-foreground">{formatLakh(item.fy23)}</td>
                <td className="text-right px-1 py-2"><ChangeIndicator value={yoy23} /></td>
                <td className="text-right px-3 py-2 font-mono-numbers text-foreground">{formatLakh(item.fy24)}</td>
                <td className="text-right px-3 py-2"><ChangeIndicator value={yoy24} /></td>
              </motion.tr>
            );
          })}
        </tbody>
      </table>
    </div>
  </Card>
);

const categoryLabels: Record<string, string> = {
  liquidity: "Liquidity",
  leverage: "Leverage",
  profitability: "Profitability",
  efficiency: "Efficiency",
  debt_service: "Debt Service",
};

const RatioCard = ({ ratio }: { ratio: RatioItem }) => {
  const latest = ratio.fy24;
  const prev = ratio.fy23;
  const improving = ratio.name.includes("Days") || ratio.name.includes("Cycle") || ratio.name === "D/E Ratio" || ratio.name === "Total Debt/EBITDA"
    ? latest < prev
    : latest > prev;

  return (
    <div className={`p-3 rounded-lg border shadow-card ${ratio.anomaly ? "border-destructive/40 bg-destructive/5 ring-1 ring-destructive/10" : "border-border bg-card"}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-display text-muted-foreground uppercase">{ratio.name}</span>
        {ratio.anomaly && <AlertTriangle className="h-3 w-3 text-destructive" />}
      </div>
      <div className="flex items-end justify-between">
        <span className={`text-lg font-mono-numbers font-bold ${ratio.anomaly ? "text-destructive" : "text-foreground"}`}>
          {latest < 0 ? "-" : ""}{Math.abs(latest).toFixed(ratio.unit === "%" || ratio.unit === "x" ? 2 : 0)}{ratio.unit === "%" ? "%" : ratio.unit === "x" ? "x" : ""}
        </span>
        <div className="flex items-center gap-1">
          {improving ? (
            <TrendingUp className="h-3 w-3 text-safe" />
          ) : (
            <TrendingDown className="h-3 w-3 text-destructive" />
          )}
          <span className={`text-[10px] font-mono-numbers ${improving ? "text-safe" : "text-destructive"}`}>
            vs {prev < 0 ? "-" : ""}{Math.abs(prev).toFixed(ratio.unit === "%" || ratio.unit === "x" ? 2 : 0)}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-1 mt-1.5">
        <div className="flex-1 h-1 bg-secondary rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full ${ratio.anomaly ? "bg-destructive" : "bg-primary"}`}
            style={{
              width: `${Math.min(100, Math.abs(latest / ratio.benchmark) * 100)}%`,
            }}
          />
        </div>
        <span className="text-[9px] text-muted-foreground font-mono-numbers">BM: {ratio.benchmark}{ratio.unit === "%" ? "%" : ratio.unit === "x" ? "x" : ""}</span>
      </div>
    </div>
  );
};

const FinancialSpreads = () => {
  const { applicationId } = usePipeline();
  const [data, setData] = useState(getFinancialSpreadsData("fraud"));

  useEffect(() => {
    if (!applicationId) return;
    api.getFinancials(applicationId).then(setData).catch(() => {});
  }, [applicationId]);

  const ratioCategories = [...new Set(data.ratios.map((r) => r.category))];
  const anomalyCount = data.ratios.filter((r) => r.anomaly).length;

  return (
    <ScrollArea className="h-[calc(100vh-120px)]">
      <div className="space-y-4 pr-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BarChart3 className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-display text-foreground">Financial Spreads</h2>
          </div>
          <div className="flex items-center gap-2">
            {anomalyCount > 0 && (
              <Badge className="bg-destructive/20 text-destructive border-destructive/30 text-xs">
                <AlertTriangle className="h-3 w-3 mr-1" />
                {anomalyCount} Anomalies
              </Badge>
            )}
            <Badge className="bg-secondary text-muted-foreground border-border text-xs">
              3-Year Spread (FY22–FY24)
            </Badge>
          </div>
        </div>

        {/* Statements */}
        <Tabs data-tour="spreads-statements" defaultValue="pnl">
          <TabsList className="bg-secondary/50 border border-border">
            <TabsTrigger value="pnl" className="text-xs font-display">Income Statement</TabsTrigger>
            <TabsTrigger value="bs" className="text-xs font-display">Balance Sheet</TabsTrigger>
            <TabsTrigger value="cf" className="text-xs font-display">Cash Flow</TabsTrigger>
          </TabsList>
          <TabsContent value="pnl" className="mt-3">
            <SpreadTable items={data.pnl} title="Profit & Loss Statement (₹ Lakhs)" />
          </TabsContent>
          <TabsContent value="bs" className="mt-3">
            <SpreadTable items={data.balanceSheet} title="Balance Sheet (₹ Lakhs)" />
          </TabsContent>
          <TabsContent value="cf" className="mt-3">
            <SpreadTable items={data.cashFlow} title="Cash Flow Statement (₹ Lakhs)" />
          </TabsContent>
        </Tabs>

        {/* Ratios */}
        <div data-tour="spreads-ratios">
          <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-3">
            Key Financial Ratios
          </h3>
          <div className="space-y-4">
            {ratioCategories.map((cat) => (
              <div key={cat}>
                <h4 className="text-xs font-display text-primary uppercase tracking-wider mb-2">
                  {categoryLabels[cat] || cat}
                </h4>
                <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
                  {data.ratios
                    .filter((r) => r.category === cat)
                    .map((ratio) => (
                      <RatioCard key={ratio.name} ratio={ratio} />
                    ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </ScrollArea>
  );
};

export default FinancialSpreads;
