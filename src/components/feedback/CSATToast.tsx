import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Star, X } from "lucide-react";
import { useCSATStore } from "@/hooks/useCSATTrigger";

/**
 * CSATToast — a small, non-blocking satisfaction prompt.
 *
 * Mount this once in AppLayout. Call `useCSATStore.getState().show(context, question)`
 * from any component after a key user action to trigger it.
 */
export function CSATToast() {
  const { visible, question, submit, hide } = useCSATStore();
  const [hoverRating, setHoverRating] = useState(0);
  const [submitted, setSubmitted] = useState(false);

  // Auto-dismiss after 12 seconds if not interacted with
  useEffect(() => {
    if (!visible) { setSubmitted(false); return; }
    const t = setTimeout(() => hide(), 12000);
    return () => clearTimeout(t);
  }, [visible, hide]);

  const handleRating = (rating: number) => {
    submit(rating);
    setSubmitted(true);
    setTimeout(hide, 1800);
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, x: 60, scale: 0.95 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: 60, scale: 0.95 }}
          transition={{ type: "spring", damping: 22, stiffness: 300 }}
          className="fixed bottom-24 right-6 z-50 w-72"
        >
          <div className="bg-white/98 backdrop-blur-xl rounded-2xl shadow-xl border border-white/30 overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-primary/8 to-transparent px-4 py-3 flex items-start justify-between border-b border-gray-100">
              <p className="text-xs font-semibold text-primary uppercase tracking-wide">
                Quick feedback
              </p>
              <button
                onClick={hide}
                aria-label="Dismiss"
                className="w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors -mt-0.5"
              >
                <X className="h-2.5 w-2.5 text-gray-400" />
              </button>
            </div>

            {/* Body */}
            <div className="px-4 py-3.5 space-y-3">
              <AnimatePresence mode="wait">
                {!submitted ? (
                  <motion.div
                    key="form"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="space-y-3"
                  >
                    <p className="text-sm font-medium text-gray-700 leading-snug">
                      {question}
                    </p>
                    <div className="flex gap-2 justify-center">
                      {[1, 2, 3, 4, 5].map((n) => (
                        <button
                          key={n}
                          onMouseEnter={() => setHoverRating(n)}
                          onMouseLeave={() => setHoverRating(0)}
                          onClick={() => handleRating(n)}
                          aria-label={`Rate ${n} star${n > 1 ? "s" : ""}`}
                          className="transition-transform hover:scale-125"
                        >
                          <Star
                            className={`h-7 w-7 transition-colors ${
                              n <= (hoverRating || 0)
                                ? "fill-yellow-400 text-yellow-400"
                                : "text-gray-200 fill-gray-200"
                            }`}
                          />
                        </button>
                      ))}
                    </div>
                    <p className="text-center text-[10px] text-muted-foreground">
                      Auto-dismisses in 12s
                    </p>
                  </motion.div>
                ) : (
                  <motion.div
                    key="thanks"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex flex-col items-center gap-1.5 py-2"
                  >
                    <span className="text-2xl">🙌</span>
                    <p className="text-sm font-semibold text-gray-700">
                      Thanks for the feedback!
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
