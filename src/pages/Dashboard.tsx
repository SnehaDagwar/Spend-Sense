import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useAppStore, useActiveBudget, useMonthExpenses } from "@/store/useAppStore";
import { computeStats } from "@/engine/predictionEngine";
import { formatINR } from "@/utils/formatters";
import { Wallet, Users, Clock, Plus, Settings, ChevronRight, X, Calendar, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";

export default function Dashboard() {
  const budget = useActiveBudget();
  const expenses = useMonthExpenses();
  const settings = useAppStore((s) => s.settings);
  const { userName } = settings.profile;

  const stats = useMemo(() => computeStats(budget, expenses), [budget, expenses]);

  const statCards = [
    {
      title: "Total Monthly Budget",
      value: formatINR(stats.income),
      icon: <Wallet className="h-5 w-5 text-red-500" />,
      iconBg: "bg-red-50",
    },
    {
      title: "Total Spent This Month",
      value: formatINR(stats.totalActual),
      icon: <Users className="h-5 w-5 text-blue-500" />,
      iconBg: "bg-blue-50",
    },
    {
      title: "Remaining Budget",
      value: formatINR(Math.max(0, stats.income - stats.totalActual)),
      icon: <Calendar className="h-5 w-5 text-yellow-500" />,
      iconBg: "bg-yellow-50",
    },
    {
      title: "Active Savings Streak",
      value: `${useAppStore((s) => s.savingsStreak)} days`,
      icon: <Clock className="h-5 w-5 text-green-500" />,
      iconBg: "bg-green-50",
    },
  ];

  return (
    <div className="flex flex-col gap-8 animate-in fade-in duration-500">
      
      {/* Top Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Hero Card */}
        <div className="lg:col-span-2 relative bg-white rounded-[24px] shadow-sm p-8 md:p-12 overflow-hidden flex items-center border border-gray-100/50">
          <div className="relative z-10 w-full max-w-sm">
            <h1 className="text-4xl md:text-5xl font-display font-medium tracking-tight text-gray-900 mb-2">
              Hi, {userName}!
            </h1>
            <p className="text-gray-500 text-lg mb-8">What are we doing today?</p>
            
            <div className="grid grid-cols-2 gap-y-4 gap-x-8">
              <Link to="/analytics" className="flex items-center gap-3 text-sm font-medium text-gray-700 hover:text-primary transition-colors group">
                <span className="flex items-center justify-center w-6 h-6 rounded-full border border-gray-200 group-hover:border-primary">
                  <CheckCircle2 className="w-4 h-4 text-gray-400 group-hover:text-primary" />
                </span>
                View Analytics
              </Link>
              <Link to="/budget" className="flex items-center gap-3 text-sm font-medium text-gray-700 hover:text-primary transition-colors group">
                <span className="flex items-center justify-center w-6 h-6 rounded-full border border-gray-200 group-hover:border-primary">
                  <Wallet className="w-4 h-4 text-yellow-400 group-hover:text-primary" />
                </span>
                Set Budget
              </Link>
              <Link to="/tracker" className="flex items-center gap-3 text-sm font-medium text-primary hover:text-primary/80 transition-colors group">
                <span className="flex items-center justify-center w-6 h-6 rounded-full border border-red-200 bg-red-50">
                  <Plus className="w-4 h-4 text-red-500" />
                </span>
                <span className="border-b border-primary border-dashed">Log Expense</span>
              </Link>
              <Link to="/insights" className="flex items-center gap-3 text-sm font-medium text-gray-700 hover:text-primary transition-colors group">
                <span className="flex items-center justify-center w-6 h-6 rounded-full border border-gray-200 group-hover:border-primary">
                  <Settings className="w-4 h-4 text-blue-400 group-hover:text-primary" />
                </span>
                Smart Insights
              </Link>
            </div>
          </div>
          
          {/* Mascot Image */}
          <div className="absolute right-0 bottom-0 w-[45%] h-[120%] flex items-end justify-center hidden sm:flex pointer-events-none">
            <img 
              src="/mascot.png" 
              alt="Mascot" 
              className="w-full h-full object-contain object-bottom drop-shadow-2xl translate-x-12 translate-y-8" 
            />
          </div>
        </div>

        {/* Right Notifications Panel */}
        <div className="lg:col-span-1 flex flex-col">
          <div className="flex items-center justify-between mb-4 px-2">
            <h3 className="flex items-center gap-2 font-display text-lg font-medium text-gray-900">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>
              Notifications
            </h3>
            <Link to="/settings?tab=notifications" className="text-sm font-medium text-primary hover:underline">See all</Link>
          </div>
          
          <div className="flex flex-col gap-3">
            <div className="bg-white rounded-[20px] p-4 flex items-start gap-4 shadow-sm border border-gray-100/50 relative group cursor-pointer hover:shadow-md transition-shadow">
              <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-yellow-400 flex items-center justify-center text-white shadow-inner">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
              </div>
              <div className="flex-1 pr-6 pt-1">
                <p className="text-sm text-gray-700 font-medium leading-snug">You're close to exceeding your 'Dining Out' budget.</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-400 absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>

            <div className="bg-white rounded-[20px] p-4 flex items-start gap-4 shadow-sm border border-gray-100/50 relative group cursor-pointer hover:shadow-md transition-shadow">
              <div className="absolute -right-2 -top-2 w-6 h-6 bg-blue-100 text-blue-500 rounded-full flex items-center justify-center text-xs shadow-sm z-10 cursor-pointer hover:bg-blue-200">
                <X className="w-3 h-3" />
              </div>
              <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-red-500 flex items-center justify-center text-white shadow-inner">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
              </div>
              <div className="flex-1 pr-6 pt-1">
                <p className="text-sm text-gray-700 font-medium leading-snug">You missed logging expenses yesterday.</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-400 absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>

            <div className="bg-white rounded-[20px] p-4 flex items-start gap-4 shadow-sm border border-gray-100/50 relative group cursor-pointer hover:shadow-md transition-shadow">
              <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-blue-500 flex items-center justify-center text-white shadow-inner">
                <Clock className="w-6 h-6" />
              </div>
              <div className="flex-1 pr-6 pt-0.5">
                <p className="text-sm text-gray-700 font-medium leading-snug mb-1">You hit a 5-day saving streak!</p>
                <p className="text-[11px] text-gray-400 uppercase tracking-wide font-semibold">Keep up the good work!</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-400 absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </div>
        </div>

      </div>

      {/* Bottom Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, i) => (
          <motion.div 
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * i }}
            className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-100/50 flex flex-col justify-between hover:shadow-md transition-shadow group relative"
          >
            <div className="flex items-start justify-between mb-8">
              <div className={`w-12 h-12 rounded-[14px] flex items-center justify-center ${stat.iconBg}`}>
                {stat.icon}
              </div>
              <button className="text-gray-400 hover:text-gray-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path></svg>
              </button>
            </div>
            
            <div className="space-y-2">
              <p className="text-sm text-gray-500 font-medium">{stat.title}</p>
              <h2 className="text-2xl font-display font-medium text-gray-900 tracking-tight">{stat.value}</h2>
            </div>
          </motion.div>
        ))}
      </div>

    </div>
  );
}
