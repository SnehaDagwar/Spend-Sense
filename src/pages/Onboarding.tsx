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
  Wallet,
  Target,
  IndianRupee,
  DollarSign,
  Euro
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

const Onboarding = () => {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    userName: "",
    income: 50000,
    currency: "INR" as "INR" | "USD" | "EUR",
    type: "Professional" as UserType,
    target: 20,
  });

  const { completeOnboarding } = useAppStore();

  const userTypes: { type: UserType; icon: any; title: string; description: string; color: string }[] = [
    { 
      type: "Student", 
      icon: GraduationCap, 
      title: "Student", 
      description: "Track pocket money, hostel expenses, subscriptions, and savings goals.",
      color: "bg-primary/10 text-primary border-primary/20"
    },
    { 
      type: "Family", 
      icon: Users, 
      title: "Family", 
      description: "Manage household budgets, family expenses, groceries, and shared goals.",
      color: "bg-secondary/10 text-secondary border-secondary/20"
    },
    { 
      type: "Professional", 
      icon: Briefcase, 
      title: "Professional", 
      description: "Track salary spending, investments, subscriptions, and monthly planning.",
      color: "bg-muted text-muted-foreground border-border"
    },
    { 
      type: "Freelancer", 
      icon: Laptop, 
      title: "Freelancer", 
      description: "Manage irregular income, project earnings, and financial stability.",
      color: "bg-accent/10 text-accent border-accent/20"
    },
  ];

  const nextStep = () => setStep(s => s + 1);
  const prevStep = () => setStep(s => s - 1);

  const handleComplete = () => {
    completeOnboarding(formData);
  };

  const containerVariants = {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
  };

  return (
    <div className="min-h-screen bg-gradient-hero flex items-center justify-center p-4 sm:p-6 overflow-hidden">
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

            <p className="text-muted-foreground max-w-md mx-auto leading-relaxed">
              Experience a new way of managing your wealth. Personalized insights, 
              predictive tracking, and smart goal management—all tailored to your lifestyle.
            </p>

            <div className="pt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
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
            key="user-type"
            variants={containerVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="max-w-4xl w-full space-y-8"
          >
            <div className="text-center">
              <h2 className="text-3xl font-display font-bold">Choose your profile</h2>
              <p className="text-muted-foreground mt-2">We'll customize your experience based on your lifestyle.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {userTypes.map((item) => (
                <Card 
                  key={item.type}
                  onClick={() => setFormData({ ...formData, type: item.type })}
                  className={cn(
                    "relative p-6 cursor-pointer border-2 transition-all duration-300 rounded-2xl overflow-hidden group hover:shadow-xl",
                    formData.type === item.type 
                      ? "border-primary bg-primary/5 shadow-glow-sm" 
                      : "border-transparent bg-white/50 hover:border-primary/20"
                  )}
                >
                  <div className="flex items-start gap-4">
                    <div className={cn("p-3 rounded-2xl shrink-0 group-hover:scale-110 transition-transform", item.color)}>
                      <item.icon className="h-6 w-6" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg mb-1">{item.title}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">{item.description}</p>
                    </div>
                  </div>
                  {formData.type === item.type && (
                    <motion.div 
                      layoutId="check"
                      className="absolute top-4 right-4 text-primary"
                    >
                      <CheckCircle2 className="h-6 w-6 fill-primary text-white" />
                    </motion.div>
                  )}
                </Card>
              ))}
            </div>

            <div className="flex justify-between items-center pt-8">
              <Button variant="ghost" onClick={prevStep} className="rounded-xl">
                <ChevronLeft className="mr-2 h-4 w-4" /> Back
              </Button>
              <Button onClick={nextStep} size="lg" className="px-8 rounded-xl bg-gradient-primary text-white shadow-glow">
                Continue <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div 
            key="personalize"
            variants={containerVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="max-w-md w-full space-y-8 glass-card p-8 md:p-10"
          >
            <div className="text-center">
              <h2 className="text-3xl font-display font-bold">Personalize</h2>
              <p className="text-muted-foreground mt-2">Just a few more details to set up your system.</p>
            </div>

            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">What should we call you?</Label>
                <Input 
                  id="name"
                  placeholder="e.g. Alex"
                  value={formData.userName}
                  onChange={(e) => setFormData({ ...formData, userName: e.target.value })}
                  className="rounded-xl h-12 bg-white/50 border-white/20 focus:border-primary/50"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="income">Monthly Income ({formData.currency})</Label>
                <div className="relative">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    {formData.currency === "INR" && <IndianRupee className="h-4 w-4" />}
                    {formData.currency === "USD" && <DollarSign className="h-4 w-4" />}
                    {formData.currency === "EUR" && <Euro className="h-4 w-4" />}
                  </div>
                  <Input 
                    id="income"
                    type="number"
                    value={formData.income}
                    onChange={(e) => setFormData({ ...formData, income: Number(e.target.value) })}
                    className="pl-10 rounded-xl h-12 bg-white/50 border-white/20 focus:border-primary/50"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="currency">Preferred Currency</Label>
                <Select 
                  value={formData.currency} 
                  onValueChange={(v: any) => setFormData({ ...formData, currency: v })}
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
                <div className="flex justify-between items-center">
                  <Label htmlFor="target">Monthly Savings Target</Label>
                  <span className="text-sm font-bold text-primary">{formData.target}%</span>
                </div>
                <input 
                  type="range"
                  min="5"
                  max="50"
                  step="5"
                  value={formData.target}
                  onChange={(e) => setFormData({ ...formData, target: Number(e.target.value) })}
                  className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <p className="text-[10px] text-muted-foreground italic text-center">
                  We'll help you save {((formData.income * formData.target) / 100).toLocaleString()} per month.
                </p>
              </div>
            </div>

            <div className="flex justify-between items-center pt-4">
              <Button variant="ghost" onClick={prevStep} className="rounded-xl">
                <ChevronLeft className="mr-2 h-4 w-4" /> Back
              </Button>
              <Button 
                onClick={handleComplete} 
                disabled={!formData.userName}
                size="lg" 
                className="px-8 rounded-xl bg-gradient-primary text-white shadow-glow"
              >
                Finish Setup <CheckCircle2 className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Progress Indicator */}
      <div className="fixed bottom-8 left-1/2 -translate-x-1/2 flex gap-2">
        {[0, 1, 2].map((i) => (
          <motion.div 
            key={i}
            animate={{ 
              width: step === i ? 24 : 8,
              backgroundColor: step === i ? "var(--primary)" : "var(--muted-foreground)"
            }}
            className="h-2 rounded-full opacity-30"
          />
        ))}
      </div>
    </div>
  );
};

const cn = (...classes: any[]) => classes.filter(Boolean).join(" ");

export default Onboarding;
