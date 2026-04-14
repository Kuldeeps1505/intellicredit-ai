import { useEffect, useRef, useState } from "react";
import { usePipeline } from "@/contexts/PipelineContext";
import { agentNodes, AgentStatus } from "@/lib/agentData";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText, BarChart3, ShieldCheck, Zap, Users, Target, FileOutput, GitBranch,
  Play, RotateCcw, CheckCircle2, XCircle, Loader2, RefreshCw,
} from "lucide-react";

const iconMap: Record<string, React.ElementType> = {
  FileText, BarChart3, ShieldCheck, Zap, Users, Target, FileOutput, GitBranch,
};

const AGENT_COLORS: Record<string, string> = {
  DocParser: "text-foreground", FinSpread: "text-info", GSTVerify: "text-safe",
  GSTREngine: "text-warning", BuyerEng: "text-caution", PromoterAI: "text-primary",
  RiskScore: "text-destructive", CAMGen: "text-foreground", CounterFact: "text-info",
};

const RENDER_GROUPS = [
  { ids: ["doc_parse"],                   parallel: false },
  { ids: ["fin_spread", "gst_verify"],    parallel: true  },
  { ids: ["gstr_engine", "buyer_engine"], parallel: true  },
  { ids: ["promoter_intel"],              parallel: false },
  { ids: ["risk_score"],                  parallel: false },
  { ids: ["cam_gen"],                     parallel: false },
  { ids: ["counter_fact"],                parallel: false },
];

