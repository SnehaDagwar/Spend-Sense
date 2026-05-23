import React from "react";
import { motion } from "framer-motion";
import { useAppStore } from "@/store/useAppStore";
import { Trophy, Star, Shield, Flame, Target, Zap, Lock, Sparkles, Award } from "lucide-react";
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

  return (
    <div className="relative overflow-hidden rounded-[32px] bg-slate-950/80 border border-white/10 p-6 md:p-8 text-white shadow-2xl mb-8 backdrop-blur-2xl">
      {/* Dynamic Aurora Blur Nodes */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        {/* Cyan Orb */}
        <motion.div
          animate={{
            x: [0, 40, -20, 0],
            y: [0, -30, 20, 0],
            scale: [1, 1.15, 0.9, 1],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -top-12 -left-12 h-64 w-64 rounded-full bg-cyan-500/15 blur-[80px]"
        />
        {/* Indigo Orb */}
        <motion.div
          animate={{
            x: [0, -30, 30, 0],
            y: [0, 40, -20, 0],
            scale: [1, 0.9, 1.2, 1],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -bottom-16 -right-16 h-72 w-72 rounded-full bg-indigo-500/20 blur-[100px]"
        />
        {/* Rose/Pink Orb */}
        <motion.div
          animate={{
            x: [0, 20, -40, 0],
            y: [0, 30, -30, 0],
            scale: [1, 1.1, 0.95, 1],
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute top-1/2 left-1/3 -translate-y-1/2 h-48 w-48 rounded-full bg-fuchsia-500/10 blur-[70px]"
        />
      </div>

      <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-8">
        {/* Profile and Level Emblem */}
        <div className="flex flex-col sm:flex-row items-center gap-6 text-center sm:text-left">
          <div className="relative flex-shrink-0">
            {/* Outer Spinning Orbit Ring */}
            <div className="absolute -inset-2 rounded-full border border-dashed border-indigo-400/20 animate-[spin_40s_linear_infinite]" />
            <div className="absolute -inset-3 rounded-full border border-indigo-500/10 animate-[spin_25s_linear_infinite_reverse]" />
            
            {/* Glassmorphic Core Badge */}
            <div className="relative h-24 w-24 rounded-2xl bg-gradient-to-tr from-slate-900 via-slate-800 to-indigo-950/80 p-[2px] shadow-[0_0_30px_rgba(99,102,241,0.15)] border border-white/10 flex items-center justify-center overflow-hidden group">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(99,102,241,0.15)_0%,transparent_70%)]" />
              <div className="relative flex flex-col items-center justify-center">
                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-indigo-300/80 mb-0.5">Level</span>
                <span className="text-4xl font-extrabold font-display bg-gradient-to-b from-white via-white to-indigo-200 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(99,102,241,0.4)]">
                  {level}
                </span>
              </div>
            </div>
            
            {/* Floating Spark Star Emblem */}
            <motion.div 
              animate={{ y: [0, -3, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              className="absolute -bottom-1 -right-1 h-8 w-8 rounded-xl bg-gradient-to-br from-indigo-400 to-purple-600 flex items-center justify-center shadow-lg border border-white/20"
            >
              <Sparkles className="h-4 w-4 text-white" />
            </motion.div>
          </div>

          <div className="space-y-1.5">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <h2 className="text-2xl font-bold font-display tracking-tight bg-gradient-to-r from-white via-indigo-100 to-indigo-200 bg-clip-text text-transparent">
                {rankName}
              </h2>
              <span className="inline-flex self-center sm:self-auto px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                Rank {level}
              </span>
            </div>
            <p className="text-sm text-slate-400 font-medium">
              Level {level} Explorer • Let's build your financial legacy.
            </p>
            
            {/* Tiny Badge collection Shelf */}
            <div className="flex items-center gap-3 pt-2">
              <span className="text-xs font-semibold text-slate-400 tracking-wide">Badges:</span>
              <div className="flex items-center gap-1.5">
                {ALL_POSSIBLE_BADGES.map((b) => {
                  const isEarned = badges.some((earned) => earned.id === b.id);
                  const IconComponent = b.icon;
                  
                  return (
                    <div
                      key={b.id}
                      className={cn(
                        "h-7 w-7 rounded-lg flex items-center justify-center border transition-all duration-300 cursor-help relative group/badge",
                        isEarned
                          ? `bg-gradient-to-br ${b.color} text-white border-white/20 shadow-md`
                          : "bg-slate-900/60 text-slate-600 border-slate-800"
                      )}
                      title={isEarned ? `Unlocked ${b.name}` : `Locked Badge`}
                    >
                      {isEarned ? (
                        <IconComponent className="h-3.5 w-3.5 animate-pulse" />
                      ) : (
                        <Lock className="h-3 w-3 text-slate-700" />
                      )}
                      
                      {/* Micro tooltip */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 opacity-0 pointer-events-none group-hover/badge:opacity-100 bg-slate-950 border border-slate-800 text-[10px] text-slate-300 px-2 py-1 rounded shadow-xl whitespace-nowrap transition-opacity duration-200 z-50">
                        {isEarned ? b.name : "Locked Badge"}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* HUD Experience Gauge Column */}
        <div className="flex-1 max-w-xl w-full space-y-4">
          {/* HUD Label Headers */}
          <div className="flex justify-between items-end">
            <div className="space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-400 block">Experience Module</span>
              <div className="flex items-center gap-1.5">
                <Award className="h-4 w-4 text-indigo-400" />
                <span className="text-sm font-bold font-mono tracking-tight text-indigo-200">
                  {xp.toLocaleString()} <span className="text-slate-400 font-sans">/ {xpForNextLevel.toLocaleString()} XP</span>
                </span>
              </div>
            </div>
            
            {/* Quick Streak Stats */}
            {savingsStreak > 0 && (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400">
                <Flame className="h-4 w-4 fill-orange-500/20 animate-pulse" />
                <span className="text-xs font-black tracking-tight font-mono">{savingsStreak}D STREAK</span>
              </div>
            )}
          </div>

          {/* The Glowing Instrument Track */}
          <div className="relative">
            <div className="h-3.5 w-full bg-slate-950/60 rounded-full border border-slate-800/80 p-[2px] overflow-hidden">
              {/* Animated Bar Fill */}
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 1.2, ease: "easeOut" }}
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-indigo-400 to-cyan-400 relative"
              >
                {/* Shimmer overlay effect */}
                <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent_0%,rgba(255,255,255,0.15)_50%,transparent_100%)] bg-[length:200%_100%] animate-shimmer" />
              </motion.div>
            </div>

            {/* Floating active glow thumb dot */}
            <motion.div
              initial={{ left: 0 }}
              animate={{ left: `${progress}%` }}
              transition={{ duration: 1.2, ease: "easeOut" }}
              className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 h-5 w-5 pointer-events-none"
            >
              <div className="h-2.5 w-2.5 rounded-full bg-white shadow-[0_0_12px_rgba(99,102,241,1),0_0_4px_rgba(34,211,238,1)] border border-indigo-300" />
            </motion.div>
          </div>

          {/* Calibrated Ticks & Next Goal */}
          <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider text-slate-500">
            <div className="flex gap-4">
              <span>0%</span>
              <span>25%</span>
              <span>50%</span>
              <span>75%</span>
            </div>
            <div className="text-indigo-400 text-right">
              {(xpForNextLevel - xp).toLocaleString()} XP to Level {level + 1}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

