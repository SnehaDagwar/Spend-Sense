/**
 * Component tests for the ExpenseTracker page.
 *
 * Verifies: form elements render, category selection, empty state,
 * expense list rendering, and add expense action calls.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockAddExpense = vi.fn();
const mockDeleteExpense = vi.fn();
const mockUpdateExpense = vi.fn();

vi.mock("@/store/useAppStore", () => ({
  useAppStore: vi.fn(),
  useActiveBudget: vi.fn(),
  useMonthExpenses: vi.fn(),
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/components/ui/CategoryIcon", () => ({
  CategoryIcon: ({ name }: { name: string }) => <span data-testid={`icon-${name}`}>{name}</span>,
}));

import { useAppStore, useActiveBudget, useMonthExpenses } from "@/store/useAppStore";
import ExpenseTracker from "@/pages/ExpenseTracker";
import { toast } from "sonner";

const MOCK_CATEGORIES = [
  { id: "cat-food", name: "Food", icon: "Utensils", color: "#FF6B6B", planned: 10000, actual: 6000 },
  { id: "cat-transport", name: "Transport", icon: "Car", color: "#6B8EFF", planned: 5000, actual: 2000 },
];

const MOCK_EXPENSES = [
  { id: "e1", amount: 500, categoryId: "cat-food", date: "2026-06-15", note: "Lunch at office", month: "2026-06" },
  { id: "e2", amount: 120, categoryId: "cat-transport", date: "2026-06-14", note: "Cab fare", month: "2026-06" },
];

function setupMocks({
  expenses = MOCK_EXPENSES,
  categories = MOCK_CATEGORIES,
}: {
  expenses?: any[];
  categories?: any[];
} = {}) {
  vi.mocked(useActiveBudget).mockReturnValue({
    id: "b1",
    month: "2026-06",
    income: 50000,
    categories,
  } as any);
  vi.mocked(useMonthExpenses).mockReturnValue(expenses as any);
  vi.mocked(useAppStore).mockReturnValue({
    addExpense: mockAddExpense,
    deleteExpense: mockDeleteExpense,
    updateExpense: mockUpdateExpense,
    settings: { userType: "Individual" },
    familyMembers: [],
  } as any);
}

function renderTracker() {
  return render(
    <MemoryRouter>
      <ExpenseTracker />
    </MemoryRouter>
  );
}

// ─── Tests ─────────────────────────────────────────────────────────────────────

describe("ExpenseTracker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupMocks();
  });

  it("renders the add expense form", () => {
    renderTracker();
    expect(screen.getByText(/log an expense/i)).toBeInTheDocument();
  });

  it("renders all category buttons in the form", () => {
    renderTracker();
    // 'Food' appears in both category button and status section
    expect(screen.getAllByText("Food").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Transport").length).toBeGreaterThan(0);
  });

  it("renders amount input", () => {
    renderTracker();
    const amountInput = screen.getByPlaceholderText("0");
    expect(amountInput).toBeInTheDocument();
    expect(amountInput).toHaveAttribute("type", "number");
  });

  it("renders note input", () => {
    renderTracker();
    const noteInput = screen.getByPlaceholderText("optional");
    expect(noteInput).toBeInTheDocument();
  });

  it("renders the Add Expense button", () => {
    renderTracker();
    expect(screen.getByRole("button", { name: /add expense/i })).toBeInTheDocument();
  });

  it("shows existing expenses in the list", () => {
    renderTracker();
    expect(screen.getByText("Lunch at office")).toBeInTheDocument();
    expect(screen.getByText("Cab fare")).toBeInTheDocument();
  });

  it("shows empty state when there are no expenses", () => {
    setupMocks({ expenses: [] });
    renderTracker();
    expect(screen.getByText(/no expenses yet/i)).toBeInTheDocument();
  });

  it("does not call addExpense when amount is empty", () => {
    renderTracker();
    const addBtn = screen.getByRole("button", { name: /add expense/i });
    fireEvent.click(addBtn);
    expect(mockAddExpense).not.toHaveBeenCalled();
    expect(toast.error).toHaveBeenCalledWith("Enter a valid amount");
  });

  it("calls addExpense with correct data when form is filled", () => {
    renderTracker();

    const amountInput = screen.getByPlaceholderText("0");
    const noteInput = screen.getByPlaceholderText("optional");

    fireEvent.change(amountInput, { target: { value: "450" } });
    fireEvent.change(noteInput, { target: { value: "Team lunch" } });

    const addBtn = screen.getByRole("button", { name: /add expense/i });
    fireEvent.click(addBtn);

    expect(mockAddExpense).toHaveBeenCalledWith(
      expect.objectContaining({
        amount: 450,
        note: "Team lunch",
      })
    );
    expect(toast.success).toHaveBeenCalledWith("Expense logged");
  });

  it("clears form after successful submission", () => {
    renderTracker();

    const amountInput = screen.getByPlaceholderText("0");
    fireEvent.change(amountInput, { target: { value: "300" } });
    const addBtn = screen.getByRole("button", { name: /add expense/i });
    fireEvent.click(addBtn);

    expect(amountInput).toHaveValue(null); // cleared
  });

  it("renders category status progress section", () => {
    renderTracker();
    expect(screen.getByText(/category status/i)).toBeInTheDocument();
  });

  it("renders All filter button in the list", () => {
    renderTracker();
    expect(screen.getByRole("button", { name: /^all$/i })).toBeInTheDocument();
  });

  it("renders search input for filtering expenses", () => {
    renderTracker();
    const searchInput = screen.getByPlaceholderText(/search notes or categories/i);
    expect(searchInput).toBeInTheDocument();
  });

  it("does not show family fields for Individual user", () => {
    renderTracker();
    expect(screen.queryByText(/Paid By/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Split With/i)).not.toBeInTheDocument();
  });

  it("shows family fields when userType is Family and members exist", () => {
    vi.mocked(useAppStore).mockReturnValue({
      addExpense: mockAddExpense,
      deleteExpense: mockDeleteExpense,
      updateExpense: mockUpdateExpense,
      settings: { userType: "Family" },
      familyMembers: [{ id: "m1", name: "Sneha" }, { id: "m2", name: "Megha" }],
    } as any);

    renderTracker();
    expect(screen.getByText(/paid by/i)).toBeInTheDocument();
    expect(screen.getByText(/split with/i)).toBeInTheDocument();
  });
});
