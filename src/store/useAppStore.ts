import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Expense, MonthlyBudget, CategoryBudget, SavingsGoal, UserSettings, Badge, Challenge, FamilyMember, UserType } from "@/types";
import { DEFAULT_CATEGORIES } from "@/constants/categories";
import { currentMonth } from "@/utils/formatters";
import { uid } from "@/utils/storage";
import { apiClient, setTokens, clearTokens, getAccessToken } from "@/lib/api";
import { toast } from "sonner";

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
  familyMembers: FamilyMember[];

  // Initialization and auth states
  isInitializing: boolean;
  authChecked: boolean;

  // Actions
  setActiveMonth: (month: string) => void;
  setHourlyWage: (wage: number) => Promise<void>;
  upsertBudget: (month: string, partial: Partial<MonthlyBudget>) => Promise<void>;
  setIncome: (month: string, income: number) => Promise<void>;
  setCategoryPlanned: (month: string, categoryId: string, planned: number) => Promise<void>;
  addCategory: (month: string, category: Omit<CategoryBudget, "id" | "isCustom">) => Promise<void>;
  removeCategory: (month: string, categoryId: string) => Promise<void>;

  addExpense: (e: Omit<Expense, "id" | "month">) => Promise<void>;
  updateExpense: (id: string, patch: Partial<Expense>) => Promise<void>;
  deleteExpense: (id: string) => Promise<void>;

  addGoal: (goal: Omit<SavingsGoal, "id">) => Promise<void>;
  updateGoal: (id: string, patch: Partial<SavingsGoal>) => Promise<void>;
  deleteGoal: (id: string) => Promise<void>;
  addContribution: (goalId: string, amount: number) => Promise<void>;

  addXP: (amount: number) => Promise<void>;
  completeChallenge: (id: string) => Promise<void>;
  claimChallenge: (id: string) => Promise<void>;
  unlockBadge: (badge: Badge) => Promise<void>;
  generateDailyChallenges: () => Promise<void>;

  addFamilyMember: (member: Omit<FamilyMember, "id">) => Promise<void>;
  updateFamilyMember: (id: string, patch: Partial<FamilyMember>) => Promise<void>;
  removeFamilyMember: (id: string) => Promise<void>;

  updateSettings: (settings: Partial<UserSettings> | ((s: UserSettings) => UserSettings)) => Promise<void>;
  completeOnboarding: (data: { userName: string, income: number, currency: any, type: any, target?: number }) => Promise<void>;
  
  // Real authentication actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string, userType: UserType) => Promise<void>;
  logout: () => Promise<void>;
  
  initializeFromBackend: () => Promise<void>;
  migrateLocalDataToServer: () => Promise<void>;
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

// ---------------------------------------------------------------------------
// Backend Data Mapping Helpers
// ---------------------------------------------------------------------------

const mapBackendBudget = (b: any): MonthlyBudget => ({
  id: b.id,
  month: b.month.slice(0, 7), // Convert YYYY-MM-DD to YYYY-MM
  income: Number(b.income),
  categories: (b.categories || []).map((c: any) => ({
    id: c.category.id,
    name: c.category.name,
    icon: c.category.icon,
    color: c.category.color,
    planned: Number(c.plannedAmount),
    isCustom: !c.category.isSystem,
  })),
});

const mapBackendExpense = (e: any): Expense => ({
  id: e.id,
  categoryId: e.categoryId,
  amount: Number(e.amount),
  date: e.expenseDate,
  note: e.note || "",
  month: e.expenseDate.slice(0, 7),
  paidBy: e.paidByMemberId,
  splitBetween: e.splitBetweenMemberIds,
});

