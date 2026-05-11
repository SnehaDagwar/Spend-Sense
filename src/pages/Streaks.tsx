import React from "react";
import { useAppStore } from "@/store/useAppStore";
import { 
  calculateLoggingStreak, 
  calculateSpendingStreak, 
  calculateBudgetStreak, 
  generateHeatmapData 
} from "@/utils/streakUtils";
import { StreakCard } from "@/components/streaks/StreakCard";
import { StreakHeatmap } from "@/components/streaks/StreakHeatmap";
import { Flame, ShieldCheck, Target, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";

const Streaks = () => {
  const expenses = useAppStore((s) => s.expenses);
  const budgets = useAppStore((s) => s.budgets);

  const loggingStreak = calculateLoggingStreak(expenses);
  const spendingStreak = calculateSpendingStreak(expenses);
  const budgetStreak = calculateBudgetStreak(budgets, expenses);
  const heatmapData = generateHeatmapData(expenses);

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  return (
    <div className="space-y-8 pb-12">
      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        <StreakCard
          title="Logging Streak"
          count={loggingStreak}
          label="Days"
          message={`${loggingStreak}-day disciplined logger streak!`}
          icon={Flame}
          color="from-orange-500 to-red-500"
          delay={0}
        />
        <StreakCard
          title="Discipline Streak"
          count={spendingStreak}
          label="Days"
          message="You avoided unnecessary spending today!"
          icon={ShieldCheck}
          color="from-emerald-500 to-teal-600"
          delay={0.1}
        />
        <StreakCard
          title="Budget Streak"
          count={budgetStreak}
          label="Months"
          message={`You stayed under budget for ${budgetStreak} months.`}
          icon={Target}
          color="from-indigo-500 to-purple-600"
          delay={0.2}
        />
      </motion.div>

      <div className="grid grid-cols-1 gap-6">
        <StreakHeatmap data={heatmapData} />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="rounded-3xl bg-gradient-to-br from-primary/10 via-secondary/5 to-primary/5 p-8 border border-primary/10 relative overflow-hidden group"
      >
        <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-110 transition-transform duration-500">
          <TrendingUp className="h-32 w-32 text-primary" />
        </div>
        
        <div className="relative z-10 max-w-2xl">
          <h2 className="text-2xl font-bold mb-3 gradient-text">Why Streaks Matter</h2>
          <p className="text-muted-foreground leading-relaxed">
            Financial freedom is built on consistent habits, not one-time wins. 
            By logging daily and avoiding discretionary spending, you're training 
            your mind to be more intentional with every rupee. 
            Keep the fire burning!
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Streaks;
