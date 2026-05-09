import { useMemo } from "react";
import { useAppStore, useActiveBudget, useMonthExpenses } from "@/store/useAppStore";
import { computeStats } from "@/engine/predictionEngine";
import { generateInsights } from "@/engine/insightEngine";
import { StatCard } from "@/components/ui/stat-card";
import { VelocityRing } from "@/components/ui/velocity-ring";
import { formatINR, formatPercent } from "@/utils/formatters";
import { Wallet, TrendingDown, PiggyBank, Receipt, ArrowUpRight, Sparkles } from "lucide-react";
import { BarChart, Bar, ResponsiveContainer, XAxis, Tooltip, Cell } from "recharts";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { CategoryIcon } from "@/components/ui/CategoryIcon";

export default function Dashboard() {
  const budget = useActiveBudget();
  const expenses = useMonthExpenses();
  const settings = useAppStore((s) => s.settings);
  const { userName, monthlySavingTarget } = settings.profile;
  const userType = settings.userType;
  
  const hourlyWage = useAppStore((s) => s.hourlyWage);
  const allExpenses = useAppStore((s) => s.expenses);
  const activeMonth = useAppStore((s) => s.activeMonth);

  const stats = useMemo(() => computeStats(budget, expenses), [budget, expenses]);
  
  // Profile specific context
  const profileContext = useMemo(() => {
    switch (userType) {
      case "Student":
        return { label: "Daily Spending Alert", value: formatINR(stats.income / stats.totalDays), desc: "Suggested max per day" };
      case "Freelancer":
        return { label: "Stability Score", value: "85%", desc: "Based on income frequency" };
      case "Family":
        return { label: "Shared Goal Progress", value: formatINR(stats.savings), desc: "Total family savings" };
      case "Professional":
        return { label: "Investment Potential", value: formatINR(stats.income * 0.15), desc: "Suggested for portfolio" };
      default:
        return null;
    }
  }, [userType, stats]);

  const insights = useMemo(() => {
    const prevMonth = (() => {
      const [y, m] = activeMonth.split("-").map(Number);
      const d = new Date(y, m - 2, 1);
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    })();
    const prev = allExpenses.filter((e) => e.month === prevMonth);
    return generateInsights(stats, expenses, hourlyWage, prev).slice(0, 3);
  }, [stats, expenses, hourlyWage, allExpenses, activeMonth]);

  // Last 7 days bar
  const last7 = useMemo(() => {
    const days = [...Array(7)].map((_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - i));
      const iso = d.toISOString().slice(0, 10);
      const total = expenses.filter((e) => e.date === iso).reduce((s, e) => s + e.amount, 0);
      return { day: d.toLocaleDateString("en-IN", { weekday: "short" }), value: total };
    });
    return days;
  }, [expenses]);

  const usagePct = stats.totalPlanned > 0 ? (stats.totalActual / stats.totalPlanned) * 100 : 0;
  const max7 = Math.max(...last7.map((d) => d.value), 1);

  const insightTone: Record<string, string> = {
    warning: "from-destructive/10 to-warning/10 border-destructive/30",
    success: "from-success/10 to-accent/10 border-success/30",
    tip: "from-primary/10 to-primary-glow/10 border-primary/30",
    prediction: "from-accent/10 to-primary/10 border-accent/30",
  };

  return (
    <div className="space-y-6 md:space-y-8 animate-fade-in">
      {/* Welcome Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <motion.h1 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-2xl md:text-3xl font-display font-bold tracking-tight"
          >
            Hi {userName}! <span className="inline-block animate-wave cursor-default">👋</span>
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="text-muted-foreground text-sm md:text-base flex items-center gap-2"
          >
            Welcome back to your <span className="bg-primary/10 text-primary px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider">{userType}</span> dashboard.
          </motion.p>
        </div>
        
        {profileContext && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="hidden sm:flex items-center gap-3 bg-white/50 border border-white/20 p-3 rounded-2xl shadow-sm"
          >
            <div className="bg-primary/10 p-2 rounded-xl">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div>
              <div className="text-[10px] uppercase font-bold text-muted-foreground leading-none mb-1">{profileContext.label}</div>
              <div className="flex items-baseline gap-1.5">
                <span className="font-bold text-sm">{profileContext.value}</span>
                <span className="text-[10px] text-muted-foreground">{profileContext.desc}</span>
              </div>
            </div>
          </motion.div>
        )}
      </div>


      {/* Stats grid */}
      <div className="grid gap-4 md:gap-5 grid-cols-2 lg:grid-cols-4">
        <StatCard label="Income" value={formatINR(stats.income)} sub={`for ${stats.totalDays} days`} icon={<Wallet className="h-5 w-5" />} accent="primary" delay={0} />
        <StatCard label="Spent" value={formatINR(stats.totalActual)} sub={`${formatPercent(usagePct)} of budget`} icon={<Receipt className="h-5 w-5" />} accent="warm" delay={0.05} />
        <StatCard label="Remaining" value={formatINR(stats.totalRemaining)} sub={`${stats.daysRemaining} days left`} icon={<TrendingDown className="h-5 w-5" />} accent="accent" delay={0.1} />
        <StatCard label="Savings rate" value={formatPercent(stats.savingsRate, 1)} sub={`${formatINR(stats.savings)} saved`} icon={<PiggyBank className="h-5 w-5" />} accent="success" delay={0.15} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Velocity & projection */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6 lg:col-span-1 flex flex-col items-center text-center">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Spend velocity</div>
          <div className="mt-4"><VelocityRing value={usagePct} /></div>
          <div className="mt-5 w-full space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Projected EOM</span>
              <span className="font-semibold">{formatINR(stats.projectedTotal)}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Projected savings</span>
              <span className={`font-semibold ${stats.projectedSavings < 0 ? "text-destructive" : "text-success"}`}>
                {formatINR(stats.projectedSavings)}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Insights preview */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-lg font-bold flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" /> Top insights
            </h2>
            <Link to="/insights"><Button variant="ghost" size="sm" className="gap-1">View all <ArrowUpRight className="h-4 w-4" /></Button></Link>
          </div>
          <div className="space-y-3">
            {insights.length === 0 && (
              <div className="glass-card p-6 text-sm text-muted-foreground">Add a few expenses to unlock insights.</div>
            )}
            {insights.map((i, idx) => (
              <motion.div
                key={i.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + idx * 0.06 }}
                className={`rounded-2xl border bg-gradient-to-br p-4 ${insightTone[i.type]}`}
              >
                <div className="font-semibold text-sm">{i.title}</div>
                <div className="text-sm text-muted-foreground mt-1">{i.message}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Last 7 days + categories */}
      <div className="grid gap-6 lg:grid-cols-3">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-6 lg:col-span-1">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-bold">Last 7 days</h3>
            <span className="text-xs text-muted-foreground">{formatINR(last7.reduce((s, d) => s + d.value, 0))}</span>
          </div>
          <div className="h-40">
            <ResponsiveContainer>
              <BarChart data={last7} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip cursor={{ fill: "hsl(var(--muted))" }} contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))", fontSize: 12 }} formatter={(v: number) => formatINR(v)} />
                <Bar dataKey="value" radius={[8, 8, 4, 4]}>
                  {last7.map((d, i) => (
                    <Cell key={i} fill={d.value >= max7 * 0.8 ? "hsl(var(--destructive))" : "url(#barGrad)"} />
                  ))}
                </Bar>
                <defs>
                  <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(var(--primary))" />
                    <stop offset="100%" stopColor="hsl(var(--primary-glow))" stopOpacity={0.5} />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }} className="glass-card p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-bold">Category progress</h3>
            <Link to="/budget"><Button variant="ghost" size="sm">Manage</Button></Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {stats.byCategory.slice(0, 6).map((c) => (
              <div key={c.categoryId} className="rounded-xl border border-border/60 p-3 hover:bg-muted/40 transition-colors">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <CategoryIcon name={c.icon} className="h-4 w-4" />
                    <span className="font-medium text-sm">{c.name}</span>
                  </div>
                  <span className="text-xs font-semibold tabular-nums">
                    {formatINR(c.actual, { compact: true })} <span className="text-muted-foreground">/ {formatINR(c.planned, { compact: true })}</span>
                  </span>
                </div>
                <Progress
                  value={Math.min(100, c.percentUsed)}
                  className="h-2"
                  style={{
                    // @ts-expect-error inline css var
                    "--progress-foreground": c.percentUsed >= 100 ? "hsl(var(--destructive))" : c.percentUsed >= 80 ? "hsl(var(--warning))" : c.color,
                  }}
                />
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
