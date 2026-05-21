import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import AppLayout from "@/components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import BudgetSetup from "./pages/BudgetSetup";
import ExpenseTracker from "./pages/ExpenseTracker";
import Analytics from "./pages/Analytics";
import Insights from "./pages/Insights";
import Reports from "./pages/Reports";
import SavingsGoals from "./pages/SavingsGoals";
import GoalDetail from "./pages/GoalDetail";
import Streaks from "./pages/Streaks";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound.tsx";

import { AnimatePresence, motion } from "framer-motion";
import { useAppStore } from "@/store/useAppStore";
import Onboarding from "./pages/Onboarding";
import Login from "./pages/Login";

import FamilyWallet from "./pages/family/FamilyWallet";
import FamilyMembers from "./pages/family/FamilyMembers";
import SplitSettle from "./pages/family/SplitSettle";

const queryClient = new QueryClient();

const AnimatedRoutes = () => {
  const location = useLocation();
  const { settings } = useAppStore();
  const { onboardingCompleted, isLoggedIn } = settings;

  // If onboarding not completed, only allow access to Onboarding page
  if (!onboardingCompleted) {
    return (
      <AnimatePresence mode="wait">
        <Routes location={location} key="onboarding">
          <Route path="*" element={<Onboarding />} />
        </Routes>
      </AnimatePresence>
    );
  }

  // If not logged in (local session), show login screen
  if (!isLoggedIn) {
    return (
      <AnimatePresence mode="wait">
        <Routes location={location} key="login">
          <Route path="*" element={<Login />} />
        </Routes>
      </AnimatePresence>
    );
  }

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<PageWrapper><Dashboard /></PageWrapper>} />
          <Route path="/budget" element={<PageWrapper><BudgetSetup /></PageWrapper>} />
          <Route path="/tracker" element={<PageWrapper><ExpenseTracker /></PageWrapper>} />
          <Route path="/analytics" element={<PageWrapper><Analytics /></PageWrapper>} />
          <Route path="/insights" element={<PageWrapper><Insights /></PageWrapper>} />
          <Route path="/reports" element={<PageWrapper><Reports /></PageWrapper>} />
          <Route path="/goals" element={<PageWrapper><SavingsGoals /></PageWrapper>} />
          <Route path="/goals/:id" element={<PageWrapper><GoalDetail /></PageWrapper>} />
          <Route path="/streaks" element={<PageWrapper><Streaks /></PageWrapper>} />
          <Route path="/settings" element={<PageWrapper><Settings /></PageWrapper>} />

          {/* Family Wallet Routes */}
          {settings.userType === "Family" && (
            <>
              <Route path="/family" element={<PageWrapper><FamilyWallet /></PageWrapper>} />
              <Route path="/family/members" element={<PageWrapper><FamilyMembers /></PageWrapper>} />
              <Route path="/family/settle" element={<PageWrapper><SplitSettle /></PageWrapper>} />
            </>
          )}
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AnimatePresence>
  );
};


const PageWrapper = ({ children }: { children: React.ReactNode }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    transition={{ duration: 0.3, ease: "easeInOut" }}
  >
    {children}
  </motion.div>
);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AnimatedRoutes />
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
