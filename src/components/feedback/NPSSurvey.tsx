import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Send, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useFeedbackStore } from "@/hooks/useFeedbackStore";
import { Analytics } from "@/lib/analytics";

interface NPSSurveyProps {
  onClose: () => void;
}

const SCORE_LABELS: Record<number, string> = {
  0: "Absolutely not",
  1: "Very unlikely",
  2: "Unlikely",
  3: "Probably not",
  4: "Not sure",
  5: "Neutral",
  6: "Maybe",
  7: "Likely",
  8: "Very likely",
  9: "Definitely!",
  10: "100% yes! 🎉",
};

const FOLLOW_UP: Record<"detractor" | "passive" | "promoter", string> = {
  detractor: "We're sorry to hear that. What's the #1 thing we could improve?",
  passive: "Thanks! What would make you love Spend Sense even more?",
  promoter: "Amazing! What do you love most about Spend Sense?",
};

function getSegment(score: number): "detractor" | "passive" | "promoter" {
  if (score >= 9) return "promoter";
  if (score >= 7) return "passive";
  return "detractor";
}

export function NPSSurvey({ onClose }: NPSSurveyProps) {
  const [score, setScore] = useState<number | null>(null);
  const [hoverScore, setHoverScore] = useState<number | null>(null);
  const [step, setStep] = useState<"score" | "followup" | "done">("score");
  const [followUp, setFollowUp] = useState("");
  const { recordNPSSubmission, markNPSShown } = useFeedbackStore();

  const activeScore = hoverScore ?? score;
  const segment = score !== null ? getSegment(score) : null;

  const handleScoreSelect = (n: number) => {
    setScore(n);
    setTimeout(() => setStep("followup"), 300);
  };

  const handleSubmit = () => {
    if (score === null) return;
    Analytics.npsSubmitted(score, followUp);
    recordNPSSubmission();
    setStep("done");
    setTimeout(onClose, 2200);
  };

  const handleDismiss = () => {
    markNPSShown();
    onClose();
  };

  return (
    <motion.div
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: 100, opacity: 0 }}
      transition={{ type: "spring", damping: 22, stiffness: 280 }}
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-[480px] px-4 sm:px-0"
    >
      <div className="bg-white/98 backdrop-blur-2xl border border-white/30 rounded-3xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-violet-500/10 via-primary/10 to-transparent px-6 py-4 border-b border-gray-100 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold text-primary uppercase tracking-widest">
              Quick Question
            </p>
            <h3 className="font-display font-bold text-gray-800 mt-0.5 text-base leading-snug">
              How likely are you to recommend Spend Sense to a friend?
            </h3>
          </div>
          <button
            onClick={handleDismiss}
            className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors shrink-0 mt-0.5"
            aria-label="Dismiss"
          >
            <X className="h-3.5 w-3.5 text-gray-500" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5">
          <AnimatePresence mode="wait">
            {step === "score" && (
              <motion.div
                key="score"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <div className="flex items-center justify-between text-[10px] text-muted-foreground font-medium px-1">
                  <span>Not at all likely</span>
                  <span>Extremely likely</span>
                </div>
                <div className="flex gap-1.5 justify-between">
                  {Array.from({ length: 11 }, (_, i) => i).map((n) => {
                    const isActive = activeScore !== null && activeScore >= n;
                    const isSelected = score === n;
                    const color =
                      n <= 6
                        ? "from-red-400 to-orange-400"
                        : n <= 8
                        ? "from-yellow-400 to-amber-400"
                        : "from-green-400 to-emerald-500";
                    return (
                      <button
                        key={n}
                        onMouseEnter={() => setHoverScore(n)}
                        onMouseLeave={() => setHoverScore(null)}
                        onClick={() => handleScoreSelect(n)}
                        aria-label={`Score ${n}`}
                        className={`
                          relative w-8 h-8 sm:w-9 sm:h-9 rounded-xl text-xs font-bold transition-all duration-150
                          ${
                            isActive
                              ? `bg-gradient-to-br ${color} text-white shadow-md scale-110`
                              : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                          }
                          ${isSelected ? "ring-2 ring-offset-1 ring-primary/40" : ""}
                        `}
                      >
                        {n}
                      </button>
                    );
                  })}
                </div>
                {activeScore !== null && (
                  <motion.p
                    key={activeScore}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center text-sm font-semibold text-gray-600"
                  >
                    {SCORE_LABELS[activeScore]}
                  </motion.p>
                )}
              </motion.div>
            )}

            {step === "followup" && segment && (
              <motion.div
                key="followup"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <p className="text-sm text-gray-700 font-medium">
                  {FOLLOW_UP[segment]}
                </p>
                <Textarea
                  placeholder="Share your thoughts... (optional)"
                  value={followUp}
                  onChange={(e) => setFollowUp(e.target.value.slice(0, 400))}
                  className="text-sm rounded-xl resize-none bg-gray-50 border-gray-200 focus:border-primary/50 min-h-[80px]"
                  autoFocus
                />
                <div className="flex gap-3">
                  <Button
                    variant="ghost"
                    onClick={handleSubmit}
                    className="text-muted-foreground text-sm"
                  >
                    Skip
                  </Button>
                  <Button
                    onClick={handleSubmit}
                    className="flex-1 bg-gradient-to-r from-primary to-violet-500 text-white rounded-xl h-10 text-sm font-semibold shadow-md hover:shadow-lg transition-all"
                  >
                    <Send className="h-3.5 w-3.5 mr-2" />
                    Submit Feedback
                  </Button>
                </div>
              </motion.div>
            )}

            {step === "done" && (
              <motion.div
                key="done"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center gap-3 py-4"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", damping: 10 }}
                  className="h-14 w-14 rounded-2xl bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center shadow-lg"
                >
                  <span className="text-2xl">🎉</span>
                </motion.div>
                <p className="font-display font-bold text-gray-800 text-base">
                  Thank you so much!
                </p>
                <p className="text-sm text-muted-foreground text-center">
                  Your feedback helps us build a better Spend Sense.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-100 px-6 py-2.5 bg-gray-50/50 flex items-center justify-between">
          <p className="text-[10px] text-muted-foreground">
            Takes &lt; 30 seconds · Anonymous
          </p>
          {step === "score" && score !== null && (
            <button
              onClick={() => setStep("followup")}
              className="flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
            >
              Continue <ChevronRight className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
