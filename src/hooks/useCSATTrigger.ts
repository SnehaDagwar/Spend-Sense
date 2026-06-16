import { create } from "zustand";
import { useFeedbackStore, wasCSATShownRecently } from "./useFeedbackStore";
import { Analytics } from "@/lib/analytics";

interface CSATState {
  visible: boolean;
  context: string;
  question: string;
  show: (context: string, question: string) => void;
  hide: () => void;
  submit: (rating: number) => void;
}

/**
 * useCSATStore — lightweight ephemeral store for the current CSAT toast.
 * Does NOT persist to localStorage; we only read history from useFeedbackStore.
 */
export const useCSATStore = create<CSATState>()((set, get) => ({
  visible: false,
  context: "",
  question: "",

  show: (context, question) => {
    const feedbackState = useFeedbackStore.getState();
    // Guard: don't show if already seen this context recently
    if (wasCSATShownRecently(feedbackState, context)) return;
    set({ visible: true, context, question });
  },

  hide: () => set({ visible: false }),

  submit: (rating) => {
    const { context, hide } = get();
    useFeedbackStore.getState().recordCSAT(context, rating);
    Analytics.csatSubmitted(rating, context);
    hide();
  },
}));

// ── Named context helpers (call from consuming components) ────────────────────

export const CSAT_CONTEXTS = {
  FIRST_EXPENSE: {
    context: "first_expense_of_month",
    question: "How easy was it to log that expense?",
  },
  GOAL_CONTRIBUTION: {
    context: "goal_contribution",
    question: "How are you feeling about your progress?",
  },
  REPORT_EXPORT: {
    context: "report_export",
    question: "Was the exported report helpful?",
  },
  BUDGET_SET: {
    context: "budget_set",
    question: "How easy was it to set up your budget?",
  },
} as const;
