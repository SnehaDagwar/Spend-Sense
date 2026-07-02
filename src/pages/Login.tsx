import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Sparkles, 
  ArrowRight, 
  Mail, 
  Lock, 
  User, 
  Users, 
  GraduationCap, 
  Briefcase, 
  Laptop 
} from "lucide-react";
import { useAppStore } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { UserType } from "@/types";
import { toast } from "sonner";

const Login = () => {
  const [isLoginTab, setIsLoginTab] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  
  // Form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [userType, setUserType] = useState<UserType>("Professional");

  const { login, register } = useAppStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || (!isLoginTab && !displayName)) {
      toast.error("Please fill in all required fields.");
      return;
    }

    setIsLoading(true);
    try {
      if (isLoginTab) {
        await login(email, password);
      } else {
        await register(email, password, displayName, userType);
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Authentication failed. Please check your details.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-hero flex items-center justify-center p-4 sm:p-6 overflow-hidden">
      {/* Background ambient glowing blobs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl -z-10 animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/10 rounded-full blur-3xl -z-10 animate-pulse" style={{ animationDelay: "2s" }} />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full space-y-6"
      >
        <div className="flex flex-col items-center">
          <div className="h-14 w-14 rounded-2xl bg-gradient-accent shadow-glow flex items-center justify-center mb-3">
            <Sparkles className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-3xl font-display font-bold tracking-tight bg-clip-text text-transparent bg-gradient-accent">Spend Sense</h1>
          <p className="text-sm text-muted-foreground mt-1">Smart Wealth Intelligence</p>
        </div>

        <Card className="glass-card p-6 md:p-8 relative overflow-hidden group border border-white/10 shadow-xl">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-primary" />
          
          {/* Tab Selector */}
          <div className="grid grid-cols-2 gap-1 bg-muted/30 p-1 rounded-xl mb-6 border border-white/5">
            <button
              onClick={() => setIsLoginTab(true)}
              className={`py-2 text-sm font-semibold rounded-lg transition-all ${
                isLoginTab 
                  ? "bg-white text-foreground shadow-sm dark:bg-zinc-800" 
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setIsLoginTab(false)}
              className={`py-2 text-sm font-semibold rounded-lg transition-all ${
                !isLoginTab 
                  ? "bg-white text-foreground shadow-sm dark:bg-zinc-800" 
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Create Account
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <AnimatePresence mode="wait">
              {!isLoginTab && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-4 overflow-hidden"
                  key="register-fields"
                >
                  <div className="space-y-2">
                    <Label htmlFor="displayName">Display Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="displayName"
                        placeholder="Your display name"
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        className="pl-10 rounded-xl h-11 bg-white/50 dark:bg-zinc-900/30 border-white/20 focus:border-primary/50"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="userType">Profile Type</Label>
                    <Select 
                      value={userType} 
                      onValueChange={(v: UserType) => setUserType(v)}
                    >
                      <SelectTrigger className="rounded-xl h-11 bg-white/50 dark:bg-zinc-900/30 border-white/20">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Student">
                          <span className="flex items-center gap-2"><GraduationCap className="h-4 w-4" /> Student</span>
                        </SelectItem>
                        <SelectItem value="Family">
                          <span className="flex items-center gap-2"><Users className="h-4 w-4" /> Family</span>
                        </SelectItem>
                        <SelectItem value="Professional">
                          <span className="flex items-center gap-2"><Briefcase className="h-4 w-4" /> Professional</span>
                        </SelectItem>
                        <SelectItem value="Freelancer">
                          <span className="flex items-center gap-2"><Laptop className="h-4 w-4" /> Freelancer</span>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 rounded-xl h-11 bg-white/50 dark:bg-zinc-900/30 border-white/20 focus:border-primary/50"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 rounded-xl h-11 bg-white/50 dark:bg-zinc-900/30 border-white/20 focus:border-primary/50"
                />
              </div>
            </div>

            <Button 
              type="submit"
              disabled={isLoading}
              size="lg" 
              className="w-full mt-4 rounded-xl bg-gradient-primary text-white shadow-glow hover:scale-[1.01] active:scale-[0.99] transition-all h-12 text-sm font-semibold"
            >
              {isLoading ? (
                <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  {isLoginTab ? "Sign In" : "Register"}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </form>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          {isLoginTab 
            ? "Your financial records are stored securely on the cloud database." 
            : "By registering, you initialize a new personal secure space."
          }
        </p>
      </motion.div>
    </div>
  );
};

export default Login;
