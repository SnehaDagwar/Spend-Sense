import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Expense, MonthlyBudget, CategoryBudget } from "@/types";
import { DEFAULT_CATEGORIES, SUGGESTED_PLAN } from "@/constants/categories";
import { currentMonth } from "@/utils/formatters";
import { uid } from "@/utils/storage";

interface AppState {
  activeMonth: string;
  budgets: Record<string, MonthlyBudget>; // keyed by month
  expenses: Expense[];
  hourlyWage: number;

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

  resetAll: () => void;
}

const seedBudget = (month: string): MonthlyBudget => ({
  id: uid(),
  month,
  income: 50000,
  categories: DEFAULT_CATEGORIES.map((c) => ({ ...c, planned: SUGGESTED_PLAN[c.id] ?? 1000 })),
});

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      activeMonth: currentMonth(),
      budgets: { [currentMonth()]: seedBudget(currentMonth()) },
      expenses: [],
      hourlyWage: 300,

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

      resetAll: () =>
        set({
          activeMonth: currentMonth(),
          budgets: { [currentMonth()]: seedBudget(currentMonth()) },
          expenses: [],
          hourlyWage: 300,
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
