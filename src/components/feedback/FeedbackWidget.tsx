import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquarePlus,
  X,
  Star,
  Send,
  Bug,
  Lightbulb,
  Heart,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Analytics } from "@/lib/analytics";
import { useFeedbackStore, FEATURE_REQUESTS } from "@/hooks/useFeedbackStore";

type Tab = "feedback" | "bug" | "feature";
type FeedbackCategory = "General" | "Feature Request" | "UI Issue" | "Performance";
type BugSeverity = "Low" | "Medium" | "High" | "Critical";

export const APP_VERSION = "1.1.0";
const FEEDBACK_EMAIL = "hello@spendsense.app";

/** Auto-capture diagnostic context for bug reports */
function buildDiagnostics(): string {
  const routes: string[] = JSON.parse(
    sessionStorage.getItem("ss_route_history") || "[]"
  );
  return [
    `URL: ${window.location.pathname}`,
    `Screen: ${window.screen.width}×${window.screen.height}`,
    `Viewport: ${window.innerWidth}×${window.innerHeight}`,
    `UA: ${navigator.userAgent.slice(0, 120)}`,
    `Recent pages: ${routes.slice(-5).join(" → ") || "—"}`,
    `App: v${APP_VERSION}`,
  ].join("\n");
}

/** Track route history in sessionStorage (called by router) */
export function trackRouteHistory(path: string) {
  const history: string[] = JSON.parse(
    sessionStorage.getItem("ss_route_history") || "[]"
  );
  if (history[history.length - 1] !== path) {
    history.push(path);
    sessionStorage.setItem(
      "ss_route_history",
      JSON.stringify(history.slice(-20))
    );
  }
}

