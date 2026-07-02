import React from "react";
import { Badge } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Trophy, Star, Shield, Flame, Target, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  trophy: Trophy,
  star: Star,
  shield: Shield,
  flame: Flame,
  target: Target,
  zap: Zap,
};

interface BadgeGridProps {
  earnedBadges: Badge[];
}

const ALL_POSSIBLE_BADGES: Badge[] = [
  { id: '1', name: 'Early Bird', description: 'Log your first expense before 8 AM', icon: 'zap', category: 'discipline' },
  { id: '2', name: 'Week Warrior', description: 'Maintain a 7-day logging streak', icon: 'flame', category: 'streaks' },
  { id: '3', name: 'Penny Pincher', description: 'Stay under ₹200 for 3 days in a row', icon: 'shield', category: 'discipline' },
  { id: '4', name: 'Master Saver', description: 'Contribute to 5 different goals', icon: 'target', category: 'savings' },
  { id: '5', name: 'Gold Standard', description: 'Complete 10 daily challenges', icon: 'star', category: 'streaks' },
];

export const BadgeGrid = ({ earnedBadges }: BadgeGridProps) => {
  return (
    <Card className="border-border/40 bg-gradient-to-br from-card to-secondary/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Trophy className="h-5 w-5 text-yellow-500" />
          Badge Collection
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 gap-4">
          <TooltipProvider>
            {ALL_POSSIBLE_BADGES.map((badge) => {
              const earned = earnedBadges.find(b => b.id === badge.id);
              const Icon = ICON_MAP[badge.icon] || Trophy;
              
              return (
                <Tooltip key={badge.id}>
                  <TooltipTrigger asChild>
                    <div className="flex flex-col items-center gap-2 group cursor-pointer">
                      <div className={cn(
                        "h-12 w-12 rounded-2xl flex items-center justify-center transition-all duration-500",
                        earned 
                          ? "bg-gradient-to-br from-yellow-400 to-orange-500 text-white shadow-lg shadow-orange-500/20 scale-110" 
                          : "bg-secondary text-muted-foreground/30 grayscale"
                      )}>
                        <Icon className={cn("h-6 w-6", earned && "animate-pulse")} />
                      </div>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-[200px]">
                    <p className="font-bold">{badge.name}</p>
                    <p className="text-xs text-muted-foreground">{badge.description}</p>
                    {earned && (
                      <p className="text-[10px] text-green-500 font-bold mt-1 uppercase tracking-tighter">
                        Unlocked on {new Date(earned.unlockedAt!).toLocaleDateString()}
                      </p>
                    )}
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </TooltipProvider>
        </div>
      </CardContent>
    </Card>
  );
};
