import { motion } from "framer-motion";

interface Props { value: number; label?: string; size?: number; }

export function VelocityRing({ value, label = "of budget used", size = 180 }: Props) {
  const v = Math.min(150, Math.max(0, value));
  const r = (size - 24) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.min(100, v) / 100) * c;
  const color = v >= 100 ? "hsl(var(--destructive))" : v >= 80 ? "hsl(var(--warning))" : "hsl(var(--primary))";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="hsl(var(--primary))" />
            <stop offset="100%" stopColor="hsl(var(--primary-glow))" />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} stroke="hsl(var(--muted))" strokeWidth={12} fill="none" />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r}
          stroke={v >= 80 ? color : "url(#ringGrad)"}
          strokeWidth={12} fill="none" strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="font-display text-3xl font-bold gradient-text">{v.toFixed(0)}%</div>
        <div className="text-xs text-muted-foreground mt-1 max-w-[100px] text-center leading-tight">{label}</div>
      </div>
    </div>
  );
}
