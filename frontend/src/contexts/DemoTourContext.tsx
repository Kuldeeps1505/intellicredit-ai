import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from "react";
import {
  LayoutDashboard,
  Upload,
  Activity,
  BarChart3,
  Table2,
  Landmark,
  Users,
  FileEdit,
  FileText,
  ClipboardList,
  LucideIcon,
} from "lucide-react";

export interface TourHighlight {
  label: string;
  selector?: string; // CSS selector to scroll to & flash
}

export interface TourStep {
  route: string;
  title: string;
  description: string;
  icon: LucideIcon;
  highlights: TourHighlight[];
  tip?: string;
}

export const tourSteps: TourStep[] = [
  {
    route: "/",
    title: "Dashboard Overview",
    description: "Your command center — view credit risk scores, application status, and key metrics at a glance.",
    icon: LayoutDashboard,
    highlights: [
      { label: "Risk score gauge", selector: "[data-tour='risk-score']" },
      { label: "Financial health strip", selector: "[data-tour='financial-health']" },
      { label: "Analysis modules", selector: "[data-tour='modules']" },
    ],
  },
  {
    route: "/upload",
    title: "Document Upload",
    description: "Upload financial documents, bank statements, and KYC files. Our AI agents will auto-extract and analyze them.",
    icon: Upload,
    highlights: [
      { label: "Application form", selector: "[data-tour='upload-form']" },
      { label: "Data source toggle", selector: "[data-tour='upload-source']" },
      { label: "Upload area", selector: "[data-tour='upload-area']" },
    ],
  },
  {
    route: "/agents",
    title: "Agent Progress",
    description: "Track AI agents in real-time as they process documents, run checks, and generate insights.",
    icon: Activity,
    highlights: [
      { label: "Pipeline progress", selector: "[data-tour='agent-progress']" },
      { label: "Agent pipeline", selector: "[data-tour='agent-pipeline']" },
      { label: "Live log stream", selector: "[data-tour='agent-logs']" },
    ],
  },
  {
    route: "/risk",
    title: "Risk Analytics",
    description: "Deep-dive into risk scores with interactive gauges, factor breakdowns, and trend analysis.",
    icon: BarChart3,
    highlights: [
      { label: "Risk gauge", selector: "[data-tour='risk-gauge']" },
      { label: "Five-Cs radar", selector: "[data-tour='risk-radar']" },
      { label: "GSTR reconciliation", selector: "[data-tour='risk-gstr']" },
      { label: "Buyer concentration", selector: "[data-tour='risk-buyer']" },
      { label: "Risk flags", selector: "[data-tour='risk-flags']" },
    ],
  },
  {
    route: "/spreads",
    title: "Financial Spreads",
    description: "Auto-generated financial spreads from uploaded statements — ratios, trends, and comparisons.",
    icon: Table2,
    highlights: [
      { label: "Financial statements", selector: "[data-tour='spreads-statements']" },
      { label: "Key ratio trends", selector: "[data-tour='spreads-ratios']" },
    ],
  },
  {
    route: "/bank-analytics",
    title: "Bank Statement Analytics",
    description: "Analyze cash flows, inflows/outflows, and banking patterns with visual breakdowns.",
    icon: Landmark,
    highlights: [
      { label: "Summary cards", selector: "[data-tour='bank-summary']" },
      { label: "Cash flow charts", selector: "[data-tour='bank-cashflow']" },
      { label: "Transaction categories", selector: "[data-tour='bank-categories']" },
      { label: "Red flag detection", selector: "[data-tour='bank-redflags']" },
    ],
  },
  {
    route: "/promoter",
    title: "Promoter Intelligence",
    description: "Background checks, CIBIL scores, litigation history, and director network mapping.",
    icon: Users,
    highlights: [
      { label: "MCA / regulatory flags", selector: "[data-tour='promoter-mca']" },
      { label: "Directors & CIBIL", selector: "[data-tour='promoter-directors']" },
      { label: "Entity network map", selector: "[data-tour='promoter-network']" },
    ],
  },
  {
    route: "/diligence",
    title: "Due Diligence",
    description: "Comprehensive due diligence reports — GST compliance, MCA filings, and regulatory checks.",
    icon: FileEdit,
    highlights: [
      { label: "Completion stats", selector: "[data-tour='diligence-stats']" },
      { label: "Verification checklist", selector: "[data-tour='diligence-checklist']" },
      { label: "Field visit report", selector: "[data-tour='diligence-fieldvisit']" },
    ],
  },
  {
    route: "/report",
    title: "CAM Report",
    description: "Auto-generated Credit Appraisal Memo ready for committee review and PDF export.",
    icon: FileText,
    highlights: [
      { label: "Key metrics", selector: "[data-tour='cam-metrics']" },
      { label: "Report sections", selector: "[data-tour='cam-sections']" },
      { label: "Recommendation", selector: "[data-tour='cam-recommendation']" },
      { label: "What-if simulator", selector: "[data-tour='cam-simulator']" },
    ],
  },
  {
    route: "/audit",
    title: "Audit Trail",
    description: "Complete audit log of every action, decision, and data point — full transparency.",
    icon: ClipboardList,
    highlights: [
      { label: "Approval workflow", selector: "[data-tour='audit-workflow']" },
      { label: "Human overrides", selector: "[data-tour='audit-overrides']" },
      { label: "Decision timeline", selector: "[data-tour='audit-timeline']" },
    ],
  },
];

