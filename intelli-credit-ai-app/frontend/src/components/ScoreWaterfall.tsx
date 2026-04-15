/**
 * SHAP-style Score Waterfall Chart
 * Shows exactly which factors added/subtracted points from the credit score.
 * RBI-grade explainability — every point accounted for.
 */
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TrendingUp, TrendingDown, Info, ChevronDown, ChevronUp } from "lucide-react";
import { api } from "@/lib/api";

interface WaterfallStep {
  label: string;
  value: number;
  cumulative: number;
  category: "positive" | "negative" | "neutral";
  detail: string;
  source: string;
}

interface ScoreExplanation {
  baseScore: number;
  finalScore: number;
  decision: string;
  steps: WaterfallStep[];
  positiveTotal: number;
  negativeTotal: number;
  dataSource: string;
}

interface Props {
  applicationId: string;
  compact?: boolean;
}

const SOURCE_COLORS: Record<string, string> = {
  DSCR:          "hsl(var(--info))",
  Leverage:      "hsl(var(--warning))",
  GST:           "hsl(var(--destructive))",
  Concentration: "hsl(var(--caution))",
  Litigation:    "hsl(var(--destructive))",
  Liquidity:     "hsl(var(--info))",
  Profitability: "hsl(var(--safe))",
  Promoter:      "hsl(var(--primary))",
  CashFlow:      "hsl(var(--warning))",
  Model:         "hsl(var(--muted-foreground))",
};

const DECISION_CONFIG = {
  APPROVE:      { color: "text-safe",        bg: "bg-safe/15 border-safe/30",               label: "APPROVE" },
  CONDITIONAL:  { color: "text-warning",     bg: "bg-warning/15 border-warning/30",         label: "CONDITIONAL" },
  REJECT:       { color: "text-destructive", bg: "bg-destructive/15 border-destructive/30", label: "REJECT" },
  PENDING:      { color: "text-muted-foreground", bg: "bg-secondary border-border",         label: "PENDING" },
};

