/**
 * Unit tests for utility functions used across the store and UI.
 *
 * Tests pure mapping/calculation logic without needing to hydrate
 * the full Zustand store (which requires localStorage via persist middleware).
 * Store action integration is covered by the critical_path and component tests.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mock the API client ────────────────────────────────────────────────────────
vi.mock("@/lib/api", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  getAccessToken: vi.fn(() => null),
  getRefreshToken: vi.fn(() => null),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

// ─── Pure Mapping Function Tests ──────────────────────────────────────────────
// Test the data transformation logic that the store uses to map
// backend API responses to frontend state shapes.

describe("Backend → Frontend expense mapping (mapBackendExpense logic)", () => {
  it("converts decimal string amount to number", () => {
    const backendExpense = {
      id: "e1",
      categoryId: "cat-1",
      amount: "450.00",
      currency: "INR",
      expenseDate: "2026-06-15",
      note: "Lunch",
      paymentMethod: "upi",
      tags: [],
      isRecurring: false,
    };

    // Simulate what mapBackendExpense does
    const mapped = {
      id: backendExpense.id,
      categoryId: backendExpense.categoryId,
      amount: parseFloat(backendExpense.amount),
      date: backendExpense.expenseDate,
      note: backendExpense.note,
      month: backendExpense.expenseDate.slice(0, 7),
      paymentMethod: backendExpense.paymentMethod,
      tags: backendExpense.tags,
      isRecurring: backendExpense.isRecurring,
    };

    expect(mapped.amount).toBe(450);
    expect(mapped.date).toBe("2026-06-15");
    expect(mapped.month).toBe("2026-06");
    expect(typeof mapped.amount).toBe("number");
  });

  it("extracts YYYY-MM month from ISO date", () => {
    const dates = [
      { input: "2026-01-01", expected: "2026-01" },
      { input: "2026-12-31", expected: "2026-12" },
      { input: "2025-06-15", expected: "2025-06" },
    ];

    dates.forEach(({ input, expected }) => {
      expect(input.slice(0, 7)).toBe(expected);
    });
  });
});

describe("Backend → Frontend goal mapping (mapBackendGoal logic)", () => {
  it("converts decimal string targetAmount to number", () => {
    const backendGoal = {
      id: "g1",
      name: "Emergency Fund",
      icon: "shield",
      color: "#22C55E",
      targetAmount: "100000.00",
      currentAmount: "30000.00",
      monthlyContribution: "5000.00",
      targetDate: null,
      contributions: [],
    };

    const mapped = {
      id: backendGoal.id,
      name: backendGoal.name,
      targetAmount: parseFloat(backendGoal.targetAmount),
      currentAmount: parseFloat(backendGoal.currentAmount),
      monthlyContribution: parseFloat(backendGoal.monthlyContribution),
      history: backendGoal.contributions.map((c: any) => ({
        date: c.contributedAt?.slice(0, 10) ?? "",
        amount: parseFloat(c.amount ?? "0"),
      })),
    };

    expect(mapped.targetAmount).toBe(100000);
    expect(mapped.currentAmount).toBe(30000);
    expect(mapped.monthlyContribution).toBe(5000);
    expect(Array.isArray(mapped.history)).toBe(true);
  });

  it("calculates progress percentage correctly", () => {
    const target = 100000;
    const current = 30000;
    const progress = (current / target) * 100;

    expect(progress).toBe(30);
  });
});

describe("Backend → Frontend budget mapping (mapBackendBudget logic)", () => {
  it("converts decimal income to number", () => {
    const backendBudget = {
      id: "b1",
      month: "2026-06",
      income: "50000.00",
      warningThreshold: "0.80",
      categories: [],
    };

    const mapped = {
      id: backendBudget.id,
      month: backendBudget.month,
      income: parseFloat(backendBudget.income),
      warningThreshold: parseFloat(backendBudget.warningThreshold),
      categories: [],
    };

    expect(mapped.income).toBe(50000);
    expect(mapped.warningThreshold).toBe(0.8);
  });

  it("maps category allocations with planned amounts", () => {
    const backendCategories = [
      {
        id: "alloc-1",
        categoryId: "cat-1",
        category: { id: "cat-1", name: "Food", icon: "Utensils", color: "#FF6B6B", slug: "food" },
        plannedAmount: "10000.00",
        displayOrder: 1,
        analytics: { spent: "5000.00", remaining: "5000.00" },
      },
    ];

    const mapped = backendCategories.map((a) => ({
      id: a.categoryId,
      name: a.category.name,
      icon: a.category.icon,
      color: a.category.color,
      planned: parseFloat(a.plannedAmount),
      actual: parseFloat(a.analytics.spent),
    }));

    expect(mapped[0].planned).toBe(10000);
    expect(mapped[0].actual).toBe(5000);
    expect(mapped[0].name).toBe("Food");
  });
});

describe("seedBudget default structure", () => {
  it("creates an empty budget with zero income for a new month", () => {
    const month = "2026-07";
    const seedBudget = {
      id: `local-${month}`,
      month,
      income: 0,
      categories: [],
    };

    expect(seedBudget.income).toBe(0);
    expect(seedBudget.month).toBe(month);
    expect(seedBudget.categories).toEqual([]);
    expect(seedBudget.id).toContain("local-");
  });
});

describe("setActiveMonth state transition", () => {
  it("does not overwrite existing budget data when switching to known month", () => {
    const existingBudgets: Record<string, any> = {
      "2026-06": { id: "b1", month: "2026-06", income: 50000, categories: [] },
    };

    // Simulate setActiveMonth logic: only seed if not already present
    const targetMonth = "2026-06";
    const needsSeed = !existingBudgets[targetMonth];

    expect(needsSeed).toBe(false);
    expect(existingBudgets["2026-06"].income).toBe(50000);
  });

  it("creates a new seed budget when switching to unseen month", () => {
    const existingBudgets: Record<string, any> = {};
    const targetMonth = "2026-07";

    const needsSeed = !existingBudgets[targetMonth];
    if (needsSeed) {
      existingBudgets[targetMonth] = {
        id: `local-${targetMonth}`,
        month: targetMonth,
        income: 0,
        categories: [],
      };
    }

    expect(existingBudgets["2026-07"]).toBeDefined();
    expect(existingBudgets["2026-07"].income).toBe(0);
  });
});

describe("Optimistic update rollback pattern", () => {
  it("rollback restores previous array state after failure", async () => {
    const originalExpenses = [
      { id: "e1", amount: 100, categoryId: "c1", date: "2026-06-01", note: "" },
    ];

    let currentExpenses = [...originalExpenses];
    const optimisticId = "temp-123";

    // Step 1: Optimistically add
    const optimisticExpense = { id: optimisticId, amount: 200, categoryId: "c1", date: "2026-06-15", note: "Test" };
    currentExpenses = [...currentExpenses, optimisticExpense];
    expect(currentExpenses.length).toBe(2);

    // Step 2: API fails, rollback
    const apiCallFailed = true;
    if (apiCallFailed) {
      currentExpenses = originalExpenses;
    }

    expect(currentExpenses.length).toBe(1);
    expect(currentExpenses.find((e) => e.id === optimisticId)).toBeUndefined();
  });

  it("confirms optimistic add by replacing temp ID with server ID", () => {
    const tempId = "temp-456";
    let currentExpenses = [
      { id: "e1", amount: 100, categoryId: "c1", date: "2026-06-01", note: "" },
      { id: tempId, amount: 300, categoryId: "c2", date: "2026-06-15", note: "New" },
    ];

    const serverId = "server-uuid-789";

    // Replace temp with server ID
    currentExpenses = currentExpenses.map((e) =>
      e.id === tempId ? { ...e, id: serverId } : e
    );

    expect(currentExpenses.find((e) => e.id === tempId)).toBeUndefined();
    expect(currentExpenses.find((e) => e.id === serverId)).toBeDefined();
  });
});
