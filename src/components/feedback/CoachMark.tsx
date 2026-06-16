import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { useFeedbackStore } from "@/hooks/useFeedbackStore";
import { Analytics } from "@/lib/analytics";

interface CoachMarkProps {
  /** Unique stable identifier stored in dismissedCoachMarks */
  id: string;
  title: string;
  description: string;
  /** React ref pointing to the element to spotlight */
  targetRef: React.RefObject<HTMLElement | null>;
  /** Tooltip placement relative to target */
  placement?: "top" | "bottom" | "left" | "right";
  /** Optional delay before appearing (ms) */
  delay?: number;
}

/**
 * CoachMark — spotlight overlay with tooltip, renders via portal.
 *
 * Automatically hidden once the user dismisses it; dismissal is
 * persisted to localStorage via useFeedbackStore.
 */
export function CoachMark({
  id,
  title,
  description,
  targetRef,
  placement = "bottom",
  delay = 800,
}: CoachMarkProps) {
  const { dismissedCoachMarks, dismissCoachMark } = useFeedbackStore();
  const [rect, setRect] = useState<DOMRect | null>(null);
  const [visible, setVisible] = useState(false);

  const isDismissed = dismissedCoachMarks.includes(id);

  useEffect(() => {
    if (isDismissed) return;
    const timer = setTimeout(() => {
      if (targetRef.current) {
        setRect(targetRef.current.getBoundingClientRect());
        setVisible(true);
      }
    }, delay);
    return () => clearTimeout(timer);
  }, [isDismissed, targetRef, delay]);

  // Recalculate on resize/scroll
  useEffect(() => {
    if (!visible || isDismissed) return;
    const recalc = () => {
      if (targetRef.current) {
        setRect(targetRef.current.getBoundingClientRect());
      }
    };
    window.addEventListener("resize", recalc, { passive: true });
    window.addEventListener("scroll", recalc, { passive: true });
    return () => {
      window.removeEventListener("resize", recalc);
      window.removeEventListener("scroll", recalc);
    };
  }, [visible, isDismissed, targetRef]);

  const handleDismiss = () => {
    setVisible(false);
    dismissCoachMark(id);
    Analytics.coachMarkDismissed(id);
  };

  if (isDismissed || !rect) return null;

  const PADDING = 8;
  const spotlightStyle: React.CSSProperties = {
    position: "fixed",
    top: rect.top - PADDING,
    left: rect.left - PADDING,
    width: rect.width + PADDING * 2,
    height: rect.height + PADDING * 2,
    borderRadius: 16,
    pointerEvents: "none",
  };

  // Tooltip positioning
  const tooltipOffset = 16;
  let tooltipStyle: React.CSSProperties = {};
  switch (placement) {
    case "bottom":
      tooltipStyle = {
        position: "fixed",
        top: rect.bottom + tooltipOffset,
        left: rect.left + rect.width / 2,
        transform: "translateX(-50%)",
      };
      break;
    case "top":
      tooltipStyle = {
        position: "fixed",
        bottom: window.innerHeight - rect.top + tooltipOffset,
        left: rect.left + rect.width / 2,
        transform: "translateX(-50%)",
      };
      break;
    case "right":
      tooltipStyle = {
        position: "fixed",
        top: rect.top + rect.height / 2,
        left: rect.right + tooltipOffset,
        transform: "translateY(-50%)",
      };
      break;
    case "left":
      tooltipStyle = {
        position: "fixed",
        top: rect.top + rect.height / 2,
        right: window.innerWidth - rect.left + tooltipOffset,
        transform: "translateY(-50%)",
      };
      break;
  }

  return createPortal(
    <AnimatePresence>
      {visible && (
        <>
          {/* Backdrop with spotlight cut-out (simulated via box-shadow) */}
          <motion.div
            key={`cm-backdrop-${id}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleDismiss}
            className="fixed inset-0 z-[9998]"
            style={{
              background: "rgba(0,0,0,0.55)",
              // Cut out the target using clip trick
            }}
          />

          {/* Spotlight ring */}
          <motion.div
            key={`cm-spot-${id}`}
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.85 }}
            style={spotlightStyle}
            className="z-[9999]"
          >
            {/* Animated pulse ring */}
            <span className="absolute inset-0 rounded-2xl border-2 border-primary animate-ping opacity-60" />
            <span className="absolute inset-0 rounded-2xl border-2 border-primary/80" />
          </motion.div>

          {/* Tooltip */}
          <motion.div
            key={`cm-tooltip-${id}`}
            initial={{ opacity: 0, y: placement === "top" ? 8 : -8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ delay: 0.1, type: "spring", damping: 20 }}
            style={tooltipStyle}
            className="z-[9999] w-60"
          >
            <div className="bg-white rounded-2xl shadow-2xl border border-white/20 overflow-hidden">
              <div className="bg-gradient-to-r from-primary/15 to-violet-500/10 px-4 py-3 border-b border-gray-100 flex items-start justify-between gap-2">
                <p className="font-display font-bold text-gray-800 text-sm">
                  {title}
                </p>
                <button
                  onClick={handleDismiss}
                  aria-label="Dismiss tip"
                  className="w-5 h-5 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center shrink-0 transition-colors"
                >
                  <X className="h-2.5 w-2.5 text-gray-500" />
                </button>
              </div>
              <div className="px-4 py-3 space-y-2.5">
                <p className="text-xs text-gray-600 leading-relaxed">
                  {description}
                </p>
                <button
                  onClick={handleDismiss}
                  className="text-xs font-semibold text-primary hover:underline"
                >
                  Got it →
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  );
}
