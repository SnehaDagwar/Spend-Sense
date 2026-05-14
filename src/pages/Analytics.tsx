import { useMemo } from "react";
import { useActiveBudget, useMonthExpenses } from "@/store/useAppStore";
import { computeStats, dailyCumulative } from "@/engine/predictionEngine";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend,
  AreaChart, Area, LineChart, Line, ReferenceLine,
} from "recharts";
import { formatINR } from "@/utils/formatters";
import { motion } from "framer-motion";
import { CategoryIcon } from "@/components/ui/CategoryIcon";

const tooltipStyle = { borderRadius: 12, border: "1px solid hsl(var(--border))", background: "hsl(var(--card))", fontSize: 12 };

export default function Analytics() {
  const budget = useActiveBudget();
  const expenses = useMonthExpenses();
  const stats = useMemo(() => computeStats(budget, expenses), [budget, expenses]);
  const cumulative = useMemo(() => dailyCumulative(budget, expenses), [budget, expenses]);

  const pieData = stats.byCategory.filter((c) => c.actual > 0).map((c) => ({ name: c.name, value: c.actual, color: c.color, icon: c.icon }));
  const compareData = stats.byCategory.map((c) => ({ name: c.name, planned: c.planned, actual: c.actual, color: c.color }));

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 animate-fade-in">
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-4 max-w-2xl rounded-xl bg-muted p-1 h-11">
          <TabsTrigger value="overview" className="rounded-lg data-[state=active]:bg-card data-[state=active]:shadow-md-soft">Overview</TabsTrigger>
          <TabsTrigger value="comparison" className="rounded-lg data-[state=active]:bg-card data-[state=active]:shadow-md-soft">Comparison</TabsTrigger>
          <TabsTrigger value="trends" className="rounded-lg data-[state=active]:bg-card data-[state=active]:shadow-md-soft">Trends</TabsTrigger>
          <TabsTrigger value="prediction" className="rounded-lg data-[state=active]:bg-card data-[state=active]:shadow-md-soft">Prediction</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="glass-card p-6">
            <h3 className="font-display font-bold mb-4">Where your money went</h3>
            <div className="h-80">
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={120} paddingAngle={2}>
                    {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                  </Pie>
                  <Tooltip formatter={(v: number) => formatINR(v)} contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="glass-card p-6">
            <h3 className="font-display font-bold mb-4">Top categories</h3>
            <div className="space-y-3">
              {[...pieData].sort((a, b) => b.value - a.value).slice(0, 6).map((d) => {
                const pct = (d.value / stats.totalActual) * 100;
                return (
                  <div key={d.name}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="font-medium flex items-center gap-2">
                        <CategoryIcon name={d.icon} className="h-4 w-4" />
                        {d.name}
                      </span>
                      <span className="tabular-nums">{formatINR(d.value)} <span className="text-xs text-muted-foreground">({pct.toFixed(0)}%)</span></span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.8, ease: "easeOut" }} className="h-full rounded-full" style={{ background: d.color }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="comparison" className="mt-6">
          <div className="glass-card p-6">
            <h3 className="font-display font-bold mb-4">Planned vs Actual</h3>
            <div className="h-96">
              <ResponsiveContainer>
                <BarChart data={compareData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} />
                  <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickFormatter={(v) => formatINR(v, { compact: true })} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => formatINR(v)} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="planned" name="Planned" fill="hsl(var(--muted-foreground))" radius={[6, 6, 0, 0]} fillOpacity={0.4} />
                  <Bar dataKey="actual" name="Actual" radius={[6, 6, 0, 0]}>
                    {compareData.map((d, i) => <Cell key={i} fill={d.actual > d.planned ? "hsl(var(--destructive))" : d.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="trends" className="mt-6">
          <div className="glass-card p-6">
            <h3 className="font-display font-bold mb-4">Daily cumulative spending</h3>
            <div className="h-96">
              <ResponsiveContainer>
                <LineChart data={cumulative} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="day" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickFormatter={(v) => formatINR(v, { compact: true })} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => isNaN(v) ? "—" : formatINR(v)} />
                  <ReferenceLine y={stats.totalPlanned} stroke="hsl(var(--warning))" strokeDasharray="4 4" label={{ value: "Budget", fill: "hsl(var(--warning))", fontSize: 11, position: "right" }} />
                  <Line type="monotone" dataKey="spent" stroke="hsl(var(--primary))" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="prediction" className="mt-6">
          <div className="glass-card p-6">
            <h3 className="font-display font-bold mb-1">Month-end projection</h3>
            <p className="text-sm text-muted-foreground mb-4">Based on your current pace, here's where you'll end up.</p>
            <div className="h-96">
              <ResponsiveContainer>
                <AreaChart data={cumulative} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.05} />
                    </linearGradient>
                    <linearGradient id="projGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="day" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickFormatter={(v) => formatINR(v, { compact: true })} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => isNaN(v) ? "—" : formatINR(v)} />
                  <ReferenceLine y={stats.income} stroke="hsl(var(--success))" strokeDasharray="4 4" label={{ value: "Income", fill: "hsl(var(--success))", fontSize: 11, position: "right" }} />
                  <ReferenceLine y={stats.totalPlanned} stroke="hsl(var(--warning))" strokeDasharray="4 4" label={{ value: "Budget", fill: "hsl(var(--warning))", fontSize: 11, position: "right" }} />
                  <Area type="monotone" dataKey="projected" stroke="hsl(var(--accent))" strokeWidth={2} strokeDasharray="6 4" fill="url(#projGrad)" />
                  <Area type="monotone" dataKey="spent" stroke="hsl(var(--primary))" strokeWidth={3} fill="url(#actualGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="grid gap-4 sm:grid-cols-3 mt-6">
              <div className="rounded-xl bg-muted/50 p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Projected total</div>
                <div className="font-display text-xl font-bold mt-1">{formatINR(stats.projectedTotal)}</div>
              </div>
              <div className="rounded-xl bg-muted/50 p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Daily average</div>
                <div className="font-display text-xl font-bold mt-1">{formatINR(stats.dailyAverage)}</div>
              </div>
              <div className="rounded-xl bg-muted/50 p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Projected savings</div>
                <div className={`font-display text-xl font-bold mt-1 ${stats.projectedSavings < 0 ? "text-destructive" : "text-success"}`}>{formatINR(stats.projectedSavings)}</div>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