export function FeedbackWidget() {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("feedback");
  const ref = useRef<HTMLDivElement>(null);
  const { addFeedbackEntry, featureVotes, toggleFeatureVote } = useFeedbackStore();

  // Feedback state
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [category, setCategory] = useState<FeedbackCategory>("General");
  const [feedbackText, setFeedbackText] = useState("");
  const [email, setEmail] = useState("");

  // Bug state
  const [severity, setSeverity] = useState<BugSeverity>("Medium");
  const [bugSteps, setBugSteps] = useState("");
  const [bugExpected, setBugExpected] = useState("");
  const [bugActual, setBugActual] = useState("");

  // Feature request state (top voted from catalog)
  const [featureNote, setFeatureNote] = useState("");

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const resetForm = () => {
    setRating(0); setHoverRating(0); setCategory("General");
    setFeedbackText(""); setEmail("");
    setSeverity("Medium"); setBugSteps(""); setBugExpected(""); setBugActual("");
    setFeatureNote("");
  };

  const handleClose = () => { setOpen(false); setTimeout(resetForm, 300); };

  const buildMailtoFeedback = () => {
    const subject = encodeURIComponent(`[Feedback] ${category} — Spend Sense Beta`);
    const body = encodeURIComponent(
      `Rating: ${rating}/5\nCategory: ${category}\n\nFeedback:\n${feedbackText}\n\nReply to: ${email || "Not provided"}\n\nApp: v${APP_VERSION} | URL: ${window.location.pathname}`
    );
    return `mailto:${FEEDBACK_EMAIL}?subject=${subject}&body=${body}`;
  };

  const buildMailtoBug = () => {
    const subject = encodeURIComponent(`[Bug][${severity}] — Spend Sense Beta`);
    const body = encodeURIComponent(
      `Severity: ${severity}\n\nSteps to reproduce:\n${bugSteps}\n\nExpected:\n${bugExpected}\n\nActual:\n${bugActual}\n\n--- Diagnostics ---\n${buildDiagnostics()}`
    );
    return `mailto:${FEEDBACK_EMAIL}?subject=${subject}&body=${body}`;
  };

  const handleSubmitFeedback = () => {
    if (!feedbackText.trim()) { toast.error("Please add some feedback text."); return; }
    Analytics.feedbackSubmitted(rating, category);
    addFeedbackEntry({
      type: "feedback",
      rating,
      category,
      text: feedbackText,
      email,
      route: window.location.pathname,
      appVersion: APP_VERSION,
    });
    window.location.href = buildMailtoFeedback();
    toast.success("Thanks! Your email client will open with your feedback.", { duration: 4000 });
    setTimeout(handleClose, 1500);
  };

  const handleSubmitBug = () => {
    if (!bugSteps.trim()) { toast.error("Please describe the steps to reproduce."); return; }
    Analytics.bugReported(severity);
    addFeedbackEntry({
      type: "bug",
      severity,
      text: bugSteps,
      route: window.location.pathname,
      appVersion: APP_VERSION,
    });
    window.location.href = buildMailtoBug();
    toast.success("Thanks for the report! Your email client will open.", { duration: 4000 });
    setTimeout(handleClose, 1500);
  };

  const handleSubmitFeatureRequest = () => {
    if (!featureNote.trim()) { toast.error("Describe the feature you'd like to see."); return; }
    const subject = encodeURIComponent(`[Feature Request] — Spend Sense`);
    const body = encodeURIComponent(
      `Feature Request:\n${featureNote}\n\nApp: v${APP_VERSION}\nURL: ${window.location.pathname}`
    );
    addFeedbackEntry({
      type: "feature_request",
      text: featureNote,
      route: window.location.pathname,
      appVersion: APP_VERSION,
    });
    window.location.href = `mailto:${FEEDBACK_EMAIL}?subject=${subject}&body=${body}`;
    toast.success("Feature request sent! We read every one. 🙌", { duration: 4000 });
    setTimeout(handleClose, 1500);
  };

  const severityColors: Record<BugSeverity, string> = {
    Low: "bg-green-100 text-green-700 border-green-200",
    Medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
    High: "bg-orange-100 text-orange-700 border-orange-200",
    Critical: "bg-red-100 text-red-700 border-red-200",
  };

  const categories: FeedbackCategory[] = ["General", "Feature Request", "UI Issue", "Performance"];

  const tabs: { id: Tab; label: string; Icon: typeof Star }[] = [
    { id: "feedback", label: "Feedback", Icon: Star },
    { id: "bug", label: "Bug", Icon: Bug },
    { id: "feature", label: "Suggest", Icon: Lightbulb },
  ];

  // Top 4 feature requests to show quick-vote in the Suggest tab
  const topFeatures = FEATURE_REQUESTS.slice(0, 4);

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3" ref={ref}>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            transition={{ type: "spring", damping: 20, stiffness: 300 }}
            className="w-[360px] bg-white/97 backdrop-blur-xl border border-white/30 rounded-3xl shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-primary/15 to-violet-500/8 px-5 py-4 flex items-center justify-between border-b border-white/20">
              <div>
                <h3 className="font-display font-bold text-gray-800 text-sm">
                  Share your thoughts
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Help us build a better Spend Sense
                </p>
              </div>
              <button
                onClick={handleClose}
                className="w-7 h-7 rounded-full bg-white/60 flex items-center justify-center hover:bg-white transition-colors"
                aria-label="Close feedback"
              >
                <X className="h-3.5 w-3.5 text-gray-500" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 p-3 bg-muted/30">
              {tabs.map(({ id, label, Icon }) => (
                <button
                  key={id}
                  onClick={() => setTab(id)}
                  className={`flex-1 py-2 px-2 rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
                    tab === id
                      ? "bg-white text-primary shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {label}
                </button>
              ))}
            </div>

            {/* Body */}
            <div className="p-4 space-y-4 max-h-[440px] overflow-y-auto">
              <AnimatePresence mode="wait">
                {tab === "feedback" && (
                  <motion.div
                    key="feedback"
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="space-y-4"
                  >
                    {/* Star Rating */}
                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-gray-600">
                        How would you rate your experience?
                      </Label>
                      <div className="flex gap-1.5">
                        {[1, 2, 3, 4, 5].map((n) => (
                          <button
                            key={n}
                            onMouseEnter={() => setHoverRating(n)}
                            onMouseLeave={() => setHoverRating(0)}
                            onClick={() => setRating(n)}
                            className="transition-transform hover:scale-110"
                            aria-label={`Rate ${n} star${n > 1 ? "s" : ""}`}
                          >
                            <Star
                              className={`h-7 w-7 transition-colors ${
                                n <= (hoverRating || rating)
                                  ? "fill-yellow-400 text-yellow-400"
                                  : "text-gray-200 fill-gray-200"
                              }`}
                            />
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Category */}
                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-gray-600">
                        Category
                      </Label>
                      <div className="flex flex-wrap gap-1.5">
                        {categories.map((c) => (
                          <button
                            key={c}
                            onClick={() => setCategory(c)}
                            className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                              category === c
                                ? "bg-primary text-white border-primary shadow-sm"
                                : "bg-white text-gray-600 border-gray-200 hover:border-primary/40"
                            }`}
                          >
                            {c}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-gray-600">
                        Your feedback
                      </Label>
                      <Textarea
                        placeholder="Tell us what you think, what's missing, or what's great..."
                        value={feedbackText}
                        onChange={(e) => setFeedbackText(e.target.value.slice(0, 500))}
                        className="text-sm rounded-xl resize-none bg-white/60 border-white/30 focus:border-primary/40 min-h-[80px]"
                      />
                      <p className="text-right text-[10px] text-muted-foreground">
                        {feedbackText.length}/500
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-gray-600">
                        Email for follow-up{" "}
                        <span className="font-normal text-muted-foreground">
                          (optional)
                        </span>
                      </Label>
                      <Input
                        type="email"
                        placeholder="you@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="text-sm rounded-xl bg-white/60 border-white/30 focus:border-primary/40 h-9"
                      />
                    </div>

                    <Button
                      onClick={handleSubmitFeedback}
                      className="w-full bg-gradient-to-r from-primary to-primary/80 text-white rounded-xl h-10 text-sm font-semibold shadow-md hover:shadow-lg transition-all"
                    >
                      <Send className="h-3.5 w-3.5 mr-2" /> Send Feedback
                    </Button>
                  </motion.div>
                )}

                {tab === "bug" && (
                  <motion.div
                    key="bug"
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="space-y-4"
                  >
                    {/* Severity */}
                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-gray-600">
                        Severity
                      </Label>
                      <div className="flex gap-1.5 flex-wrap">
                        {(["Low", "Medium", "High", "Critical"] as BugSeverity[]).map(
                          (s) => (
                            <button
                              key={s}
                              onClick={() => setSeverity(s)}
                              className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
                                severity === s
                                  ? severityColors[s] + " shadow-sm ring-2 ring-offset-1 ring-current/20"
                                  : "bg-white text-gray-500 border-gray-200"
                              }`}
                            >
                              {s}
                            </button>
                          )
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-gray-600">
                        Steps to reproduce
                      </Label>
                      <Textarea
                        placeholder={"1. Go to...\n2. Click on...\n3. Notice that..."}
                        value={bugSteps}
                        onChange={(e) => setBugSteps(e.target.value)}
                        className="text-sm rounded-xl resize-none bg-white/60 border-white/30 focus:border-primary/40 min-h-[72px]"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-gray-600">
                        What did you expect?
                      </Label>
                      <Textarea
                        placeholder="I expected..."
                        value={bugExpected}
                        onChange={(e) => setBugExpected(e.target.value)}
                        className="text-sm rounded-xl resize-none bg-white/60 border-white/30 focus:border-primary/40 min-h-[52px]"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-gray-600">
                        What actually happened?
                      </Label>
                      <Textarea
                        placeholder="Instead, what happened was..."
                        value={bugActual}
                        onChange={(e) => setBugActual(e.target.value)}
                        className="text-sm rounded-xl resize-none bg-white/60 border-white/30 focus:border-primary/40 min-h-[52px]"
                      />
                    </div>

                    {/* Auto-captured diagnostics */}
                    <div className="bg-muted/40 rounded-xl px-3 py-2 text-[10px] text-muted-foreground space-y-0.5">
                      <p className="font-semibold text-gray-600 mb-1">
                        🔬 Auto-captured diagnostics
                      </p>
                      <p>📍 Page: <span className="font-mono">{window.location.pathname}</span></p>
                      <p>🖥️ Screen: {window.screen.width}×{window.screen.height}</p>
                      <p>🔖 Version: v{APP_VERSION}</p>
                    </div>

                    <Button
                      onClick={handleSubmitBug}
                      className="w-full bg-gradient-to-r from-destructive/80 to-destructive text-white rounded-xl h-10 text-sm font-semibold shadow-md hover:shadow-lg transition-all"
                    >
                      <Bug className="h-3.5 w-3.5 mr-2" /> Report Bug
                    </Button>
                  </motion.div>
                )}

                {tab === "feature" && (
                  <motion.div
                    key="feature"
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="space-y-4"
                  >
                    <p className="text-xs text-muted-foreground">
                      Vote for features you want, or describe your own idea.
                    </p>

                    {/* Quick-vote top features */}
                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-gray-600">
                        Popular requests
                      </Label>
                      {topFeatures.map((f) => {
                        const voted = !!featureVotes[f.id];
                        return (
                          <div
                            key={f.id}
                            className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${
                              voted
                                ? "border-primary/30 bg-primary/5"
                                : "border-gray-200 hover:border-gray-300"
                            }`}
                          >
                            <span className="text-lg">{f.icon}</span>
                            <p className="flex-1 text-xs font-medium text-gray-700 leading-snug">
                              {f.title}
                            </p>
                            <button
                              onClick={() => {
                                const wasVoted = voted;
                                toggleFeatureVote(f.id);
                                Analytics.featureVoteToggled(
                                  f.id,
                                  wasVoted ? "unvote" : "vote"
                                );
                              }}
                              aria-label={voted ? "Remove vote" : "Vote"}
                              className={`w-7 h-7 rounded-lg flex items-center justify-center border transition-all ${
                                voted
                                  ? "bg-primary/10 border-primary/30 text-primary"
                                  : "bg-white border-gray-200 text-gray-400 hover:border-primary/30 hover:text-primary"
                              }`}
                            >
                              <Heart
                                className={`h-3.5 w-3.5 transition-all ${
                                  voted ? "fill-primary text-primary" : ""
                                }`}
                              />
                            </button>
                          </div>
                        );
                      })}
                    </div>

                    {/* Custom idea */}
                    <div className="space-y-2">
                      <Label className="text-xs font-semibold text-gray-600">
                        Your idea{" "}
                        <span className="font-normal text-muted-foreground">
                          (describe it below)
                        </span>
                      </Label>
                      <Textarea
                        placeholder="I'd love a feature that..."
                        value={featureNote}
                        onChange={(e) => setFeatureNote(e.target.value.slice(0, 400))}
                        className="text-sm rounded-xl resize-none bg-white/60 border-white/30 focus:border-primary/40 min-h-[72px]"
                      />
                      <p className="text-right text-[10px] text-muted-foreground">
                        {featureNote.length}/400
                      </p>
                    </div>

                    <Button
                      onClick={handleSubmitFeatureRequest}
                      disabled={!featureNote.trim()}
                      className="w-full bg-gradient-to-r from-violet-500 to-primary text-white rounded-xl h-10 text-sm font-semibold shadow-md hover:shadow-lg transition-all disabled:opacity-50"
                    >
                      <Lightbulb className="h-3.5 w-3.5 mr-2" /> Submit Idea
                    </Button>

                    <p className="text-center text-[10px] text-muted-foreground">
                      See the full list in{" "}
                      <span className="font-semibold">
                        Settings → Feedback
                      </span>
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Footer */}
            <div className="border-t border-white/20 px-4 py-2.5 bg-muted/20 text-center">
              <p className="text-[10px] text-muted-foreground">
                Spend Sense v{APP_VERSION} — Beta Program
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* FAB */}
      <motion.button
        onClick={() => setOpen((o) => !o)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className={`w-14 h-14 rounded-2xl shadow-xl flex items-center justify-center transition-all ${
          open
            ? "bg-white text-primary border-2 border-primary/30"
            : "bg-gradient-to-br from-primary to-violet-500 text-white shadow-primary/30"
        }`}
        aria-label="Open feedback"
        title="Send feedback or report a bug"
      >
        <AnimatePresence mode="wait">
          {open ? (
            <motion.div
              key="close"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <X className="h-5 w-5" />
            </motion.div>
          ) : (
            <motion.div
              key="open"
              initial={{ rotate: 90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: -90, opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <MessageSquarePlus className="h-5 w-5" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    </div>
  );
}
