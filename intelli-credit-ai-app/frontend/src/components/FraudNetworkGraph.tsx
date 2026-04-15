/**
 * Fraud Network Graph — D3 Force-Directed
 * Real-time visualization of director → NPA/shell company connections.
 * NPA nodes pulse red. Suspicious edges are dashed red.
 * Fraud score badge shown per director node.
 */
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

interface NetworkNode {
  id: string;
  label: string;
  type: "director" | "company" | "shell" | "npa" | "related";
  risk: "clean" | "warning" | "danger";
  fraudScore?: number;
  amount?: string;
  din?: string;
  isPulsing?: boolean;
}

interface NetworkEdge {
  from: string;
  to: string;
  label: string;
  suspicious: boolean;
  edgeType?: string;
  amount?: string;
}

interface Props {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  width?: number;
  height?: number;
  compact?: boolean;
}

// Node visual config
const NODE_CONFIG = {
  company:  { r: 28, fill: "#1e3a5f", stroke: "#3b82f6", emoji: "🏢" },
  director: { r: 22, fill: "#1e40af", stroke: "#60a5fa", emoji: "👤" },
  npa:      { r: 20, fill: "#7f1d1d", stroke: "#ef4444", emoji: "💀" },
  shell:    { r: 18, fill: "#78350f", stroke: "#f59e0b", emoji: "🐚" },
  related:  { r: 16, fill: "#374151", stroke: "#9ca3af", emoji: "🔗" },
};

const RISK_STROKE = {
  clean:   "#22c55e",
  warning: "#f59e0b",
  danger:  "#ef4444",
};