const AgentProgress = () => {
  const {
    running, finished, nodeStates, visibleLogs, overallProgress,
    riskToasts, startPipeline, applicationId, setApplicationId,
  } = usePipeline();

  const logEndRef = useRef<HTMLDivElement>(null);
  const [tick, setTick] = useState(0);

  // Tick every second to update elapsed timers on running agents
  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, [running]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [visibleLogs]);

  // Re-hydrate state from backend on mount
  useEffect(() => {
    if (applicationId) setApplicationId(applicationId);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const getStatusIcon = (status: AgentStatus) => {
    if (status === "running")  return <Loader2 className="h-4 w-4 animate-spin text-info" />;
    if (status === "complete") return <CheckCircle2 className="h-4 w-4 text-safe" />;
    if (status === "error")    return <XCircle className="h-4 w-4 text-destructive" />;
    return null;
  };

  const getLogColor = (level: string) => {
    if (level === "critical") return "text-destructive";
    if (level === "warning")  return "text-warning";
    return "text-muted-foreground";
  };

  const hasData = Object.keys(nodeStates).length > 0 || overallProgress > 0 || visibleLogs.length > 0;
  const isDone  = finished || overallProgress >= 100;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div data-tour="agent-progress" className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-display text-muted-foreground uppercase tracking-wider">
              Pipeline Progress
            </h2>
            {running && (
              <Badge className="bg-info/20 text-info border-info/30 text-[10px] flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" /> Running
              </Badge>
            )}
            {isDone && (
              <Badge className="bg-safe/20 text-safe border-safe/30 text-[10px]">✓ Complete</Badge>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className="font-mono-numbers text-sm text-foreground">{Math.round(overallProgress)}%</span>
            {!applicationId && (
              <span className="text-xs text-muted-foreground font-body">Upload documents first</span>
            )}
            {applicationId && !running && !isDone && (
              <Button size="sm" onClick={() => startPipeline()} className="gap-1.5">
                <Play className="h-3.5 w-3.5" /> Run Pipeline
              </Button>
            )}
            {applicationId && hasData && !running && (
              <Button size="sm" variant="outline" onClick={() => setApplicationId(applicationId)} className="gap-1.5">
                <RefreshCw className="h-3.5 w-3.5" /> Refresh
              </Button>
            )}
            {isDone && (
              <Button size="sm" variant="outline" onClick={() => startPipeline()} className="gap-1.5">
                <RotateCcw className="h-3.5 w-3.5" /> Re-run
              </Button>
            )}
          </div>
        </div>
        <Progress value={overallProgress} className="h-2" />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-[340px_1fr] gap-4 h-[calc(100vh-220px)]">

        {/* Agent nodes */}
        <Card data-tour="agent-pipeline" className="p-4 overflow-y-auto">
          <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider mb-4">
            Agent Pipeline
          </h3>
          <div className="space-y-0">
            {RENDER_GROUPS.map((group, gi) => (
              <div key={gi}>
                {gi > 0 && (
                  <div className="flex justify-center py-1">
                    <div className={`w-px h-5 ${
                      nodeStates[group.ids[0]]?.status === "complete" ||
                      nodeStates[group.ids[0]]?.status === "running"
                        ? "bg-primary" : "bg-border"
                    }`} />
                  </div>
                )}
                <div className={`flex ${group.parallel ? "gap-2 justify-center" : "justify-center"}`}>
                  {group.ids.map((id) => {
                    const node = agentNodes.find((n) => n.id === id);
                    const state = nodeStates[id] ?? { status: "idle" as AgentStatus, elapsed: 0 };
                    const IconComp = iconMap[node?.icon ?? ""] ?? FileText;
                    return (
                      <div
                        key={id}
                        className={`flex items-center gap-2.5 px-3 py-2 rounded-lg border transition-all ${
                          group.parallel ? "flex-1 max-w-[155px]" : "w-full max-w-[280px]"
                        } ${
                          state.status === "running"  ? "border-info bg-info/5" :
                          state.status === "complete" ? "border-safe/30 bg-safe/5" :
                          state.status === "error"    ? "border-destructive bg-destructive/5" :
                          "border-border bg-card"
                        }`}
                      >
                        <div className={`relative flex items-center justify-center w-8 h-8 rounded-full shrink-0 ${
                          state.status === "running"  ? "bg-info/20" :
                          state.status === "complete" ? "bg-primary" : "bg-muted"
                        }`}>
                          {state.status === "running" && (
                            <span className="absolute inset-0 rounded-full animate-ping bg-info/20" />
                          )}
                          {state.status === "complete"
                            ? <CheckCircle2 className="h-4 w-4 text-primary-foreground" />
                            : <IconComp className={`h-4 w-4 ${state.status === "running" ? "text-info" : "text-muted-foreground"}`} />
                          }
                        </div>
                        <div className="min-w-0 flex-1">
                          <span className={`text-xs font-display truncate block ${
                            state.status === "idle" ? "text-muted-foreground" : "text-foreground"
                          }`}>
                            {node?.shortName ?? id}
                          </span>
                          <div className="flex items-center gap-1 mt-0.5">
                            {getStatusIcon(state.status)}
                            <span className="text-[10px] font-mono-numbers text-muted-foreground">
                              {state.status === "idle"     ? "Waiting" :
                               state.status === "running"  ? `${state.elapsed + tick}s` :
                               state.status === "complete" ? `${state.elapsed}s ✓` : "Error"}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Log stream */}
        <Card data-tour="agent-logs" className="flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
              Live Log Stream
            </h3>
            <Badge variant="secondary" className="text-[10px] font-mono-numbers">
              {visibleLogs.length} entries
            </Badge>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-3 font-mono-numbers text-xs space-y-0.5 bg-background/50 min-h-full">
              {visibleLogs.length === 0 && (
                <div className="flex flex-col items-center justify-center h-40 gap-2 text-muted-foreground">
                  {!applicationId
                    ? <p className="text-sm font-body">Upload documents first</p>
                    : running
                    ? <><Loader2 className="h-5 w-5 animate-spin text-info" /><p className="text-sm font-body">Pipeline starting...</p></>
                    : <p className="text-sm font-body">Click "Run Pipeline" to start analysis</p>
                  }
                </div>
              )}
              <AnimatePresence initial={false}>
                {visibleLogs.map((log, i) => (
                  <motion.div
                    key={`${log.timestamp}-${i}`}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.12 }}
                    className={`py-0.5 ${log.level === "critical" ? "bg-destructive/10 px-2 rounded -mx-2" : ""}`}
                  >
                    <span className="text-muted-foreground/60">[{log.timestamp}]</span>{" "}
                    <span className={`font-semibold ${AGENT_COLORS[log.agent] ?? "text-muted-foreground"}`}>
                      [{log.agent}]
                    </span>{" "}
                    <span className={getLogColor(log.level)}>{log.message}</span>
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={logEndRef} />
            </div>
          </ScrollArea>
        </Card>
      </div>

      {/* Risk toasts */}
      <div className="fixed bottom-6 right-6 z-50 space-y-2 max-w-sm">
        <AnimatePresence>
          {riskToasts.map((toast, i) => (
            <motion.div
              key={toast.timestamp + toast.message}
              initial={{ opacity: 0, x: 100 }} animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 100 }} transition={{ duration: 0.3, delay: i * 0.1 }}
              className={`px-4 py-3 rounded-lg border shadow-lg ${
                toast.level === "critical"
                  ? "bg-destructive/20 border-destructive text-destructive"
                  : "bg-warning/20 border-warning text-warning"
              }`}
            >
              <div className="flex items-start gap-2">
                <span className="text-base">🚨</span>
                <div>
                  <p className="text-xs font-display font-bold">{toast.agent}</p>
                  <p className="text-xs font-body mt-0.5">{toast.message}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default AgentProgress;
