import { NavLink, useLocation } from "react-router-dom";
import { 
  LayoutDashboard, 
  Wallet, 
  Receipt, 
  BarChart3, 
  Sparkles, 
  FileText, 
  Settings, 
  Target,
  Lightbulb,
  Flame
} from "lucide-react";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarHeader, SidebarFooter, useSidebar,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";

const items = [
  { title: "Dashboard", url: "/", icon: LayoutDashboard },
  { title: "Budget", url: "/budget", icon: Wallet },
  { title: "Tracker", url: "/tracker", icon: Receipt },
  { title: "Analytics", url: "/analytics", icon: BarChart3 },
  { title: "Insights", url: "/insights", icon: Sparkles },
  { title: "Goals", url: "/goals", icon: Target },
  { title: "Streaks", url: "/streaks", icon: Flame },
  { title: "Reports", url: "/reports", icon: FileText },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const { pathname } = useLocation();
  const isActive = (path: string) => pathname === path;

  return (
    <Sidebar 
      collapsible="icon" 
      className="border-r border-sidebar-border bg-gradient-to-b from-white to-secondary/30"
    >
      <SidebarHeader className="px-4 py-6">
        <NavLink to="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-primary shadow-glow group-hover:scale-105 transition-transform duration-300">
            <Sparkles className="h-5 w-5 text-primary-foreground" />
          </div>
          {!collapsed && (
            <div className="leading-tight">
              <div className="font-display text-xl font-bold gradient-text tracking-tight">Spend Sense</div>
              <div className="text-[10px] text-muted-foreground font-semibold tracking-[0.1em] uppercase opacity-80">Understand your spending</div>
            </div>
          )}
        </NavLink>
      </SidebarHeader>

      <SidebarContent className="px-3">
        <SidebarGroup>
          {!collapsed && (
            <SidebarGroupLabel className="px-2 mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/60">
              Workspace
            </SidebarGroupLabel>
          )}
          <SidebarGroupContent>
            <SidebarMenu className="gap-1.5">
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton 
                    asChild 
                    isActive={isActive(item.url)} 
                    className={cn(
                      "group h-11 rounded-xl transition-all duration-200 px-3",
                      "data-[active=true]:bg-gradient-primary data-[active=true]:text-primary-foreground data-[active=true]:shadow-glow-sm",
                      "hover:translate-x-1 hover:bg-primary/5 active:scale-95"
                    )}
                  >
                    <NavLink to={item.url} className="flex items-center gap-3 w-full relative">
                      {isActive(item.url) && !collapsed && (
                        <div className="absolute -left-3 top-1/2 -translate-y-1/2 w-1 h-6 bg-white rounded-r-full" />
                      )}
                      <item.icon className={cn(
                        "h-[18px] w-[18px] shrink-0 transition-colors duration-300",
                        isActive(item.url) ? "text-primary-foreground" : "text-primary group-hover:text-primary-glow"
                      )} />
                      {!collapsed && <span className="font-semibold text-sm tracking-tight">{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="px-3 pb-6 gap-4">
        {!collapsed && (
          <div className="relative group overflow-hidden rounded-2xl bg-gradient-to-br from-primary via-primary to-primary-glow p-4 text-white shadow-lg">
            <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-white/10 blur-2xl group-hover:bg-white/20 transition-colors" />
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded-lg bg-white/20">
                <Lightbulb className="h-3.5 w-3.5" />
              </div>
              <span className="text-[10px] font-bold tracking-widest uppercase opacity-80">Pro Tip</span>
            </div>
            <div className="text-sm font-medium leading-snug">Track more - Guess Less</div>
          </div>
        )}
        
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton 
              asChild 
              isActive={isActive("/settings")}
              className={cn(
                "group h-11 rounded-xl transition-all duration-200 px-3",
                "data-[active=true]:bg-gradient-primary data-[active=true]:text-primary-foreground data-[active=true]:shadow-glow-sm",
                "hover:translate-x-1 hover:bg-primary/5"
              )}
            >
              <NavLink to="/settings" className="flex items-center gap-3">
                <Settings className={cn(
                  "h-[18px] w-[18px] shrink-0 transition-colors duration-300",
                  isActive("/settings") ? "text-primary-foreground" : "text-primary group-hover:text-primary-glow"
                )} />
                {!collapsed && <span className="font-semibold text-sm tracking-tight">Settings</span>}
              </NavLink>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
