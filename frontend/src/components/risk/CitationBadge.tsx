import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface CitationBadgeProps {
  document: string;
  page: number;
  method: string;
  confidence: number;
}

export function CitationBadge({ document, page, method, confidence }: CitationBadgeProps) {
  return (
    <Tooltip delayDuration={100}>
      <TooltipTrigger asChild>
        <sup className="text-[9px] font-display text-primary cursor-help ml-0.5 hover:text-primary/80 transition-colors">
          [src]
        </sup>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-[220px] p-3 space-y-1.5">
        <div className="space-y-1">
          <div className="flex justify-between text-[10px]">
            <span className="text-muted-foreground">Document:</span>
            <span className="text-foreground font-medium">{document}</span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-muted-foreground">Page:</span>
            <span className="text-foreground font-mono-numbers">{page}</span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-muted-foreground">Method:</span>
            <span className="text-foreground">{method}</span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-muted-foreground">Confidence:</span>
            <span className="text-safe font-mono-numbers font-bold">{confidence}%</span>
          </div>
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