const AUTO_PLAY_INTERVAL = 2500;
const NO_HIGHLIGHT_INTERVAL = 10000; // 10s per page when highlights disabled
interface DemoTourContextType {
  isActive: boolean;
  currentStep: number;
  activeHighlightIndex: number; // -1 = none, 0+ = cycling through highlights
  totalSteps: number;
  step: TourStep | null;
  isAutoPlaying: boolean;
  highlightsEnabled: boolean;
  startTour: () => void;
  endTour: () => void;
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (n: number) => void;
  toggleAutoPlay: () => void;
  toggleHighlights: () => void;
}

const DemoTourContext = createContext<DemoTourContextType | null>(null);

export function DemoTourProvider({ children }: { children: React.ReactNode }) {
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const [activeHighlightIndex, setActiveHighlightIndex] = useState(-1);
  const [highlightsEnabled, setHighlightsEnabled] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Use refs for sub-step state to avoid stale closures
  const subStepRef = useRef(-1);
  const currentStepRef = useRef(0);
  const highlightsEnabledRef = useRef(true);

  // Keep refs in sync
  useEffect(() => { currentStepRef.current = currentStep; }, [currentStep]);
  useEffect(() => { highlightsEnabledRef.current = highlightsEnabled; }, [highlightsEnabled]);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const clearBlur = useCallback(() => {
    document.querySelectorAll(".tour-highlight-flash").forEach(el => el.classList.remove("tour-highlight-flash"));
  }, []);

  const scrollToHighlight = useCallback((stepIdx: number, highlightIdx: number) => {
    const step = tourSteps[stepIdx];
    if (!step) return;
    const h = step.highlights[highlightIdx];
    if (h?.selector) {
      setTimeout(() => {
        // Clear any previous highlight first
        document.querySelectorAll(".tour-highlight-flash").forEach(el => el.classList.remove("tour-highlight-flash"));
        const el = document.querySelector(h.selector!);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
          el.classList.add("tour-highlight-flash");
          setTimeout(() => {
            el.classList.remove("tour-highlight-flash");
          }, 2000);
        }
      }, 300);
    }
  }, []);

  const startAutoPlay = useCallback(() => {
    clearTimer();
    subStepRef.current = -1;
    setActiveHighlightIndex(-1);

    const tick = () => {
      const stepIdx = currentStepRef.current;
      const step = tourSteps[stepIdx];
      const selectableHighlights = step?.highlights.filter(h => h.selector) ?? [];
      const maxSub = selectableHighlights.length;

      if (highlightsEnabledRef.current && maxSub > 0 && subStepRef.current < maxSub - 1) {
        // Advance to next highlight within this step
        subStepRef.current += 1;
        setActiveHighlightIndex(subStepRef.current);
        const selectableIdx = subStepRef.current;
        let realIdx = -1;
        let count = -1;
        for (let i = 0; i < step.highlights.length; i++) {
          if (step.highlights[i].selector) {
            count++;
            if (count === selectableIdx) { realIdx = i; break; }
          }
        }
        if (realIdx >= 0) scrollToHighlight(stepIdx, realIdx);
        // Schedule next tick at highlight interval
        timerRef.current = setTimeout(tick, AUTO_PLAY_INTERVAL);
      } else {
        // Move to next step
        subStepRef.current = -1;
        setActiveHighlightIndex(-1);
        clearBlur();
        if (stepIdx >= tourSteps.length - 1) {
          setIsAutoPlaying(false);
          setIsActive(false);
          setCurrentStep(0);
        } else {
          setCurrentStep(stepIdx + 1);
          // Schedule next tick — use longer interval if highlights are off
          const nextDelay = highlightsEnabledRef.current ? AUTO_PLAY_INTERVAL : NO_HIGHLIGHT_INTERVAL;
          timerRef.current = setTimeout(tick, nextDelay);
        }
      }
    };

    // Initial delay before first tick
    const initialDelay = highlightsEnabledRef.current ? AUTO_PLAY_INTERVAL : NO_HIGHLIGHT_INTERVAL;
    timerRef.current = setTimeout(tick, initialDelay);
  }, [clearTimer, scrollToHighlight, clearBlur]);

  useEffect(() => {
    if (isAutoPlaying && isActive) {
      startAutoPlay();
    } else {
      clearTimer();
      subStepRef.current = -1;
      setActiveHighlightIndex(-1);
    }
    return clearTimer;
  }, [isAutoPlaying, isActive, startAutoPlay, clearTimer]);

  const resetAutoPlayTimer = useCallback(() => {
    if (isAutoPlaying) {
      subStepRef.current = -1;
      setActiveHighlightIndex(-1);
      startAutoPlay();
    }
  }, [isAutoPlaying, startAutoPlay]);

  const startTour = useCallback(() => {
    setCurrentStep(0);
    setIsActive(true);
    setIsAutoPlaying(false);
    setActiveHighlightIndex(-1);
  }, []);

  const endTour = useCallback(() => {
    setIsActive(false);
    setCurrentStep(0);
    setIsAutoPlaying(false);
    setActiveHighlightIndex(-1);
    clearTimer();
    clearBlur();
  }, [clearTimer, clearBlur]);

  const nextStep = useCallback(() => {
    clearBlur();
    setCurrentStep((prev) => {
      if (prev >= tourSteps.length - 1) {
        setIsActive(false);
        setIsAutoPlaying(false);
        return 0;
      }
      return prev + 1;
    });
    resetAutoPlayTimer();
  }, [resetAutoPlayTimer, clearBlur]);

  const prevStep = useCallback(() => {
    clearBlur();
    setCurrentStep((prev) => Math.max(0, prev - 1));
    resetAutoPlayTimer();
  }, [resetAutoPlayTimer, clearBlur]);

  const goToStep = useCallback((n: number) => {
    if (n >= 0 && n < tourSteps.length) {
      clearBlur();
      setCurrentStep(n);
      resetAutoPlayTimer();
    }
  }, [resetAutoPlayTimer, clearBlur]);

  const toggleAutoPlay = useCallback(() => {
    setIsAutoPlaying((prev) => !prev);
  }, []);

  const toggleHighlights = useCallback(() => {
    setHighlightsEnabled((prev) => {
      if (prev) {
        // Turning off — clear any active highlights
        clearBlur();
        setActiveHighlightIndex(-1);
        subStepRef.current = -1;
      }
      return !prev;
    });
  }, [clearBlur]);

  return (
    <DemoTourContext.Provider
      value={{
        isActive,
        currentStep,
        activeHighlightIndex: highlightsEnabled ? activeHighlightIndex : -1,
        totalSteps: tourSteps.length,
        step: isActive ? tourSteps[currentStep] : null,
        isAutoPlaying,
        highlightsEnabled,
        startTour,
        endTour,
        nextStep,
        prevStep,
        goToStep,
        toggleAutoPlay,
        toggleHighlights,
      }}
    >
      {children}
    </DemoTourContext.Provider>
  );
}

export function useDemoTour() {
  const ctx = useContext(DemoTourContext);
  if (!ctx) throw new Error("useDemoTour must be used within DemoTourProvider");
  return ctx;
}
