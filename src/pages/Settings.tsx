import React, { useState } from "react";
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
  Trophy
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

const Settings = () => {
  const { settings, updateSettings } = useAppStore();
  const [localSettings, setLocalSettings] = useState(settings);

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

      <Tabs defaultValue="profile" className="space-y-8">
        <TabsList className="grid w-full grid-cols-2 max-w-md bg-muted/50 p-1 backdrop-blur-sm border border-white/10 rounded-xl">
          <TabsTrigger value="profile" className="rounded-lg data-[state=active]:bg-gradient-primary data-[state=active]:text-white data-[state=active]:shadow-glow transition-all">
            <User className="h-4 w-4 mr-2" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="notifications" className="rounded-lg data-[state=active]:bg-gradient-primary data-[state=active]:text-white data-[state=active]:shadow-glow transition-all">
            <Bell className="h-4 w-4 mr-2" />
            Notifications
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid gap-6"
          >
            {/* User Profile Card */}
            <motion.div variants={itemVariants}>
              <Card className="glass-card overflow-hidden border-white/10 shadow-xl">
                <CardHeader className="bg-gradient-to-r from-primary/10 to-transparent border-b border-white/5">
                  <div className="flex items-center gap-4">
                    <div className="relative group">
                      <Avatar className="h-20 w-20 border-2 border-primary/20 group-hover:border-primary/50 transition-all duration-300">
                        <AvatarImage src={localSettings.profile.avatar} />
                        <AvatarFallback className="bg-gradient-primary text-white text-2xl">
                          {localSettings.profile.userName.charAt(0)}
                        </AvatarFallback>
                      </Avatar>
                      <button className="absolute bottom-0 right-0 p-1.5 bg-white text-primary rounded-full shadow-lg border border-primary/10 hover:scale-110 transition-transform">
                        <UserCircle className="h-4 w-4" />
                      </button>
                    </div>
                    <div>
                      <CardTitle className="text-2xl font-bold">Personal Information</CardTitle>
                      <CardDescription>Update your basic profile details</CardDescription>
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
                  <div className="space-y-2">
                    <Label htmlFor="goals">Financial Goals Preference</Label>
                    <div className="relative">
                      <Target className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input 
                        id="goals" 
                        value={localSettings.profile.financialGoalsPreference}
                        onChange={(e) => updateProfile("financialGoalsPreference", e.target.value)}
                        className="pl-10 bg-white/5 border-white/10 focus:border-primary/50 transition-all"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="startDay">Preferred Start Day of Month</Label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input 
                        id="startDay" 
                        type="number"
                        min={1}
                        max={31}
                        value={localSettings.profile.preferredStartDay}
                        onChange={(e) => updateProfile("preferredStartDay", Number(e.target.value))}
                        className="pl-10 bg-white/5 border-white/10 focus:border-primary/50 transition-all"
                      />
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
                    {/* Notification Toggles */}
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
                        <Switch 
                          checked={localSettings.notifications.budgetLimit}
                          onCheckedChange={(v) => updateNotifications("budgetLimit", v)}
                        />
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
                        <Switch 
                          checked={localSettings.notifications.overspending}
                          onCheckedChange={(v) => updateNotifications("overspending", v)}
                        />
                      </div>

                      <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:border-primary/20 transition-all group">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                            <Target className="h-5 w-5 text-primary group-hover:scale-110 transition-transform" />
                          </div>
                          <div>
                            <Label className="font-semibold">Goal Reminders</Label>
                            <p className="text-xs text-muted-foreground">Stay on track with your goals</p>
                          </div>
                        </div>
                        <Switch 
                          checked={localSettings.notifications.goalReminders}
                          onCheckedChange={(v) => updateNotifications("goalReminders", v)}
                        />
                      </div>
                    </div>

                    <div className="space-y-6">
                      <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:border-primary/20 transition-all group">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                            <Layout className="h-5 w-5 text-primary group-hover:scale-110 transition-transform" />
                          </div>
                          <div>
                            <Label className="font-semibold">Weekly Financial Summaries</Label>
                            <p className="text-xs text-muted-foreground">Get a recap of your week</p>
                          </div>
                        </div>
                        <Switch 
                          checked={localSettings.notifications.weeklySummary}
                          onCheckedChange={(v) => updateNotifications("weeklySummary", v)}
                        />
                      </div>

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
                        <Switch 
                          checked={localSettings.notifications.dailySpending}
                          onCheckedChange={(v) => updateNotifications("dailySpending", v)}
                        />
                      </div>

                      <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:border-primary/20 transition-all group">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                            <Trophy className="h-5 w-5 text-primary group-hover:scale-110 transition-transform" />
                          </div>
                          <div>
                            <Label className="font-semibold">Achievement Notifications</Label>
                            <p className="text-xs text-muted-foreground">Celebrate your milestones</p>
                          </div>
                        </div>
                        <Switch 
                          checked={localSettings.notifications.achievements}
                          onCheckedChange={(v) => updateNotifications("achievements", v)}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="mt-8 p-6 rounded-2xl bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/20">
                    <div className="grid gap-6 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="timing">Notification Timing</Label>
                        <Select 
                          value={localSettings.notifications.timing} 
                          onValueChange={(v) => updateNotifications("timing", v)}
                        >
                          <SelectTrigger className="bg-white/5 border-white/10">
                            <SelectValue placeholder="Choose Timing" />
                          </SelectTrigger>
                          <SelectContent className="bg-background/95 backdrop-blur-md">
                            <SelectItem value="Morning">Morning (8:00 AM)</SelectItem>
                            <SelectItem value="Evening">Evening (8:00 PM)</SelectItem>
                            <SelectItem value="Custom">Custom Time</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {localSettings.notifications.timing === "Custom" && (
                        <div className="space-y-2">
                          <Label htmlFor="customTime">Custom Time</Label>
                          <Input 
                            id="customTime" 
                            type="time"
                            value={localSettings.notifications.customTime}
                            onChange={(e) => updateNotifications("customTime", e.target.value)}
                            className="bg-white/5 border-white/10 focus:border-primary/50 transition-all"
                          />
                        </div>
                      )}
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
      </Tabs>
    </div>
  );
};

export default Settings;
