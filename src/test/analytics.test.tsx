import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Analytics from "../pages/Analytics";
import { useActiveBudget, useMonthExpenses } from "@/store/useAppStore";

// Mock the Zustand selectors
vi.mock("@/store/useAppStore", () => ({
  useActiveBudget: vi.fn(),
  useMonthExpenses: vi.fn(),
  useAppStore: () => ({
    activeMonth: "2026-05",
  }),
}));

interface WithChildren { children: React.ReactNode; className?: string; style?: React.CSSProperties }
interface TabProps extends WithChildren { defaultValue?: string; activeTab?: string; setActiveTab?: (v: string) => void }
interface TabTriggerProps extends WithChildren { value: string; activeTab?: string; setActiveTab?: (v: string) => void; className?: string }
interface TabContentProps extends WithChildren { value: string; activeTab?: string; className?: string }

// Mock Recharts to avoid layout issues in JSDOM environment
vi.mock("recharts", () => {
  return {
    ResponsiveContainer: ({ children }: WithChildren) => <div style={{ width: 400, height: 300 }}>{children}</div>,
    PieChart: ({ children }: WithChildren) => <svg>{children}</svg>,
    Pie: () => <g></g>,
    Cell: () => <path></path>,
    BarChart: ({ children }: WithChildren) => <svg>{children}</svg>,
    Bar: () => <rect></rect>,
    XAxis: () => <g></g>,
    YAxis: () => <g></g>,
    CartesianGrid: () => <g></g>,
    Legend: () => <g></g>,
    LineChart: ({ children }: WithChildren) => <svg>{children}</svg>,
    Line: () => <path></path>,
    AreaChart: ({ children }: WithChildren) => <svg>{children}</svg>,
    Area: () => <path></path>,
    ReferenceLine: () => <line></line>,
    Tooltip: () => <div></div>,
  };
});

// Mock Framer Motion
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock Tabs component to handle tabs switching directly in tests
vi.mock("@/components/ui/tabs", () => {
  return {
    Tabs: ({ children, defaultValue, className }: TabProps) => {
      const [active, setActive] = React.useState(defaultValue);
      return (
        <div className={className} data-active-tab={active}>
          {React.Children.map(children, (child) => {
            if (React.isValidElement(child)) {
              return React.cloneElement(child as React.ReactElement<Record<string, unknown>>, { activeTab: active, setActiveTab: setActive });
            }
            return child;
          })}
        </div>
      );
    },
    TabsList: ({ children, activeTab, setActiveTab, className }: TabProps & { activeTab?: string; setActiveTab?: (v: string) => void }) => (
      <div className={className} role="tablist">
        {React.Children.map(children, (child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child as React.ReactElement<Record<string, unknown>>, { activeTab, setActiveTab });
          }
          return child;
        })}
      </div>
    ),
    TabsTrigger: ({ children, value, activeTab, setActiveTab, className }: TabTriggerProps) => (
      <button
        role="tab"
        className={`${className} ${activeTab === value ? "active" : ""}`}
        onClick={() => setActiveTab?.(value)}
      >
        {children}
      </button>
    ),
    TabsContent: ({ children, value, activeTab, className }: TabContentProps) => {
      if (activeTab !== value) return null;
      return <div className={className}>{children}</div>;
    },
  };
});

describe("Analytics Component Tests", () => {
  const mockBudget = {
    id: "b1",
    month: "2026-05",
    income: 50000,
    categories: [
      { id: "c1", name: "Food", icon: "Utensils", color: "#FF0000", planned: 5000, isCustom: false },
      { id: "c2", name: "Utilities", icon: "Bolt", color: "#0000FF", planned: 2000, isCustom: false },
    ],
  };

  const mockExpenses = [
    { id: "e1", categoryId: "c1", amount: 1500, date: "2026-05-05", note: "Grocery", month: "2026-05" },
    { id: "e2", categoryId: "c1", amount: 500, date: "2026-05-10", note: "Restaurant", month: "2026-05" },
    { id: "e3", categoryId: "c2", amount: 2000, date: "2026-05-12", note: "Electricity", month: "2026-05" },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useActiveBudget).mockReturnValue(mockBudget);
    vi.mocked(useMonthExpenses).mockReturnValue(mockExpenses);
  });

  it("renders layout tabs", () => {
    render(<Analytics />);
    
    expect(screen.getByRole("tab", { name: /Overview/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Comparison/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Trends/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Prediction/i })).toBeInTheDocument();
  });

  it("displays correct category distribution totals in Overview", () => {
    render(<Analytics />);
    
    // Overview tab should render headers
    expect(screen.getByText("Where your money went")).toBeInTheDocument();
    expect(screen.getByText("Top categories")).toBeInTheDocument();

    // Verify category list rendering & calculation totals
    // Utilities: actual = 2000, percentage: 2000 / (2000 + 2000) = 50%
    // Food: actual = 2000, percentage: 50%
    expect(screen.getByText("Utilities")).toBeInTheDocument();
    expect(screen.getByText("Food")).toBeInTheDocument();
    
    // Verify cumulative display (Recharts mock doesn't crash)
    const elements = screen.getAllByText(/50%/);
    expect(elements.length).toBeGreaterThan(0);
  });

  it("switches tabs correctly to display comparison metrics", () => {
    render(<Analytics />);
    
    const comparisonTab = screen.getByRole("tab", { name: /Comparison/i });
    fireEvent.click(comparisonTab);

    expect(screen.getByText("Planned vs Actual")).toBeInTheDocument();
  });

  it("switches to trends and predictions", () => {
    render(<Analytics />);
    
    const trendsTab = screen.getByRole("tab", { name: /Trends/i });
    fireEvent.click(trendsTab);
    expect(screen.getByText("Daily cumulative spending")).toBeInTheDocument();
    
    const predTab = screen.getByRole("tab", { name: /Prediction/i });
    fireEvent.click(predTab);
    expect(screen.getByText("Month-end projection")).toBeInTheDocument();
    expect(screen.getByText("Daily average")).toBeInTheDocument();
  });
});
