import { useState, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useAppStore } from "@/store/useAppStore";
import { formatINR } from "@/utils/formatters";
import { 
  ArrowLeft, 
  Target, 
  Trash2, 
  Edit3, 
  TrendingUp, 
  Calendar, 
  Zap, 
  ChevronRight,
  ShieldAlert, 
  Plane, 
  Home, 
  Car, 
  GraduationCap, 
  Laptop,
  AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { format, addMonths, isAfter, startOfMonth, parseISO, eachMonthOfInterval, subMonths } from "date-fns";
import { 
  BarChart, Bar, 
  LineChart, Line, 
  XAxis, YAxis, 
  CartesianGrid, Tooltip, 
  ResponsiveContainer, AreaChart, Area 
} from "recharts";
import { toast } from "sonner";
import { 
  AlertDialog, 
  AlertDialogAction, 
  AlertDialogCancel, 
  AlertDialogContent, 
  AlertDialogDescription, 
  AlertDialogFooter, 
  AlertDialogHeader, 
  AlertDialogTitle, 
  AlertDialogTrigger 
} from "@/components/ui/alert-dialog";
import { AddGoalDialog } from "@/components/goals/AddGoalDialog";

const iconMap: Record<string, any> = {
  Target, ShieldAlert, Plane, Home, Car, GraduationCap, Laptop,
};

export default function GoalDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { goals, deleteGoal, updateGoal } = useAppStore();
  const [isEditOpen, setIsEditOpen] = useState(false);

  const goal = useMemo(() => goals.find((g) => g.id === id), [goals, id]);

  if (!goal) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold">Goal Not Found</h2>
        <p className="text-muted-foreground mt-2">The goal you are looking for does not exist or has been deleted.</p>
        <Button onClick={() => navigate("/goals")} className="mt-6" variant="outline">
          Back to Goals
        </Button>
      </div>
    );
  }

  const Icon = iconMap[goal.icon] || Target;
  const percentageComplete = Math.min(100, (goal.currentAmount / goal.targetAmount) * 100);
  const remainingAmount = Math.max(0, goal.targetAmount - goal.currentAmount);

  // Consistency Calculation
  const consistencyScore = useMemo(() => {
    if (goal.history.length === 0) return 0;
    const months = eachMonthOfInterval({
      start: subMonths(new Date(), 5),
      end: new Date(),
    });
    const contributionCount = months.filter(m => 
      goal.history.some(h => startOfMonth(parseISO(h.date)).getTime() === startOfMonth(m).getTime())
    ).length;
    return Math.round((contributionCount / months.length) * 100);
  }, [goal.history]);

  // Chart Data
  const chartData = useMemo(() => {
    const months = eachMonthOfInterval({
      start: subMonths(new Date(), 5),
      end: new Date(),
    }).map(m => format(m, "MMM"));

    let runningTotal = goal.currentAmount - goal.history.reduce((acc, h) => acc + h.amount, 0);
    
    return months.map(m => {
      const monthContributions = goal.history.filter(h => format(parseISO(h.date), "MMM") === m);
      const monthlyTotal = monthContributions.reduce((acc, h) => acc + h.amount, 0);
      runningTotal += monthlyTotal;
      return {
        month: m,
        contribution: monthlyTotal,
        total: runningTotal,
      };
    });
  }, [goal.history, goal.currentAmount]);

  // AI Insights
  const insights = useMemo(() => {
    const monthsLeft = goal.monthlyContribution > 0 ? Math.ceil(remainingAmount / goal.monthlyContribution) : Infinity;
    const projectedDate = goal.monthlyContribution > 0 ? addMonths(new Date(), monthsLeft) : null;
    
    const messages = [];
    
    if (consistencyScore > 80) {
      messages.push({
        title: "Incredible Consistency!",
        text: "You've been saving regularly for the last 6 months. Keep this momentum up!",
        type: "success"
      });
    } else if (consistencyScore < 50) {
      messages.push({
        title: "Consistency Warning",
        text: "You've missed a few months of contributions. Setting up automatic transfers could help.",
        type: "warning"
      });
    }

    if (goal.targetDate && projectedDate && isAfter(projectedDate, new Date(goal.targetDate))) {
      const extraNeeded = Math.ceil(remainingAmount / (Math.max(1, (new Date(goal.targetDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24 * 30.44)))) - goal.monthlyContribution;
      messages.push({
        title: "Action Required",
        text: `You are behind schedule. Increase your monthly contribution by ${formatINR(extraNeeded)} to hit your target date.`,
        type: "destructive"
      });
    } else {
      messages.push({
        title: "On Track",
        text: "You are currently on track to reach your goal by the predicted date.",
        type: "info"
      });
    }

    return messages;
  }, [goal, remainingAmount, consistencyScore]);

  const handleDelete = () => {
    deleteGoal(goal.id);
    toast.success("Goal deleted successfully");
    navigate("/goals");
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8 animate-in fade-in duration-500">
      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => navigate("/goals")} className="gap-2 -ml-4 text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          Back to Goals
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setIsEditOpen(true)} className="gap-2">
            <Edit3 className="h-4 w-4" />
            Edit Goal
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2 text-destructive hover:bg-destructive/10">
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. This will permanently delete the "{goal.name}" goal and all its history.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                  Delete Goal
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      {/* Hero Header */}
      <div className="flex flex-col md:flex-row gap-8 items-start md:items-center">
        <div 
          className="h-20 w-20 rounded-3xl flex items-center justify-center text-white shadow-lg"
          style={{ backgroundColor: goal.color || "hsl(var(--primary))" }}
        >
          <Icon className="h-10 w-10" />
        </div>
        <div className="flex-grow space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-4xl font-bold font-display tracking-tight">{goal.name}</h1>
            <Badge variant={percentageComplete >= 100 ? "default" : "secondary"} className="h-6">
              {percentageComplete >= 100 ? "Completed" : "Active"}
            </Badge>
          </div>
          <p className="text-xl text-muted-foreground font-medium">
            Progress: {formatINR(goal.currentAmount)} of {formatINR(goal.targetAmount)}
          </p>
        </div>
      </div>

      {/* Progress Section */}
      <div className="space-y-4">
        <div className="flex justify-between text-sm font-semibold">
          <span>{percentageComplete.toFixed(1)}% Complete</span>
          <span>{formatINR(remainingAmount)} Remaining</span>
        </div>
        <Progress 
          value={percentageComplete} 
          className="h-4 bg-muted" 
          indicatorColor={goal.color} 
        />
      </div>

      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card className="bg-gradient-to-br from-primary/5 to-transparent border-primary/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-primary mb-2">
              <Zap className="h-5 w-5" />
              <span className="text-sm font-bold uppercase tracking-wider">Consistency</span>
            </div>
            <p className="text-3xl font-bold font-display">{consistencyScore}%</p>
            <p className="text-xs text-muted-foreground mt-1">Based on monthly contributions</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-blue-600 mb-2">
              <Calendar className="h-5 w-5" />
              <span className="text-sm font-bold uppercase tracking-wider">Predicted Date</span>
            </div>
            <p className="text-3xl font-bold font-display">
              {goal.monthlyContribution > 0 
                ? format(addMonths(new Date(), Math.ceil(remainingAmount / goal.monthlyContribution)), "MMM yyyy")
                : "N/A"
              }
            </p>
            <p className="text-xs text-muted-foreground mt-1">Based on current saving rate</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-green-600 mb-2">
              <TrendingUp className="h-5 w-5" />
              <span className="text-sm font-bold uppercase tracking-wider">Saving Rate</span>
            </div>
            <p className="text-3xl font-bold font-display">{formatINR(goal.monthlyContribution)}</p>
            <p className="text-xs text-muted-foreground mt-1">Target monthly contribution</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Goal Growth</CardTitle>
            <CardDescription>Visualizing your savings over time</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={goal.color || "hsl(var(--primary))"} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={goal.color || "hsl(var(--primary))"} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{fill: "hsl(var(--muted-foreground))", fontSize: 12}} />
                <YAxis hide />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: "hsl(var(--background))", 
                    borderColor: "hsl(var(--border))",
                    borderRadius: "12px",
                    boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)"
                  }} 
                  formatter={(v: number) => formatINR(v)}
                />
                <Area 
                  type="monotone" 
                  dataKey="total" 
                  stroke={goal.color || "hsl(var(--primary))"} 
                  fillOpacity={1} 
                  fill="url(#colorTotal)" 
                  strokeWidth={3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Monthly Contributions</CardTitle>
            <CardDescription>Amount saved each month</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{fill: "hsl(var(--muted-foreground))", fontSize: 12}} />
                <YAxis hide />
                <Tooltip 
                  cursor={{fill: "hsl(var(--muted))", opacity: 0.4}}
                  contentStyle={{ 
                    backgroundColor: "hsl(var(--background))", 
                    borderColor: "hsl(var(--border))",
                    borderRadius: "12px"
                  }}
                  formatter={(v: number) => formatINR(v)}
                />
                <Bar 
                  dataKey="contribution" 
                  fill={goal.color || "hsl(var(--primary))"} 
                  radius={[6, 6, 0, 0]} 
                  barSize={32}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Insights & History */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-6">
          <h2 className="text-xl font-bold font-display flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" /> AI Insights
          </h2>
          <div className="space-y-4">
            {insights.map((insight, idx) => (
              <Card key={idx} className={`border-l-4 ${
                insight.type === "destructive" ? "border-l-destructive bg-destructive/5" : 
                insight.type === "success" ? "border-l-green-500 bg-green-500/5" : 
                "border-l-blue-500 bg-blue-500/5"
              }`}>
                <CardContent className="pt-4">
                  <p className="font-bold text-sm mb-1">{insight.title}</p>
                  <p className="text-sm text-muted-foreground leading-relaxed">{insight.text}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-xl font-bold font-display">Contribution History</h2>
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <div className="divide-y divide-border">
                {goal.history.length === 0 ? (
                  <div className="p-8 text-center text-muted-foreground italic">No history yet.</div>
                ) : (
                  goal.history.sort((a, b) => parseISO(b.date).getTime() - parseISO(a.date).getTime()).map((h, i) => (
                    <div key={i} className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                          <TrendingUp className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-semibold">{formatINR(h.amount)}</p>
                          <p className="text-xs text-muted-foreground">{format(parseISO(h.date), "MMMM dd, yyyy")}</p>
                        </div>
                      </div>
                      <Badge variant="outline">Confirmed</Badge>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <AddGoalDialog 
        open={isEditOpen} 
        onOpenChange={setIsEditOpen} 
        editingGoal={goal} 
      />
    </div>
  );
}
