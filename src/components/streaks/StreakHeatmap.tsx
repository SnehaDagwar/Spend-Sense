import React from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface HeatmapData {
  date: string;
  count: number;
}

interface StreakHeatmapProps {
  data: HeatmapData[];
  title?: string;
  description?: string;
}

export const StreakHeatmap = ({ 
  data, 
  title = "Consistency Map", 
  description = "Your daily logging activity over the last 6 months" 
}: StreakHeatmapProps) => {
  // Group by weeks for the grid
  const weeks: HeatmapData[][] = [];

  // We want to show the data in a grid (7 rows for days of week, cols for weeks)
  // But standard GitHub style is columns are weeks.
  
  // To make it easy, we'll just chunk the data into 7s
  const reversedData = [...data].reverse();
  for (let i = 0; i < reversedData.length; i += 7) {
    weeks.push(reversedData.slice(i, i + 7));
  }

  const getColor = (count: number) => {
    if (count === 0) return "bg-secondary/40";
    if (count === 1) return "bg-primary/30";
    if (count === 2) return "bg-primary/60";
    return "bg-primary";
  };

  return (
    <Card className="overflow-hidden border-border/40 bg-gradient-to-b from-card to-secondary/10">
      <CardHeader>
        <CardTitle className="text-xl font-bold">
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4">
          <div className="flex gap-1 overflow-x-auto pb-4 scrollbar-hide">
            <TooltipProvider>
              {weeks.map((week, weekIdx) => (
                <div key={weekIdx} className="flex flex-col gap-1 shrink-0">
                  {week.map((day, dayIdx) => (
                    <Tooltip key={dayIdx}>
                      <TooltipTrigger asChild>
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ delay: (weekIdx * 7 + dayIdx) * 0.002 }}
                          className={cn(
                            "h-3 w-3 rounded-sm transition-colors duration-300",
                            getColor(day.count)
                          )}
                        />
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        <p className="text-xs font-medium">
                          {new Date(day.date).toLocaleDateString(undefined, { 
                            month: 'short', 
                            day: 'numeric', 
                            year: 'numeric' 
                          })}
                        </p>
                        <p className="text-[10px] text-muted-foreground">
                          {day.count} {day.count === 1 ? 'expense' : 'expenses'} logged
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  ))}
                </div>
              ))}
            </TooltipProvider>
          </div>
          
          <div className="flex items-center justify-end gap-2 text-[10px] font-medium text-muted-foreground uppercase tracking-widest">
            <span>Less</span>
            <div className="flex gap-1">
              <div className="h-3 w-3 rounded-sm bg-secondary/40" />
              <div className="h-3 w-3 rounded-sm bg-primary/30" />
              <div className="h-3 w-3 rounded-sm bg-primary/60" />
              <div className="h-3 w-3 rounded-sm bg-primary" />
            </div>
            <span>More</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
