import { useActiveBudget, useMonthExpenses } from "@/store/useAppStore";
import { formatINR, formatPercent } from "@/utils/formatters";
import { Progress } from "@/components/ui/progress";
import { Target, TrendingDown, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";
import { CategoryIcon } from "@/components/ui/CategoryIcon";

export function CategoryGoals() {
  const budget = useActiveBudget();
  const expenses = useMonthExpenses();

  const goals = budget.categories.map((cat) => {
    const actual = expenses
      .filter((e) => e.categoryId === cat.id)
      .reduce((sum, e) => sum + e.amount, 0);
    const savingsTarget = cat.planned * 0.1; // Default 10% savings goal
    const currentSavings = cat.planned - actual;
    const progress = Math.min(100, Math.max(0, (currentSavings / (savingsTarget || 1)) * 100));

    return {
      ...cat,
      actual,
      savingsTarget,
      currentSavings,
      progress,
    };
  }).filter(g => g.planned > 0);

  if (goals.length === 0) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Target className="h-5 w-5 text-primary" />
        <h3 className="font-display font-bold">Savings Goals (10% Target)</h3>
      </div>
      
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {goals.map((g, idx) => (
          <motion.div
            key={g.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: idx * 0.05 }}
            className="glass-card p-4 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <CategoryIcon name={g.icon} className="h-4 w-4" />
                <span className="font-semibold text-sm">{g.name}</span>
              </div>
              {g.progress >= 100 ? (
                <CheckCircle2 className="h-4 w-4 text-success" />
              ) : (
                <TrendingDown className="h-4 w-4 text-muted-foreground" />
              )}
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Target: {formatINR(g.savingsTarget, { compact: true })}</span>
                <span className="font-medium">{formatPercent(g.progress)}</span>
              </div>
              <Progress 
                value={g.progress} 
                className="h-1.5"
                // @ts-expect-error inline css var
                style={{ "--progress-foreground": g.progress >= 100 ? "hsl(var(--success))" : "hsl(var(--primary))" }}
              />
              <div className="text-[10px] text-muted-foreground text-right">
                {g.currentSavings > 0 
                  ? `${formatINR(g.currentSavings, { compact: true })} saved so far` 
                  : "Overspent budget"}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
