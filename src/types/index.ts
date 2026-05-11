export interface CategoryBudget {
  id: string;
  name: string;
  icon: string;
  color: string; // CSS color value (hsl)
  planned: number;
  isCustom: boolean;
}

export interface MonthlyBudget {
  id: string;
  month: string; // "YYYY-MM"
  income: number;
  categories: CategoryBudget[];
}

export interface Expense {
  id: string;
  categoryId: string;
  amount: number;
  date: string; // ISO date
  note: string;
  month: string; // "YYYY-MM"
}

export type InsightType = "warning" | "success" | "tip" | "prediction";

export interface InsightMessage {
  id: string;
  type: InsightType;
  categoryId?: string;
  category?: string;
  title: string;
  message: string;
  severity: 1 | 2 | 3;
  actionLabel?: string;
  actionHref?: string;
}

export interface GoalContribution {
  date: string; // ISO date
  amount: number;
}

export interface SavingsGoal {
  id: string;
  name: string;
  icon: string;
  targetAmount: number;
  currentAmount: number;
  monthlyContribution: number;
  targetDate?: string;
  color?: string;
  history: GoalContribution[];
}

export type UserType = "Student" | "Family" | "Professional" | "Freelancer";

export interface UserSettings {
  onboardingCompleted: boolean;
  isLoggedIn: boolean;
  userType?: UserType;
  profile: {
    userName: string;
    defaultMonthlyIncome: number;
    currency: "INR" | "USD" | "EUR";
    financialGoalsPreference: string;
    preferredStartDay: number;
    avatar?: string;
    monthlySavingTarget?: number;
  };
  notifications: {
    budgetLimit: boolean;
    overspending: boolean;
    goalReminders: boolean;
    dailySpending: boolean;
    weeklySummary: boolean;
    achievements: boolean;
    subscriptionRenewal: boolean;
    timing: "Morning" | "Evening" | "Custom";
    customTime?: string;
  };
}

export interface Badge {
  id: string;
  name: string;
  icon: string;
  description: string;
  unlockedAt?: string;
  category: "streaks" | "savings" | "discipline" | "social";
}

export interface Challenge {
  id: string;
  title: string;
  description: string;
  rewardXP: number;
  type: 'spending_limit' | 'no_category' | 'save_amount' | 'zero_spend';
  targetValue?: number;
  categoryId?: string;
  date: string; // YYYY-MM-DD
  status: 'active' | 'completed' | 'claimed';
}
