import React from "react";
import { useAppStore, useActiveBudget, useMonthExpenses } from "@/store/useAppStore";
import { Card } from "@/components/ui/card";
import { Users, Sparkles, TrendingUp, PiggyBank, Heart } from "lucide-react";
import { Progress } from "@/components/ui/progress";

const FamilyWallet = () => {
  const { familyMembers, settings } = useAppStore();
  const activeBudget = useActiveBudget();
  const monthExpenses = useMonthExpenses();

  const totalIncome = activeBudget?.income || 0;
  const totalSpent = monthExpenses.reduce((acc, curr) => acc + curr.amount, 0);
  const remaining = totalIncome - totalSpent;
  const percentageSpent = totalIncome > 0 ? (totalSpent / totalIncome) * 100 : 0;

  const currencySymbol = settings.profile.currency === "INR" ? "₹" : 
                         settings.profile.currency === "USD" ? "$" : "€";

  const insights = [
    { title: "Groceries Spikes", message: "Family spent 15% more on groceries this week.", type: "warning" },
    { title: "Saving Opportunity", message: "If you cut dining out, you can save ₹2,000 more.", type: "tip" },
    { title: "Great Job", message: "You are well within your utility bills limit.", type: "success" }
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3">
        <div className="p-3 bg-gradient-secondary rounded-2xl shadow-glow">
          <Heart className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-display font-bold">Family Wallet</h1>
          <p className="text-muted-foreground mt-1">Shared finances, managed together.</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="p-6 bg-gradient-primary text-white shadow-glow border-none relative overflow-hidden">
          <div className="absolute right-0 top-0 opacity-10 blur-xl">
            <PiggyBank className="w-32 h-32" />
          </div>
          <div className="relative z-10">
            <h3 className="text-primary-foreground/80 font-medium">Family Balance</h3>
            <p className="text-4xl font-display font-bold mt-2">{currencySymbol}{remaining.toLocaleString()}</p>
            <div className="mt-4 pt-4 border-t border-white/20">
              <span className="text-sm opacity-80">Total Income: {currencySymbol}{totalIncome.toLocaleString()}</span>
            </div>
          </div>
        </Card>

        <Card className="p-6 glass-card border-none flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-muted-foreground font-medium">Monthly Spending</h3>
              <TrendingUp className="h-5 w-5 text-accent" />
            </div>
            <p className="text-3xl font-display font-bold">{currencySymbol}{totalSpent.toLocaleString()}</p>
          </div>
          <div className="space-y-2 mt-4">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{percentageSpent.toFixed(0)}% of Budget</span>
              <span>{currencySymbol}{totalIncome.toLocaleString()}</span>
            </div>
            <Progress value={percentageSpent} className="h-2" indicatorColor="bg-accent" />
          </div>
        </Card>

        <Card className="p-6 glass-card border-none flex flex-col justify-between group hover:shadow-lg transition-all cursor-pointer">
          <div>
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-muted-foreground font-medium">Members</h3>
              <Users className="h-5 w-5 text-secondary" />
            </div>
            <p className="text-3xl font-display font-bold">{familyMembers.length}</p>
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            {familyMembers.filter(m => m.role === 'Child').length} Children, {familyMembers.filter(m => m.role !== 'Child').length} Adults
          </p>
        </Card>
      </div>

      <div>
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="h-5 w-5 text-yellow-500" />
          <h2 className="text-xl font-display font-bold">Smart Family Insights</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {insights.map((insight, idx) => (
            <Card key={idx} className={`p-5 border-none glass-card ${
              insight.type === 'warning' ? 'bg-red-50/50' : 
              insight.type === 'tip' ? 'bg-blue-50/50' : 'bg-green-50/50'
            }`}>
              <h4 className="font-bold mb-1">{insight.title}</h4>
              <p className="text-sm text-muted-foreground">{insight.message}</p>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FamilyWallet;
