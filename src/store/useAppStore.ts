import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Expense, MonthlyBudget, CategoryBudget, SavingsGoal, UserSettings, Badge, Challenge } from "@/types";
import { DEFAULT_CATEGORIES, SUGGESTED_PLAN } from "@/constants/categories";
import { currentMonth } from "@/utils/formatters";
import { uid } from "@/utils/storage";

interface AppState {
  activeMonth: string;
  budgets: Record<string, MonthlyBudget>; // keyed by month
  expenses: Expense[];
  hourlyWage: number;
  goals: SavingsGoal[];
  savingsStreak: number;
  xp: number;
  level: number;
  badges: Badge[];
  challenges: Challenge[];
  settings: UserSettings;

  setActiveMonth: (month: string) => void;
  setHourlyWage: (wage: number) => void;
  upsertBudget: (month: string, partial: Partial<MonthlyBudget>) => void;
  setIncome: (month: string, income: number) => void;
  setCategoryPlanned: (month: string, categoryId: string, planned: number) => void;
  addCategory: (month: string, category: Omit<CategoryBudget, "id" | "isCustom">) => void;
  removeCategory: (month: string, categoryId: string) => void;

  addExpense: (e: Omit<Expense, "id" | "month">) => void;
  updateExpense: (id: string, patch: Partial<Expense>) => void;
  deleteExpense: (id: string) => void;

  addGoal: (goal: Omit<SavingsGoal, "id">) => void;
  updateGoal: (id: string, patch: Partial<SavingsGoal>) => void;
  deleteGoal: (id: string) => void;
  addContribution: (goalId: string, amount: number) => void;

  addXP: (amount: number) => void;
  completeChallenge: (id: string) => void;
  claimChallenge: (id: string) => void;
  unlockBadge: (badge: Badge) => void;
  generateDailyChallenges: () => void;

  updateSettings: (settings: Partial<UserSettings> | ((s: UserSettings) => UserSettings)) => void;
  completeOnboarding: (data: { userName: string, income: number, currency: any, type: any, target?: number }) => void;
  login: () => void;
  logout: () => void;
  resetOnboarding: () => void;
  resetAll: () => void;
}

const seedBudget = (month: string): MonthlyBudget => ({
  id: uid(),
  month,
  income: 0,
  categories: DEFAULT_CATEGORIES.map((c) => ({ ...c, planned: 0 })),
});

