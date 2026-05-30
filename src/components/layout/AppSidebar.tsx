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
  Flame,
  Users,
  Handshake,
  Heart
} from "lucide-react";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarHeader, SidebarFooter, useSidebar,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/useAppStore";

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
  const { settings } = useAppStore();
  const isFamily = settings.userType === "Family";

  const familyItems = [
    { title: "Family Wallet", url: "/family", icon: Heart },
    { title: "Members", url: "/family/members", icon: Users },
    { title: "Split & Settle", url: "/family/settle", icon: Handshake },
  ];
  return (
    <Sidebar 
      collapsible="icon" 
      className="border-r border-white/40 bg-white/40 backdrop-blur-2xl"
    >
      <SidebarHeader className="px-4 py-6">
        <NavLink to="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-primary shadow-glow group-hover:scale-105 transition-transform duration-300">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          {!collapsed && (
            <div className="leading-tight">
              <div className="font-display text-xl font-bold bg-clip-text text-transparent bg-gradient-primary tracking-tight">Spend Sense</div>
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
                      "group h-11 rounded-full transition-all duration-200 px-4",
                      "data-[active=true]:bg-primary data-[active=true]:text-white data-[active=true]:shadow-sm-soft",
                      "hover:translate-x-1 hover:bg-primary/10 active:scale-95 text-foreground/80"
                    )}
                  >
                    <NavLink to={item.url} className="flex items-center gap-3 w-full relative">
                      {isActive(item.url) && !collapsed && (
                        <div className="absolute -left-3 top-1/2 -translate-y-1/2 w-1 h-6 bg-white rounded-r-full" />
                      )}
                      <item.icon className={cn(
                        "h-[18px] w-[18px] shrink-0 transition-colors duration-300",
                        isActive(item.url) ? "text-white" : "text-muted-foreground group-hover:text-primary"
                      )} />
                      {!collapsed && <span className={cn("font-medium text-sm tracking-tight", isActive(item.url) ? "font-bold" : "")}>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}

              {isFamily && (
                <>
                  <SidebarGroupLabel className="px-2 mt-4 mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/60">
                    Family
                  </SidebarGroupLabel>
                  {familyItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton 
                        asChild 
                        isActive={isActive(item.url)} 
                        className={cn(
                          "group h-11 rounded-full transition-all duration-200 px-4 text-secondary-foreground",
                          "data-[active=true]:bg-secondary/20 data-[active=true]:text-secondary",
                          "hover:translate-x-1 hover:bg-secondary/10 text-foreground/80"
                        )}
                      >
                        <NavLink to={item.url} className="flex items-center gap-3 w-full relative">
                          {isActive(item.url) && !collapsed && (
                            <div className="absolute -left-3 top-1/2 -translate-y-1/2 w-1 h-6 bg-secondary rounded-r-full" />
                          )}
                          <item.icon className={cn(
                            "h-[18px] w-[18px] shrink-0 transition-colors duration-300",
                            isActive(item.url) ? "text-secondary" : "text-muted-foreground group-hover:text-secondary"
                          )} />
                          {!collapsed && <span className={cn("font-medium text-sm tracking-tight", isActive(item.url) ? "font-bold" : "")}>{item.title}</span>}
                        </NavLink>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </>
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="px-3 pb-6 gap-4">
        {!collapsed && (
          <div className="relative group overflow-hidden rounded-2xl bg-gradient-to-br from-orange-400 to-orange-500 p-5 text-white shadow-md">
            <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-white/20 blur-2xl group-hover:bg-white/30 transition-colors" />
            <div className="flex flex-col gap-2 relative z-10">
              <span className="text-xs font-bold tracking-widest uppercase text-white/90">Track More , Guess Less</span>
              <div className="text-sm font-semibold leading-snug">Track More, Guess less</div>
            </div>
          </div>
        )}
        
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton 
              asChild 
              isActive={isActive("/settings")}
              className={cn(
                "group h-11 rounded-full transition-all duration-200 px-4",
                "data-[active=true]:bg-primary data-[active=true]:text-white data-[active=true]:shadow-sm-soft",
                "hover:translate-x-1 hover:bg-primary/10 text-foreground/80"
              )}
            >
              <NavLink to="/settings" className="flex items-center gap-3">
                <Settings className={cn(
                  "h-[18px] w-[18px] shrink-0 transition-colors duration-300",
                  isActive("/settings") ? "text-white" : "text-muted-foreground group-hover:text-primary"
                )} />
                {!collapsed && <span className={cn("font-medium text-sm tracking-tight", isActive("/settings") ? "font-bold" : "")}>Settings</span>}
              </NavLink>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
