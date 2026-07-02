/**
 * Pure unit tests for all utility functions:
 * - formatINR, formatPercent, monthLabel, currentMonth, daysInMonth, dayOfMonth
 * - streakUtils (computeCurrentStreak, isStreakAlive)
 * - challengeUtils (getDailyChallenges)
 */

import { describe, it, expect } from "vitest";

// ─── Formatter Utils ─────────────────────────────────────────────────────────

import {
  formatINR,
  formatPercent,
  monthLabel,
  currentMonth,
  daysInMonth,
  dayOfMonth,
} from "@/utils/formatters";

describe("formatINR", () => {
  it("formats whole number in INR locale", () => {
    const result = formatINR(50000);
    expect(result).toContain("50,000");
    expect(result).toContain("₹");
  });

  it("formats zero as ₹0", () => {
    const result = formatINR(0);
    expect(result).toContain("0");
  });

  it("formats negative value", () => {
    const result = formatINR(-1000);
    expect(result).toContain("1,000");
  });

  it("compact mode uses K suffix for thousands", () => {
    const result = formatINR(50000, { compact: true });
    // Either "₹50K" or "₹50k" depending on locale
    expect(result.toLowerCase()).toMatch(/50[\s]?k/);
  });

  it("compact mode does not abbreviate numbers below 1000", () => {
    const result = formatINR(500, { compact: true });
    expect(result).toContain("500");
  });

  it("non-compact large number shows full amount", () => {
    const result = formatINR(1500000);
    expect(result).toContain("15,00,000");
  });
});

describe("formatPercent", () => {
  it("formats 0 as 0%", () => {
    expect(formatPercent(0)).toBe("0%");
  });

  it("formats 100 as 100%", () => {
    expect(formatPercent(100)).toBe("100%");
  });

  it("formats with 2 decimal places", () => {
    expect(formatPercent(33.333, 2)).toBe("33.33%");
  });

  it("rounds up with 0 decimal places", () => {
    expect(formatPercent(66.7, 0)).toBe("67%");
  });
});

describe("monthLabel", () => {
  it("converts YYYY-MM to human-readable month name and year", () => {
    const label = monthLabel("2026-06");
    expect(label).toContain("June");
    expect(label).toContain("2026");
  });

  it("handles January correctly", () => {
    const label = monthLabel("2026-01");
    expect(label).toContain("January");
  });

  it("handles December correctly", () => {
    const label = monthLabel("2025-12");
    expect(label).toContain("December");
    expect(label).toContain("2025");
  });
});

describe("currentMonth", () => {
  it("returns a string in YYYY-MM format", () => {
    const month = currentMonth();
    expect(month).toMatch(/^\d{4}-\d{2}$/);
  });

  it("returns the actual current month", () => {
    const now = new Date();
    const expected = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    expect(currentMonth()).toBe(expected);
  });
});

describe("daysInMonth", () => {
  it("returns 31 for January", () => {
    expect(daysInMonth("2026-01")).toBe(31);
  });

  it("returns 28 for February in non-leap year", () => {
    expect(daysInMonth("2025-02")).toBe(28);
  });

  it("returns 29 for February in leap year", () => {
    expect(daysInMonth("2024-02")).toBe(29);
  });

  it("returns 30 for April", () => {
    expect(daysInMonth("2026-04")).toBe(30);
  });

  it("returns 31 for December", () => {
    expect(daysInMonth("2026-12")).toBe(31);
  });
});

describe("dayOfMonth", () => {
  it("returns 0 for a future month", () => {
    // A month well in the future
    const futureMonth = "2099-12";
    expect(dayOfMonth(futureMonth)).toBe(0);
  });

  it("returns full days for a past month", () => {
    // Jan 2025 is already over
    const result = dayOfMonth("2025-01");
    expect(result).toBe(31);
  });
});

// ─── Streak Utils ─────────────────────────────────────────────────────────────