const defaultSettings: UserSettings = {
  onboardingCompleted: false,
  isLoggedIn: false,
  profile: {
    userName: "New User",
    defaultMonthlyIncome: 50000,
    currency: "INR",
    financialGoalsPreference: "Balanced",
    preferredStartDay: 1,
  },
  notifications: {
    budgetLimit: true,
    overspending: true,
    goalReminders: true,
    dailySpending: false,
    weeklySummary: true,
    achievements: true,
    subscriptionRenewal: true,
    timing: "Evening",
  },
};

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      activeMonth: currentMonth(),
      budgets: { [currentMonth()]: seedBudget(currentMonth()) },
      expenses: [],
      hourlyWage: 300,
      goals: [],
      savingsStreak: 0,
      xp: 0,
      level: 1,
      badges: [],
      challenges: [],
      settings: defaultSettings,

      setActiveMonth: (month) => {
        const { budgets } = get();
        if (!budgets[month]) {
          set({ budgets: { ...budgets, [month]: seedBudget(month) }, activeMonth: month });
        } else {
          set({ activeMonth: month });
        }
      },
      setHourlyWage: (wage) => set({ hourlyWage: wage }),

      upsertBudget: (month, partial) => {
        const { budgets } = get();
        const existing = budgets[month] ?? seedBudget(month);
        set({ budgets: { ...budgets, [month]: { ...existing, ...partial } } });
      },

      setIncome: (month, income) => {
        const { budgets } = get();
        const existing = budgets[month] ?? seedBudget(month);
        set({ budgets: { ...budgets, [month]: { ...existing, income } } });
      },

      setCategoryPlanned: (month, categoryId, planned) => {
        const { budgets } = get();
        const existing = budgets[month] ?? seedBudget(month);
        const categories = existing.categories.map((c) =>
          c.id === categoryId ? { ...c, planned } : c
        );
        set({ budgets: { ...budgets, [month]: { ...existing, categories } } });
      },

      addCategory: (month, cat) => {
        const { budgets } = get();
        const existing = budgets[month] ?? seedBudget(month);
        const newCat: CategoryBudget = { ...cat, id: uid(), isCustom: true };
        set({ budgets: { ...budgets, [month]: { ...existing, categories: [...existing.categories, newCat] } } });
      },

      removeCategory: (month, categoryId) => {
        const { budgets } = get();
        const existing = budgets[month] ?? seedBudget(month);
        set({
          budgets: {
            ...budgets,
            [month]: { ...existing, categories: existing.categories.filter((c) => c.id !== categoryId) },
          },
        });
      },

      addExpense: (e) => {
        const month = e.date.slice(0, 7);
        const expense: Expense = { ...e, id: uid(), month };
        set({ expenses: [expense, ...get().expenses] });
      },

      updateExpense: (id, patch) => {
        set({
          expenses: get().expenses.map((e) => {
            if (e.id !== id) return e;
            const merged = { ...e, ...patch };
            if (patch.date) merged.month = patch.date.slice(0, 7);
            return merged;
          }),
        });
      },

      deleteExpense: (id) => set({ expenses: get().expenses.filter((e) => e.id !== id) }),

      addGoal: (goal) => {
        set({ goals: [...get().goals, { ...goal, id: uid(), history: [] }] });
      },

      updateGoal: (id, patch) => {
        set({
          goals: get().goals.map((g) => (g.id === id ? { ...g, ...patch } : g)),
        });
      },

      deleteGoal: (id) => set({ goals: get().goals.filter((g) => g.id !== id) }),

      addContribution: (goalId, amount) => {
        set({
          goals: get().goals.map((g) => {
            if (g.id !== goalId) return g;
            return {
              ...g,
              currentAmount: g.currentAmount + amount,
              history: [...g.history, { date: new Date().toISOString(), amount }],
            };
          }),
        });
      },

      addXP: (amount) => {
        const { xp, level } = get();
        const newXP = xp + amount;
        const xpForNextLevel = level * 1000;
        
        if (newXP >= xpForNextLevel) {
          set({ xp: newXP - xpForNextLevel, level: level + 1 });
        } else {
          set({ xp: newXP });
        }
      },

      completeChallenge: (id) => {
        set({
          challenges: get().challenges.map((c) => 
            c.id === id ? { ...c, status: 'completed' } : c
          )
        });
      },

      claimChallenge: (id) => {
        const { challenges, addXP } = get();
        const challenge = challenges.find(c => c.id === id);
        if (challenge && challenge.status === 'completed') {
          addXP(challenge.rewardXP);
          set({
            challenges: challenges.map(c => 
              c.id === id ? { ...c, status: 'claimed' } : c
            )
          });
        }
      },

      unlockBadge: (badge) => {
        const { badges } = get();
        if (!badges.find(b => b.id === badge.id)) {
          set({ badges: [...badges, { ...badge, unlockedAt: new Date().toISOString() }] });
        }
      },

      generateDailyChallenges: () => {
        const today = new Date().toISOString().split('T')[0];
        const { challenges } = get();
        
        // Don't regenerate if we already have active challenges for today
        if (challenges.some(c => c.date === today)) return;

        const newChallenges: Challenge[] = [
          {
            id: uid(),
            title: "Disciplined Spender",
            description: "Spend less than ₹200 today",
            rewardXP: 150,
            type: 'spending_limit',
            targetValue: 200,
            date: today,
            status: 'active'
          },
          {
            id: uid(),
            title: "Home Cooked",
            description: "No food delivery today",
            rewardXP: 100,
            type: 'no_category',
            categoryId: 'food',
            date: today,
            status: 'active'
          },
          {
            id: uid(),
            title: "Tiny Saver",
            description: "Save ₹100 today",
            rewardXP: 120,
            type: 'save_amount',
            targetValue: 100,
            date: today,
            status: 'active'
          }
        ];

        set({ challenges: [...challenges, ...newChallenges] });
      },

      updateSettings: (updater) => {
        const { settings } = get();
        const newSettings = typeof updater === "function" ? updater(settings) : { ...settings, ...updater };
        set({ settings: newSettings });
      },

      completeOnboarding: (data) => {
        const { settings } = get();
        set({
          settings: {
            ...settings,
            onboardingCompleted: true,
            isLoggedIn: true,
            userType: data.type,
            profile: {
              ...settings.profile,
              userName: data.userName,
              defaultMonthlyIncome: data.income,
              currency: data.currency,
              monthlySavingTarget: data.target,
            }
          },
          // Also update the current month's budget income
          budgets: {
            ...get().budgets,
            [currentMonth()]: {
              ...get().budgets[currentMonth()],
              income: data.income,
            }
          }
        });
      },

      login: () => {
        const { settings } = get();
        set({ settings: { ...settings, isLoggedIn: true } });
      },

      logout: () => {
        const { settings } = get();
        set({ settings: { ...settings, isLoggedIn: false } });
      },

      resetOnboarding: () => {
        const { settings } = get();
        set({ settings: { ...settings, onboardingCompleted: false, isLoggedIn: false } });
      },

      resetAll: () =>
        set({
          activeMonth: currentMonth(),
          budgets: { [currentMonth()]: seedBudget(currentMonth()) },
          expenses: [],
          hourlyWage: 300,
          goals: [],
          savingsStreak: 0,
          settings: defaultSettings,
        }),
    }),

    { 
      name: "spend-sense-store-v1",
      onRehydrateStorage: () => (state) => {
        if (state) {
          // Sync default category icons with constants (fixes old emoji data)
          Object.values(state.budgets).forEach((budget) => {
            budget.categories = budget.categories.map((cat) => {
              const defaultCat = DEFAULT_CATEGORIES.find((dc) => dc.id === cat.id);
              if (defaultCat && !cat.isCustom) {
                return { ...cat, icon: defaultCat.icon };
              }
              return cat;
            });
          });
        }
      },
    }
  )
);

// Selectors
export const useActiveBudget = () => {
  const { activeMonth, budgets } = useAppStore();
  return budgets[activeMonth];
};

export const useMonthExpenses = (month?: string) => {
  const { activeMonth, expenses } = useAppStore();
  const m = month ?? activeMonth;
  return expenses.filter((e) => e.month === m);
};
