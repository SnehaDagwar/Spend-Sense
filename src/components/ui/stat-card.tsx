import { motion } from "framer-motion";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Props {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  icon?: ReactNode;
  accent?: "primary" | "success" | "warm" | "accent";
  delay?: number;
}

const accents: Record<string, string> = {
  primary: "bg-gradient-primary",
  success: "bg-gradient-success",
  warm: "bg-gradient-warm",
  accent: "bg-gradient-accent",
};

export function StatCard({ label, value, sub, icon, accent = "primary", delay = 0 }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="stat-card"
    >
      <div className={cn("absolute inset-x-0 top-0 h-1", accents[accent])} />
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</div>
          <div className="mt-2 font-display text-2xl md:text-3xl font-bold leading-none">{value}</div>
          {sub && <div className="mt-2 text-xs text-muted-foreground">{sub}</div>}
        </div>
        {icon && (
          <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white shadow-md-soft", accents[accent])}>
            {icon}
          </div>
        )}
      </div>
    </motion.div>
  );
}