import {
  calculateLoggingStreak,
  calculateBudgetStreak,
  generateHeatmapData,
} from "@/utils/streakUtils";

describe("calculateLoggingStreak", () => {
  it("returns 0 for empty expenses array", () => {
    expect(calculateLoggingStreak([])).toBe(0);
  });

  it("returns 1 for single expense today", () => {
    const today = new Date().toISOString().slice(0, 10);
    const expenses = [{ date: today, amount: 100, categoryId: "c1" }] as Pick<import("@/types").Expense, "date" | "amount" | "categoryId">[];
    expect(calculateLoggingStreak(expenses as import("@/types").Expense[])).toBeGreaterThanOrEqual(1);
  });

  it("returns 0 when most recent expense was 2+ days ago", () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
      .toISOString()
      .slice(0, 10);
    const expenses = [{ date: threeDaysAgo, amount: 50, categoryId: "c1" }] as Pick<import("@/types").Expense, "date" | "amount" | "categoryId">[];
    expect(calculateLoggingStreak(expenses as import("@/types").Expense[])).toBe(0);
  });

  it("counts consecutive days correctly", () => {
    const today = new Date();
    const todayStr = today.toISOString().slice(0, 10);
    const yesterdayStr = new Date(today.getTime() - 86400000).toISOString().slice(0, 10);
    const dayBeforeStr = new Date(today.getTime() - 2 * 86400000).toISOString().slice(0, 10);

    const expenses = [
      { date: todayStr, amount: 100, categoryId: "c1" },
      { date: yesterdayStr, amount: 200, categoryId: "c2" },
      { date: dayBeforeStr, amount: 50, categoryId: "c1" },
    ] as Pick<import("@/types").Expense, "date" | "amount" | "categoryId">[];

    expect(calculateLoggingStreak(expenses as import("@/types").Expense[])).toBe(3);
  });
});

describe("calculateBudgetStreak", () => {
  it("returns 0 when no budgets exist", () => {
    expect(calculateBudgetStreak({}, [])).toBe(0);
  });

  it("returns 1 when current month is under budget", () => {
    const month = "2026-06";
    const budgets = { [month]: { id: "b1", month, income: 50000, categories: [] } } as Record<string, import("@/types").MonthlyBudget>;
    const expenses = [{ id: "e1", amount: 30000, date: "2026-06-15", month, categoryId: "c1", note: "" }] as import("@/types").Expense[];

    expect(calculateBudgetStreak(budgets, expenses)).toBe(1);
  });

  it("returns 0 when current month is over budget", () => {
    const month = "2026-06";
    const budgets = { [month]: { id: "b1", month, income: 10000, categories: [] } } as Record<string, import("@/types").MonthlyBudget>;
    const expenses = [{ id: "e1", amount: 15000, date: "2026-06-15", month, categoryId: "c1", note: "" }] as import("@/types").Expense[];

    expect(calculateBudgetStreak(budgets, expenses)).toBe(0);
  });
});

describe("generateHeatmapData", () => {
  it("returns an array of date-count pairs", () => {
    const result = generateHeatmapData([], 7);
    expect(Array.isArray(result)).toBe(true);
    expect(result.length).toBe(7);
    result.forEach((item) => {
      expect(item).toHaveProperty("date");
      expect(item).toHaveProperty("count");
    });
  });

  it("counts expenses per date correctly", () => {
    const today = new Date().toISOString().slice(0, 10);
    const expenses = [
      { date: today, amount: 100, categoryId: "c1", id: "e1", note: "", month: today.slice(0, 7) },
      { date: today, amount: 200, categoryId: "c2", id: "e2", note: "", month: today.slice(0, 7) },
    ] as import("@/types").Expense[];

    const result = generateHeatmapData(expenses, 7);
    const todayEntry = result.find((r) => r.date === today);
    expect(todayEntry?.count).toBe(2);
  });
});
