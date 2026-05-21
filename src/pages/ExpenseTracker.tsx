import { useMemo, useState } from "react";
import { useAppStore, useActiveBudget, useMonthExpenses } from "@/store/useAppStore";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { formatINR } from "@/utils/formatters";
import * as Icons from "lucide-react";
import { Search, Trash2, Pencil, Check, X, Receipt } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { CategoryIcon } from "@/components/ui/CategoryIcon";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";

export default function ExpenseTracker() {
  const budget = useActiveBudget();
  const expenses = useMonthExpenses();
  const { addExpense, updateExpense, deleteExpense, settings, familyMembers } = useAppStore();

  const [categoryId, setCategoryId] = useState(budget.categories[0]?.id ?? "");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [note, setNote] = useState("");
  const [paidBy, setPaidBy] = useState<string>("");
  const [sharedWith, setSharedWith] = useState<string[]>([]);
  const [filter, setFilter] = useState("");
  const [filterCat, setFilterCat] = useState<string>("all");
  const [editId, setEditId] = useState<string | null>(null);
  const [editAmount, setEditAmount] = useState("");
  const [editNote, setEditNote] = useState("");

  const submit = () => {
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) return toast.error("Enter a valid amount");
    addExpense({ 
      amount: amt, 
      categoryId, 
      date, 
      note,
      ...(settings.userType === "Family" && { paidBy, splitBetween: sharedWith }) 
    });
    toast.success("Expense logged");
    setAmount(""); setNote("");
  };

  const filtered = useMemo(() => {
    return expenses
      .filter((e) => (filterCat === "all" ? true : e.categoryId === filterCat))
      .filter((e) => {
        if (!filter) return true;
        const cat = budget.categories.find((c) => c.id === e.categoryId)?.name.toLowerCase() ?? "";
        return cat.includes(filter.toLowerCase()) || e.note.toLowerCase().includes(filter.toLowerCase());
      })
      .sort((a, b) => (b.date + b.id).localeCompare(a.date + a.id));
  }, [expenses, filter, filterCat, budget.categories]);

  const catTotals = useMemo(() => {
    const map = new Map<string, number>();
    expenses.forEach((e) => map.set(e.categoryId, (map.get(e.categoryId) ?? 0) + e.amount));
    return map;
  }, [expenses]);

  const getCat = (id: string) => budget.categories.find((c) => c.id === id);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Add form */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 lg:col-span-1 h-fit lg:sticky lg:top-20 space-y-4">
          <h3 className="font-display font-bold">Log an expense</h3>
          <div>
            <Label className="mb-2 block text-xs uppercase tracking-wider text-muted-foreground">Category</Label>
            <div className="grid grid-cols-4 gap-1.5">
              {budget.categories.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setCategoryId(c.id)}
                  className={`flex flex-col items-center gap-1 rounded-lg border p-2 text-[10px] transition-all ${
                    categoryId === c.id ? "border-primary bg-primary/10 shadow-glow" : "border-border hover:bg-muted"
                  }`}
                >
                  <CategoryIcon name={c.icon} className="h-4 w-4" />
                  <span className="truncate w-full text-center mt-1">{c.name}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">Amount</Label>
              <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="0" className="text-lg font-semibold" />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">Date</Label>
              <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
          </div>
          <div>
            <Label className="text-xs uppercase tracking-wider text-muted-foreground">Note</Label>
            <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="optional" />
          </div>
          
          {settings.userType === "Family" && familyMembers.length > 0 && (
            <div className="space-y-4 pt-2 border-t border-border/60">
              <div>
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Paid By</Label>
                <Select value={paidBy} onValueChange={setPaidBy}>
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Select member" />
                  </SelectTrigger>
                  <SelectContent>
                    {familyMembers.map(m => (
                      <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs uppercase tracking-wider text-muted-foreground mb-2 block">Split With</Label>
                <div className="grid grid-cols-2 gap-2">
                  {familyMembers.map(m => (
                    <div key={m.id} className="flex items-center space-x-2">
                      <Checkbox 
                        id={`split-${m.id}`} 
                        checked={sharedWith.includes(m.id)}
                        onCheckedChange={(checked) => {
                          if (checked) setSharedWith([...sharedWith, m.id]);
                          else setSharedWith(sharedWith.filter(id => id !== m.id));
                        }}
                      />
                      <label htmlFor={`split-${m.id}`} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                        {m.name}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <Button className="w-full bg-gradient-primary shadow-glow mt-4" onClick={submit}>Add expense</Button>

          <div className="pt-4 border-t border-border/60 space-y-2.5">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Category status</div>
            {budget.categories.map((c) => {
              const actual = catTotals.get(c.id) ?? 0;
              const pct = c.planned > 0 ? (actual / c.planned) * 100 : 0;
              return (
                <div key={c.id}>
                  <div className="flex items-center justify-between text-xs mb-0.5">
                    <span className="flex items-center gap-1.5"><CategoryIcon name={c.icon} className="h-3 w-3" /> {c.name}</span>
                    <span className="tabular-nums">{formatINR(actual, { compact: true })} / {formatINR(c.planned, { compact: true })}</span>
                  </div>
                  <Progress
                    value={Math.min(100, pct)} className="h-1.5"
                    style={{
                      // @ts-expect-error css var
                      "--progress-foreground": pct >= 100 ? "hsl(var(--destructive))" : pct >= 80 ? "hsl(var(--warning))" : c.color,
                    }}
                  />
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* List */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6 lg:col-span-2 space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[180px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Search notes or categories..." className="pl-9" />
            </div>
            <div className="flex gap-1.5 flex-wrap">
              <button onClick={() => setFilterCat("all")} className={`text-xs px-3 py-1.5 rounded-lg border ${filterCat === "all" ? "bg-primary text-primary-foreground border-primary" : "border-border hover:bg-muted"}`}>All</button>
              {budget.categories.map((c) => (
                <button key={c.id} onClick={() => setFilterCat(c.id)} className={`text-xs px-3 py-1.5 rounded-lg border flex items-center gap-1.5 ${filterCat === c.id ? "bg-primary text-primary-foreground border-primary" : "border-border hover:bg-muted"}`}>
                  <CategoryIcon name={c.icon} className={`h-3 w-3 ${filterCat === c.id ? "text-primary-foreground" : "text-primary"}`} /> {c.name}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2 max-h-[600px] overflow-auto scrollbar-thin pr-1">
            {filtered.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <div className="h-16 w-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                  <Receipt className="h-8 w-8 opacity-20" />
                </div>
                <div className="text-sm">No expenses yet. Add your first one!</div>
              </div>
            )}
            <AnimatePresence>
              {filtered.map((e) => {
                const c = getCat(e.categoryId);
                const isEdit = editId === e.id;
                return (
                  <motion.div
                    key={e.id}
                    layout
                    initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: -20 }}
                    className="flex items-center gap-3 rounded-xl border border-border/60 p-3 hover:bg-muted/40 transition-colors group"
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10" style={{ color: c?.color }}>
                      {c ? <CategoryIcon name={c.icon} className="h-5 w-5" /> : <Receipt className="h-5 w-5 text-muted-foreground" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-sm">{c?.name ?? "Unknown"}</span>
                        <Badge variant="secondary" className="text-[10px] font-normal">{new Date(e.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</Badge>
                      </div>
                      {isEdit ? (
                        <Input value={editNote} onChange={(ev) => setEditNote(ev.target.value)} className="h-7 text-xs mt-1" placeholder="Note" />
                      ) : (
                        e.note && <div className="text-xs text-muted-foreground truncate mt-0.5">{e.note}</div>
                      )}
                    </div>
                    {isEdit ? (
                      <Input type="number" value={editAmount} onChange={(ev) => setEditAmount(ev.target.value)} className="w-24 text-right font-semibold h-9" />
                    ) : (
                      <div className="font-display font-bold tabular-nums">{formatINR(e.amount)}</div>
                    )}
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {isEdit ? (
                        <>
                          <Button size="icon" variant="ghost" className="h-8 w-8 text-success" onClick={() => {
                            updateExpense(e.id, { amount: parseFloat(editAmount) || e.amount, note: editNote });
                            setEditId(null);
                          }}><Check className="h-4 w-4" /></Button>
                          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => setEditId(null)}><X className="h-4 w-4" /></Button>
                        </>
                      ) : (
                        <>
                          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => { setEditId(e.id); setEditAmount(String(e.amount)); setEditNote(e.note); }}>
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button size="icon" variant="ghost" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => { deleteExpense(e.id); toast.success("Deleted"); }}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
