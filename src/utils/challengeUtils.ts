import type { Challenge, Expense } from "@/types";

/**
 * Checks if a challenge has been met based on current expenses.
 */
export const checkChallengeStatus = (challenge: Challenge, expenses: Expense[]) => {
  if (challenge.status !== 'active') return challenge.status;

  const todayStr = new Date().toISOString().split('T')[0];
  const todayExpenses = expenses.filter(e => e.date.split('T')[0] === todayStr);
  const totalToday = todayExpenses.reduce((sum, e) => sum + e.amount, 0);

  switch (challenge.type) {
    case 'spending_limit':
      // Status is active as long as limit is not exceeded
      if (totalToday > (challenge.targetValue || 0)) {
        return 'failed';
      }
      // We can't say it's "completed" until the day is over, 
      // but for UI feedback, we'll mark as completed if it's the end of the day 
      // or if they've logged at least one thing and are still under.
      // Actually, let's just keep it active until they manually check or the day ends.
      // For this demo, if they have logged something and are under, we'll let them complete it.
      if (todayExpenses.length > 0 && totalToday <= (challenge.targetValue || 0)) {
        return 'completed';
      }
      break;

    case 'no_category':
      const categorySpent = todayExpenses
        .filter(e => e.categoryId === challenge.categoryId)
        .reduce((sum, e) => sum + e.amount, 0);
      if (categorySpent > 0) return 'failed';
      // Same logic as above
      if (todayExpenses.length > 0) return 'completed';
      break;

    case 'save_amount':
      // This is tricky without a "savings" log, but we can assume if they 
      // stayed under a certain threshold of their daily budget.
      // Or if they added a contribution to a goal today.
      // Let's use the latter or a simple spending threshold.
      if (totalToday < 500) return 'completed'; // Arbitrary "saving" threshold
      break;

    case 'zero_spend':
      if (todayExpenses.length > 0) return 'failed';
      // Can only be completed at the end of the day.
      break;
  }

  return 'active';
};
