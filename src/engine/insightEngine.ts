import type { InsightMessage, Expense } from "@/types";
import type { MonthStats } from "./predictionEngine";
import { formatINR, formatPercent } from "@/utils/formatters";
import { uid } from "@/utils/storage";

export const generateInsights = (
  stats: MonthStats,
  expenses: Expense[],
  hourlyWage: number,
  prevMonthExpenses: Expense[] = []
): InsightMessage[] => {
  const out: InsightMessage[] = [];

  // Per-category rules
  stats.byCategory.forEach((c) => {
    if (c.planned === 0) return;
    if (c.percentUsed >= 100) {
      out.push({
        id: uid(), type: "warning", severity: 3,
        categoryId: c.categoryId, category: c.name,
        title: `${c.icon} ${c.name} budget exceeded`,
        message: `You've hit ${formatPercent(c.percentUsed)} of your ${c.name} budget — ${formatINR(c.actual - c.planned)} over plan.`,
        actionLabel: "Adjust budget", actionHref: "/budget",
      });
    } else if (c.percentUsed >= 80) {
      out.push({
        id: uid(), type: "warning", severity: 2,
        categoryId: c.categoryId, category: c.name,
        title: `${c.icon} ${c.name} at ${formatPercent(c.percentUsed)}`,
        message: `Only ${formatINR(c.remaining)} left for the rest of the month.`,
      });
    } else if (c.percentUsed <= 25 && stats.daysElapsed > stats.totalDays * 0.5) {
      out.push({
        id: uid(), type: "success", severity: 1,
        categoryId: c.categoryId, category: c.name,
        title: `${c.icon} Great control on ${c.name}`,
        message: `You're well under budget — keep it up and you'll save ${formatINR(c.remaining)}.`,
      });
    }

    // Velocity warning
    if (c.projectedEOM > c.planned && c.percentUsed < 100 && c.percentUsed > 30) {
      out.push({
        id: uid(), type: "prediction", severity: 2,
        categoryId: c.categoryId, category: c.name,
        title: `📈 ${c.name} on track to overspend`,
        message: `At this rate, ${c.name} will end at ${formatINR(c.projectedEOM)} — ${formatINR(c.projectedEOM - c.planned)} over budget.`,
      });
    }

    // Safe-to-spend tip
    if (c.safeDaily > 0 && c.percentUsed < 80 && stats.daysRemaining > 0) {
      out.push({
        id: uid(), type: "tip", severity: 1,
        categoryId: c.categoryId, category: c.name,
        title: `💰 Safe to spend on ${c.name}`,
        message: `You can safely spend ${formatINR(c.safeDaily)}/day on ${c.name} for the rest of the month.`,
      });
    }
  });

  // Subscription detection (same amount across months)
  const prevAmounts = new Map<string, number[]>();
  prevMonthExpenses.forEach((e) => {
    const key = `${e.categoryId}:${e.amount}`;
    prevAmounts.set(key, [...(prevAmounts.get(key) ?? []), e.amount]);
  });
  expenses.forEach((e) => {
    const key = `${e.categoryId}:${e.amount}`;
    if (prevAmounts.has(key)) {
      out.push({
        id: uid(), type: "tip", severity: 2,
        categoryId: e.categoryId,
        title: `👻 Recurring charge detected`,
        message: `${formatINR(e.amount)} appears as a recurring charge — likely a subscription.`,
      });
    }
  });

  // Time to earn
  if (stats.totalActual > 0 && hourlyWage > 0) {
    const hours = stats.totalActual / hourlyWage;
    out.push({
      id: uid(), type: "tip", severity: 1,
      title: `⏰ Time to earn`,
      message: `Your spending this month equals ${hours.toFixed(1)} hours of work at ${formatINR(hourlyWage)}/hr.`,
    });
  }

  // EOM prediction
  if (stats.daysElapsed >= 3) {
    const ratio = stats.income > 0 ? (stats.projectedTotal / stats.income) * 100 : 0;
    out.push({
      id: uid(), type: "prediction", severity: stats.projectedTotal > stats.totalPlanned ? 3 : 1,
      title: `🔮 Month-end projection`,
      message: `Projected total: ${formatINR(stats.projectedTotal)} (${formatPercent(ratio)} of income). Expected savings: ${formatINR(stats.projectedSavings)}.`,
    });
  }

  // Saving goal suggestion — find biggest non-fixed category
  const top = [...stats.byCategory].filter((c) => c.actual > 0).sort((a, b) => b.actual - a.actual)[0];
  if (top) {
    const save = top.actual * 0.3;
    out.push({
      id: uid(), type: "tip", severity: 1,
      categoryId: top.categoryId, category: top.name,
      title: `💡 Quick win`,
      message: `Reducing ${top.name} by 30% would save you ${formatINR(save)} this month.`,
    });
  }

  return out.sort((a, b) => b.severity - a.severity);
};
