import { useMemo } from "react";
import { useAppStore, useActiveBudget, useMonthExpenses } from "@/store/useAppStore";
import { computeStats } from "@/engine/predictionEngine";
import { generateInsights } from "@/engine/insightEngine";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { LucideIcon, AlertTriangle, CheckCircle2, Lightbulb, Sparkles } from "lucide-react";

const TONE: Record<string, { wrap: string; icon: LucideIcon; iconBg: string }> = {
  warning: { wrap: "from-destructive/10 via-warning/5 to-transparent border-destructive/30", icon: AlertTriangle, iconBg: "bg-destructive text-destructive-foreground" },
  success: { wrap: "from-success/10 via-accent/5 to-transparent border-success/30", icon: CheckCircle2, iconBg: "bg-success text-success-foreground" },
  tip: { wrap: "from-primary/10 via-primary-glow/5 to-transparent border-primary/30", icon: Lightbulb, iconBg: "bg-gradient-primary text-primary-foreground" },
  prediction: { wrap: "from-accent/10 via-primary/5 to-transparent border-accent/30", icon: Sparkles, iconBg: "bg-gradient-accent text-accent-foreground" },
};

const SECTIONS: { key: "warning" | "success" | "tip" | "prediction"; title: string; emoji: string }[] = [
  { key: "warning", title: "Warnings", emoji: "⚠️" },
  { key: "prediction", title: "Predictions", emoji: "🔮" },
  { key: "tip", title: "Tips", emoji: "💡" },
  { key: "success", title: "Wins", emoji: "✅" },
];

export default function Insights() {
  const budget = useActiveBudget();
  const expenses = useMonthExpenses();
  const hourlyWage = useAppStore((s) => s.hourlyWage);
  const allExpenses = useAppStore((s) => s.expenses);
  const activeMonth = useAppStore((s) => s.activeMonth);

  const insights = useMemo(() => {
    const stats = computeStats(budget, expenses);
    const [y, m] = activeMonth.split("-").map(Number);
    const d = new Date(y, m - 2, 1);
    const prevMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    const prev = allExpenses.filter((e) => e.month === prevMonth);
    return generateInsights(stats, expenses, hourlyWage, prev);
  }, [budget, expenses, hourlyWage, allExpenses, activeMonth]);

  return (
    <div className="space-y-8 animate-fade-in">
      {SECTIONS.map((sec) => {
        const items = insights.filter((i) => i.type === sec.key);
        if (items.length === 0) return null;
        const Tone = TONE[sec.key];
        return (
          <section key={sec.key} className="space-y-3">
            <h2 className="font-display text-lg font-bold flex items-center gap-2">
              <span>{sec.emoji}</span> {sec.title}
              <span className="text-xs font-medium text-muted-foreground bg-muted rounded-full px-2 py-0.5">{items.length}</span>
            </h2>
            <div className="grid gap-3 md:grid-cols-2">
              {items.map((i, idx) => {
                const Icon = Tone.icon;
                return (
                  <motion.div
                    key={i.id}
                    initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.04 }}
                    className={`relative rounded-2xl border bg-gradient-to-br ${Tone.wrap} p-5 backdrop-blur-sm`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${Tone.iconBg} shadow-md-soft`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-sm">{i.title}</div>
                        <div className="text-sm text-muted-foreground mt-1 leading-relaxed">{i.message}</div>
                        {i.actionLabel && i.actionHref && (
                          <Link to={i.actionHref}>
                            <Button size="sm" variant="outline" className="mt-3 rounded-lg">{i.actionLabel}</Button>
                          </Link>
                        )}
                      </div>
                      {i.severity === 3 && <span className="text-[10px] font-bold uppercase tracking-wider text-destructive bg-destructive/10 px-2 py-0.5 rounded-full">Critical</span>}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </section>
        );
      })}

      {insights.length === 0 && (
        <div className="glass-card p-12 text-center">
          <div className="text-5xl mb-3">🧠</div>
          <h3 className="font-display text-lg font-bold mb-1">Add some expenses</h3>
          <p className="text-sm text-muted-foreground mb-4">We'll generate smart insights as soon as you log a few transactions.</p>
          <Link to="/tracker"><Button className="bg-gradient-primary shadow-glow">Go to tracker</Button></Link>
        </div>
      )}
    </div>
  );
}
