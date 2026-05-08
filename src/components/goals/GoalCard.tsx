import { formatINR } from "@/utils/formatters";
import { SavingsGoal } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { LucideIcon, Target, ShieldAlert, Plane, Home, Car, GraduationCap, Laptop } from "lucide-react";
import { motion } from "framer-motion";
import { format, addMonths, isAfter } from "date-fns";
import { Link } from "react-router-dom";

const iconMap: Record<string, LucideIcon> = {
  Target,
  ShieldAlert,
  Plane,
  Home,
  Car,
  GraduationCap,
  Laptop,
};

interface GoalCardProps {
  goal: SavingsGoal;
}

export function GoalCard({ goal }: GoalCardProps) {
  const Icon = iconMap[goal.icon] || Target;

  const percentageComplete = Math.min(
    100,
    Math.max(0, (goal.currentAmount / goal.targetAmount) * 100)
  );

  const remainingAmount = Math.max(0, goal.targetAmount - goal.currentAmount);
  
  // Calculate predicted completion date
  let statusText = "On Track";
  let statusVariant: "default" | "secondary" | "destructive" | "outline" = "secondary";
  let predictedDate = null;

  if (goal.currentAmount >= goal.targetAmount) {
    statusText = "Completed";
    statusVariant = "default";
  } else if (goal.monthlyContribution > 0) {
    const monthsRemaining = Math.ceil(remainingAmount / goal.monthlyContribution);
    predictedDate = addMonths(new Date(), monthsRemaining);

    if (goal.targetDate) {
      const targetDateObj = new Date(goal.targetDate);
      if (isAfter(predictedDate, targetDateObj)) {
        statusText = "Behind Schedule";
        statusVariant = "destructive";
      }
    }
  } else {
    statusText = "No Contribution";
    statusVariant = "outline";
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="h-full"
    >
      <Link to={`/goals/${goal.id}`} className="block h-full">
        <Card className="h-full overflow-hidden hover:shadow-md transition-shadow cursor-pointer">
          <CardContent className="p-6 flex flex-col h-full">
          <div className="flex justify-between items-start mb-6">
            <div className="flex items-center gap-3">
              <div
                className="flex h-10 w-10 items-center justify-center rounded-xl text-white shadow-sm"
                style={{ backgroundColor: goal.color || "hsl(var(--primary))" }}
              >
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">{goal.name}</h3>
                <p className="text-sm text-muted-foreground font-medium">
                  {formatINR(goal.targetAmount)} target
                </p>
              </div>
            </div>
            <Badge variant={statusVariant} className="font-medium">
              {statusText}
            </Badge>
          </div>

          <div className="flex-grow flex flex-col justify-end">
            <div className="mb-2 flex justify-between items-end">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Saved so far</p>
                <p className="text-2xl font-bold font-display tracking-tight">
                  {formatINR(goal.currentAmount)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground mb-1">Remaining</p>
                <p className="text-sm font-semibold">{formatINR(remainingAmount)}</p>
              </div>
            </div>

            <div className="relative pt-2">
              <div className="flex justify-between text-xs font-medium mb-1.5 px-1">
                <span className="text-muted-foreground">{percentageComplete.toFixed(1)}%</span>
                {predictedDate && (
                  <span className="text-muted-foreground">
                    Goal: {format(predictedDate, "MMM yyyy")}
                  </span>
                )}
              </div>
              <Progress 
                value={percentageComplete} 
                className="h-2.5 bg-muted" 
                indicatorColor={goal.color} 
              />
            </div>

            <div className="mt-5 pt-4 border-t border-border/50 flex justify-between items-center text-sm">
              <span className="text-muted-foreground">Monthly Contribution</span>
              <span className="font-medium text-foreground">
                {formatINR(goal.monthlyContribution)}/mo
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
      </Link>
    </motion.div>
  );
}
