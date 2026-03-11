import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface RiskGaugeProps {
  score: number;
  category: string;
  defaultProb12m: number;
  defaultProb24m: number;
}

export function RiskGauge({ score, category, defaultProb12m, defaultProb24m }: RiskGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    setAnimatedScore(0);
    const timeout = setTimeout(() => setAnimatedScore(score), 100);
    return () => clearTimeout(timeout);
  }, [score]);

  // Arc goes from -135deg to +135deg (270 degree sweep)
  const sweepAngle = 270;
  const startAngle = -135;
  const radius = 80;
  const cx = 100;
  const cy = 100;

  const polarToCartesian = (angle: number) => {
    const rad = (angle * Math.PI) / 180;
    return { x: cx + radius * Math.cos(rad), y: cy + radius * Math.sin(rad) };
  };

  const createArc = (startA: number, endA: number) => {
    const start = polarToCartesian(startA - 90);
    const end = polarToCartesian(endA - 90);
    const largeArc = endA - startA > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y}`;
  };

  // Color zones: 0-30 red, 31-60 amber, 61-80 green, 81-100 dark green
  const getScoreColor = () => {
    if (score <= 30) return "hsl(var(--destructive))";
    if (score <= 60) return "hsl(var(--warning))";
    if (score <= 80) return "hsl(var(--safe))";
    return "hsl(var(--safe))";
  };

  const needleAngle = startAngle + (animatedScore / 100) * sweepAngle;

  // Zone arcs
  const zones = [
    { start: 0, end: 30, color: "hsl(var(--destructive) / 0.3)" },
    { start: 30, end: 60, color: "hsl(var(--warning) / 0.3)" },
    { start: 60, end: 80, color: "hsl(var(--safe) / 0.2)" },
    { start: 80, end: 100, color: "hsl(var(--safe) / 0.35)" },
  ];

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 140" className="w-full max-w-[240px]">
        {/* Background arc */}
        <path
          d={createArc(startAngle, startAngle + sweepAngle)}
          fill="none"
          stroke="hsl(var(--border))"
          strokeWidth="12"
          strokeLinecap="round"
        />

        {/* Zone arcs */}
        {zones.map((zone, i) => {
          const zoneStart = startAngle + (zone.start / 100) * sweepAngle;
          const zoneEnd = startAngle + (zone.end / 100) * sweepAngle;
          return (
            <path
              key={i}
              d={createArc(zoneStart, zoneEnd)}
              fill="none"
              stroke={zone.color}
              strokeWidth="12"
              strokeLinecap="butt"
            />
          );
        })}

        {/* Active arc */}
        <motion.path
          d={createArc(startAngle, startAngle + (animatedScore / 100) * sweepAngle)}
          fill="none"
          stroke={getScoreColor()}
          strokeWidth="12"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1, ease: "easeOut" }}
        />

        {/* Needle */}
        <motion.line
          x1={cx}
          y1={cy}
          x2={cx}
          y2={cy - radius + 15}
          stroke={getScoreColor()}
          strokeWidth="2.5"
          strokeLinecap="round"
          style={{ transformOrigin: `${cx}px ${cy}px` }}
          animate={{ rotate: needleAngle + 90 }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
        <circle cx={cx} cy={cy} r="4" fill={getScoreColor()} />
      </svg>

      {/* Score display */}
      <div className="text-center -mt-2">
        <motion.span
          className="text-4xl font-mono-numbers font-bold"
          style={{ color: getScoreColor() }}
          key={score}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {animatedScore}
        </motion.span>
        <span className="text-lg text-muted-foreground font-mono-numbers">/100</span>
      </div>

      <motion.div
        key={category}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="mt-1 px-3 py-1 rounded-full text-xs font-display font-bold uppercase tracking-wider"
        style={{
          backgroundColor: `${getScoreColor()}20`,
          color: getScoreColor(),
          border: `1px solid ${getScoreColor()}40`,
        }}
      >
        {category} RISK
      </motion.div>

      <div className="mt-3 text-center space-y-0.5">
        <p className="text-[10px] text-muted-foreground font-mono-numbers">
          Default Prob 12m: <span className="text-foreground">{defaultProb12m}%</span>
        </p>
        <p className="text-[10px] text-muted-foreground font-mono-numbers">
          Default Prob 24m: <span className="text-foreground">{defaultProb24m}%</span>
        </p>
      </div>
    </div>
  );
}
