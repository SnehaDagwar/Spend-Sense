import type { Expense, MonthlyBudget } from "@/types";
import { dayOfMonth, daysInMonth } from "@/utils/formatters";

export interface CategoryStat {
  categoryId: string;
  name: string;
  icon: string;
  color: string;
  planned: number;
  actual: number;
  remaining: number;
  percentUsed: number;
  projectedEOM: number;
  safeDaily: number;
}

export interface MonthStats {
  income: number;
  totalPlanned: number;
  totalActual: number;
  totalRemaining: number;
  savings: number;
  savingsRate: number;
  projectedTotal: number;
  projectedSavings: number;
  daysElapsed: number;
  totalDays: number;
  daysRemaining: number;
  byCategory: CategoryStat[];
  dailyAverage: number;
}

export const computeStats = (budget: MonthlyBudget, expenses: Expense[]): MonthStats => {
  const totalDays = daysInMonth(budget.month);
  const elapsed = Math.max(1, dayOfMonth(budget.month));
  const remainingDays = Math.max(0, totalDays - elapsed);

  const byCategory: CategoryStat[] = budget.categories.map((c) => {
    const items = expenses.filter((e) => e.categoryId === c.id);
    const actual = items.reduce((s, e) => s + e.amount, 0);
    const remaining = Math.max(0, c.planned - actual);
    const percentUsed = c.planned > 0 ? (actual / c.planned) * 100 : 0;
    const dailyRate = actual / elapsed;
    const projectedEOM = dailyRate * totalDays;
    const safeDaily = remainingDays > 0 ? remaining / remainingDays : 0;
    return {
      categoryId: c.id, name: c.name, icon: c.icon, color: c.color,
      planned: c.planned, actual, remaining, percentUsed, projectedEOM, safeDaily,
    };
  });

  const totalPlanned = budget.categories.reduce((s, c) => s + c.planned, 0);
  const totalActual = byCategory.reduce((s, c) => s + c.actual, 0);
  const totalRemaining = Math.max(0, totalPlanned - totalActual);
  const savings = budget.income - totalActual;
  const savingsRate = budget.income > 0 ? (savings / budget.income) * 100 : 0;
  const dailyAverage = totalActual / elapsed;
  const projectedTotal = dailyAverage * totalDays;
  const projectedSavings = budget.income - projectedTotal;

  return {
    income: budget.income,
    totalPlanned, totalActual, totalRemaining, savings, savingsRate,
    projectedTotal, projectedSavings,
    daysElapsed: elapsed, totalDays, daysRemaining: remainingDays,
    byCategory, dailyAverage,
  };
};

export const dailyCumulative = (budget: MonthlyBudget, expenses: Expense[]) => {
  const total = daysInMonth(budget.month);
  const elapsed = dayOfMonth(budget.month);
  const arr: { day: number; spent: number; projected: number; income: number }[] = [];
  const dailyTotals = new Array(total + 1).fill(0);
  expenses.forEach((e) => {
    const d = new Date(e.date).getDate();
    if (d >= 1 && d <= total) dailyTotals[d] += e.amount;
  });
  let cum = 0;
  const dailyAvg = elapsed > 0
    ? dailyTotals.slice(1, elapsed + 1).reduce((s, v) => s + v, 0) / elapsed
    : 0;
  for (let d = 1; d <= total; d++) {
    if (d <= elapsed) { cum += dailyTotals[d]; arr.push({ day: d, spent: cum, projected: cum, income: budget.income }); }
    else arr.push({ day: d, spent: NaN, projected: cum + dailyAvg * (d - elapsed), income: budget.income });
  }
  return arr;
};
