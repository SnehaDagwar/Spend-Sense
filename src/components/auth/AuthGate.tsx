import React from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles, ShieldCheck, Lock, ArrowRight, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface AuthGateProps {
  children: React.ReactNode;
  isLoggedIn: boolean;
  featureName?: string;
}

export const AuthGate = ({ children, isLoggedIn, featureName = "this feature" }: AuthGateProps) => {
  const navigate = useNavigate();

  if (isLoggedIn) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-4 sm:p-6 overflow-hidden">
      {/* Background ambient glowing blobs */}
      <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-primary/10 rounded-full blur-3xl -z-10 animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-secondary/10 rounded-full blur-3xl -z-10 animate-pulse" style={{ animationDelay: "2s" }} />

      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full space-y-6"
      >
        <Card className="glass-card p-8 md:p-10 relative overflow-hidden group border border-white/10 shadow-2xl text-center">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-primary" />
          
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="h-16 w-16 rounded-2xl bg-gradient-accent shadow-glow flex items-center justify-center">
                <Lock className="h-7 w-7 text-white" />
              </div>
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
                className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-emerald-500 flex items-center justify-center border-2 border-white dark:border-zinc-900"
              >
                <Sparkles className="h-2.5 w-2.5 text-white" />
              </motion.div>
            </div>
          </div>

          <h2 className="text-2xl font-display font-bold tracking-tight bg-clip-text text-transparent bg-gradient-accent mb-3">
            Cloud Sync Required
          </h2>
          
          <p className="text-sm text-muted-foreground leading-relaxed mb-8">
            Access to <strong>{featureName}</strong> is restricted to registered cloud users. 
            Create a free account or sign in to sync your budgets across devices, enable real-time collaboration, and secure your financial data.
          </p>

          <div className="flex flex-col gap-3">
            <Button
              onClick={() => navigate("/login")}
              size="lg"
              className="w-full rounded-xl bg-gradient-primary text-white shadow-glow hover:scale-[1.01] active:scale-[0.99] transition-all h-12 text-sm font-semibold flex items-center justify-center gap-2"
            >
              Sign In / Register
              <ArrowRight className="h-4 w-4" />
            </Button>
            
            <Button
              onClick={() => navigate(-1)}
              variant="ghost"
              size="lg"
              className="w-full rounded-xl border border-white/10 h-12 text-sm font-medium flex items-center justify-center gap-2 text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="h-4 w-4" />
              Go Back
            </Button>
          </div>
        </Card>

        <p className="text-center text-xs text-muted-foreground flex items-center justify-center gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
          Your local session data will auto-merge when you register.
        </p>
      </motion.div>
    </div>
  );
};

export default AuthGate;
