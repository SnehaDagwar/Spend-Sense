import { Outlet, useLocation } from "react-router-dom";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "./AppSidebar";
import { useAppStore } from "@/store/useAppStore";
import { monthLabel } from "@/utils/formatters";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { useState } from "react";
import { QuickAddDialog } from "@/components/tracker/QuickAddDialog";
import { AIInsightWidget } from "@/components/insights/AIInsightWidget";

const TITLES: Record<string, { title: string; sub: string }> = {
  "/": { title: "Dashboard", sub: "Your money at a glance" },
  "/budget": { title: "Budget Setup", sub: "Plan your month" },
  "/tracker": { title: "Expense Tracker", sub: "Log every rupee" },
  "/analytics": { title: "Analytics", sub: "Patterns in your spending" },
  "/insights": { title: "Insights", sub: "Smart suggestions, just for you" },
  "/reports": { title: "Reports", sub: "Export and share" },
};

export default function AppLayout() {
  const { pathname } = useLocation();
  const activeMonth = useAppStore((s) => s.activeMonth);
  const meta = TITLES[pathname] ?? { title: "Spend Sense", sub: "" };
  const [quickOpen, setQuickOpen] = useState(false);

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="sticky top-0 z-30 h-16 flex items-center gap-4 border-b border-border/60 bg-background/80 backdrop-blur-xl px-4 md:px-6">
            <SidebarTrigger className="rounded-lg" />
            <div className="min-w-0 flex-1">
              <h1 className="font-display text-lg md:text-xl font-bold leading-none truncate">{meta.title}</h1>
              <p className="text-xs text-muted-foreground mt-0.5 truncate">{meta.sub} · {monthLabel(activeMonth)}</p>
            </div>
            <Button
              onClick={() => setQuickOpen(true)}
              className="bg-gradient-primary hover:opacity-95 shadow-glow rounded-xl gap-1.5 hidden sm:inline-flex text-white"
            >
              <Plus className="h-4 w-4" /> Add expense
            </Button>
            <Button
              size="icon"
              onClick={() => setQuickOpen(true)}
              className="bg-gradient-primary hover:opacity-95 shadow-glow rounded-xl sm:hidden text-white"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </header>
          <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-[1400px] w-full mx-auto">
            <Outlet />
          </main>
        </div>
      </div>
      <QuickAddDialog open={quickOpen} onOpenChange={setQuickOpen} />
      <AIInsightWidget />
    </SidebarProvider>
  );
}