export function ScoreWaterfall({ applicationId, compact = false }: Props) {
  const [data, setData] = useState<ScoreExplanation | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  useEffect(() => {
    if (!applicationId) return;
    setLoading(true);
    api.getScoreExplanation(applicationId)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [applicationId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32 text-muted-foreground text-xs">
        <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full mr-2" />
        Computing score explanation...
      </div>
    );
  }

  if (!data || data.dataSource === "pending") {
    return (
      <div className="flex items-center justify-center h-24 text-muted-foreground text-xs">
        Run pipeline to see score explanation
      </div>
    );
  }

  const dec = DECISION_CONFIG[data.decision as keyof typeof DECISION_CONFIG] ?? DECISION_CONFIG.PENDING;
  const maxAbsValue = Math.max(...data.steps.map(s => Math.abs(s.value)), 1);
  const BAR_MAX_WIDTH = compact ? 120 : 200;

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] text-muted-foreground font-display uppercase tracking-wider">
            Score Decomposition — SHAP Style
          </p>
          <p className="text-[9px] text-muted-foreground mt-0.5">
            Base: {data.baseScore} → Final: {data.finalScore}/100
          </p>
        </div>
        <div className={`px-3 py-1.5 rounded-lg border text-xs font-display font-bold ${dec.bg} ${dec.color}`}>
          {dec.label}
        </div>
      </div>

      {/* Summary pills */}
      <div className="flex gap-2">
        <div className="flex items-center gap-1 px-2 py-1 bg-safe/10 border border-safe/20 rounded-full">
          <TrendingUp className="h-3 w-3 text-safe" />
          <span className="text-[10px] font-mono-numbers text-safe font-bold">+{data.positiveTotal}</span>
        </div>
        <div className="flex items-center gap-1 px-2 py-1 bg-destructive/10 border border-destructive/20 rounded-full">
          <TrendingDown className="h-3 w-3 text-destructive" />
          <span className="text-[10px] font-mono-numbers text-destructive font-bold">{data.negativeTotal}</span>
        </div>
        <div className="ml-auto flex items-center gap-1 px-2 py-1 bg-secondary border border-border rounded-full">
          <span className="text-[10px] font-mono-numbers text-foreground font-bold">
            = {data.finalScore}/100
          </span>
        </div>
      </div>

      {/* Waterfall rows */}
      <div className="space-y-1">
        {/* Base score row */}
        <div className="flex items-center gap-2 py-1.5 border-b border-border/50">
          <span className="text-[10px] font-display text-muted-foreground w-32 shrink-0">Base Score</span>
          <div className="flex items-center gap-1 flex-1">
            <div
              className="h-5 rounded-sm bg-secondary border border-border"
              style={{ width: `${(data.baseScore / 100) * BAR_MAX_WIDTH}px` }}
            />
            <span className="text-[10px] font-mono-numbers text-muted-foreground">{data.baseScore}</span>
          </div>
        </div>

        {/* Step rows */}
        {data.steps.map((step, i) => {
          const barWidth = Math.round((Math.abs(step.value) / maxAbsValue) * BAR_MAX_WIDTH * 0.7);
          const isPos = step.category === "positive";
          const isNeg = step.category === "negative";
          const barColor = isPos ? "hsl(var(--safe))" : isNeg ? "hsl(var(--destructive))" : "hsl(var(--muted-foreground))";
          const sourceColor = SOURCE_COLORS[step.source] || "hsl(var(--muted-foreground))";
          const isExpanded = expandedStep === i;

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <button
                className={`w-full flex items-center gap-2 py-1.5 rounded-md px-1 transition-colors text-left ${
                  isExpanded ? "bg-secondary/50" : "hover:bg-secondary/30"
                }`}
                onClick={() => setExpandedStep(isExpanded ? null : i)}
              >
                {/* Label */}
                <span className={`text-[10px] font-display w-32 shrink-0 truncate ${
                  isPos ? "text-safe" : isNeg ? "text-destructive" : "text-muted-foreground"
                }`}>
                  {step.label}
                </span>

                {/* Bar */}
                <div className="flex items-center gap-1 flex-1 min-w-0">
                  {/* Negative bar goes left, positive goes right */}
                  <div className="flex items-center justify-end" style={{ width: `${BAR_MAX_WIDTH * 0.5}px` }}>
                    {isNeg && (
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: barWidth }}
                        transition={{ delay: i * 0.04 + 0.1, duration: 0.4 }}
                        className="h-4 rounded-sm"
                        style={{ backgroundColor: barColor, opacity: 0.85 }}
                      />
                    )}
                  </div>
                  {/* Center line */}
                  <div className="w-px h-4 bg-border shrink-0" />
                  <div className="flex items-center" style={{ width: `${BAR_MAX_WIDTH * 0.5}px` }}>
                    {isPos && (
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: barWidth }}
                        transition={{ delay: i * 0.04 + 0.1, duration: 0.4 }}
                        className="h-4 rounded-sm"
                        style={{ backgroundColor: barColor, opacity: 0.85 }}
                      />
                    )}
                  </div>
                </div>

                {/* Value */}
                <span className={`text-[10px] font-mono-numbers font-bold w-10 text-right shrink-0 ${
                  isPos ? "text-safe" : isNeg ? "text-destructive" : "text-muted-foreground"
                }`}>
                  {isPos ? "+" : ""}{step.value}
                </span>

                {/* Cumulative */}
                <span className="text-[10px] font-mono-numbers text-muted-foreground w-8 text-right shrink-0">
                  {step.cumulative}
                </span>

                {/* Source tag */}
                {!compact && (
                  <span
                    className="text-[8px] px-1.5 py-0.5 rounded font-display shrink-0"
                    style={{ backgroundColor: `${sourceColor}20`, color: sourceColor, border: `1px solid ${sourceColor}40` }}
                  >
                    {step.source}
                  </span>
                )}

                {/* Expand icon */}
                {isExpanded
                  ? <ChevronUp className="h-3 w-3 text-muted-foreground shrink-0" />
                  : <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
                }
              </button>

              {/* Expanded detail */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="overflow-hidden"
                  >
                    <div className="ml-1 mr-1 mb-1 px-3 py-2 bg-secondary/30 rounded-md border border-border/50">
                      <div className="flex items-start gap-1.5">
                        <Info className="h-3 w-3 text-muted-foreground shrink-0 mt-0.5" />
                        <p className="text-[10px] text-muted-foreground font-body leading-relaxed">
                          {step.detail}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}

        {/* Final score row */}
        <div className="flex items-center gap-2 py-2 border-t border-border mt-1">
          <span className="text-[10px] font-display font-bold text-foreground w-32 shrink-0">Final Score</span>
          <div className="flex items-center gap-1 flex-1">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(data.finalScore / 100) * BAR_MAX_WIDTH}px` }}
              transition={{ delay: data.steps.length * 0.04 + 0.2, duration: 0.5 }}
              className="h-5 rounded-sm"
              style={{
                backgroundColor: data.finalScore >= 75 ? "hsl(var(--safe))"
                  : data.finalScore >= 50 ? "hsl(var(--warning))"
                  : "hsl(var(--destructive))",
              }}
            />
            <span className={`text-sm font-mono-numbers font-bold ml-1 ${
              data.finalScore >= 75 ? "text-safe"
                : data.finalScore >= 50 ? "text-warning"
                : "text-destructive"
            }`}>
              {data.finalScore}/100
            </span>
          </div>
        </div>
      </div>

      {/* RBI note */}
      {!compact && (
        <p className="text-[9px] text-muted-foreground/60 font-body">
          ⓘ Score decomposition uses logistic regression coefficients calibrated to RBI NPA benchmarks.
          Each factor's contribution is computed as coefficient × feature value × weight.
        </p>
      )}
    </div>
  );
}
