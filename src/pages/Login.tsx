import React from "react";
import { motion } from "framer-motion";
import { 
  Sparkles, 
  ArrowRight, 
  UserCircle2, 
  LogOut, 
  RefreshCcw 
} from "lucide-react";
import { useAppStore } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const Login = () => {
  const { settings, login, resetOnboarding, resetAll } = useAppStore();
  const { userName, avatar } = settings.profile;

  const handleReset = () => {
    if (window.confirm("Are you sure you want to reset everything? This will delete all your financial data.")) {
      resetAll();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-hero flex items-center justify-center p-4 sm:p-6 overflow-hidden">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full space-y-8"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="h-16 w-16 rounded-2xl bg-gradient-primary shadow-glow flex items-center justify-center mb-4">
            <Sparkles className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-display font-bold tracking-tight">Spend Sense</h1>
        </div>

        <Card className="glass-card p-8 text-center space-y-6 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-primary" />
          
          <div className="flex flex-col items-center">
            <div className="h-24 w-24 rounded-full border-4 border-primary/20 p-1 mb-4 bg-muted overflow-hidden">
              {avatar ? (
                <img src={avatar} alt={userName} className="h-full w-full object-cover" />
              ) : (
                <UserCircle2 className="h-full w-full text-muted-foreground" />
              )}
            </div>
            <h2 className="text-2xl font-bold">Welcome back, {userName}</h2>
            <p className="text-muted-foreground text-sm">{settings.userType} Profile</p>
          </div>

          <Button 
            onClick={login}
            size="lg" 
            className="w-full rounded-2xl bg-gradient-primary text-white shadow-glow hover:scale-[1.02] active:scale-[0.98] transition-all h-14 text-lg"
          >
            Continue Session
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>

          <div className="pt-4 grid grid-cols-2 gap-3">
            <Button 
              variant="outline" 
              onClick={resetOnboarding}
              className="rounded-xl h-11 text-xs gap-2 border-primary/20 hover:bg-primary/5"
            >
              <RefreshCcw className="h-3 w-3" /> Re-setup Profile
            </Button>
            <Button 
              variant="outline" 
              onClick={handleReset}
              className="rounded-xl h-11 text-xs gap-2 border-destructive/20 hover:bg-destructive/5 text-destructive"
            >
              <LogOut className="h-3 w-3" /> Reset Everything
            </Button>
          </div>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          All your data is stored locally on this device.
        </p>
      </motion.div>
    </div>
  );
};

export default Login;
