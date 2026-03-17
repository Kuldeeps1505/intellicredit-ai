import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useDemoTour } from "@/contexts/DemoTourContext";
import { ChevronLeft, ChevronRight, X, Pause, Play, Crosshair, CrosshairIcon } from "lucide-react";

import { tourSteps } from "@/contexts/DemoTourContext";

const AUTO_PLAY_TICK = 2.5; // seconds per sub-step, must match context

export function DemoTourOverlay() {
  const {
    isActive, currentStep, totalSteps, step,
    nextStep, prevStep, endTour, goToStep,
    isAutoPlaying, toggleAutoPlay, activeHighlightIndex,
    highlightsEnabled, toggleHighlights,
  } = useDemoTour();
  const navigate = useNavigate();

  useEffect(() => {
    if (isActive && step) {
      navigate(step.route);
      // Scroll to top of page so user sees the heading first
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [isActive, step, navigate]);

  useEffect(() => {
    if (!isActive) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") endTour();
      if (e.key === "ArrowRight") nextStep();
      if (e.key === "ArrowLeft") prevStep();
      if (e.key === " ") { e.preventDefault(); toggleAutoPlay(); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isActive, endTour, nextStep, prevStep, toggleAutoPlay]);

  return (
    <AnimatePresence>
      {isActive && step && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="fixed inset-0 z-[100] pointer-events-none"
        >
          <motion.div
            drag
            dragMomentum={false}
            initial={{ opacity: 0, y: 40, scale: 0.95 }}
            animate={{ opacity: isAutoPlaying ? 0.4 : 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 40, scale: 0.95 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="pointer-events-auto absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-lg cursor-grab active:cursor-grabbing hover:!opacity-100"
          >
            <motion.div
              key={currentStep}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.25 }}
              className="mx-4 rounded-2xl border border-border bg-card shadow-2xl overflow-hidden"
            >
              {/* Progress bar */}
              <div className="h-1 bg-muted">
                <motion.div
                  className="h-full bg-primary"
                  initial={{ width: 0 }}
                  animate={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                />
              </div>

              <div className="p-5">
                {/* Header */}
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-3">
                    {/* Page-specific icon with auto-play ring */}
                    <div className="relative h-10 w-10 shrink-0">
                      <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                        <step.icon className="h-4 w-4 text-primary" />
                      </div>
                      {isAutoPlaying && step && (() => {
                        const selectableCount = step.highlights.filter(h => h.selector).length;
                        const totalTicks = selectableCount + 1; // highlights + 1 for page transition
                        const ringDuration = totalTicks * AUTO_PLAY_TICK;
                        return (
                          <svg className="absolute inset-0 h-10 w-10 -rotate-90" viewBox="0 0 40 40">
                            <motion.circle
                              cx="20" cy="20" r="18"
                              fill="none"
                              stroke="hsl(var(--primary))"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeDasharray={Math.PI * 36}
                              key={`ring-${currentStep}`}
                              initial={{ strokeDashoffset: 0 }}
                              animate={{ strokeDashoffset: Math.PI * 36 }}
                              transition={{ duration: ringDuration, ease: "linear" }}
                            />
                          </svg>
                        );
                      })()}
                    </div>
                    <div>
                      <p className="text-[11px] font-mono text-muted-foreground uppercase tracking-wider">
                        Step {currentStep + 1} of {totalSteps}
                      </p>
                      <h3 className="font-semibold text-lg text-foreground leading-tight">
                        {step.title}
                      </h3>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={toggleHighlights}
                      className={`h-8 w-8 rounded-lg flex items-center justify-center transition-colors ${
                        highlightsEnabled
                          ? "text-primary bg-primary/10 hover:bg-primary/20"
                          : "text-muted-foreground hover:text-foreground hover:bg-muted"
                      }`}
                      title={highlightsEnabled ? "Disable highlights" : "Enable highlights"}
                    >
                      <Crosshair className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={endTour}
                      className="h-8 w-8 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                      title="Exit tour"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Description */}
                <p className="text-sm text-muted-foreground leading-relaxed mb-3">
                  {step.description}
                </p>

                {/* Feature highlight chips */}
                {highlightsEnabled && step.highlights.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {step.highlights.map((h, idx) => {
                      // Track selectable index for matching activeHighlightIndex
                      const selectableHighlights = step.highlights.filter(x => x.selector);
                      const selectableIdx = h.selector ? selectableHighlights.indexOf(h) : -1;
                      const isActiveChip = isAutoPlaying && selectableIdx === activeHighlightIndex;

                      return (
                        <button
                          key={h.label}
                          onPointerDown={(e) => e.stopPropagation()}
                          onClick={() => {
                            if (h.selector) {
                              document.querySelectorAll(".tour-highlight-flash").forEach(e => e.classList.remove("tour-highlight-flash"));
                              const el = document.querySelector(h.selector);
                              if (el) {
                                el.scrollIntoView({ behavior: "smooth", block: "center" });
                                el.classList.add("tour-highlight-flash");
                                setTimeout(() => {
                                  el.classList.remove("tour-highlight-flash");
                                }, 2000);
                              }
                            }
                          }}
                          className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-300 ${
                            isActiveChip
                              ? "bg-primary text-primary-foreground ring-2 ring-primary/50 scale-105"
                              : h.selector
                                ? "bg-primary/10 text-primary hover:bg-primary/20 cursor-pointer"
                                : "bg-secondary text-secondary-foreground cursor-default"
                          }`}
                        >
                          {h.label}
                          {h.selector && !isActiveChip && <span className="text-[10px] opacity-60">↗</span>}
                        </button>
                      );
                    })}
                  </div>
                )}


                {/* Step dots */}
                <div className="flex items-center justify-center gap-1.5 mt-1">
                  {Array.from({ length: totalSteps }).map((_, i) => (
                    <div
                      key={i}
                      className={`rounded-full transition-all duration-300 ${
                        i === currentStep
                          ? "w-6 h-1.5 bg-primary"
                          : i < currentStep
                            ? "w-1.5 h-1.5 bg-primary/40"
                            : "w-1.5 h-1.5 bg-muted-foreground/20"
                      }`}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