export function FraudNetworkGraph({ nodes, edges, width = 600, height = 400, compact = false }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [hoveredNode, setHoveredNode] = useState<NetworkNode | null>(null);
  const [tick, setTick] = useState(0);

  // Force-directed layout simulation
  useEffect(() => {
    if (!nodes.length) return;

    const cx = width / 2;
    const cy = height / 2;

    // Initialize positions
    const pos: Record<string, { x: number; y: number; vx: number; vy: number }> = {};

    // Company node at center
    const companyNode = nodes.find(n => n.type === "company");
    if (companyNode) {
      pos[companyNode.id] = { x: cx, y: cy, vx: 0, vy: 0 };
    }

    // Directors in inner ring
    const directors = nodes.filter(n => n.type === "director");
    directors.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / directors.length - Math.PI / 2;
      const r = compact ? 100 : 130;
      pos[n.id] = { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle), vx: 0, vy: 0 };
    });

    // NPA/shell nodes in outer ring around their director
    const outerNodes = nodes.filter(n => n.type === "npa" || n.type === "shell" || n.type === "related");
    outerNodes.forEach((n, i) => {
      // Find parent director via edges
      const parentEdge = edges.find(e => e.to === n.id);
      const parentPos = parentEdge ? pos[parentEdge.from] : null;
      if (parentPos) {
        const angle = (2 * Math.PI * i) / outerNodes.length;
        const r = compact ? 60 : 80;
        pos[n.id] = {
          x: parentPos.x + r * Math.cos(angle),
          y: parentPos.y + r * Math.sin(angle),
          vx: 0, vy: 0,
        };
      } else {
        const angle = (2 * Math.PI * i) / outerNodes.length;
        const r = compact ? 160 : 200;
        pos[n.id] = { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle), vx: 0, vy: 0 };
      }
    });

    // Run force simulation
    const ITERATIONS = 80;
    const REPULSION = 2000;
    const ATTRACTION = 0.05;
    const DAMPING = 0.85;

    for (let iter = 0; iter < ITERATIONS; iter++) {
      // Repulsion between all nodes
      const nodeIds = Object.keys(pos);
      for (let i = 0; i < nodeIds.length; i++) {
        for (let j = i + 1; j < nodeIds.length; j++) {
          const a = pos[nodeIds[i]];
          const b = pos[nodeIds[j]];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = REPULSION / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx -= fx; a.vy -= fy;
          b.vx += fx; b.vy += fy;
        }
      }

      // Attraction along edges
      edges.forEach(e => {
        const a = pos[e.from];
        const b = pos[e.to];
        if (!a || !b) return;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const targetDist = e.suspicious ? (compact ? 90 : 110) : (compact ? 110 : 140);
        const force = (dist - targetDist) * ATTRACTION;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx += fx; a.vy += fy;
        b.vx -= fx; b.vy -= fy;
      });

      // Center gravity
      Object.values(pos).forEach(p => {
        p.vx += (cx - p.x) * 0.01;
        p.vy += (cy - p.y) * 0.01;
      });

      // Apply velocity + damping + boundary
      Object.values(pos).forEach(p => {
        p.vx *= DAMPING; p.vy *= DAMPING;
        p.x = Math.max(30, Math.min(width - 30, p.x + p.vx));
        p.y = Math.max(30, Math.min(height - 30, p.y + p.vy));
      });
    }

    const finalPos: Record<string, { x: number; y: number }> = {};
    Object.entries(pos).forEach(([id, p]) => { finalPos[id] = { x: p.x, y: p.y }; });
    setPositions(finalPos);
  }, [nodes, edges, width, height, compact]);

  // Pulse tick for NPA/shell nodes
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1200);
    return () => clearInterval(id);
  }, []);

  const handleMouseDown = (e: React.MouseEvent) => {
    setDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragging) return;
    setOffset({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };
  const handleMouseUp = () => setDragging(false);

  const suspiciousCount = edges.filter(e => e.suspicious).length;
  const npaCount = nodes.filter(n => n.type === "npa").length;
  const shellCount = nodes.filter(n => n.type === "shell").length;

  return (
    <div className="relative select-none">
      {/* Stats bar */}
      {!compact && (
        <div className="flex items-center gap-3 mb-2 flex-wrap">
          <span className="text-[10px] font-mono-numbers text-muted-foreground">
            {nodes.length} entities · {edges.length} connections
          </span>
          {suspiciousCount > 0 && (
            <span className="text-[10px] font-display text-destructive flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" /> {suspiciousCount} suspicious links
            </span>
          )}
          {npaCount > 0 && (
            <span className="text-[10px] bg-destructive/20 text-destructive px-1.5 py-0.5 rounded font-display">
              💀 {npaCount} NPA entities
            </span>
          )}
          {shellCount > 0 && (
            <span className="text-[10px] bg-warning/20 text-warning px-1.5 py-0.5 rounded font-display">
              🐚 {shellCount} shell companies
            </span>
          )}
          {/* Zoom controls */}
          <div className="ml-auto flex items-center gap-1">
            <button onClick={() => setScale(s => Math.min(s + 0.2, 2.5))}
              className="p-1 rounded hover:bg-secondary text-muted-foreground hover:text-foreground">
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
            <button onClick={() => setScale(s => Math.max(s - 0.2, 0.4))}
              className="p-1 rounded hover:bg-secondary text-muted-foreground hover:text-foreground">
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <button onClick={() => { setScale(1); setOffset({ x: 0, y: 0 }); }}
              className="p-1 rounded hover:bg-secondary text-muted-foreground hover:text-foreground">
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* SVG Graph */}
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className={`w-full rounded-lg border border-border bg-background/50 ${dragging ? "cursor-grabbing" : "cursor-grab"}`}
        style={{ maxHeight: compact ? 260 : 400 }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <defs>
          {/* Glow filter for NPA nodes */}
          <filter id="npa-glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="shell-glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          {/* Arrow marker for suspicious edges */}
          <marker id="arrow-red" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#ef4444" opacity="0.8" />
          </marker>
          <marker id="arrow-gray" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#6b7280" opacity="0.4" />
          </marker>
        </defs>

        <g transform={`translate(${offset.x},${offset.y}) scale(${scale})`}>
          {/* Edges */}
          {edges.map((edge, i) => {
            const from = positions[edge.from];
            const to = positions[edge.to];
            if (!from || !to) return null;
            const midX = (from.x + to.x) / 2;
            const midY = (from.y + to.y) / 2;
            return (
              <g key={`edge-${i}`}>
                <line
                  x1={from.x} y1={from.y} x2={to.x} y2={to.y}
                  stroke={edge.suspicious ? "#ef4444" : "#374151"}
                  strokeWidth={edge.suspicious ? 2 : 1}
                  strokeDasharray={edge.suspicious ? "6,3" : "none"}
                  opacity={edge.suspicious ? 0.85 : 0.35}
                  markerEnd={edge.suspicious ? "url(#arrow-red)" : "url(#arrow-gray)"}
                />
                {!compact && (
                  <text x={midX} y={midY - 5} fill={edge.suspicious ? "#ef4444" : "#6b7280"}
                    fontSize="7" textAnchor="middle" fontFamily="monospace" opacity={0.9}>
                    {edge.label}
                    {edge.amount ? ` ${edge.amount}` : ""}
                  </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const pos = positions[node.id];
            if (!pos) return null;
            const cfg = NODE_CONFIG[node.type] || NODE_CONFIG.related;
            const strokeColor = RISK_STROKE[node.risk] || "#6b7280";
            const isPulsing = node.isPulsing;
            const pulseScale = isPulsing ? (1 + 0.15 * Math.sin(tick * 1.5)) : 1;

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x},${pos.y})`}
                onMouseEnter={() => setHoveredNode(node)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: "pointer" }}
              >
                {/* Pulse ring for NPA/shell nodes */}
                {isPulsing && (
                  <circle
                    r={cfg.r * pulseScale + 8}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={1.5}
                    opacity={0.3 + 0.2 * Math.sin(tick * 1.5)}
                  />
                )}
                {/* Second pulse ring */}
                {isPulsing && (
                  <circle
                    r={cfg.r * pulseScale + 16}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={0.8}
                    opacity={0.15 + 0.1 * Math.sin(tick * 1.5 + 1)}
                  />
                )}
                {/* Main node circle */}
                <circle
                  r={cfg.r}
                  fill={cfg.fill}
                  stroke={strokeColor}
                  strokeWidth={node.risk === "danger" ? 2.5 : 1.5}
                  filter={node.type === "npa" ? "url(#npa-glow)" : node.type === "shell" ? "url(#shell-glow)" : undefined}
                />
                {/* Emoji icon */}
                <text textAnchor="middle" dominantBaseline="middle" fontSize={compact ? 10 : 12} y={-2}>
                  {cfg.emoji}
                </text>
                {/* Label */}
                <text
                  textAnchor="middle"
                  y={cfg.r + 11}
                  fontSize={compact ? 6 : 7.5}
                  fill={node.risk === "danger" ? "#fca5a5" : node.risk === "warning" ? "#fcd34d" : "#d1d5db"}
                  fontFamily="monospace"
                  fontWeight={node.risk === "danger" ? "bold" : "normal"}
                >
                  {node.label.slice(0, compact ? 8 : 12)}
                </text>
                {/* Fraud score badge */}
                {!compact && node.fraudScore && node.fraudScore > 0 && (
                  <g transform={`translate(${cfg.r - 4}, ${-cfg.r + 4})`}>
                    <circle r={8} fill={node.fraudScore > 60 ? "#dc2626" : "#d97706"} />
                    <text textAnchor="middle" dominantBaseline="middle" fontSize="6"
                      fill="white" fontWeight="bold">
                      {Math.round(node.fraudScore)}
                    </text>
                  </g>
                )}
                {/* NPA amount label */}
                {node.amount && !compact && (
                  <text textAnchor="middle" y={cfg.r + 20} fontSize="6"
                    fill="#fca5a5" fontFamily="monospace">
                    {node.amount}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {/* Hover tooltip */}
      {hoveredNode && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-2 left-2 bg-card border border-border rounded-lg px-3 py-2 text-xs shadow-lg z-10 max-w-[220px]"
        >
          <p className="font-display text-foreground font-bold">{hoveredNode.label}</p>
          <p className="text-muted-foreground capitalize">{hoveredNode.type} · {hoveredNode.risk} risk</p>
          {hoveredNode.din && <p className="text-muted-foreground font-mono-numbers">DIN: {hoveredNode.din}</p>}
          {hoveredNode.amount && <p className="text-destructive font-mono-numbers">{hoveredNode.amount}</p>}
          {hoveredNode.fraudScore !== undefined && hoveredNode.fraudScore > 0 && (
            <p className={`font-display font-bold ${hoveredNode.fraudScore > 60 ? "text-destructive" : "text-warning"}`}>
              Fraud Score: {hoveredNode.fraudScore}/100
            </p>
          )}
        </motion.div>
      )}

      {/* Legend */}
      {!compact && (
        <div className="flex gap-4 mt-2 flex-wrap">
          {[
            { icon: "🏢", label: "Company", color: "text-muted-foreground" },
            { icon: "👤", label: "Director", color: "text-muted-foreground" },
            { icon: "💀", label: "NPA Entity", color: "text-destructive" },
            { icon: "🐚", label: "Shell Co", color: "text-warning" },
            { icon: "🔗", label: "Related", color: "text-muted-foreground" },
          ].map(l => (
            <span key={l.label} className={`text-[9px] flex items-center gap-1 ${l.color}`}>
              <span>{l.icon}</span> {l.label}
            </span>
          ))}
          <span className="text-[9px] text-destructive flex items-center gap-1 ml-auto">
            <span className="inline-block w-4 border-t-2 border-dashed border-destructive" /> Suspicious link
          </span>
        </div>
      )}
    </div>
  );
}
