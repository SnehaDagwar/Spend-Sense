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
      className="stat-card flex flex-col justify-between"
    >
      {icon && (
        <div className={cn("flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-white shadow-glow mb-4", accents[accent])}>
          {icon}
        </div>
      )}
      <div className="min-w-0">
        <div className="text-sm font-semibold tracking-tight text-foreground/80">{label}</div>
        <div className="mt-1 font-display text-3xl font-bold leading-none">{value}</div>
        {sub && <div className="mt-2 text-xs font-medium text-muted-foreground">{sub}</div>}
      </div>
    </motion.div>
  );
}
