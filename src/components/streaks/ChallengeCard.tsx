import React from "react";
import { motion } from "framer-motion";
import { Challenge } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, Circle, Clock, Zap, Gift } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/useAppStore";

interface ChallengeCardProps {
  challenge: Challenge;
}

export const ChallengeCard = ({ challenge }: ChallengeCardProps) => {
  const { claimChallenge } = useAppStore();

  const isCompleted = challenge.status === 'completed';
  const isClaimed = challenge.status === 'claimed';
  const isActive = challenge.status === 'active';

  return (
    <Card className={cn(
      "relative overflow-hidden transition-all duration-300",
      isCompleted && "border-green-500/50 bg-green-50/50 dark:bg-green-950/20",
      isClaimed && "opacity-60 grayscale-[0.5]"
    )}>
      <CardContent className="p-5">
        <div className="flex gap-4 items-start">
          <div className={cn(
            "p-3 rounded-xl shrink-0",
            isActive && "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
            isCompleted && "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400",
            isClaimed && "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
          )}>
            {isClaimed ? <CheckCircle2 className="h-6 w-6" /> : <Zap className="h-6 w-6" />}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex justify-between items-start mb-1">
              <h4 className="font-bold text-lg tracking-tight truncate">{challenge.title}</h4>
              <div className="flex items-center gap-1 px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded-full text-[10px] font-black uppercase tracking-widest">
                <StarIcon className="h-3 w-3 fill-current" />
                {challenge.rewardXP} XP
              </div>
            </div>
            <p className="text-sm text-muted-foreground leading-snug mb-4">
              {challenge.description}
            </p>
            
            <div className="flex items-center justify-between mt-auto">
              <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>Ends in 4h 20m</span>
              </div>
              
              {isCompleted ? (
                <Button 
                  onClick={() => claimChallenge(challenge.id)}
                  className="bg-gradient-to-r from-green-500 to-emerald-600 hover:opacity-90 text-white shadow-lg shadow-green-500/20 h-8 rounded-lg text-xs gap-1.5"
                >
                  <Gift className="h-3.5 w-3.5" /> Claim Reward
                </Button>
              ) : isClaimed ? (
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400 text-xs font-bold">
                  <CheckCircle2 className="h-4 w-4" /> Claimed
                </div>
              ) : (
                <div className="text-xs font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 px-3 py-1 rounded-lg">
                  In Progress
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
      
      {/* Background patterns */}
      <div className="absolute -right-4 -bottom-4 opacity-5">
        <Zap className="h-24 w-24 rotate-12" />
      </div>
    </Card>
  );
};

const StarIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    {...props}
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
  </svg>
);
