import React, { useEffect } from "react";
import { useAppStore } from "@/store/useAppStore";
import { 
  calculateLoggingStreak, 
  calculateSpendingStreak, 
  calculateBudgetStreak, 
  generateHeatmapData 
} from "@/utils/streakUtils";
import { checkChallengeStatus } from "@/utils/challengeUtils";
import { StreakCard } from "@/components/streaks/StreakCard";
import { StreakHeatmap } from "@/components/streaks/StreakHeatmap";
import { GamificationHeader } from "@/components/streaks/GamificationHeader";
import { ChallengeCard } from "@/components/streaks/ChallengeCard";
import { BadgeGrid } from "@/components/streaks/BadgeGrid";
import { Flame, ShieldCheck, Target, TrendingUp, Zap } from "lucide-react";
import { motion } from "framer-motion";

const Streaks = () => {
  const { 
    expenses, 
    budgets, 
    challenges, 
    badges,
    generateDailyChallenges,
    completeChallenge 
  } = useAppStore();

  useEffect(() => {
    generateDailyChallenges();
  }, []);

  // Update challenge statuses based on latest expenses
  useEffect(() => {
    challenges.forEach(challenge => {
      if (challenge.status === 'active') {
        const newStatus = checkChallengeStatus(challenge, expenses);
        if (newStatus === 'completed' || newStatus === 'failed') {
          completeChallenge(challenge.id);
        }
      }
    });
  }, [expenses]);

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

  const todayStr = new Date().toISOString().split('T')[0];
  const todayChallenges = challenges.filter(c => c.date === todayStr);

  return (
    <div className="space-y-8 pb-12">
      <GamificationHeader />

      <section>
        <div className="flex items-center gap-2 mb-4">
          <Zap className="h-5 w-5 text-blue-500" />
          <h3 className="text-xl font-bold tracking-tight">Daily Challenges</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {todayChallenges.map((challenge) => (
            <ChallengeCard key={challenge.id} challenge={challenge} />
          ))}
          {todayChallenges.length === 0 && (
            <p className="text-sm text-muted-foreground italic">No challenges for today yet. Come back tomorrow!</p>
          )}
        </div>
      </section>

      <section>
        <div className="flex items-center gap-2 mb-4">
          <Flame className="h-5 w-5 text-orange-500" />
          <h3 className="text-xl font-bold tracking-tight">Consistency Streaks</h3>
        </div>
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
            color="from-accent to-accent/70"
            delay={0}
          />
          <StreakCard
            title="Discipline Streak"
            count={spendingStreak}
            label="Days"
            message="You avoided unnecessary spending today!"
            icon={ShieldCheck}
            color="from-success to-success/70"
            delay={0.1}
          />
          <StreakCard
            title="Budget Streak"
            count={budgetStreak}
            label="Months"
            message={`You stayed under budget for ${budgetStreak} months.`}
            icon={Target}
            color="from-primary to-secondary"
            delay={0.2}
          />
        </motion.div>
      </section>

      <div className="grid grid-cols-1 gap-8">
        <StreakHeatmap data={heatmapData} />
        <BadgeGrid earnedBadges={badges} />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="rounded-2xl bg-gradient-to-br from-primary/10 via-secondary/5 to-primary/5 p-8 border border-primary/10 relative overflow-hidden group"
      >
        <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-110 transition-transform duration-500">
          <TrendingUp className="h-32 w-32 text-primary" />
        </div>
        
        <div className="relative z-10 max-w-2xl">
          <h2 className="text-2xl font-bold mb-3 gradient-text">Why Gamification?</h2>
          <p className="text-muted-foreground leading-relaxed">
            Managing money shouldn't be boring. By turning your financial goals 
            into a game, you stay motivated and build long-term wealth without 
            even noticing the effort. Earn XP, collect badges, and level up 
            your financial future!
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Streaks;
