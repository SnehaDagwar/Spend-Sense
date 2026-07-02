import React from "react";
import { motion } from "framer-motion";
import { useAppStore } from "@/store/useAppStore";
import { Star, Shield, Flame, Target, Zap, Lock, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const ALL_POSSIBLE_BADGES = [
  { id: '1', name: 'Early Bird', icon: Zap, color: 'from-amber-400 to-orange-500 shadow-orange-500/20' },
  { id: '2', name: 'Week Warrior', icon: Flame, color: 'from-orange-500 to-rose-600 shadow-rose-500/20' },
  { id: '3', name: 'Penny Pincher', icon: Shield, color: 'from-emerald-400 to-teal-500 shadow-emerald-500/20' },
  { id: '4', name: 'Master Saver', icon: Target, color: 'from-blue-400 to-indigo-600 shadow-indigo-500/20' },
  { id: '5', name: 'Gold Standard', icon: Star, color: 'from-violet-400 to-fuchsia-600 shadow-fuchsia-500/20' },
];

export const GamificationHeader = () => {
  const { xp, level, badges, savingsStreak } = useAppStore();
  const xpForNextLevel = level * 1000;
  const progress = Math.min((xp / xpForNextLevel) * 100, 100);

  // Dynamic rank name based on level
  const getRankName = (lvl: number) => {
    if (lvl === 1) return "Budget Apprentice";
    if (lvl === 2) return "Thrift Pathfinder";
    if (lvl === 3) return "Wealth Alchemist";
    if (lvl === 4) return "Capital Commander";
    return "Financial Sovereign";
  };

  const rankName = getRankName(level);

  // Math for SVG Progress ring
  const radius = 32;
  const circumference = 2 * Math.PI * radius; // ~201.06
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 animate-in fade-in duration-500">
      
      {/* CARD 1: Level & Rank Core */}
      <div className="relative overflow-hidden rounded-[24px] bg-gradient-to-br from-indigo-50/90 via-indigo-50/45 to-white/95 dark:from-indigo-950/40 dark:via-indigo-950/20 dark:to-slate-900/90 border border-indigo-100/80 dark:border-indigo-950/50 p-6 text-slate-800 dark:text-white shadow-[0_10px_30px_-5px_rgba(99,102,241,0.08)] backdrop-blur-xl flex items-center gap-5 group transition-all duration-300 hover:shadow-[0_20px_40px_-10px_rgba(99,102,241,0.15)] hover:border-indigo-400/40">
        {/* Glow Node */}
        <div className="absolute -top-12 -left-12 h-32 w-32 rounded-full bg-indigo-400/20 dark:bg-indigo-500/10 blur-[40px] group-hover:bg-indigo-400/30 dark:group-hover:bg-indigo-500/20 transition-all duration-500" />
        
        {/* Radial Progress Ring */}
        <div className="relative flex-shrink-0 w-20 h-20 flex items-center justify-center">
          <svg className="absolute inset-0 w-full h-full transform -rotate-90">
            <defs>
              <linearGradient id="headerXpGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#6366f1" /> {/* Indigo-500 */}
                <stop offset="100%" stopColor="#06b6d4" /> {/* Cyan-500 */}
              </linearGradient>
            </defs>
            <circle
              cx="40"
              cy="40"
              r={radius}
              className="stroke-indigo-100/80 dark:stroke-indigo-950/50"
              strokeWidth="5"
              fill="transparent"
            />
            <motion.circle
              cx="40"
              cy="40"
              r={radius}
              stroke="url(#headerXpGradient)"
              strokeWidth="5"
              fill="transparent"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1.5, ease: "easeOut" }}
              strokeLinecap="round"
            />
          </svg>
          
          <div className="w-14 h-14 rounded-full bg-white dark:bg-slate-950 border border-indigo-100/50 dark:border-slate-800 flex flex-col items-center justify-center shadow-inner relative z-10">
            <span className="text-[8px] font-bold uppercase tracking-[0.1em] text-indigo-400 dark:text-slate-400">LVL</span>
            <span className="text-xl font-black bg-gradient-to-b from-indigo-900 to-indigo-950 dark:from-white dark:to-slate-300 bg-clip-text text-transparent leading-none">
              {level}
            </span>
          </div>
        </div>

        <div className="flex-1 space-y-1 z-10">
          <div className="flex items-center gap-2">
            <h4 className="text-lg font-bold font-display tracking-tight bg-gradient-to-r from-indigo-900 via-indigo-950 to-indigo-900 dark:from-white dark:via-indigo-100 dark:to-indigo-200 bg-clip-text text-transparent">
              {rankName}
            </h4>
          </div>
          <p className="text-xs text-indigo-600 dark:text-indigo-300/80 font-semibold">
            Rank {level} Explorer
          </p>
          <p className="text-[10px] text-indigo-700/60 dark:text-slate-400 font-medium leading-relaxed">
            Building your financial legacy.
          </p>
        </div>

        {/* Small floating sparkles icon */}
        <div className="absolute top-4 right-4 text-indigo-400/40 dark:text-indigo-500/30 group-hover:text-indigo-500/80 dark:group-hover:text-indigo-400/80 transition-colors duration-300">
          <Sparkles className="h-4 w-4 animate-pulse" />
        </div>
      </div>

      {/* CARD 2: XP Tracking & Streaks */}
      <div className="relative overflow-hidden rounded-[24px] bg-gradient-to-br from-cyan-50/90 via-cyan-50/45 to-white/95 dark:from-cyan-950/40 dark:via-cyan-950/20 dark:to-slate-900/90 border border-cyan-100/80 dark:border-cyan-950/50 p-6 text-slate-800 dark:text-white shadow-[0_10px_30px_-5px_rgba(6,182,212,0.08)] backdrop-blur-xl flex flex-col justify-between gap-4 group transition-all duration-300 hover:shadow-[0_20px_40px_-10px_rgba(6,182,212,0.15)] hover:border-cyan-400/40">
        {/* Glow Node */}
        <div className="absolute -bottom-12 -right-12 h-32 w-32 rounded-full bg-cyan-400/20 dark:bg-cyan-500/10 blur-[40px] group-hover:bg-cyan-400/30 dark:group-hover:bg-cyan-500/20 transition-all duration-500" />
        
        <div className="flex items-center justify-between gap-4 z-10">
          <div className="space-y-0.5">
            <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-cyan-500 dark:text-slate-400">Experience Tracker</span>
            <div className="flex items-baseline gap-1">
              <span className="text-lg font-bold font-mono text-cyan-600 dark:text-cyan-300">{xp.toLocaleString()}</span>
              <span className="text-xs text-cyan-700/60 dark:text-slate-400">/ {xpForNextLevel.toLocaleString()} XP</span>
            </div>
          </div>

          {/* Streak Badge */}
          {savingsStreak > 0 ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-600 dark:text-orange-400 shadow-[0_4px_12px_rgba(249,115,22,0.05)]">
              <Flame className="h-3.5 w-3.5 fill-orange-500/20 animate-bounce" />
              <span className="text-[9px] font-black tracking-wider font-mono">{savingsStreak}D STREAK</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-cyan-100/50 dark:bg-slate-950 border border-cyan-200/50 dark:border-slate-800 text-cyan-500 dark:text-slate-500">
              <Flame className="h-3.5 w-3.5" />
              <span className="text-[8px] font-bold tracking-wider uppercase">NO STREAK</span>
            </div>
          )}
        </div>

        {/* Sleek Progress Bar */}
        <div className="space-y-2 z-10">
          <div className="relative pt-1">
            <div className="h-2 w-full bg-cyan-100/80 dark:bg-slate-950 rounded-full border border-cyan-200/30 dark:border-slate-800 overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 1.5, ease: "easeOut" }}
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-400 relative"
              >
                {/* Subtle moving shine overlay */}
                <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent_0%,rgba(255,255,255,0.15)_50%,transparent_100%)] bg-[length:200%_100%] animate-shimmer" />
              </motion.div>
            </div>
            
            {/* Glow Pin */}
            <motion.div
              initial={{ left: 0 }}
              animate={{ left: `${progress}%` }}
              transition={{ duration: 1.5, ease: "easeOut" }}
              className="absolute top-[3px] -translate-x-1/2 h-4 w-4 pointer-events-none flex items-center justify-center"
            >
              <div className="h-2 w-2 rounded-full bg-white shadow-[0_0_10px_rgba(34,211,238,1)]" />
            </motion.div>
          </div>

          <div className="flex justify-between items-center text-[9px] font-bold uppercase tracking-wider text-cyan-700/50 dark:text-slate-500">
            <span>Progress: {progress.toFixed(0)}%</span>
            <span className="text-cyan-600 dark:text-cyan-400 font-mono">
              {(xpForNextLevel - xp).toLocaleString()} XP to Lvl {level + 1}
            </span>
          </div>
        </div>
      </div>

      {/* CARD 3: Badges Showcase */}
      <div className="relative overflow-hidden rounded-[24px] bg-gradient-to-br from-violet-50/90 via-violet-50/45 to-white/95 dark:from-violet-950/40 dark:via-violet-950/20 dark:to-slate-900/90 border border-violet-100/80 dark:border-violet-950/50 p-6 text-slate-800 dark:text-white shadow-[0_10px_30px_-5px_rgba(139,92,246,0.08)] backdrop-blur-xl flex flex-col justify-between gap-3 group transition-all duration-300 hover:shadow-[0_20px_40px_-10px_rgba(139,92,246,0.15)] hover:border-violet-400/40">
        {/* Glow Node */}
        <div className="absolute -top-12 -right-12 h-32 w-32 rounded-full bg-violet-400/20 dark:bg-violet-500/10 blur-[40px] group-hover:bg-violet-400/30 dark:group-hover:bg-violet-500/20 transition-all duration-500" />
        
        <div className="z-10">
          <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-violet-500 dark:text-slate-400 block mb-3">Badge Cabinet</span>
          
          <div className="flex items-center gap-2">
            {ALL_POSSIBLE_BADGES.map((b) => {
              const isEarned = badges.some((earned) => earned.id === b.id);
              const IconComponent = b.icon;
              
              return (
                <motion.div
                  key={b.id}
                  whileHover={{ scale: isEarned ? 1.15 : 1, rotate: isEarned ? [0, -5, 5, 0] : 0 }}
                  className={cn(
                    "h-9 w-9 rounded-xl flex items-center justify-center border transition-all duration-300 relative group/badge cursor-pointer",
                    isEarned
                      ? `bg-gradient-to-br ${b.color} text-white border-white/20 shadow-[0_4px_12px_rgba(0,0,0,0.15)]`
                      : "bg-violet-100/40 dark:bg-slate-950 text-violet-300 dark:text-slate-800 border-violet-200/30 dark:border-slate-800"
                  )}
                >
                  {isEarned ? (
                    <IconComponent className="h-4 w-4" />
                  ) : (
                    <Lock className="h-3.5 w-3.5 text-violet-400 dark:text-slate-800" />
                  )}
                  
                  {/* Premium Hover Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2.5 opacity-0 pointer-events-none group-hover/badge:opacity-100 bg-slate-950 border border-slate-800 text-[10px] text-slate-200 px-2.5 py-1.5 rounded-lg shadow-2xl whitespace-nowrap transition-all duration-200 z-50 translate-y-1 group-hover/badge:translate-y-0">
                    <div className="font-bold mb-0.5">{isEarned ? b.name : "Locked Badge"}</div>
                    <div className="text-[9px] text-slate-400">
                      {isEarned ? "Unlocked Achievement" : "Unlock by hitting goals"}
                    </div>
                    <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-[5px] border-4 border-transparent border-t-slate-950" />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        <div className="flex justify-between items-center text-[9px] font-bold uppercase tracking-wider text-violet-700/50 dark:text-slate-500 z-10">
          <span>Unlocked Achievements</span>
          <span className="text-violet-600 dark:text-violet-400 font-mono">
            {badges.length} / {ALL_POSSIBLE_BADGES.length}
          </span>
        </div>
      </div>

    </div>
  );
};

