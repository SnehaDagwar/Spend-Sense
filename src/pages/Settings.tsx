import React, { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { 
  User, 
  Bell, 
  ChevronRight, 
  Save, 
  UserCircle, 
  CircleDollarSign, 
  Calendar, 
  Target,
  ShieldCheck,
  Zap,
  Clock,
  Layout,
  Trophy,
  ShieldAlert,
  LogOut,
  RefreshCcw,
  Settings2,
  MessageSquarePlus
} from "lucide-react";
import { useAppStore } from "@/store/useAppStore";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { toast } from "sonner";
import { UserType } from "@/types";
import { FeatureRequestBoard } from "@/components/feedback/FeatureRequestBoard";

const AVATARS = [
  { id: "girl", label: "Anime Girl", url: "/avatars/girl.png" },
  { id: "boy", label: "Anime Boy", url: "/avatars/boy.png" },
  { id: "woman", label: "Anime Woman", url: "/avatars/woman.png" },
  { id: "man", label: "Anime Man", url: "/avatars/man.png" },
];

const Settings = () => {
  const { settings, updateSettings, logout, resetOnboarding, resetAll } = useAppStore();
  const [localSettings, setLocalSettings] = useState(settings);
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const activeTab = searchParams.get("tab") || "profile";

  const handleTabChange = (value: string) => {
    setSearchParams({ tab: value });
  };

  const handleSave = () => {
    updateSettings(localSettings);
    toast.success("Settings saved successfully!");
  };

  const updateProfile = (field: keyof typeof settings.profile, value: any) => {
    setLocalSettings((prev) => ({
      ...prev,
      profile: { ...prev.profile, [field]: value },
    }));
  };

  const updateNotifications = (field: keyof typeof settings.notifications, value: any) => {
    setLocalSettings((prev) => ({
      ...prev,
      notifications: { ...prev.notifications, [field]: value },
    }));
  };

  const handleDeepReset = () => {
    if (window.confirm("Are you sure? This will delete all your expenses, budgets, and goals.")) {
      resetAll();
      toast.success("All data reset.");
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 },
  };

  return (
    <div className="container max-w-5xl py-8 px-4 sm:px-6">
      <header className="mb-8">
        <h1 className="text-3xl font-display font-bold gradient-text">Settings</h1>
        <p className="text-muted-foreground mt-2">Manage your account preferences and notifications.</p>
      </header>

      <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-8">
        <TabsList className="grid w-full grid-cols-4 max-w-xl bg-muted/50 p-1 backdrop-blur-sm border border-white/10 rounded-xl">
          <TabsTrigger value="profile" className="rounded-lg data-[state=active]:bg-gradient-primary data-[state=active]:text-white data-[state=active]:shadow-glow transition-all">
            <User className="h-4 w-4 mr-2" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="notifications" className="rounded-lg data-[state=active]:bg-gradient-primary data-[state=active]:text-white data-[state=active]:shadow-glow transition-all">
            <Bell className="h-4 w-4 mr-2" />
            Alerts
          </TabsTrigger>
          <TabsTrigger value="system" className="rounded-lg data-[state=active]:bg-gradient-primary data-[state=active]:text-white data-[state=active]:shadow-glow transition-all">
            <Settings2 className="h-4 w-4 mr-2" />
            System
          </TabsTrigger>
          <TabsTrigger value="feedback" className="rounded-lg data-[state=active]:bg-gradient-primary data-[state=active]:text-white data-[state=active]:shadow-glow transition-all">
            <MessageSquarePlus className="h-4 w-4 mr-2" />
            Feedback
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid gap-6"
          >
            {!settings.isLoggedIn && (
              <motion.div variants={itemVariants}>
                <Card className="border border-amber-500/20 bg-amber-500/5 relative overflow-hidden rounded-2xl p-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <h4 className="font-bold text-base text-amber-600 dark:text-amber-400">Cloud Sync & Backup Disabled</h4>
                      <p className="text-sm text-muted-foreground max-w-xl">
                        You are currently using Spend Sense locally. Create a free account or sign in to sync your budgets across devices and enable real-time collaboration.
                      </p>
                    </div>
                    <Button 
                      onClick={() => navigate("/login")} 
                      className="shrink-0 bg-amber-500 hover:bg-amber-600 text-white rounded-xl shadow-glow-sm"
                    >
                      Enable Cloud Sync
                    </Button>
                  </div>
                </Card>
              </motion.div>
            )}

            <motion.div variants={itemVariants}>
              <Card className="glass-card overflow-hidden border-white/10 shadow-xl">
                <CardHeader className="bg-gradient-to-r from-primary/10 to-transparent border-b border-white/5">
                  <div className="flex items-center gap-4">
                    <div className="relative group">
                      <Avatar className="h-20 w-20 border-2 border-primary/20 group-hover:border-primary/50 transition-all duration-300">
                        <AvatarImage src={localSettings.profile.avatar || "/avatars/girl.png"} />
                        <AvatarFallback className="bg-gradient-primary text-white text-2xl">
                          {localSettings.profile.userName.charAt(0)}
                        </AvatarFallback>
                      </Avatar>
                    </div>
                    <div>
                      <CardTitle className="text-2xl font-bold">Personal Information</CardTitle>
                      <CardDescription>Experience mode: {localSettings.userType}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-6 grid gap-6 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="userName">User Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input 
                        id="userName" 
                        value={localSettings.profile.userName}
                        onChange={(e) => updateProfile("userName", e.target.value)}
                        className="pl-10 bg-white/5 border-white/10 focus:border-primary/50 transition-all"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="userType">Experience Profile</Label>
                    <Select 
                      value={localSettings.userType} 
                      onValueChange={(v: UserType) => setLocalSettings(s => ({ ...s, userType: v }))}
                    >
                      <SelectTrigger className="bg-white/5 border-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Student">Student</SelectItem>
                        <SelectItem value="Family">Family</SelectItem>
                        <SelectItem value="Professional">Professional</SelectItem>
                        <SelectItem value="Freelancer">Freelancer</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="income">Monthly Income Default</Label>
                    <div className="relative">
                      <CircleDollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input 
                        id="income" 
                        type="number"
                        value={localSettings.profile.defaultMonthlyIncome}
                        onChange={(e) => updateProfile("defaultMonthlyIncome", Number(e.target.value))}
                        className="pl-10 bg-white/5 border-white/10 focus:border-primary/50 transition-all"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="currency">Currency Selection</Label>
                    <Select 
                      value={localSettings.profile.currency} 
                      onValueChange={(v) => updateProfile("currency", v)}
                    >
                      <SelectTrigger className="bg-white/5 border-white/10">
                        <SelectValue placeholder="Select Currency" />
                      </SelectTrigger>
                      <SelectContent className="bg-background/95 backdrop-blur-md">
                        <SelectItem value="INR">INR (₹) - Indian Rupee</SelectItem>
                        <SelectItem value="USD">USD ($) - US Dollar</SelectItem>
                        <SelectItem value="EUR">EUR (€) - Euro</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2 col-span-1 sm:col-span-2 pt-2">
                    <Label>Profile Picture</Label>
                    <div className="flex gap-4 mt-2">
                      {AVATARS.map((avatar) => {
                        const isSelected = localSettings.profile.avatar === avatar.url || (!localSettings.profile.avatar && avatar.id === "girl");
                        return (
                          <div 
                            key={avatar.id}
                            className={`cursor-pointer rounded-2xl border-2 p-1.5 transition-all ${
                              isSelected 
                                ? 'border-primary shadow-glow bg-primary/5' 
                                : 'border-transparent hover:border-border'
                            }`}
                            onClick={() => updateProfile("avatar", avatar.url)}
                          >
                            <img src={avatar.url} alt={avatar.label} className="w-16 h-16 rounded-xl bg-gray-100 shadow-sm" />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div variants={itemVariants} className="flex justify-end">
              <Button onClick={handleSave} size="lg" className="bg-gradient-primary text-white shadow-glow hover:scale-[1.02] transition-transform">
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </Button>
            </motion.div>
          </motion.div>
        </TabsContent>

        <TabsContent value="notifications">
          {/* ... existing notification cards ... */}
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid gap-6"
          >
            <motion.div variants={itemVariants}>
              <Card className="glass-card border-white/10 shadow-xl">
                <CardHeader className="bg-gradient-to-r from-primary/10 to-transparent border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-primary/20 flex items-center justify-center">
                      <Bell className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle>Alerts & Reminders</CardTitle>
                      <CardDescription>Customize how and when you want to be notified</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="grid gap-6 sm:grid-cols-2">
                    <div className="space-y-6">
                      <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:border-primary/20 transition-all group">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                            <Zap className="h-5 w-5 text-primary group-hover:scale-110 transition-transform" />
                          </div>
                          <div>
                            <Label className="font-semibold">Budget Limit Alerts</Label>
                            <p className="text-xs text-muted-foreground">Notify when reaching 80% of budget</p>
                          </div>
                        </div>
                        <Switch checked={localSettings.notifications.budgetLimit} onCheckedChange={(v) => updateNotifications("budgetLimit", v)} />
                      </div>
                      
                      <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:border-primary/20 transition-all group">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                            <ShieldCheck className="h-5 w-5 text-primary group-hover:scale-110 transition-transform" />
                          </div>
                          <div>
                            <Label className="font-semibold">Overspending Alerts</Label>
                            <p className="text-xs text-muted-foreground">Notify immediately on overspend</p>
                          </div>
                        </div>
                        <Switch checked={localSettings.notifications.overspending} onCheckedChange={(v) => updateNotifications("overspending", v)} />
                      </div>
                    </div>

                    <div className="space-y-6">
                      <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:border-primary/20 transition-all group">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                            <Clock className="h-5 w-5 text-primary group-hover:scale-110 transition-transform" />
                          </div>
                          <div>
                            <Label className="font-semibold">Daily Spending Reminders</Label>
                            <p className="text-xs text-muted-foreground">Log your expenses daily</p>
                          </div>
                        </div>
                        <Switch checked={localSettings.notifications.dailySpending} onCheckedChange={(v) => updateNotifications("dailySpending", v)} />
                      </div>

                      <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:border-primary/20 transition-all group">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                            <Trophy className="h-5 w-5 text-primary group-hover:scale-110 transition-transform" />
                          </div>
                          <div>
                            <Label className="font-semibold">Achievements</Label>
                            <p className="text-xs text-muted-foreground">Celebrate your milestones</p>
                          </div>
                        </div>
                        <Switch checked={localSettings.notifications.achievements} onCheckedChange={(v) => updateNotifications("achievements", v)} />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        </TabsContent>

        <TabsContent value="system">
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid gap-6"
          >
            <motion.div variants={itemVariants}>
              <Card className="glass-card border-white/10 shadow-xl overflow-hidden">
                <CardHeader className="bg-destructive/5 border-b border-destructive/10">
                  <div className="flex items-center gap-3">
                    <ShieldAlert className="h-5 w-5 text-destructive" />
                    <CardTitle className="text-destructive">Danger Zone</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="pt-6 space-y-6">
                  {settings.isLoggedIn ? (
                    <div className="flex items-center justify-between p-4 rounded-xl border border-border">
                      <div className="space-y-1">
                        <div className="font-bold">End Session</div>
                        <div className="text-xs text-muted-foreground">Log out of the current cloud session.</div>
                      </div>
                      <Button variant="outline" onClick={logout} className="rounded-xl gap-2">
                        <LogOut className="h-4 w-4" /> Logout
                      </Button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between p-4 rounded-xl border border-border bg-primary/5">
                      <div className="space-y-1">
                        <div className="font-bold text-primary">Enable Cloud Sync</div>
                        <div className="text-xs text-muted-foreground">Sign in to save data to the cloud database and sync devices.</div>
                      </div>
                      <Button onClick={() => navigate("/login")} className="rounded-xl bg-gradient-primary text-white gap-2 shadow-glow">
                        <User className="h-4 w-4" /> Log In / Register
                      </Button>
                    </div>
                  )}

                  <div className="flex items-center justify-between p-4 rounded-xl border border-border">
                    <div className="space-y-1">
                      <div className="font-bold">Re-run Onboarding</div>
                      <div className="text-xs text-muted-foreground">Redo the initialization process. Data remains.</div>
                    </div>
                    <Button variant="outline" onClick={resetOnboarding} className="rounded-xl gap-2">
                      <RefreshCcw className="h-4 w-4" /> Start Over
                    </Button>
                  </div>

                  <div className="flex items-center justify-between p-4 rounded-xl border border-destructive/20 bg-destructive/5">
                    <div className="space-y-1">
                      <div className="font-bold text-destructive">Factory Reset</div>
                      <div className="text-xs text-muted-foreground">Wipe ALL data and settings permanently.</div>
                    </div>
                    <Button variant="destructive" onClick={handleDeepReset} className="rounded-xl gap-2">
                      <ShieldAlert className="h-4 w-4" /> Reset All Data
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        </TabsContent>

        <TabsContent value="feedback">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid gap-6"
          >
            <motion.div variants={itemVariants}>
              <Card className="glass-card border-white/10 shadow-xl">
                <CardHeader className="bg-gradient-to-r from-violet-500/10 to-primary/5 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
                      <MessageSquarePlus className="h-5 w-5 text-violet-600" />
                    </div>
                    <div>
                      <CardTitle>Shape the Roadmap</CardTitle>
                      <CardDescription>Vote on features and share your ideas with the team</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <FeatureRequestBoard />
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Settings;
