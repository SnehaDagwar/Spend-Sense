import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, X, Lightbulb, TrendingUp, AlertTriangle } from "lucide-react";
import { useAppStore, useActiveBudget, useMonthExpenses } from "@/store/useAppStore";
import { computeStats } from "@/engine/predictionEngine";
import { generateInsights } from "@/engine/insightEngine";
import { Button } from "@/components/ui/button";

export function AIInsightWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const budget = useActiveBudget();
  const expenses = useMonthExpenses();
  const hourlyWage = useAppStore((s) => s.hourlyWage);
  const allExpenses = useAppStore((s) => s.expenses);
  const activeMonth = useAppStore((s) => s.activeMonth);

  const stats = useMemo(() => computeStats(budget, expenses), [budget, expenses]);
  const insights = useMemo(() => {
    const prevMonth = (() => {
      const [y, m] = activeMonth.split("-").map(Number);
      const d = new Date(y, m - 2, 1);
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    })();
    const prev = allExpenses.filter((e) => e.month === prevMonth);
    return generateInsights(stats, expenses, hourlyWage, prev);
  }, [stats, expenses, hourlyWage, allExpenses, activeMonth]);

  const randomInsight = useMemo(() => {
    if (insights.length === 0) return null;
    return insights[Math.floor(Math.random() * insights.length)];
  }, [insights]);

  const iconMap: Record<string, React.ReactNode> = {
    warning: <AlertTriangle className="h-5 w-5 text-warning" />,
    success: <TrendingUp className="h-5 w-5 text-success" />,
    tip: <Lightbulb className="h-5 w-5 text-primary" />,
    prediction: <Sparkles className="h-5 w-5 text-accent" />,
  };

  return (
    <>
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-gradient-primary shadow-glow flex items-center justify-center z-50 text-white"
      >
        <Sparkles className="h-6 w-6" />
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-[60] flex items-end justify-center p-4 sm:items-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="absolute inset-0 bg-background/60 backdrop-blur-sm"
            />
            
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="relative w-full max-w-md glass-card p-6 shadow-glow"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Sparkles className="h-4 w-4 text-primary" />
                  </div>
                  <h3 className="font-display font-bold">Smart Insight</h3>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setIsOpen(false)} className="rounded-full">
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {randomInsight ? (
                <div className="space-y-4">
                  <div className="flex items-start gap-3 p-4 rounded-2xl bg-muted/40 border border-border/40">
                    <div className="mt-0.5">{iconMap[randomInsight.type]}</div>
                    <div>
                      <div className="font-semibold text-sm">{randomInsight.title}</div>
                      <div className="text-sm text-muted-foreground mt-1 leading-relaxed">
                        {randomInsight.message}
                      </div>
                    </div>
                  </div>
                  <Button 
                    className="w-full rounded-xl bg-gradient-primary shadow-glow"
                    onClick={() => setIsOpen(false)}
                  >
                    Got it, thanks!
                  </Button>
                </div>
              ) : (
                <div className="py-8 text-center">
                  <div className="text-sm text-muted-foreground">
                    Log more expenses to unlock personalized AI insights.
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
