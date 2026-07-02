import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Sparkles, 
  GraduationCap, 
  Users, 
  Briefcase, 
  Laptop, 
  ChevronRight, 
  ChevronLeft,
  CheckCircle2,
  IndianRupee,
  DollarSign,
  Euro,
  Brain,
  Trophy,
  ShieldCheck,
  BarChart3
} from "lucide-react";
import { useAppStore } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { UserType } from "@/types";

const FEATURE_HIGHLIGHTS = [
  { icon: Brain, label: "AI-powered insights", color: "text-violet-500 bg-violet-50" },
  { icon: BarChart3, label: "Smart budget tracking", color: "text-blue-500 bg-blue-50" },
  { icon: Trophy, label: "Gamified streaks & badges", color: "text-amber-500 bg-amber-50" },
  { icon: ShieldCheck, label: "Goal-based savings", color: "text-green-500 bg-green-50" },
];

const TOTAL_STEPS = 2;

function StepProgressBar({ current }: { current: number }) {
  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 flex items-center gap-2 z-10">
      {Array.from({ length: TOTAL_STEPS }, (_, i) => (
        <motion.div
          key={i}
          animate={{
            width: current === i ? 28 : 8,
            backgroundColor:
              i < current
                ? "var(--primary)"
                : current === i
                ? "var(--primary)"
                : "#d1d5db",
            opacity: i <= current ? 1 : 0.4,
          }}
          transition={{ duration: 0.3 }}
          className="h-2 rounded-full"
        />
      ))}
    </div>
  );
}

