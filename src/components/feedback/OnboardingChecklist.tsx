import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import { CheckCircle2, ChevronRight, X } from "lucide-react";
import { useFeedbackStore, CHECKLIST_IDS } from "@/hooks/useFeedbackStore";
import { Analytics } from "@/lib/analytics";

interface ChecklistItem {
  id: string;
  emoji: string;
  label: string;
  sublabel: string;
  href: string;
}

const ITEMS: ChecklistItem[] = [
  {
    id: CHECKLIST_IDS.SET_BUDGET,
    emoji: "💸",
    label: "Set your first budget",
    sublabel: "Plan your monthly spending",
    href: "/budget",
  },
  {
    id: CHECKLIST_IDS.LOG_EXPENSE,
    emoji: "📝",
    label: "Log your first expense",
    sublabel: "Track what you spent today",
    href: "/tracker",
  },
  {
    id: CHECKLIST_IDS.CREATE_GOAL,
    emoji: "🎯",
    label: "Create a savings goal",
    sublabel: "Start working toward something",
    href: "/goals",
  },
  {
    id: CHECKLIST_IDS.VIEW_INSIGHTS,
    emoji: "🧠",
    label: "Explore your insights",
    sublabel: "Let AI analyse your spending",
    href: "/insights",
  },
];

/**
 * OnboardingChecklist — floating card that helps new users take their
 * first steps after completing onboarding.
 *
 * Dismissed globally once all items are done or the user closes it.
 */
export function OnboardingChecklist() {
  const {
    checklistItems,
    checklistDismissed,
    completeChecklistItem,
    dismissChecklist,
  } = useFeedbackStore();

  const completedIds = Object.keys(checklistItems);
  const totalDone = completedIds.length;
  const allDone = totalDone >= ITEMS.length;

  // Auto-dismiss when all items are completed
  if (checklistDismissed && !allDone) return null;
  if (checklistDismissed) return null;

  const handleItemClick = (id: string) => {
    if (!checklistItems[id]) {
      completeChecklistItem(id);
      Analytics.checklistItemCompleted(id);
    }
  };

  const progressPct = Math.round((totalDone / ITEMS.length) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, x: 60 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 60 }}
      transition={{ type: "spring", damping: 22, stiffness: 260, delay: 0.6 }}
      className="fixed bottom-6 right-6 z-40 w-72"
    >
      <div className="bg-white/98 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/20 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary/10 to-violet-500/5 px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-base">🚀</span>
            <div>
              <p className="text-xs font-bold text-gray-800 leading-none">
                Get started
              </p>
              <p className="text-[10px] text-muted-foreground mt-0.5">
                {totalDone}/{ITEMS.length} completed
              </p>
            </div>
          </div>
          <button
            onClick={dismissChecklist}
            aria-label="Dismiss checklist"
            className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors"
          >
            <X className="h-3 w-3 text-gray-400" />
          </button>
        </div>

        {/* Progress bar */}
        <div className="h-1 bg-gray-100">
          <motion.div
            className="h-full bg-gradient-to-r from-primary to-violet-500"
            initial={{ width: 0 }}
            animate={{ width: `${progressPct}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>

        {/* Items */}
        <div className="py-1.5">
          {ITEMS.map((item) => {
            const done = !!checklistItems[item.id];
            return (
              <Link
                key={item.id}
                to={item.href}
                onClick={() => handleItemClick(item.id)}
                className={`flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 transition-colors group ${
                  done ? "opacity-60" : ""
                }`}
              >
                <span className="text-lg shrink-0">{item.emoji}</span>
                <div className="flex-1 min-w-0">
                  <p
                    className={`text-xs font-semibold leading-none ${
                      done ? "line-through text-gray-400" : "text-gray-800"
                    }`}
                  >
                    {item.label}
                  </p>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    {item.sublabel}
                  </p>
                </div>
                {done ? (
                  <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-gray-300 group-hover:text-primary transition-colors shrink-0" />
                )}
              </Link>
            );
          })}
        </div>

        {/* All done banner */}
        <AnimatePresence>
          {allDone && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              className="border-t border-gray-100 bg-green-50 px-4 py-3 flex items-center gap-2"
            >
              <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
              <p className="text-xs font-semibold text-green-700">
                You're all set! Great start 🎉
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
