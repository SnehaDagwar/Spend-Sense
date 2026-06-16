import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useFeedbackStore } from "@/hooks/useFeedbackStore";
import { Analytics } from "@/lib/analytics";

// ── Changelog ─────────────────────────────────────────────────────────────────

export const APP_VERSION = "1.1.0";

interface ChangeEntry {
  version: string;
  date: string;
  highlights: Array<{ icon: string; title: string; description: string }>;
}

const CHANGELOG: ChangeEntry[] = [
  {
    version: "1.1.0",
    date: "June 2026",
    highlights: [
      {
        icon: "🧠",
        title: "AI Insights Engine",
        description:
          "Gemini-powered financial insights that analyse your spending patterns and surface personalised recommendations.",
      },
      {
        icon: "🏆",
        title: "Gamification & Streaks",
        description:
          "Earn XP, level up, and unlock 20 badges across discipline, savings, and streaks — all synced to the cloud.",
      },
      {
        icon: "👨‍👩‍👧",
        title: "Family Wallet",
        description:
          "Track shared expenses, split bills, and settle up with family members in one place.",
      },
      {
        icon: "📊",
        title: "Advanced Analytics",
        description:
          "Richer charts — category breakdowns, spending trends, and month-over-month comparisons.",
      },
      {
        icon: "💬",
        title: "Feedback Hub",
        description:
          "In-app feedback, bug reports, and feature voting so you can shape Spend Sense's future.",
      },
    ],
  },
  {
    version: "1.0.0",
    date: "May 2026",
    highlights: [
      {
        icon: "🚀",
        title: "Spend Sense Beta Launch",
        description:
          "Budget tracking, expense logging, savings goals, and reports — all local-first.",
      },
    ],
  },
];

// ── Component ──────────────────────────────────────────────────────────────────

export function WhatsNewModal() {
  const { lastSeenVersion, setLastSeenVersion } = useFeedbackStore();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (lastSeenVersion !== APP_VERSION) {
      // Small delay so the app finishes rendering before modal appears
      const t = setTimeout(() => setOpen(true), 1200);
      return () => clearTimeout(t);
    }
  }, [lastSeenVersion]);

  const handleClose = () => {
    Analytics.whatsNewViewed(APP_VERSION);
    setLastSeenVersion(APP_VERSION);
    setOpen(false);
  };

  const current = CHANGELOG[0];

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.93, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.93, y: 20 }}
            transition={{ type: "spring", damping: 22, stiffness: 280 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
          >
            <div className="bg-white/98 backdrop-blur-2xl border border-white/30 rounded-3xl shadow-2xl w-full max-w-md overflow-hidden pointer-events-auto">
              {/* Header */}
              <div className="relative bg-gradient-to-br from-primary/20 via-violet-500/10 to-transparent px-6 py-6 border-b border-gray-100">
                <div className="flex items-start gap-4">
                  <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-primary to-violet-500 flex items-center justify-center shadow-lg shrink-0">
                    <Sparkles className="h-6 w-6 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-primary uppercase tracking-widest">
                      What's New
                    </p>
                    <h2 className="font-display font-bold text-gray-900 text-xl mt-0.5">
                      Spend Sense v{current.version}
                    </h2>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {current.date}
                    </p>
                  </div>
                  <button
                    onClick={handleClose}
                    aria-label="Close"
                    className="w-8 h-8 rounded-full bg-white/60 flex items-center justify-center hover:bg-white transition-colors shrink-0"
                  >
                    <X className="h-4 w-4 text-gray-500" />
                  </button>
                </div>
              </div>

              {/* Feature list */}
              <div className="px-6 py-4 space-y-3 max-h-[320px] overflow-y-auto">
                {current.highlights.map((item, i) => (
                  <motion.div
                    key={item.title}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.08 * i }}
                    className="flex items-start gap-3 p-3 rounded-2xl bg-gray-50/80 hover:bg-gray-100/80 transition-colors"
                  >
                    <span className="text-xl shrink-0 mt-0.5">{item.icon}</span>
                    <div>
                      <p className="font-semibold text-gray-800 text-sm">
                        {item.title}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">
                        {item.description}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between gap-4">
                <p className="text-[10px] text-muted-foreground">
                  Spend Sense v{APP_VERSION} · Beta Program
                </p>
                <Button
                  onClick={handleClose}
                  className="bg-gradient-to-r from-primary to-violet-500 text-white rounded-xl px-6 h-10 text-sm font-semibold shadow-md hover:shadow-lg transition-all"
                >
                  Awesome, let's go! 🚀
                </Button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
