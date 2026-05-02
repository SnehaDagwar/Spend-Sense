import { useMemo, useState } from "react";
import { useAppStore, useActiveBudget } from "@/store/useAppStore";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { formatINR, monthLabel, currentMonth } from "@/utils/formatters";
import { PieChart, Pie, ResponsiveContainer, Cell, Tooltip } from "recharts";
import { Plus, Trash2, ChevronLeft, ChevronRight, Wallet } from "lucide-react";
import { motion } from "framer-motion";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { CategoryGoals } from "@/components/budget/CategoryGoals";

const shiftMonth = (m: string, by: number) => {
  const [y, mo] = m.split("-").map(Number);
  const d = new Date(y, mo - 1 + by, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
};

export default function BudgetSetup() {
  const budget = useActiveBudget();
  const { activeMonth, setActiveMonth, setIncome, setCategoryPlanned, addCategory, removeCategory, hourlyWage, setHourlyWage } = useAppStore();
  const [addOpen, setAddOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [newIcon, setNewIcon] = useState("✨");
  const [newPlanned, setNewPlanned] = useState("");

  const totalPlanned = budget.categories.reduce((s, c) => s + c.planned, 0);
  const allocPct = budget.income > 0 ? (totalPlanned / budget.income) * 100 : 0;

  const pieData = useMemo(
    () => budget.categories.filter((c) => c.planned > 0).map((c) => ({ name: c.name, value: c.planned, color: c.color, icon: c.icon })),
    [budget.categories]
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap items-center gap-3 justify-between">
        <div className="inline-flex items-center gap-1 rounded-xl border border-border/60 bg-card p-1 shadow-sm-soft">
          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => setActiveMonth(shiftMonth(activeMonth, -1))}><ChevronLeft className="h-4 w-4" /></Button>
          <div className="px-3 text-sm font-semibold min-w-[140px] text-center">{monthLabel(activeMonth)}</div>
          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => setActiveMonth(shiftMonth(activeMonth, 1))}><ChevronRight className="h-4 w-4" /></Button>
          {activeMonth !== currentMonth() && (
            <Button size="sm" variant="ghost" className="h-8" onClick={() => setActiveMonth(currentMonth())}>Today</Button>
          )}
        </div>
        <Button onClick={() => setAddOpen(true)} variant="outline" className="rounded-xl gap-1.5"><Plus className="h-4 w-4" /> Add category</Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 lg:col-span-2 space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label className="mb-2 block text-xs uppercase tracking-wider text-muted-foreground">Monthly income (₹)</Label>
              <div className="relative">
                <Wallet className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input type="number" value={budget.income} onChange={(e) => setIncome(activeMonth, parseFloat(e.target.value) || 0)} className="pl-9 text-lg font-semibold h-12" />
              </div>
            </div>
            {/* Hourly wage removed as requested */}
          </div>

          <div className="rounded-xl bg-muted/50 p-4 flex items-center justify-between">
            <div>
              <div className="text-xs text-muted-foreground uppercase tracking-wider">Total allocated</div>
              <div className="font-display text-2xl font-bold mt-1">{formatINR(totalPlanned)}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-muted-foreground uppercase tracking-wider">% of income</div>
              <div className={`font-display text-2xl font-bold mt-1 ${allocPct > 100 ? "text-destructive" : allocPct > 90 ? "text-warning" : "text-success"}`}>
                {allocPct.toFixed(0)}%
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {budget.categories.map((c) => (
              <div key={c.id} className="rounded-xl border border-border/60 p-4 hover:bg-muted/30 transition-colors">
                <div className="flex items-center gap-3 mb-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg text-xl" style={{ background: `${c.color}20` }}>{c.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold">{c.name}</div>
                    <div className="text-xs text-muted-foreground">Planned: {formatINR(c.planned)}</div>
                  </div>
                  <Input
                    type="number"
                    value={c.planned}
                    onChange={(e) => setCategoryPlanned(activeMonth, c.id, parseFloat(e.target.value) || 0)}
                    className="w-28 text-right font-semibold"
                  />
                  {c.isCustom && (
                    <Button size="icon" variant="ghost" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => removeCategory(activeMonth, c.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
                <Slider
                  value={[c.planned]}
                  max={Math.max(20000, budget.income)}
                  step={100}
                  onValueChange={(v) => setCategoryPlanned(activeMonth, c.id, v[0])}
                />
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6 lg:col-span-1">
          <h3 className="font-display font-bold mb-4">Allocation preview</h3>
          <div className="h-64">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95} paddingAngle={2}>
                  {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <Tooltip formatter={(v: number) => formatINR(v)} contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 space-y-1.5 max-h-64 overflow-auto scrollbar-thin pr-1">
            {pieData.map((d) => (
              <div key={d.name} className="flex items-center justify-between text-xs py-1">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ background: d.color }} />
                  <span className="truncate">{d.icon} {d.name}</span>
                </div>
                <span className="tabular-nums font-medium">{formatINR(d.value, { compact: true })}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader><DialogTitle className="font-display">Add custom category</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">Name</Label>
              <Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="e.g. Gym" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Icon (emoji)</Label>
                <Input value={newIcon} onChange={(e) => setNewIcon(e.target.value)} maxLength={2} />
              </div>
              <div>
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Planned (₹)</Label>
                <Input type="number" value={newPlanned} onChange={(e) => setNewPlanned(e.target.value)} />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddOpen(false)}>Cancel</Button>
            <Button
              className="bg-gradient-primary"
              onClick={() => {
                if (!newName.trim()) return toast.error("Name required");
                addCategory(activeMonth, {
                  name: newName.trim(),
                  icon: newIcon || "✨",
                  color: `hsl(${Math.floor(Math.random() * 360)} 70% 60%)`,
                  planned: parseFloat(newPlanned) || 0,
                });
                setNewName(""); setNewIcon("✨"); setNewPlanned("");
                setAddOpen(false);
                toast.success("Category added");
              }}
            >
              Add
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <CategoryGoals />
    </div>
  );
}