const mapBackendGoal = (g: any): SavingsGoal => ({
  id: g.id,
  name: g.name,
  icon: g.icon,
  targetAmount: Number(g.targetAmount),
  currentAmount: Number(g.currentAmount),
  monthlyContribution: Number(g.monthlyContribution),
  targetDate: g.targetDate || undefined,
  color: g.color || undefined,
  history: (g.contributions || []).map((c: any) => ({
    date: c.contributedAt || c.date,
    amount: Number(c.amount),
  })),
});

const mapBackendSettings = (user: any, prefs: any, notifs: any): UserSettings => ({
  onboardingCompleted: user.onboardingCompleted,
  isLoggedIn: true,
  userType: user.userType,
  profile: {
    userName: user.displayName,
    defaultMonthlyIncome: prefs ? Number(prefs.defaultMonthlyIncome) : 50000,
    currency: (prefs ? prefs.currency : "INR") as any,
    financialGoalsPreference: prefs ? prefs.financialGoalsPreference : "Balanced",
    preferredStartDay: prefs ? prefs.preferredStartDay : 1,
    avatar: prefs ? prefs.avatarUrl : undefined,
    monthlySavingTarget: prefs && prefs.monthlySavingTargetPercent ? (Number(prefs.defaultMonthlyIncome) * Number(prefs.monthlySavingTargetPercent)) / 100 : undefined,
  },
  notifications: {
    budgetLimit: notifs ? notifs.budgetLimit : true,
    overspending: notifs ? notifs.overspending : true,
    goalReminders: notifs ? notifs.goalReminders : true,
    dailySpending: notifs ? notifs.dailySpending : false,
    weeklySummary: notifs ? notifs.weeklySummary : true,
    achievements: notifs ? notifs.achievements : true,
    subscriptionRenewal: notifs ? notifs.subscriptionRenewal : true,
    timing: notifs ? notifs.timing : "Evening",
    customTime: notifs && notifs.customTime ? notifs.customTime : undefined,
  },
});

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
      familyMembers: [],

      isInitializing: false,
      authChecked: false,

      setActiveMonth: (month) => {
        const { budgets } = get();
        if (!budgets[month]) {
          set({ budgets: { ...budgets, [month]: seedBudget(month) }, activeMonth: month });
        } else {
          set({ activeMonth: month });
        }
      },

      setHourlyWage: async (wage) => {
        set({ hourlyWage: wage });
        try {
          await apiClient.patch("/me/preferences", { hourlyWage: wage });
        } catch (err) {
          console.error("Failed to update hourly wage on server", err);
        }
      },

      upsertBudget: async (month, partial) => {
        const { budgets } = get();
        const existing = budgets[month] ?? seedBudget(month);
        const updated = { ...existing, ...partial };
        set({ budgets: { ...budgets, [month]: updated } });

        try {
          // Find if budget exists on server
          const budgetsList = await apiClient.get(`/budgets?from=${month}&to=${month}`);
          if (budgetsList.items && budgetsList.items.length > 0) {
            const serverId = budgetsList.items[0].id;
            await apiClient.patch(`/budgets/${serverId}`, {
              income: updated.income,
            });
          } else {
            await apiClient.post("/budgets", {
              month,
              income: updated.income,
            });
          }
        } catch (err) {
          toast.error("Failed to sync budget to server.");
          console.error(err);
        }
      },

      setIncome: async (month, income) => {
        const { budgets } = get();
        const existing = budgets[month] ?? seedBudget(month);
        set({ budgets: { ...budgets, [month]: { ...existing, income } } });

        try {
          const budgetsList = await apiClient.get(`/budgets?from=${month}&to=${month}`);
          if (budgetsList.items && budgetsList.items.length > 0) {
            await apiClient.patch(`/budgets/${budgetsList.items[0].id}`, { income });
          } else {
            await apiClient.post("/budgets", { month, income });
          }
        } catch (err) {
          console.error("Income sync failed", err);
        }
      },

      setCategoryPlanned: async (month, categoryId, planned) => {
        const { budgets } = get();
        const existing = budgets[month] ?? seedBudget(month);
        
        // Optimistic UI update
        const categories = existing.categories.map((c) =>
          c.id === categoryId ? { ...c, planned } : c
        );
        set({ budgets: { ...budgets, [month]: { ...existing, categories } } });

        try {
          // Fetch server budget to update allocation
          const budgetsList = await apiClient.get(`/budgets?from=${month}&to=${month}`);
          let serverBudget;
          if (budgetsList.items && budgetsList.items.length > 0) {
            serverBudget = await apiClient.get(`/budgets/${budgetsList.items[0].id}`);
          } else {
            serverBudget = await apiClient.post("/budgets", { month, income: existing.income });
          }

          // Create full list of allocations for replace_all_allocations or update single allocation
          const existingAllocations = serverBudget.categories.map((c: any) => ({
            category_id: c.category.id,
            planned_amount: c.category.id === categoryId ? planned : Number(c.plannedAmount),
            display_order: c.displayOrder,
          }));

          // If current category is not in server budget category list, append it
          if (!existingAllocations.some((a: any) => a.category_id === categoryId)) {
            existingAllocations.push({
              category_id: categoryId,
              planned_amount: planned,
              display_order: existingAllocations.length,
            });
          }

          // Re-update full allocations to DB
          await apiClient.patch(`/budgets/${serverBudget.id}`, {
            income: Number(serverBudget.income),
            categories: existingAllocations,
          });
        } catch (err) {
          toast.error("Failed to sync category budget limit.");
          console.error(err);
        }
      },

      addCategory: async (month, cat) => {
        const { budgets } = get();
        const existing = budgets[month] ?? seedBudget(month);
        const tempId = uid();
        const newCat: CategoryBudget = { ...cat, id: tempId, isCustom: true };
        
        set({ budgets: { ...budgets, [month]: { ...existing, categories: [...existing.categories, newCat] } } });

        try {
          // 1. Create custom category on server
          const slug = cat.name.toLowerCase().replace(/[^a-z0-9]/g, "-").slice(0, 50);
          const serverCat = await apiClient.post("/categories", {
            slug,
            name: cat.name,
            icon: cat.icon,
            color: cat.color,
            displayOrder: 10,
          });

          // 2. Replace temp id with server id in Zustand state
          const state = get();
          const activeBudget = state.budgets[month];
          if (activeBudget) {
            const mappedCats = activeBudget.categories.map(c => c.id === tempId ? { ...c, id: serverCat.id } : c);
            set({ budgets: { ...state.budgets, [month]: { ...activeBudget, categories: mappedCats } } });
            
            // 3. Add allocation for it
            await state.setCategoryPlanned(month, serverCat.id, cat.planned);
          }
        } catch (err) {
          toast.error("Failed to add category to server.");
          console.error(err);
        }
      },

      removeCategory: async (month, categoryId) => {
        const { budgets } = get();
        const existing = budgets[month] ?? seedBudget(month);
        set({
          budgets: {
            ...budgets,
            [month]: { ...existing, categories: existing.categories.filter((c) => c.id !== categoryId) },
          },
        });

        try {
          await apiClient.delete(`/categories/${categoryId}?force=true`);
        } catch (err) {
          console.error("Failed to remove category on server", err);
        }
      },

      addExpense: async (e) => {
        const month = e.date.slice(0, 7);
        const tempId = uid();
        const expense: Expense = { ...e, id: tempId, month };
        
        // Optimistic UI update
        set({ expenses: [expense, ...get().expenses] });

        try {
          const res = await apiClient.post("/expenses", {
            categoryId: e.categoryId,
            amount: e.amount,
            expenseDate: e.date,
            note: e.note,
            paymentMethod: e.paymentMethod,
            merchant: e.merchant || undefined,
            tags: e.tags,
            currency: e.currency,
            isRecurring: e.isRecurring,
            paidByMemberId: e.paidBy || null,
            splitBetweenMemberIds: e.splitBetween || [],
          });

          // Update Zustand store with the real server-returned expense (with real ID)
          set({
            expenses: get().expenses.map((item) => item.id === tempId ? mapBackendExpense(res) : item),
          });
          toast.success("Expense tracked!");
        } catch (err: any) {
          // Rollback on failure
          set({ expenses: get().expenses.filter((item) => item.id !== tempId) });
          toast.error(err.message || "Failed to save expense.");
        }
      },

      updateExpense: async (id, patch) => {
        const previousExpenses = get().expenses;
        // Optimistic update
        set({
          expenses: previousExpenses.map((e) => {
            if (e.id !== id) return e;
            const merged = { ...e, ...patch };
            if (patch.date) merged.month = patch.date.slice(0, 7);
            return merged;
          }),
        });

        try {
          const payload: any = {};
          if (patch.categoryId) payload.categoryId = patch.categoryId;
          if (patch.amount) payload.amount = patch.amount;
          if (patch.date) payload.expenseDate = patch.date;
          if (patch.note !== undefined) payload.note = patch.note;
          if (patch.paymentMethod) payload.paymentMethod = patch.paymentMethod;
          if (patch.merchant !== undefined) payload.merchant = patch.merchant;
          if (patch.tags) payload.tags = patch.tags;
          if (patch.currency) payload.currency = patch.currency;
          if (patch.isRecurring !== undefined) payload.isRecurring = patch.isRecurring;
          if (patch.paidBy !== undefined) payload.paidByMemberId = patch.paidBy;
          if (patch.splitBetween !== undefined) payload.splitBetweenMemberIds = patch.splitBetween;

          const res = await apiClient.patch(`/expenses/${id}`, payload);
          set({
            expenses: get().expenses.map((e) => e.id === id ? mapBackendExpense(res) : e),
          });
        } catch (err: any) {
          // Rollback
          set({ expenses: previousExpenses });
          toast.error("Failed to update expense.");
        }
      },

      deleteExpense: async (id) => {
        const previousExpenses = get().expenses;
        // Optimistic UI update
        set({ expenses: previousExpenses.filter((e) => e.id !== id) });

        try {
          await apiClient.delete(`/expenses/${id}`);
          toast.success("Expense deleted.");
        } catch (err) {
          // Rollback
          set({ expenses: previousExpenses });
          toast.error("Failed to delete expense.");
        }
      },

      addGoal: async (goal) => {
        const tempId = uid();
        const optimisticGoal: SavingsGoal = { ...goal, id: tempId, history: [] };
        set({ goals: [...get().goals, optimisticGoal] });

        try {
          const res = await apiClient.post("/goals", {
            name: goal.name,
            icon: goal.icon,
            targetAmount: goal.targetAmount,
            currentAmount: goal.currentAmount,
            monthlyContribution: goal.monthlyContribution,
            targetDate: goal.targetDate || null,
            color: goal.color || null,
          });

          set({
            goals: get().goals.map((g) => g.id === tempId ? mapBackendGoal(res) : g),
          });
          toast.success("Savings goal created!");
        } catch (err) {
          set({ goals: get().goals.filter((g) => g.id !== tempId) });
          toast.error("Failed to create savings goal.");
        }
      },

      updateGoal: async (id, patch) => {
        const prevGoals = get().goals;
        set({
          goals: prevGoals.map((g) => (g.id === id ? { ...g, ...patch } : g)),
        });

        try {
          const payload: any = {};
          if (patch.name) payload.name = patch.name;
          if (patch.icon) payload.icon = patch.icon;
          if (patch.targetAmount) payload.targetAmount = patch.targetAmount;
          if (patch.currentAmount !== undefined) payload.currentAmount = patch.currentAmount;
          if (patch.monthlyContribution) payload.monthlyContribution = patch.monthlyContribution;
          if (patch.targetDate !== undefined) payload.targetDate = patch.targetDate;
          if (patch.color) payload.color = patch.color;

          const res = await apiClient.patch(`/goals/${id}`, payload);
          set({
            goals: get().goals.map((g) => g.id === id ? mapBackendGoal(res) : g),
          });
        } catch (err) {
          set({ goals: prevGoals });
          toast.error("Failed to update goal.");
        }
      },

      deleteGoal: async (id) => {
        const prevGoals = get().goals;
        set({ goals: prevGoals.filter((g) => g.id !== id) });

        try {
          await apiClient.delete(`/goals/${id}`);
          toast.success("Goal deleted.");
        } catch (err) {
          set({ goals: prevGoals });
          toast.error("Failed to delete goal.");
        }
      },

      addContribution: async (goalId, amount) => {
        const prevGoals = get().goals;
        
        // Optimistic UI update
        set({
          goals: prevGoals.map((g) => {
            if (g.id !== goalId) return g;
            return {
              ...g,
              currentAmount: g.currentAmount + amount,
              history: [...g.history, { date: new Date().toISOString(), amount }],
            };
          }),
        });

        try {
          const res = await apiClient.post(`/goals/${goalId}/contributions`, {
            amount,
            note: "Contribution",
          });
          set({
            goals: get().goals.map((g) => g.id === goalId ? mapBackendGoal(res) : g),
          });
          toast.success("Contribution added!");
        } catch (err) {
          set({ goals: prevGoals });
          toast.error("Failed to add contribution.");
        }
      },

      addXP: async (amount) => {
        // Handled server-side through event tracking, but we sync it locally for micro-animations
        const { xp, level } = get();
        const newXP = xp + amount;
        const xpForNextLevel = level * 1000;
        
        if (newXP >= xpForNextLevel) {
          set({ xp: newXP - xpForNextLevel, level: level + 1 });
        } else {
          set({ xp: newXP });
        }
      },

      completeChallenge: async (id) => {
        set({
          challenges: get().challenges.map((c) => 
            c.id === id ? { ...c, status: 'completed' } : c
          )
        });
        
        try {
          // Log completion to server via a joined challenge or event dispatch
          // Endpoint: POST /gamification/challenges/{id}/join (used as checkin/status update)
          await apiClient.post(`/gamification/challenges/${id}/join`, {});
        } catch (err) {
          console.error("Challenge completion sync failed", err);
        }
      },

      claimChallenge: async (id) => {
        const { challenges, addXP } = get();
        const challenge = challenges.find(c => c.id === id);
        if (challenge && challenge.status === 'completed') {
          addXP(challenge.rewardXP);
          set({
            challenges: challenges.map(c => 
              c.id === id ? { ...c, status: 'claimed' } : c
            )
          });

          try {
            await apiClient.post(`/gamification/challenges/${id}/join`, {});
          } catch (err) {
            console.error("Failed to claim challenge on server", err);
          }
        }
      },

      unlockBadge: async (badge) => {
        const { badges } = get();
        if (!badges.find(b => b.id === badge.id)) {
          set({ badges: [...badges, { ...badge, unlockedAt: new Date().toISOString() }] });
        }
      },

      generateDailyChallenges: async () => {
        try {
          const list = await apiClient.get("/gamification/challenges");
          set({
            challenges: list.items.map((c: any) => ({
              id: c.id,
              title: c.title,
              description: c.description,
              rewardXP: c.rewardXp,
              type: c.challengeType,
              date: c.date,
              status: c.status,
            })),
          });
        } catch (err) {
          console.error("Failed to sync challenges from server", err);
        }
      },

      addFamilyMember: async (member) => {
        const prevMembers = get().familyMembers;
        const tempId = uid();
        set({ familyMembers: [...prevMembers, { ...member, id: tempId }] });

        try {
          // 1. Get user family details
          const families = await apiClient.get("/family/memberships");
          let familyId;
          if (families.items && families.items.length > 0) {
            familyId = families.items[0].familyId;
          } else {
            // Create family
            const fam = await apiClient.post("/family", { name: "Family Wallet" });
            familyId = fam.id;
          }

          // 2. Add member
          const res = await apiClient.post(`/family/${familyId}/invite`, {
            displayName: member.name,
            role: member.role,
            email: member.email || undefined,
            spendingLimit: member.spendingLimit || null,
          });

          set({
            familyMembers: get().familyMembers.map((m) => m.id === tempId ? {
              id: res.id,
              name: res.displayName,
              role: res.role,
              email: res.email || undefined,
              spendingLimit: Number(res.spendingLimit) || undefined,
            } : m),
          });
          toast.success("Family member added.");
        } catch (err) {
          set({ familyMembers: prevMembers });
          toast.error("Failed to add family member.");
        }
      },

      updateFamilyMember: async (id, patch) => {
        const prevMembers = get().familyMembers;
        set({
          familyMembers: prevMembers.map((m) => (m.id === id ? { ...m, ...patch } : m)),
        });

        try {
          const families = await apiClient.get("/family/memberships");
          if (families.items && families.items.length > 0) {
            const familyId = families.items[0].familyId;
            await apiClient.patch(`/family/${familyId}/member/${id}`, {
              role: patch.role,
              spendingLimit: patch.spendingLimit !== undefined ? patch.spendingLimit : undefined,
            });
          }
        } catch (err) {
          set({ familyMembers: prevMembers });
          toast.error("Failed to update family member.");
        }
      },

      removeFamilyMember: async (id) => {
        const prevMembers = get().familyMembers;
        set({ familyMembers: prevMembers.filter((m) => m.id !== id) });

        try {
          const families = await apiClient.get("/family/memberships");
          if (families.items && families.items.length > 0) {
            const familyId = families.items[0].familyId;
            await apiClient.delete(`/family/${familyId}/member/${id}`);
            toast.success("Family member removed.");
          }
        } catch (err) {
          set({ familyMembers: prevMembers });
          toast.error("Failed to remove family member.");
        }
      },

      updateSettings: async (updater) => {
        const { settings } = get();
        const newSettings = typeof updater === "function" ? updater(settings) : { ...settings, ...updater };
        set({ settings: newSettings });

        try {
          // Sync preferences
          await apiClient.patch("/me/preferences", {
            currency: newSettings.profile.currency,
            defaultMonthlyIncome: newSettings.profile.defaultMonthlyIncome,
            financialGoalsPreference: newSettings.profile.financialGoalsPreference,
            preferredStartDay: newSettings.profile.preferredStartDay,
            avatarUrl: newSettings.profile.avatar,
          });

          // Sync notifications
          await apiClient.patch("/me/notifications", {
            budgetLimit: newSettings.notifications.budgetLimit,
            overspending: newSettings.notifications.overspending,
            goalReminders: newSettings.notifications.goalReminders,
            dailySpending: newSettings.notifications.dailySpending,
            weeklySummary: newSettings.notifications.weeklySummary,
            achievements: newSettings.notifications.achievements,
            subscriptionRenewal: newSettings.notifications.subscriptionRenewal,
            timing: newSettings.notifications.timing,
            customTime: newSettings.notifications.customTime || null,
          });
        } catch (err) {
          console.error("Failed to sync settings on server", err);
        }
      },

      completeOnboarding: async (data) => {
        try {
          const res = await apiClient.post("/me/onboarding", {
            displayName: data.userName,
            userType: data.type,
            currency: data.currency,
            defaultMonthlyIncome: data.income,
            monthlySavingTargetPercent: data.target || 20,
            activeMonth: currentMonth(),
          });

          const mappedSettings = mapBackendSettings(res.user, res.preferences, res.notifications);
          set({
            settings: mappedSettings,
            activeMonth: currentMonth(),
          });

          // Also pull budgets/categories created during onboarding
          const state = get();
          await state.initializeFromBackend();
          toast.success("Onboarding completed successfully!");
        } catch (err: any) {
          toast.error(err.message || "Failed to complete onboarding.");
        }
      },

      login: async (email, password) => {
        try {
          const res = await apiClient.post("/auth/login", { email, password });
          setTokens(res.accessToken, res.refreshToken);

          const mappedSettings = mapBackendSettings(res.user, null, null);
          set({ settings: mappedSettings });
          
          await get().initializeFromBackend();
          toast.success("Logged in successfully!");
        } catch (err: any) {
          throw err;
        }
      },

      register: async (email, password, displayName, userType) => {
        try {
          const res = await apiClient.post("/auth/register", {
            email,
            password,
            displayName,
            userType,
          });
          setTokens(res.accessToken, res.refreshToken);

          const mappedSettings = mapBackendSettings(res.user, null, null);
          set({ settings: mappedSettings });
          
          await get().initializeFromBackend();
          toast.success("Account created successfully!");
        } catch (err: any) {
          throw err;
        }
      },

      logout: async () => {
        const token = getRefreshToken();
        try {
          if (token) {
            await apiClient.post("/auth/logout", { refreshToken: token });
          }
        } catch (err) {
          console.error("Server logout error", err);
        } finally {
          clearTokens();
          get().resetAll();
          toast.success("Logged out successfully.");
        }
      },

      initializeFromBackend: async () => {
        if (!getAccessToken()) {
          set({ authChecked: true, isInitializing: false });
          return;
        }

        set({ isInitializing: true });

        try {
          // 1. Fetch current profile preferences
          const profile = await apiClient.get("/me");
          const mappedSettings = mapBackendSettings(
            profile.user,
            profile.preferences,
            profile.notifications
          );

          // 2. Fetch categories
          const cats = await apiClient.get("/categories");
          
          // 3. Fetch budgets
          const budgetsList = await apiClient.get("/budgets");
          const mappedBudgets: Record<string, MonthlyBudget> = {};
          
          // Hydrate each budget with full category details
          for (const b of budgetsList.items || []) {
            const detail = await apiClient.get(`/budgets/${b.id}`);
            mappedBudgets[b.month.slice(0, 7)] = mapBackendBudget(detail);
          }

          // If current month budget doesn't exist, create/seed it
          const curMonth = currentMonth();
          if (!mappedBudgets[curMonth]) {
            mappedBudgets[curMonth] = seedBudget(curMonth);
          }

          // 4. Fetch expenses
          const expensesList = await apiClient.get("/expenses?limit=200");
          const mappedExpenses = (expensesList.items || []).map(mapBackendExpense);

          // 5. Fetch savings goals
          const goalsList = await apiClient.get("/goals");
          const mappedGoals = (goalsList.items || []).map(mapBackendGoal);

          // 6. Fetch gamification profile (XP, Level, Streak)
          let xp = 0, level = 1, savingsStreak = 0;
          try {
            const gamificationProfile = await apiClient.get("/gamification/profile");
            xp = gamificationProfile.xp || 0;
            level = gamificationProfile.level || 1;
            savingsStreak = gamificationProfile.currentStreak || 0;
          } catch (gErr) {
            console.warn("Could not fetch gamification details", gErr);
          }

          // 7. Fetch family members if userType is Family
          let mappedFamilyMembers: FamilyMember[] = [];
          if (profile.user.userType === "Family") {
            try {
              const memberships = await apiClient.get("/family/memberships");
              if (memberships.items && memberships.items.length > 0) {
                const familyId = memberships.items[0].familyId;
                const fam = await apiClient.get(`/family/${familyId}`);
                mappedFamilyMembers = (fam.members || []).map((m: any) => ({
                  id: m.id,
                  name: m.displayName,
                  role: m.role,
                  spendingLimit: Number(m.spendingLimit) || undefined,
                }));
              }
            } catch (fErr) {
              console.warn("Could not fetch family members", fErr);
            }
          }

          // Update Zustand store state
          set({
            settings: mappedSettings,
            budgets: mappedBudgets,
            expenses: mappedExpenses,
            goals: mappedGoals,
            xp,
            level,
            savingsStreak,
            familyMembers: mappedFamilyMembers,
            authChecked: true,
            isInitializing: false,
          });

          // Check if local-to-server migration is needed
          await get().migrateLocalDataToServer();

        } catch (err) {
          console.error("Failed to initialize Spend Sense store from backend", err);
          set({ authChecked: true, isInitializing: false });
        }
      },

      migrateLocalDataToServer: async () => {
        const state = get();
        
        // If user is logged in, onboarding is completed, and we have local data but backend has 0 records
        const localExpensesCount = state.expenses.length;
        const localGoalsCount = state.goals.length;

        if (localExpensesCount === 0 && localGoalsCount === 0) {
          return;
        }

        // We check if the server is actually empty by querying the API
        try {
          const serverExpenses = await apiClient.get("/expenses?limit=1");
          const serverGoals = await apiClient.get("/goals");

          const hasServerData = (serverExpenses.items && serverExpenses.items.length > 0) || (serverGoals.items && serverGoals.items.length > 0);
          if (hasServerData) {
            // Server already has data, don't auto-migrate local data to prevent duplication
            return;
          }

          toast.info("Syncing your local finance history to the server...");

          // 1. Sync custom categories first
          const customCategories = new Set<string>();
          state.expenses.forEach(e => {
            const hasCat = DEFAULT_CATEGORIES.some(c => c.id === e.categoryId);
            if (!hasCat) customCategories.add(e.categoryId);
          });

          // Map local category UUIDs to server category UUIDs
          const categoryIdMap: Record<string, string> = {};

          // 2. Sync budgets
          for (const m of Object.keys(state.budgets)) {
            const b = state.budgets[m];
            if (b.income > 0) {
              await apiClient.post("/budgets", { month: m, income: b.income });
            }
          }

          // 3. Sync expenses
          for (const e of state.expenses) {
            // Find category
            let catId = e.categoryId;
            // Send request
            await apiClient.post("/expenses", {
              categoryId: catId,
              amount: e.amount,
              expenseDate: e.date,
              note: e.note,
              paymentMethod: "cash",
              tags: [],
              currency: state.settings.profile.currency || "INR",
              isRecurring: false,
            });
          }

          // 4. Sync goals
          for (const g of state.goals) {
            await apiClient.post("/goals", {
              name: g.name,
              icon: g.icon,
              targetAmount: g.targetAmount,
              currentAmount: g.currentAmount,
              monthlyContribution: g.monthlyContribution,
              targetDate: g.targetDate || null,
              color: g.color || null,
            });
          }

          toast.success("All your local data has been migrated to the server!");
          
          // Re-fetch clean server state to replace temp IDs
          await state.initializeFromBackend();

        } catch (err) {
          console.error("Local storage data migration failed", err);
        }
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
          familyMembers: [],
        }),
    }),

    { 
      name: "spend-sense-store-v1",
      // Only persist basic settings or token existence locally
      partialize: (state) => ({
        settings: {
          ...state.settings,
          isLoggedIn: state.settings.isLoggedIn,
          onboardingCompleted: state.settings.onboardingCompleted,
        },
      }),
    }
  )
);

// Selectors
export const useActiveBudget = () => {
  const { activeMonth, budgets } = useAppStore();
  return budgets[activeMonth] || {
    id: "fallback",
    month: activeMonth,
    income: 0,
    categories: [],
  };
};

export const useMonthExpenses = (month?: string) => {
  const { activeMonth, expenses } = useAppStore();
  const m = month ?? activeMonth;
  return expenses.filter((e) => e.month === m);
};
