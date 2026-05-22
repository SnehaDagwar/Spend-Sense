import { Outlet, useLocation } from "react-router-dom";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "./AppSidebar";
import { useAppStore } from "@/store/useAppStore";
import { monthLabel } from "@/utils/formatters";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { QuickAddDialog } from "@/components/tracker/QuickAddDialog";
import { AIInsightWidget } from "@/components/insights/AIInsightWidget";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

const TITLES: Record<string, { title: string; sub: string }> = {
  "/": { title: "Dashboard", sub: "Your money at a glance" },
  "/budget": { title: "Budget Setup", sub: "Plan your month" },
  "/tracker": { title: "Expense Tracker", sub: "Log every rupee" },
  "/analytics": { title: "Analytics", sub: "Patterns in your spending" },
  "/insights": { title: "Insights", sub: "Smart suggestions, just for you" },
  "/reports": { title: "Reports", sub: "Export and share" },
  "/streaks": { title: "Your Streaks", sub: "Track your consistency" },
};

export default function AppLayout() {
  const { pathname } = useLocation();
  const activeMonth = useAppStore((s) => s.activeMonth);
  const setActiveMonth = useAppStore((s) => s.setActiveMonth);
  const { settings } = useAppStore();
  const [quickOpen, setQuickOpen] = useState(false);

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="sticky top-0 z-30 h-[88px] flex items-center justify-between gap-4 bg-transparent px-6 md:px-10">
            <div className="flex items-center gap-4 flex-1">
              <SidebarTrigger className="rounded-full bg-white shadow-sm hover:bg-gray-50 md:hidden" />
              
              {/* Search Bar */}
              <div className="hidden md:flex items-center bg-white px-4 py-2.5 rounded-2xl shadow-sm border border-gray-100/50 w-full max-w-sm">
                <svg className="w-5 h-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                <input type="text" placeholder="Search..." className="bg-transparent border-none outline-none text-sm w-full placeholder:text-gray-400" />
              </div>
            </div>

            <div className="flex items-center gap-4 lg:gap-6">
              {/* Month Selector */}
              <Popover>
                <PopoverTrigger asChild>
                  <button className="hidden lg:flex items-center gap-2 text-sm font-medium text-gray-600 bg-white px-4 py-2.5 rounded-2xl shadow-sm border border-gray-100/50 hover:bg-gray-50 transition-colors">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    {monthLabel(activeMonth)}
                    <svg className="w-4 h-4 ml-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                  </button>
                </PopoverTrigger>
                <PopoverContent className="w-48 p-2" align="end">
                  <div className="flex flex-col gap-1 max-h-[300px] overflow-y-auto pr-1">
                    {Array.from({ length: 12 }).map((_, i) => {
                      const d = new Date();
                      d.setMonth(d.getMonth() - i);
                      const m = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
                      return (
                        <button
                          key={m}
                          onClick={() => setActiveMonth(m)}
                          className={`px-3 py-2 text-sm text-left rounded-lg transition-colors ${
                            activeMonth === m 
                              ? 'bg-primary/10 text-primary font-semibold' 
                              : 'hover:bg-gray-100 text-gray-700 font-medium'
                          }`}
                        >
                          {monthLabel(m)}
                        </button>
                      );
                    })}
                  </div>
                </PopoverContent>
              </Popover>

              {/* Action Icons */}
              <div className="flex items-center gap-3">
                <Link to="/insights" className="w-10 h-10 rounded-full bg-white shadow-sm border border-gray-100/50 flex items-center justify-center text-gray-500 hover:text-primary transition-colors">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
                </Link>
                <Popover>
                  <PopoverTrigger asChild>
                    <button className="w-10 h-10 rounded-full bg-white shadow-sm border border-gray-100/50 flex items-center justify-center text-gray-500 hover:text-primary transition-colors relative">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>
                      <span className="absolute top-2 right-2.5 w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></span>
                    </button>
                  </PopoverTrigger>
                  <PopoverContent align="end" className="w-80 p-0 rounded-2xl overflow-hidden shadow-xl border-white/10 glass-card">
                    <div className="bg-gradient-to-r from-primary/10 to-transparent p-4 border-b border-gray-100">
                      <h4 className="font-display font-bold text-gray-800">Notifications</h4>
                    </div>
                    <div className="p-2 space-y-1 max-h-[300px] overflow-y-auto">
                      <div className="flex items-start gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer group">
                        <div className="h-10 w-10 rounded-full bg-yellow-100 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                          <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                        </div>
                        <div>
                          <p className="font-semibold text-sm text-gray-800">Budget Warning</p>
                          <p className="text-gray-500 text-xs mt-0.5 leading-relaxed">You have reached 80% of your Dining budget this month.</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer group">
                        <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        </div>
                        <div>
                          <p className="font-semibold text-sm text-gray-800">Goal Achieved!</p>
                          <p className="text-gray-500 text-xs mt-0.5 leading-relaxed">Congratulations! You've maintained your savings streak.</p>
                        </div>
                      </div>
                    </div>
                  </PopoverContent>
                </Popover>
              </div>

              {/* Profile */}
              <DropdownMenu>
                <DropdownMenuTrigger className="outline-none">
                  <div className="hidden sm:flex items-center gap-3 bg-white pl-2 pr-4 py-1.5 rounded-full shadow-sm border border-gray-100/50 hover:bg-gray-50 transition-colors cursor-pointer">
                    <img src={settings.profile.avatar || "/avatars/girl.png"} alt="Profile" className="w-8 h-8 rounded-full bg-gray-100" />
                    <div className="flex flex-col text-left">
                      <span className="text-sm font-bold text-gray-800 leading-none">{settings.profile.userName}</span>
                      <span className="text-[10px] text-gray-400 font-medium mt-0.5">{settings.userType}</span>
                    </div>
                  </div>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuItem asChild>
                    <Link to="/settings" className="w-full cursor-pointer flex items-center">
                      Profile Settings
                    </Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Create New CTA */}
              <Button
                onClick={() => setQuickOpen(true)}
                className="bg-primary hover:bg-primary/90 text-white rounded-xl shadow-md shadow-primary/20 gap-2 h-10 px-5 hidden sm:inline-flex"
              >
                <Plus className="h-4 w-4" /> Create new
              </Button>
            </div>
          </header>
          <main className="flex-1 p-4 md:p-6 lg:p-10 lg:pt-2 w-full mx-auto">
            <Outlet />
          </main>
        </div>
      </div>
      <QuickAddDialog open={quickOpen} onOpenChange={setQuickOpen} />
      <AIInsightWidget />
    </SidebarProvider>
  );
}
