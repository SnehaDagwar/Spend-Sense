import React from "react";
import { motion } from "framer-motion";
import { useAppStore } from "@/store/useAppStore";
import { Progress } from "@/components/ui/progress";
import { Trophy, Star, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

export const GamificationHeader = () => {
  const { xp, level, badges } = useAppStore();
  const xpForNextLevel = level * 1000;
  const progress = (xp / xpForNextLevel) * 100;

  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 p-8 text-white shadow-xl mb-8">
      {/* Decorative Elements */}
      <div className="absolute -right-8 -top-8 h-48 w-48 rounded-full bg-white/10 blur-3xl" />
      <div className="absolute -left-8 -bottom-8 h-32 w-32 rounded-full bg-pink-500/20 blur-2xl" />
      
      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          <div className="relative">
            <div className="h-20 w-20 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/30 shadow-inner">
              <span className="text-3xl font-black">{level}</span>
            </div>
            <div className="absolute -bottom-2 -right-2 h-8 w-8 rounded-full bg-yellow-400 flex items-center justify-center shadow-lg border-2 border-purple-600">
              <Star className="h-4 w-4 text-purple-700 fill-purple-700" />
            </div>
          </div>
          
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Level {level} Explorer</h2>
            <div className="flex items-center gap-2 mt-1 opacity-80 text-sm font-medium">
              <Trophy className="h-4 w-4" />
              <span>{badges.length} Badges Earned</span>
            </div>
          </div>
        </div>
        
        <div className="flex-1 max-w-md">
          <div className="flex justify-between items-end mb-2">
            <span className="text-sm font-bold uppercase tracking-widest opacity-80">Experience Points</span>
            <span className="text-sm font-black">{xp} / {xpForNextLevel} XP</span>
          </div>
          <div className="h-3 w-full bg-black/20 rounded-full overflow-hidden border border-white/10">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="h-full bg-gradient-to-r from-yellow-300 to-yellow-500 shadow-[0_0_15px_rgba(253,224,71,0.5)]"
            />
          </div>
          <p className="text-[10px] mt-2 font-bold uppercase tracking-[0.2em] opacity-60 text-right">
            {xpForNextLevel - xp} XP to Level {level + 1}
          </p>
        </div>
      </div>
    </div>
  );
};
