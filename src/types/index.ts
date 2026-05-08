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

export interface SavingsGoal {
  id: string;
  name: string;
  icon: string;
  targetAmount: number;
  currentAmount: number;
  monthlyContribution: number;
  targetDate?: string;
  color?: string;
}
