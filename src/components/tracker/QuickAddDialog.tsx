import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useAppStore, useActiveBudget } from "@/store/useAppStore";
import { toast } from "sonner";

interface Props { open: boolean; onOpenChange: (v: boolean) => void; }

export function QuickAddDialog({ open, onOpenChange }: Props) {
  const budget = useActiveBudget();
  const addExpense = useAppStore((s) => s.addExpense);
  const [categoryId, setCategoryId] = useState(budget?.categories[0]?.id ?? "");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [note, setNote] = useState("");

  useEffect(() => {
    if (budget && !categoryId) setCategoryId(budget.categories[0]?.id ?? "");
  }, [budget, categoryId]);

  const submit = () => {
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) return toast.error("Enter a valid amount");
    if (!categoryId) return toast.error("Pick a category");
    addExpense({ amount: amt, categoryId, date, note });
    toast.success("Expense added");
    setAmount(""); setNote("");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-display">Quick add expense</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label className="mb-2 block text-xs uppercase tracking-wider text-muted-foreground">Category</Label>
            <div className="grid grid-cols-4 gap-2">
              {budget?.categories.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setCategoryId(c.id)}
                  className={`flex flex-col items-center gap-1 rounded-xl border p-2 text-xs transition-all ${
                    categoryId === c.id ? "border-primary bg-primary/10 shadow-glow" : "border-border hover:bg-muted"
                  }`}
                >
                  <span className="text-xl">{c.icon}</span>
                  <span className="truncate font-medium">{c.name}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="mb-1.5 block text-xs uppercase tracking-wider text-muted-foreground">Amount (₹)</Label>
              <Input type="number" inputMode="decimal" placeholder="0" value={amount} onChange={(e) => setAmount(e.target.value)} className="text-lg font-semibold" autoFocus />
            </div>
            <div>
              <Label className="mb-1.5 block text-xs uppercase tracking-wider text-muted-foreground">Date</Label>
              <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
          </div>
          <div>
            <Label className="mb-1.5 block text-xs uppercase tracking-wider text-muted-foreground">Note (optional)</Label>
            <Input placeholder="e.g. Lunch with team" value={note} onChange={(e) => setNote(e.target.value)} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={submit} className="bg-gradient-primary shadow-glow">Add expense</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
