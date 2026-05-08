import { useState } from "react";
import { Plus, Target, TrendingUp, Calendar, Zap } from "lucide-react";
import { useAppStore } from "@/store/useAppStore";
import { formatINR } from "@/utils/formatters";
import { GoalCard } from "@/components/goals/GoalCard";
import { AddGoalDialog } from "@/components/goals/AddGoalDialog";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

export default function SavingsGoals() {
  const { goals, savingsStreak } = useAppStore();
  const [isAddGoalOpen, setIsAddGoalOpen] = useState(false);

  const totalActiveGoals = goals.length;
  const totalSaved = goals.reduce((acc, goal) => acc + goal.currentAmount, 0);
  const totalTarget = goals.reduce((acc, goal) => acc + goal.targetAmount, 0);
  const totalMonthlyContribution = goals.reduce((acc, goal) => acc + goal.monthlyContribution, 0);
  const overallPercentage = totalTarget > 0 ? (totalSaved / totalTarget) * 100 : 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold font-display gradient-text tracking-tight">Savings Goals</h1>
          <p className="text-muted-foreground mt-1">Track and manage your financial milestones.</p>
        </div>
        <Button onClick={() => setIsAddGoalOpen(true)} className="rounded-xl shadow-glow bg-gradient-primary hover:opacity-90 transition-opacity">
          <Plus className="mr-2 h-4 w-4" />
          Add New Goal
        </Button>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Target className="h-5 w-5" />
            </div>
            <p className="text-sm font-medium text-muted-foreground">Active Goals</p>
          </div>
          <p className="text-3xl font-bold font-display">{totalActiveGoals}</p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-green-500/10 text-green-600">
              <TrendingUp className="h-5 w-5" />
            </div>
            <p className="text-sm font-medium text-muted-foreground">Total Saved</p>
          </div>
          <p className="text-3xl font-bold font-display">{formatINR(totalSaved)}</p>
          <p className="text-xs text-muted-foreground mt-1">
            {overallPercentage.toFixed(1)}% of total target
          </p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-600">
              <Calendar className="h-5 w-5" />
            </div>
            <p className="text-sm font-medium text-muted-foreground">Monthly Contribution</p>
          </div>
          <p className="text-3xl font-bold font-display">{formatINR(totalMonthlyContribution)}</p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600">
              <Zap className="h-5 w-5" />
            </div>
            <p className="text-sm font-medium text-muted-foreground">Savings Streak</p>
          </div>
          <p className="text-3xl font-bold font-display">{savingsStreak} Months</p>
        </motion.div>
      </div>

      {/* Goals Grid */}
      {goals.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 border border-dashed rounded-3xl bg-muted/30">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <Target className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-xl font-semibold mb-2">No savings goals yet</h3>
          <p className="text-muted-foreground text-center max-w-md mb-6">
            Set a new savings goal to start tracking your progress towards your financial milestones.
          </p>
          <Button onClick={() => setIsAddGoalOpen(true)} variant="outline" className="rounded-xl">
            Create your first goal
          </Button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {goals.map((goal) => (
            <GoalCard key={goal.id} goal={goal} />
          ))}
        </div>
      )}

      <AddGoalDialog open={isAddGoalOpen} onOpenChange={setIsAddGoalOpen} />
    </div>
  );
}
