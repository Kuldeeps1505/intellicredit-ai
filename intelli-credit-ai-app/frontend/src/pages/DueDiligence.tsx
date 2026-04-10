import { useState, useEffect } from "react";
import { usePipeline } from "@/contexts/PipelineContext";
import { getDiligenceData } from "@/lib/diligenceData";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { motion } from "framer-motion";
import {
  CheckCircle2, XCircle, Clock, AlertTriangle, MinusCircle,
  FileSearch, MapPin, Camera, Eye, ArrowRight,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const statusConfig = {
  verified: { icon: CheckCircle2, color: "text-safe", bg: "bg-safe/15", label: "VERIFIED" },
  pending: { icon: Clock, color: "text-warning", bg: "bg-warning/15", label: "PENDING" },
  flagged: { icon: XCircle, color: "text-destructive", bg: "bg-destructive/15", label: "FLAGGED" },
  waived: { icon: MinusCircle, color: "text-muted-foreground", bg: "bg-muted", label: "WAIVED" },
  not_applicable: { icon: MinusCircle, color: "text-muted-foreground", bg: "bg-muted", label: "N/A" },
};


const DueDiligence = () => {
  const { applicationId } = usePipeline();
  const [data, setData] = useState(getDiligenceData("fraud"));
  const navigate = useNavigate();

  useEffect(() => {
    if (!applicationId) return;
    api.getDiligence(applicationId).then(setData).catch(() => {});
  }, [applicationId]);

  const categories = [...new Set(data.checks.map((c) => c.category))];
  const verified = data.checks.filter((c) => c.status === "verified").length;
  const flagged = data.checks.filter((c) => c.status === "flagged").length;
  const pending = data.checks.filter((c) => c.status === "pending").length;

  const overallColor = data.overallStatus === "clear" ? "text-safe" :
    data.overallStatus === "concerns" ? "text-warning" : "text-destructive";

  return (
    <ScrollArea className="h-[calc(100vh-120px)]">
      <div className="space-y-4 pr-2">
        {/* Header Stats */}
        <div data-tour="diligence-stats" className="grid grid-cols-4 gap-3">
          <Card className="p-4">
            <p className="text-xs text-muted-foreground font-display uppercase tracking-wider">Completion</p>
            <div className="flex items-end gap-2 mt-1">
              <span className={`text-2xl font-mono-numbers font-bold ${overallColor}`}>{data.completionPercent}%</span>
            </div>
            <Progress value={data.completionPercent} className="mt-2 h-1.5" />
          </Card>
          <Card className="p-4">
            <p className="text-xs text-muted-foreground font-display uppercase tracking-wider">Verified</p>
            <span className="text-2xl font-mono-numbers font-bold text-safe">{verified}</span>
            <p className="text-xs text-muted-foreground">of {data.checks.length} checks</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-muted-foreground font-display uppercase tracking-wider">Flagged</p>
            <span className={`text-2xl font-mono-numbers font-bold ${flagged > 0 ? "text-destructive" : "text-safe"}`}>{flagged}</span>
            <p className="text-xs text-muted-foreground">items require attention</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-muted-foreground font-display uppercase tracking-wider">Pending</p>
            <span className={`text-2xl font-mono-numbers font-bold ${pending > 0 ? "text-warning" : "text-safe"}`}>{pending}</span>
            <p className="text-xs text-muted-foreground">awaiting verification</p>
          </Card>
        </div>

        {/* Checklist by Category */}
        <Card data-tour="diligence-checklist" className="p-4">
          <div className="flex items-center gap-2 mb-4">
            <FileSearch className="h-4 w-4 text-primary" />
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
              Verification Checklist
            </h3>
          </div>
          {categories.map((cat) => (
            <div key={cat} className="mb-4 last:mb-0">
              <p className="text-xs font-display text-primary uppercase tracking-wider mb-2 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                {cat}
              </p>
              <div className="space-y-1">
                {data.checks
                  .filter((c) => c.category === cat)
                  .map((check, i) => {
                    const cfg = statusConfig[check.status];
                    const Icon = cfg.icon;
                    return (
                      <motion.div
                        key={check.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.03 }}
                        className={`grid grid-cols-[24px_1fr_80px_1fr_100px] gap-3 items-center px-3 py-2.5 rounded-md ${
                          check.status === "flagged" ? "bg-destructive/10 border border-destructive/20" : "bg-secondary/20"
                        }`}
                      >
                        <Icon className={`h-4 w-4 ${cfg.color}`} />
                        <span className="text-xs text-foreground font-body">{check.item}</span>
                        <Badge className={`text-[9px] px-1.5 py-0 ${cfg.bg} ${cfg.color} border-transparent justify-center`}>
                          {cfg.label}
                        </Badge>
                        <span className="text-xs text-muted-foreground font-body truncate">{check.notes}</span>
                        <span className="text-[10px] text-muted-foreground font-mono-numbers text-right">
                          {check.timestamp || "—"}
                        </span>
                      </motion.div>
                    );
                  })}
              </div>
            </div>
          ))}
        </Card>

        {/* Field Visit Report - Full Width */}
        <Card data-tour="diligence-fieldvisit" className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <MapPin className="h-4 w-4 text-primary" />
            <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
              Field Visit Report
            </h3>
          </div>
          {data.fieldVisits.map((visit, i) => (
            <div key={i} className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-foreground font-body font-medium">{visit.location}</p>
                  <p className="text-xs text-muted-foreground">
                    {visit.date} · Officer: {visit.officer}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={`text-[10px] ${
                    visit.rating === "satisfactory" ? "bg-safe/20 text-safe border-safe/30" :
                    visit.rating === "concerns" ? "bg-warning/20 text-warning border-warning/30" :
                    "bg-destructive/20 text-destructive border-destructive/30"
                  }`}>
                    {visit.rating.toUpperCase()}
                  </Badge>
                  <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                    <Camera className="h-3 w-3" /> {visit.photoCount}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
                {visit.observations.map((obs, j) => (
                  <motion.div
                    key={j}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: j * 0.06 }}
                    className="flex items-start gap-2 text-xs text-muted-foreground"
                  >
                    <Eye className="h-3 w-3 mt-0.5 shrink-0 text-primary" />
                    <span>{obs}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          ))}
        </Card>

        {/* Link to Audit Trail for Compliance */}
        <Card
          className="p-4 cursor-pointer hover:border-primary/50 transition-colors group"
          onClick={() => navigate("/audit")}
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">Regulatory Compliance</h3>
              <p className="text-xs text-muted-foreground mt-1">
                View compliance status, regulatory checks & audit trail
              </p>
            </div>
            <div className="flex items-center gap-2 text-primary group-hover:translate-x-1 transition-transform">
              <span className="text-xs font-display">View in Audit Trail</span>
              <ArrowRight className="h-4 w-4" />
            </div>
          </div>
        </Card>
      </div>
    </ScrollArea>
  );
};

export default DueDiligence;
