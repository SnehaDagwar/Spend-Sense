import React from "react";
import { motion } from "framer-motion";
import { Flame, LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StreakCardProps {
  title: string;
  count: number;
  label: string;
  message: string;
  icon?: LucideIcon;
  color?: string; // e.g. "from-orange-500 to-red-600"
  delay?: number;
}

export const StreakCard = ({ 
  title, 
  count, 
  label, 
  message, 
  icon: Icon = Flame, 
  color = "from-orange-500 to-red-500",
  delay = 0 
}: StreakCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
    >
      <Card className="relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300">
        <div className={cn("absolute inset-0 bg-gradient-to-br opacity-[0.03] group-hover:opacity-[0.05] transition-opacity", color)} />
        <CardContent className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">{title}</p>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-4xl font-bold tracking-tighter">{count}</span>
                <span className="text-sm font-semibold text-muted-foreground uppercase tracking-widest">{label}</span>
              </div>
            </div>
            <motion.div 
              animate={count > 0 ? {
                scale: [1, 1.2, 1],
                rotate: [0, 5, -5, 0],
              } : {}}
              transition={{ 
                repeat: Infinity, 
                duration: 2, 
                ease: "easeInOut" 
              }}
              className={cn(
                "p-3 rounded-2xl bg-gradient-to-br shadow-lg shadow-primary/20",
                count > 0 ? color : "from-muted to-muted-foreground/20"
              )}
            >
              <Icon className={cn("h-6 w-6 text-white", count === 0 && "opacity-50")} />
            </motion.div>
          </div>
          
          <div className="space-y-3">
            <div className="h-1.5 w-full bg-secondary/50 rounded-full overflow-hidden">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${Math.min((count / 30) * 100, 100)}%` }}
                transition={{ duration: 1, delay: delay + 0.5 }}
                className={cn("h-full bg-gradient-to-r", color)}
              />
            </div>
            <p className="text-sm font-medium leading-tight">
              {count > 0 ? message : "Start your streak today!"}
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};
