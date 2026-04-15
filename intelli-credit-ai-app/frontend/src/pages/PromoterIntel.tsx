import { useState, useEffect } from "react";
import { usePipeline } from "@/contexts/PipelineContext";
import { getPromoterData } from "@/lib/promoterData";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { motion } from "framer-motion";
import {
  Users, AlertTriangle, Shield, ShieldAlert, ShieldX,
  ExternalLink, Newspaper, Scale, Maximize2, X,
} from "lucide-react";
import { useMemo } from "react";
import { FraudNetworkGraph } from "@/components/FraudNetworkGraph";

const riskColors = {
  clean: "hsl(var(--safe))",
  warning: "hsl(var(--warning))",
  danger: "hsl(var(--destructive))",
};

const typeIcons: Record<string, string> = {
  director: "👤",
  company: "🏢",
  shell: "🐚",
  npa: "💀",
  related: "🔗",
};

const PromoterIntel = () => {
  const { applicationId } = usePipeline();
  const [data, setData] = useState(getPromoterData("fraud"));
  const [mapExpanded, setMapExpanded] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!applicationId) return;
    api.getPromoter(applicationId).then(setData).catch(() => {});
  }, [applicationId]);

  // Simple force-layout positions for network graph
  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {};
    const nodes = data.networkNodes;
    const cx = 300, cy = 200, radius = 140;
    nodes.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
      positions[n.id] = {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      };
    });
    return positions;
  }, [data.networkNodes]);

  const renderNetworkSvg = () => (
    <>
      {data.networkEdges.map((edge, i) => {
        const from = nodePositions[edge.from];
        const to = nodePositions[edge.to];
        if (!from || !to) return null;
        return (
          <g key={i}>
            <line
              x1={from.x} y1={from.y} x2={to.x} y2={to.y}
              stroke={edge.suspicious ? "hsl(var(--destructive))" : "hsl(var(--border))"}
              strokeWidth={edge.suspicious ? 2 : 1}
              strokeDasharray={edge.suspicious ? "6,3" : "none"}
              opacity={edge.suspicious ? 0.8 : 0.4}
            />
            <text
              x={(from.x + to.x) / 2}
              y={(from.y + to.y) / 2 - 6}
              fill="hsl(var(--muted-foreground))"
              fontSize="8"
              textAnchor="middle"
              fontFamily="IBM Plex Mono"
            >
              {edge.label}
            </text>
          </g>
        );
      })}
      {data.networkNodes.map((node) => {
        const pos = nodePositions[node.id];
        if (!pos) return null;
        const color = riskColors[node.risk];
        const r = node.type === "director" ? 22 : 18;
        return (
          <g key={node.id}>
            <circle cx={pos.x} cy={pos.y} r={r + 4} fill="none" stroke={color} strokeWidth={1} opacity={0.3} />
            <circle cx={pos.x} cy={pos.y} r={r} fill="hsl(var(--card))" stroke={color} strokeWidth={2} />
            <text x={pos.x} y={pos.y - 2} fill="currentColor" fontSize="12" textAnchor="middle" dominantBaseline="middle">
              {typeIcons[node.type] || "•"}
            </text>
            <text x={pos.x} y={pos.y + r + 14} fill="hsl(var(--foreground))" fontSize="9" textAnchor="middle" fontFamily="IBM Plex Mono">
              {node.label}
            </text>
            {node.risk === "danger" && (
              <circle cx={pos.x + r - 4} cy={pos.y - r + 4} r={5} fill="hsl(var(--destructive))" />
            )}
          </g>
        );
      })}
    </>
  );

  const overallRiskConfig = {
    low: { icon: Shield, color: "text-safe", bg: "bg-safe/15 border-safe/30", label: "LOW RISK" },
    medium: { icon: ShieldAlert, color: "text-warning", bg: "bg-warning/15 border-warning/30", label: "MEDIUM RISK" },
    high: { icon: ShieldX, color: "text-destructive", bg: "bg-destructive/15 border-destructive/30", label: "HIGH RISK" },
    critical: { icon: ShieldX, color: "text-destructive", bg: "bg-destructive/15 border-destructive/30 animate-border-glow-red", label: "CRITICAL RISK" },
  };

  const riskConfig = overallRiskConfig[data.overallPromoterRisk];
  const RiskIcon = riskConfig.icon;

  return (
    <ScrollArea className="h-[calc(100vh-120px)]">
      <div className="space-y-4 pr-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Users className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-display text-foreground">Promoter Intelligence</h2>
          </div>
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border ${riskConfig.bg}`}>
            <RiskIcon className={`h-4 w-4 ${riskConfig.color}`} />
            <span className={`text-sm font-display font-bold ${riskConfig.color}`}>{riskConfig.label}</span>
          </div>
        </div>

        {/* MCA Flags */}
        {data.mca21Flags.length > 0 && (
          <Card data-tour="promoter-mca" className="p-4 border-destructive/30 bg-destructive/5">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-destructive" />
              <h3 className="text-xs font-display text-destructive uppercase tracking-wider">
                MCA21 / Regulatory Flags ({data.mca21Flags.length})
              </h3>
            </div>
            <ul className="space-y-1.5">
              {data.mca21Flags.map((flag, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className="text-xs text-destructive/90 font-body flex items-start gap-2"
                >
                  <span className="text-destructive mt-0.5">•</span>
                  {flag}
                </motion.li>
              ))}
            </ul>
          </Card>
        )}

        {/* Director Cards + Network Graph */}
        <div data-tour="promoter-directors" className="grid grid-cols-[1fr_1fr] gap-4">
          {/* Director Cards */}
          <div className="space-y-3">
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">Directors & Key Personnel</h3>
            {data.directors.map((dir, i) => (
              <motion.div
                key={dir.din}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
              >
                <Card className={`p-4 ${dir.riskLevel === "flagged" ? "border-l-2 border-l-destructive" : dir.riskLevel === "watchlist" ? "border-l-2 border-l-warning" : ""}`}>
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="text-sm font-display text-foreground font-medium">{dir.name}</p>
                      <p className="text-[10px] text-muted-foreground font-mono-numbers">DIN: {dir.din} · {dir.designation}</p>
                    </div>
                    <Badge className={`text-[9px] ${
                      dir.riskLevel === "flagged" ? "bg-destructive/20 text-destructive border-destructive/30" :
                      dir.riskLevel === "watchlist" ? "bg-warning/20 text-warning border-warning/30" :
                      "bg-safe/20 text-safe border-safe/30"
                    }`}>
                      {dir.riskLevel.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-[10px]">
                    <div className="bg-secondary/50 rounded px-2 py-1.5">
                      <p className="text-muted-foreground">CIBIL</p>
                      <p className={`font-mono-numbers font-bold ${dir.cibilScore >= 750 ? "text-safe" : dir.cibilScore >= 650 ? "text-warning" : "text-destructive"}`}>
                        {dir.cibilScore}
                      </p>
                    </div>
                    <div className="bg-secondary/50 rounded px-2 py-1.5">
                      <p className="text-muted-foreground">Net Worth</p>
                      <p className="font-mono-numbers text-foreground">{dir.netWorth}</p>
                    </div>
                    <div className="bg-secondary/50 rounded px-2 py-1.5">
                      <p className="text-muted-foreground">NPA Links</p>
                      <p className={`font-mono-numbers font-bold ${dir.npaLinks > 0 ? "text-destructive" : "text-safe"}`}>
                        {dir.npaLinks}
                      </p>
                    </div>
                    <div className="bg-secondary/50 rounded px-2 py-1.5">
                      <p className="text-muted-foreground">Shell Links</p>
                      <p className={`font-mono-numbers font-bold ${dir.shellLinks > 0 ? "text-destructive" : "text-safe"}`}>
                        {dir.shellLinks}
                      </p>
                    </div>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-2">{dir.experience} · {dir.linkedEntities} linked entities</p>
                </Card>
              </motion.div>
            ))}
          </div>

          {/* Network Graph — D3 Force-Directed Fraud Network */}
          <Card data-tour="promoter-network" className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">Fraud Network Map</h3>
                {(data as any).fraudSummary && (
                  <p className="text-[10px] text-destructive mt-0.5">{(data as any).fraudSummary}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                {(data as any).totalFraudScore > 0 && (
                  <div className="flex items-center gap-1 px-2 py-1 bg-destructive/15 border border-destructive/30 rounded-full">
                    <AlertTriangle className="h-3 w-3 text-destructive" />
                    <span className="text-[10px] font-display text-destructive font-bold">
                      Fraud Score: {Math.round((data as any).totalFraudScore)}
                    </span>
                  </div>
                )}
                <button
                  onClick={() => setMapExpanded(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-primary/10 hover:bg-primary/20 text-primary text-[10px] font-display transition-colors"
                >
                  <Maximize2 className="h-3 w-3" /> Expand
                </button>
              </div>
            </div>
            <FraudNetworkGraph
              nodes={data.networkNodes as any}
              edges={data.networkEdges as any}
              width={500}
              height={280}
              compact
            />
          </Card>

          {/* Fullscreen Network Map Overlay */}
          {mapExpanded && (
            <div className="fixed inset-0 z-50 bg-background/95 backdrop-blur-md flex flex-col">
              {/* Overlay Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <h2 className="text-sm font-display text-foreground font-bold">Entity Network Map</h2>
                  <span className="text-[10px] font-mono-numbers text-muted-foreground">
                    {data.networkNodes.length} entities · {data.networkEdges.length} connections
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setZoom(z => Math.min(z + 0.25, 3))}
                    className="w-8 h-8 rounded-md bg-secondary hover:bg-secondary/80 text-foreground flex items-center justify-center text-sm font-mono-numbers transition-colors"
                  >+</button>
                  <span className="text-[10px] font-mono-numbers text-muted-foreground w-12 text-center">{Math.round(zoom * 100)}%</span>
                  <button
                    onClick={() => setZoom(z => Math.max(z - 0.25, 0.5))}
                    className="w-8 h-8 rounded-md bg-secondary hover:bg-secondary/80 text-foreground flex items-center justify-center text-sm font-mono-numbers transition-colors"
                  >−</button>
                  <button
                    onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
                    className="px-3 h-8 rounded-md bg-secondary hover:bg-secondary/80 text-[10px] font-display text-muted-foreground transition-colors"
                  >Reset</button>
                  <div className="w-px h-6 bg-border mx-1" />
                  <button
                    onClick={() => setMapExpanded(false)}
                    className="flex items-center gap-1.5 px-3 h-8 rounded-md bg-destructive/10 hover:bg-destructive/20 text-destructive text-[10px] font-display transition-colors"
                  >
                    <X className="h-3.5 w-3.5" /> Close
                  </button>
                </div>
              </div>

              {/* Fullscreen SVG with pan/zoom */}
              <div
                className="flex-1 overflow-hidden cursor-grab active:cursor-grabbing"
                onWheel={(e) => {
                  e.preventDefault();
                  setZoom(z => Math.min(Math.max(z + (e.deltaY < 0 ? 0.1 : -0.1), 0.5), 3));
                }}
                onMouseDown={(e) => {
                  const startX = e.clientX;
                  const startY = e.clientY;
                  const startPan = { ...pan };
                  const onMove = (ev: MouseEvent) => {
                    setPan({
                      x: startPan.x + (ev.clientX - startX) / zoom,
                      y: startPan.y + (ev.clientY - startY) / zoom,
                    });
                  };
                  const onUp = () => {
                    window.removeEventListener("mousemove", onMove);
                    window.removeEventListener("mouseup", onUp);
                  };
                  window.addEventListener("mousemove", onMove);
                  window.addEventListener("mouseup", onUp);
                }}
              >
                <svg
                  viewBox={`${300 - 300 / zoom - pan.x} ${200 - 200 / zoom - pan.y} ${600 / zoom} ${400 / zoom}`}
                  className="w-full h-full"
                >
                  {renderNetworkSvg()}
                </svg>
              </div>

              {/* Overlay Legend */}
              <div className="flex gap-6 justify-center py-3 border-t border-border">
                {[
                  { icon: "👤", label: "Director" },
                  { icon: "🏢", label: "Company" },
                  { icon: "🐚", label: "Shell" },
                  { icon: "💀", label: "NPA" },
                  { icon: "🔗", label: "Related" },
                ].map((l) => (
                  <span key={l.label} className="text-xs text-muted-foreground flex items-center gap-1.5">
                    <span>{l.icon}</span> {l.label}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Litigation Timeline + News */}
        <div className="grid grid-cols-2 gap-4">
          {/* Litigation */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Scale className="h-4 w-4 text-primary" />
              <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
                Litigation Timeline ({data.litigation.length})
              </h3>
            </div>
            <div className="space-y-3 relative">
              <div className="absolute left-[7px] top-2 bottom-2 w-px bg-border" />
              {data.litigation.map((c, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className="relative pl-6"
                >
                  <div className={`absolute left-0 top-1.5 w-[14px] h-[14px] rounded-full border-2 ${
                    c.severity === "critical" ? "border-destructive bg-destructive/20" :
                    c.severity === "high" ? "border-warning bg-warning/20" :
                    "border-muted-foreground bg-muted"
                  }`} />
                  <div className="bg-secondary/30 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-mono-numbers text-muted-foreground">{c.date}</span>
                      <div className="flex items-center gap-2">
                        <Badge className={`text-[8px] px-1.5 py-0 ${
                          c.status === "pending" ? "bg-warning/20 text-warning border-warning/30" :
                          c.status === "disposed" ? "bg-muted text-muted-foreground border-border" :
                          "bg-safe/20 text-safe border-safe/30"
                        }`}>
                          {c.status.toUpperCase()}
                        </Badge>
                        <span className="text-[10px] font-mono-numbers text-foreground">{c.amount}</span>
                      </div>
                    </div>
                    <p className="text-xs text-foreground font-body">{c.description}</p>
                    <p className="text-[9px] text-muted-foreground mt-1">{c.court} · {c.caseType}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </Card>

          {/* News Sentiment */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Newspaper className="h-4 w-4 text-primary" />
              <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
                News & Sentiment Feed
              </h3>
            </div>
            <div className="space-y-2">
              {data.news.map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className={`p-3 rounded-lg border ${
                    item.sentiment === "negative" ? "border-destructive/20 bg-destructive/5" :
                    item.sentiment === "positive" ? "border-safe/20 bg-safe/5" :
                    "border-border bg-secondary/30"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-mono-numbers text-muted-foreground">{item.date}</span>
                    <div className="flex items-center gap-2">
                      <span className={`text-[9px] font-display font-bold ${
                        item.sentiment === "negative" ? "text-destructive" :
                        item.sentiment === "positive" ? "text-safe" : "text-muted-foreground"
                      }`}>
                        {item.sentiment === "negative" ? "▼ NEG" : item.sentiment === "positive" ? "▲ POS" : "— NEU"}
                      </span>
                      <span className="text-[9px] font-mono-numbers text-muted-foreground">{item.relevance}%</span>
                    </div>
                  </div>
                  <p className="text-xs text-foreground font-body">{item.headline}</p>
                  <p className="text-[9px] text-muted-foreground mt-1">{item.source}</p>
                </motion.div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </ScrollArea>
  );
};

export default PromoterIntel;