const Onboarding = () => {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    userName: "",
    income: 0,
    currency: "INR" as "INR" | "USD" | "EUR",
    profession: "Employee" as string,
    type: "Professional" as UserType,
    target: 20,
  });

  const { completeOnboarding } = useAppStore();

  const professions: { id: string; type: UserType; icon: React.ComponentType<{ className?: string }>; title: string; description: string; color: string }[] = [
    { 
      id: "Student",
      type: "Student", 
      icon: GraduationCap, 
      title: "Student", 
      description: "Track pocket money, college expenses, and savings goals.",
      color: "bg-primary/10 text-primary border-primary/20"
    },
    { 
      id: "Employee",
      type: "Professional", 
      icon: Briefcase, 
      title: "Employee", 
      description: "Track salary budgets, bills, subscriptions, and savings.",
      color: "bg-violet-500/10 text-violet-500 border-violet-500/20"
    },
    { 
      id: "Business",
      type: "Professional", 
      icon: Users, 
      title: "Business Owner", 
      description: "Manage business operations, cash flows, and growth targets.",
      color: "bg-blue-500/10 text-blue-500 border-blue-500/20"
    },
    { 
      id: "Freelancer",
      type: "Freelancer", 
      icon: Laptop, 
      title: "Freelancer", 
      description: "Track irregular client invoices, gig earnings, and savings.",
      color: "bg-amber-500/10 text-amber-500 border-amber-500/20"
    },
    { 
      id: "Other",
      type: "Professional", 
      icon: Sparkles, 
      title: "Other", 
      description: "General personal finance and custom milestone planning.",
      color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
    },
  ];

  const [isCompleting, setIsCompleting] = useState(false);

  const nextStep = () => setStep(s => s + 1);
  const prevStep = () => setStep(s => s - 1);

  const handleComplete = async () => {
    setIsCompleting(true);
    try {
      await completeOnboarding({
        userName: formData.userName,
        income: formData.income || 0,
        currency: formData.currency,
        type: formData.type,
        target: formData.target,
      });
    } finally {
      setIsCompleting(false);
    }
  };

  const containerVariants = {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
  };

  return (
    <div className="min-h-screen bg-gradient-hero flex items-center justify-center p-4 sm:p-6 overflow-hidden">
      {/* Background ambient glowing blobs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl -z-10 animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/10 rounded-full blur-3xl -z-10 animate-pulse" style={{ animationDelay: "2s" }} />

      {/* Step progress bar — visible on steps 1+ */}
      {step > 0 && <StepProgressBar current={step - 1} />}

      <AnimatePresence mode="wait">
        {step === 0 && (
          <motion.div 
            key="welcome"
            variants={containerVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="max-w-2xl w-full text-center space-y-8"
          >
            <div className="flex flex-col items-center">
              <motion.div 
                initial={{ scale: 0, rotate: -20 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: "spring", damping: 12 }}
                className="h-20 w-20 rounded-2xl bg-gradient-accent shadow-glow flex items-center justify-center mb-6"
              >
                <Sparkles className="h-10 w-10 text-white" />
              </motion.div>
              <h1 className="text-4xl sm:text-6xl font-display font-bold tracking-tight">
                <span className="bg-clip-text text-transparent bg-gradient-accent">Spend Sense</span>
              </h1>
              <p className="mt-4 text-xl sm:text-2xl text-muted-foreground font-medium">
                Your AI-powered personal finance intelligence system
              </p>
            </div>

            {/* Feature highlights */}
            <div className="grid grid-cols-2 gap-3 max-w-sm mx-auto">
              {FEATURE_HIGHLIGHTS.map(({ icon: Icon, label, color }, i) => (
                <motion.div
                  key={label}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + i * 0.1 }}
                  className="flex items-center gap-2.5 bg-white/60 backdrop-blur-sm rounded-2xl px-3 py-2.5 border border-white/30 shadow-sm"
                >
                  <div className={`h-7 w-7 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
                    <Icon className="h-3.5 w-3.5" />
                  </div>
                  <span className="text-xs font-semibold text-gray-700 leading-tight">{label}</span>
                </motion.div>
              ))}
            </div>

            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button 
                onClick={nextStep}
                size="lg" 
                className="w-full sm:w-auto px-12 rounded-2xl bg-gradient-primary text-white shadow-glow hover:scale-105 transition-all text-lg h-14"
              >
                Get Started
                <ChevronRight className="ml-2 h-5 w-5" />
              </Button>
            </div>
          </motion.div>
        )}

        {step === 1 && (
          <motion.div 
            key="profile-setup"
            variants={containerVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="max-w-2xl w-full space-y-6 glass-card p-6 sm:p-8 border border-white/10 shadow-xl"
          >
            <div className="text-center mb-4">
              <h2 className="text-3xl font-display font-bold">Tell us about yourself</h2>
              <p className="text-muted-foreground mt-2">Let's customize Spend Sense to match your lifestyle.</p>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="userName" className="text-sm font-semibold">What is your name?</Label>
                <Input 
                  id="userName"
                  placeholder="e.g. Alex"
                  value={formData.userName}
                  onChange={(e) => setFormData({ ...formData, userName: e.target.value })}
                  className="rounded-xl h-12 bg-white/50 border-white/20 focus:border-primary/50 text-base"
                />
              </div>

              <div className="space-y-2 pt-2">
                <Label className="text-sm font-semibold">What is your profession?</Label>
                <div className="grid grid-cols-1 gap-2.5 max-h-[280px] overflow-y-auto pr-1">
                  {professions.map((item) => (
                    <Card 
                      key={item.id}
                      onClick={() => setFormData({ ...formData, profession: item.id, type: item.type })}
                      className={cn(
                        "relative p-4 cursor-pointer border-2 transition-all duration-200 rounded-xl overflow-hidden group",
                        formData.profession === item.id 
                          ? "border-primary bg-primary/5 shadow-glow-sm" 
                          : "border-transparent bg-white/40 hover:border-primary/20"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <div className={cn("p-2.5 rounded-xl shrink-0 group-hover:scale-105 transition-transform", item.color)}>
                          <item.icon className="h-5 w-5" />
                        </div>
                        <div>
                          <h3 className="font-bold text-sm text-foreground">{item.title}</h3>
                          <p className="text-xs text-muted-foreground leading-normal mt-0.5">{item.description}</p>
                        </div>
                      </div>
                      {formData.profession === item.id && (
                        <motion.div 
                          layoutId="check"
                          className="absolute top-1/2 -translate-y-1/2 right-4 text-primary"
                        >
                          <CheckCircle2 className="h-5 w-5 fill-primary text-white" />
                        </motion.div>
                      )}
                    </Card>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-white/10">
              <Button variant="ghost" onClick={prevStep} className="rounded-xl">
                <ChevronLeft className="mr-2 h-4 w-4" /> Back
              </Button>
              <Button 
                onClick={nextStep} 
                disabled={!formData.userName.trim()}
                size="lg" 
                className="px-8 rounded-xl bg-gradient-primary text-white shadow-glow"
              >
                Continue <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div 
            key="financial-setup"
            variants={containerVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="max-w-md w-full space-y-6 glass-card p-6 sm:p-8 border border-white/10 shadow-xl"
          >
            <div className="text-center">
              <h2 className="text-3xl font-display font-bold">Financial Setup</h2>
              <p className="text-muted-foreground mt-2">Customize your default budget and goals.</p>
            </div>

            <div className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="currency" className="text-sm font-semibold">Preferred Currency</Label>
                <Select 
                  value={formData.currency} 
                  onValueChange={(v: "INR" | "USD" | "EUR") => setFormData({ ...formData, currency: v })}
                >
                  <SelectTrigger className="rounded-xl h-12 bg-white/50 border-white/20">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="INR">INR (₹) - Indian Rupee</SelectItem>
                    <SelectItem value="USD">USD ($) - US Dollar</SelectItem>
                    <SelectItem value="EUR">EUR (€) - Euro</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="income" className="text-sm font-semibold flex justify-between">
                  Monthly Income <span className="text-xs text-muted-foreground font-normal">(Optional)</span>
                </Label>
                <div className="relative">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    {formData.currency === "INR" && <IndianRupee className="h-4 w-4" />}
                    {formData.currency === "USD" && <DollarSign className="h-4 w-4" />}
                    {formData.currency === "EUR" && <Euro className="h-4 w-4" />}
                  </div>
                  <Input 
                    id="income"
                    type="number"
                    placeholder="Enter monthly income"
                    value={formData.income || ""}
                    onChange={(e) => setFormData({ ...formData, income: Number(e.target.value) })}
                    className="pl-10 rounded-xl h-12 bg-white/50 border-white/20 focus:border-primary/50 text-base"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <Label htmlFor="target" className="text-sm font-semibold flex justify-between w-full">
                    Savings Target <span className="text-xs text-muted-foreground font-normal">(Optional)</span>
                  </Label>
                  <span className="text-sm font-bold text-primary">{formData.target}%</span>
                </div>
                <input 
                  id="target"
                  type="range"
                  min="5"
                  max="50"
                  step="5"
                  value={formData.target}
                  onChange={(e) => setFormData({ ...formData, target: Number(e.target.value) })}
                  className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                />
                {formData.income > 0 ? (
                  <p className="text-[10px] text-muted-foreground italic text-center">
                    We'll help you save {((formData.income * formData.target) / 100).toLocaleString(undefined, { style: "currency", currency: formData.currency, maximumFractionDigits: 0 })} per month.
                  </p>
                ) : (
                  <p className="text-[10px] text-muted-foreground italic text-center">
                    Set a monthly percentage-based goal to track your saving discipline.
                  </p>
                )}
              </div>
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-white/10">
              <Button variant="ghost" onClick={prevStep} className="rounded-xl">
                <ChevronLeft className="mr-2 h-4 w-4" /> Back
              </Button>
              <Button 
                onClick={handleComplete} 
                disabled={isCompleting}
                size="lg" 
                className="px-8 rounded-xl bg-gradient-primary text-white shadow-glow"
              >
                {isCompleting ? (
                  <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    Finish Setup <CheckCircle2 className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Step labels */}
      {step > 0 && (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 text-center">
          <p className="text-xs text-muted-foreground font-medium">
            Step {step} of {TOTAL_STEPS}
          </p>
        </div>
      )}
    </div>
  );
};

const cn = (...classes: (string | undefined | null | false)[]) => classes.filter(Boolean).join(" ");

export default Onboarding;
