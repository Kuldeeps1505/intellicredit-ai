import { useLocation, useNavigate } from "react-router-dom";
import { usePipeline } from "@/contexts/PipelineContext";
import { useTheme } from "@/contexts/ThemeContext";
import { Wifi, Palette } from "lucide-react";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";

const pageTitles: Record<string, string> = {
  "/": "Dashboard", "/upload": "Document Upload", "/agents": "Agent Progress",
  "/risk": "Risk Analytics", "/spreads": "Financial Spreads", "/bank-analytics": "Bank Analytics",
  "/promoter": "Promoter Intel", "/diligence": "Due Diligence", "/report": "CAM Report", "/audit": "Audit Trail",
};

export function AppHeader() {
  const location = useLocation();
  const navigate = useNavigate();
  const { application, pipelineStatus } = usePipeline();
  const { toggleTheme, themeName } = useTheme();
  const title = pageTitles[location.pathname] || "IntelliCredit AI";

  const companyName = application?.companyName ?? "No Application";
  const cin = application?.cin ?? "—";
  const score = application?.score;

  const scoreColor = !score ? "bg-secondary text-muted-foreground border-border" :
    score >= 70 ? "bg-safe text-white border-safe/50" :
    score >= 50 ? "bg-warning text-white border-warning/50" :
    "bg-destructive text-destructive-foreground border-destructive/50";

  const statusLabel = pipelineStatus === "running" ? "Running" :
    pipelineStatus === "completed" ? "Complete" :
    pipelineStatus === "error" ? "Error" : "Idle";

  return (
    <header className="h-14 border-b border-border/50 bg-card backdrop-blur-sm shadow-header flex items-center justify-between px-6 sticky top-0 z-40">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground font-body">IntelliCredit</span>
        <span className="text-muted-foreground/40">/</span>
        <span className="text-primary/80 font-display font-medium truncate max-w-[180px]">{companyName}</span>
        <span className="text-muted-foreground/40">/</span>
        <span className="text-foreground font-display font-medium">{title}</span>
      </div>

      <div className="flex items-center gap-3">
        <Tooltip>
          <TooltipTrigger asChild>
            <button onClick={toggleTheme} className="p-1.5 rounded-md hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground" aria-label="Toggle theme">
              <Palette className="h-4 w-4" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom"><span className="text-xs">{themeName}</span></TooltipContent>
        </Tooltip>

        {score != null && (
          <button onClick={() => navigate("/risk")}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono-numbers font-bold border shadow-md cursor-pointer transition-all hover:scale-105 ${scoreColor}`}
            title="Jump to Risk Analytics">
            <span>{score}</span>
            <span className="text-[8px] font-display opacity-80">/100</span>
          </button>
        )}

        {cin !== "—" && (
          <div className="bg-secondary px-3 py-1 rounded-md text-xs font-mono-numbers text-muted-foreground">
            {cin.slice(0, 12)}…
          </div>
        )}

        <div className="bg-secondary px-3 py-1 rounded-full text-[10px] font-display uppercase tracking-wider text-muted-foreground">
          {statusLabel}
        </div>

        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-safe opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-safe"></span>
          </span>
          <Wifi className="h-3.5 w-3.5 text-safe" />
        </div>
      </div>
    </header>
  );
}
