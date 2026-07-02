import type { Expense, MonthlyBudget } from "@/types";


/**
 * Calculates the current daily logging streak.
 * A day is counted if there is at least one expense logged.
 */
export const calculateLoggingStreak = (expenses: Expense[]) => {
  if (expenses.length === 0) return 0;

  const dates = new Set(expenses.map(e => e.date.split('T')[0]));
  const today = new Date();
  let streak = 0;
  const currentDate = new Date(today);

  // Check if anything logged today or yesterday to continue the streak
  const todayStr = today.toISOString().split('T')[0];
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayStr = yesterday.toISOString().split('T')[0];

  if (!dates.has(todayStr) && !dates.has(yesterdayStr)) {
    return 0;
  }

  // If logged today, start from today, otherwise start from yesterday
  if (!dates.has(todayStr)) {
    currentDate.setDate(currentDate.getDate() - 1);
  }

  while (dates.has(currentDate.toISOString().split('T')[0])) {
    streak++;
    currentDate.setDate(currentDate.getDate() - 1);
  }

  return streak;
};

/**
 * Calculates the "No Unnecessary Spending" streak.
 * Discretionary categories: 'shopping', 'others'.
 */
export const calculateSpendingStreak = (expenses: Expense[], discretionaryIds: string[] = ['shopping', 'others']) => {
  const discretionaryExpenses = expenses.filter(e => discretionaryIds.includes(e.categoryId));
  const discretionaryDates = new Set(discretionaryExpenses.map(e => e.date.split('T')[0]));
  
  const today = new Date();
  let streak = 0;
  const currentDate = new Date(today);

  // If spent unnecessarily today, streak is 0
  const todayStr = today.toISOString().split('T')[0];
  if (discretionaryDates.has(todayStr)) return 0;

  // Walk backwards and count days WITHOUT discretionary spending
  // We stop if we find a day with discretionary spending
  while (true) {
    const dateStr = currentDate.toISOString().split('T')[0];
    if (discretionaryDates.has(dateStr)) break;
    
    // Also check if we've gone back too far or if there are no expenses at all recorded before this?
    // Actually, a "no spending" streak can start from the first day the user started using the app.
    // For simplicity, we'll cap it at 365 days or until the earliest expense.
    streak++;
    currentDate.setDate(currentDate.getDate() - 1);
    if (streak > 365) break; 
  }

  return streak;
};

/**
 * Calculates budget-following streak in months.
 */
export const calculateBudgetStreak = (budgets: Record<string, MonthlyBudget>, expenses: Expense[]) => {
  const months = Object.keys(budgets).sort().reverse();
  let streak = 0;

  for (const month of months) {
    const monthIncome = budgets[month].income;
    if (monthIncome === 0) break; // Haven't set up budget for this month?

    const monthExpenses = expenses.filter(e => e.month === month).reduce((sum, e) => sum + e.amount, 0);
    if (monthExpenses <= monthIncome) {
      streak++;
    } else {
      break;
    }
  }

  return streak;
};

/**
 * Generates heatmap data for the last N days.
 */
export const generateHeatmapData = (expenses: Expense[], days: number = 180) => {
  const data: Record<string, number> = {};
  const today = new Date();
  
  for (let i = 0; i < days; i++) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];
    data[dateStr] = 0;
  }

  expenses.forEach(e => {
    const dateStr = e.date.split('T')[0];
    if (data[dateStr] !== undefined) {
      data[dateStr]++;
    }
  });

  return Object.entries(data).map(([date, count]) => ({ date, count }));
};
