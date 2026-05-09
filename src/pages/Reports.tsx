import { useMemo } from "react";
import { useAppStore, useActiveBudget, useMonthExpenses } from "@/store/useAppStore";
import { computeStats } from "@/engine/predictionEngine";
import { formatINR, formatPercent, monthLabel } from "@/utils/formatters";
import { Button } from "@/components/ui/button";
import { Download, FileSpreadsheet, FileText } from "lucide-react";
import { motion } from "framer-motion";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { toast } from "sonner";

// jsPDF's built-in Helvetica font does not support the ₹ Unicode symbol.
// This formatter produces ASCII-safe output for PDF tables.
const fmtPDF = (n: number): string => {
  const abs = Math.abs(n);
  const formatted = new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(abs);
  return `${n < 0 ? "-" : ""}Rs. ${formatted}`;
};

export default function Reports() {
  const budget = useActiveBudget();
  const expenses = useMonthExpenses();
  const allExpenses = useAppStore((s) => s.expenses);
  const budgets = useAppStore((s) => s.budgets);
  const activeMonth = useAppStore((s) => s.activeMonth);

  const stats = useMemo(() => computeStats(budget, expenses), [budget, expenses]);

  // Month-over-month
  const mom = useMemo(() => {
    const months = Object.keys(budgets).sort().slice(-6);
    return months.map((m) => {
      const b = budgets[m];
      const exp = allExpenses.filter((e) => e.month === m);
      const s = computeStats(b, exp);
      return { month: m, label: monthLabel(m), spent: s.totalActual, income: s.income, saved: s.savings, savingsRate: s.savingsRate };
    });
  }, [budgets, allExpenses]);

  const topCats = [...stats.byCategory].filter((c) => c.actual > 0).sort((a, b) => b.actual - a.actual).slice(0, 5);

  const exportPDF = () => {
    const doc = new jsPDF();
    doc.setFont("helvetica", "bold"); doc.setFontSize(22); doc.text("Spend Sense", 14, 20);
    doc.setFont("helvetica", "normal"); doc.setFontSize(11); doc.setTextColor(100);
    doc.text(`Monthly Report — ${monthLabel(activeMonth)}`, 14, 28);
    doc.setTextColor(0);

    autoTable(doc, {
      startY: 38,
      head: [["Metric", "Value"]],
      body: [
        ["Income", fmtPDF(stats.income)],
        ["Total Spent", fmtPDF(stats.totalActual)],
        ["Total Saved", fmtPDF(stats.savings)],
        ["Savings Rate", formatPercent(stats.savingsRate, 1)],
        ["Projected EOM", fmtPDF(stats.projectedTotal)],
        ["Days Elapsed", `${stats.daysElapsed} / ${stats.totalDays}`],
      ],
      theme: "grid",
      headStyles: { fillColor: [99, 76, 230] },
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const lastY = (doc as any).lastAutoTable?.finalY || 38;

    autoTable(doc, {
      startY: lastY + 10,
      head: [["Category", "Planned", "Actual", "Remaining", "% Used"]],
      // Strip Lucide icon names (e.g. "UtensilsCrossed") — use only the category name
      body: stats.byCategory.map((c) => [
        c.name,
        fmtPDF(c.planned),
        fmtPDF(c.actual),
        fmtPDF(c.remaining),
        formatPercent(c.percentUsed),
      ]),
      theme: "striped",
      headStyles: { fillColor: [99, 76, 230] },
    });

    doc.save(`spend-sense-${activeMonth}.pdf`);
    toast.success("PDF downloaded");
  };

  const exportCSV = () => {
    const rows = [["Date", "Category", "Amount", "Note"]];
    expenses.forEach((e) => {
      const cat = budget.categories.find((c) => c.id === e.categoryId)?.name ?? "Unknown";
      rows.push([e.date, cat, String(e.amount), e.note.replace(/,/g, ";")]);
    });
    const csv = rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `spend-sense-${activeMonth}.csv`; a.click();
    URL.revokeObjectURL(url);
    toast.success("CSV downloaded");
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap gap-3 justify-end">
        <Button variant="outline" onClick={exportCSV} className="gap-2 rounded-xl"><FileSpreadsheet className="h-4 w-4" /> Export CSV</Button>
        <Button onClick={exportPDF} className="gap-2 rounded-xl bg-gradient-primary shadow-glow"><Download className="h-4 w-4" /> Export PDF</Button>
      </div>

      <div className="glass-card p-6 md:p-8">
        <div className="flex items-start justify-between mb-6 flex-wrap gap-3">
          <div>
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Monthly summary</div>
            <h2 className="font-display text-2xl md:text-3xl font-bold mt-1">{monthLabel(activeMonth)}</h2>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground"><FileText className="h-4 w-4" /> Generated {new Date().toLocaleDateString("en-IN")}</div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          {[
            { label: "Income", value: formatINR(stats.income), tone: "primary" },
            { label: "Spent", value: formatINR(stats.totalActual), tone: "warm" },
            { label: "Saved", value: formatINR(stats.savings), tone: "success" },
            { label: "Savings rate", value: formatPercent(stats.savingsRate, 1), tone: "accent" },
          ].map((s) => (
            <div key={s.label} className="rounded-xl bg-muted/40 p-5">
              <div className="text-xs uppercase tracking-wider text-muted-foreground">{s.label}</div>
              <div className="font-display text-2xl font-bold mt-1">{s.value}</div>
            </div>
          ))}
        </div>

        <div className="mt-8">
          <h3 className="font-display font-bold mb-3">Top spending categories</h3>
          <div className="space-y-2">
            {topCats.map((c, i) => (
              <div key={c.categoryId} className="flex items-center gap-3 rounded-xl border border-border/60 p-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg text-base font-bold text-muted-foreground bg-muted">#{i + 1}</div>
                <div className="text-xl">{c.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm">{c.name}</div>
                  <div className="text-xs text-muted-foreground">{formatPercent((c.actual / stats.totalActual) * 100)} of total · {formatPercent(c.percentUsed)} of budget</div>
                </div>
                <div className="font-display font-bold tabular-nums">{formatINR(c.actual)}</div>
              </div>
            ))}
            {topCats.length === 0 && <div className="text-sm text-muted-foreground py-6 text-center">No expenses logged this month yet.</div>}
          </div>
        </div>

        <div className="mt-8">
          <h3 className="font-display font-bold mb-3">Month-over-month</h3>
          <div className="overflow-x-auto rounded-xl border border-border/60">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="text-left px-4 py-3">Month</th>
                  <th className="text-right px-4 py-3">Income</th>
                  <th className="text-right px-4 py-3">Spent</th>
                  <th className="text-right px-4 py-3">Saved</th>
                  <th className="text-right px-4 py-3">Rate</th>
                </tr>
              </thead>
              <tbody>
                {mom.map((m) => (
                  <tr key={m.month} className={`border-t border-border/60 ${m.month === activeMonth ? "bg-primary/5" : ""}`}>
                    <td className="px-4 py-3 font-medium">{m.label}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatINR(m.income)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatINR(m.spent)}</td>
                    <td className={`px-4 py-3 text-right tabular-nums font-semibold ${m.saved < 0 ? "text-destructive" : "text-success"}`}>{formatINR(m.saved)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatPercent(m.savingsRate, 1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
