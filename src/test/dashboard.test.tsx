/**
 * Component tests for the Dashboard page.
 *
 * Verifies: stat cards render, links are present, and
 * user name from store settings is displayed.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { useAppStore } from "@/store/useAppStore";

// ── Mock the store ────────────────────────────────────────────────────────────
vi.mock("@/store/useAppStore", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/store/useAppStore")>();
  return {
    ...actual,
    useAppStore: vi.fn(),
    useActiveBudget: vi.fn(() => ({
      income: 50000,
      categories: [
        { id: "c1", name: "Food", planned: 10000, actual: 6000 },
        { id: "c2", name: "Transport", planned: 5000, actual: 2000 },
      ],
    })),
    useMonthExpenses: vi.fn(() => [
      { id: "e1", amount: 500, date: "2026-06-01", categoryId: "c1", note: "Lunch" },
      { id: "e2", amount: 200, date: "2026-06-05", categoryId: "c2", note: "Cab" },
    ]),
  };
});

// ── Mock the prediction engine ─────────────────────────────────────────────────
vi.mock("@/engine/predictionEngine", () => ({
  computeStats: vi.fn(() => ({
    income: 50000,
    totalActual: 8000,
    totalPlanned: 15000,
    byCategory: [],
  })),
}));

// ── Mock framer-motion to skip animation in JSDOM ────────────────────────────
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: React.ComponentPropsWithoutRef<"div">) => <div {...props}>{children}</div>,
  },
}));

import Dashboard from "@/pages/Dashboard";

interface MockStoreState {
  settings: {
    profile: {
      userName: string;
    };
  };
  savingsStreak: number;
}

function renderDashboard() {
  vi.mocked(useAppStore).mockImplementation((selector: (state: MockStoreState) => unknown) =>
    selector({
      settings: {
        profile: { userName: "Finance Ninja" },
      },
      savingsStreak: 7,
    })
  );

  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  );
}

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders without crashing", () => {
    renderDashboard();
    expect(document.body).toBeTruthy();
  });

  it("displays the user's name in the greeting", () => {
    renderDashboard();
    expect(screen.getByText(/hi, finance ninja/i)).toBeInTheDocument();
  });

  it("renders 4 stat cards", () => {
    renderDashboard();
    expect(screen.getByText("Total Monthly Budget")).toBeInTheDocument();
    expect(screen.getByText("Total Spent This Month")).toBeInTheDocument();
    expect(screen.getByText("Remaining Budget")).toBeInTheDocument();
    expect(screen.getByText("Active Savings Streak")).toBeInTheDocument();
  });

  it("renders navigation links to key pages", () => {
    renderDashboard();

    const viewAnalyticsLink = screen.getByRole("link", { name: /view analytics/i });
    const setBudgetLink = screen.getByRole("link", { name: /set budget/i });
    const logExpenseLink = screen.getByRole("link", { name: /log expense/i });

    expect(viewAnalyticsLink).toBeInTheDocument();
    expect(setBudgetLink).toBeInTheDocument();
    expect(logExpenseLink).toBeInTheDocument();
  });

  it("links to the correct routes", () => {
    renderDashboard();

    expect(screen.getByRole("link", { name: /view analytics/i })).toHaveAttribute("href", "/analytics");
    expect(screen.getByRole("link", { name: /set budget/i })).toHaveAttribute("href", "/budget");
    expect(screen.getByRole("link", { name: /log expense/i })).toHaveAttribute("href", "/tracker");
  });

  it("shows notifications panel", () => {
    renderDashboard();
    expect(screen.getByText("Notifications")).toBeInTheDocument();
  });

  it("shows formatted budget value in stat card", () => {
    renderDashboard();
    // formatINR(50000) = ₹50,000
    expect(screen.getByText(/50,000/)).toBeInTheDocument();
  });
});
