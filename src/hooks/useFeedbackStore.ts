/**
 * useFeedbackStore.ts
 *
 * Isolated Zustand slice for all user-feedback state:
 * - NPS survey scheduling
 * - CSAT submissions log
 * - Feature request votes (local)
 * - Coach mark dismissals
 * - What's New version tracking
 * - Onboarding checklist completion
 * - Feedback entries (localStorage persistence)
 *
 * Intentionally separate from useAppStore so backend sync can be
 * added in a future phase without coupling to core financial state.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface FeedbackEntry {
  id: string;
  type: "feedback" | "bug" | "feature_request";
  rating?: number;
  category?: string;
  text: string;
  email?: string;
  severity?: string;
  timestamp: string;
  route: string;
  appVersion: string;
}

export interface FeatureVote {
  featureId: string;
  votedAt: string;
}

export interface OnboardingChecklistItem {
  id: string;
  completedAt?: string;
}

// ── Feature Request Catalog ────────────────────────────────────────────────────

export interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  icon: string;
  tag: "planned" | "considering" | "under-review" | "shipped";
}

export const FEATURE_REQUESTS: FeatureRequest[] = [
  {
    id: "recurring-expenses",
    title: "Recurring Expenses",
    description: "Auto-log recurring bills and subscriptions so you never miss them.",
    icon: "🔄",
    tag: "planned",
  },
  {
    id: "dark-mode",
    title: "Dark Mode",
    description: "A true dark UI theme with OLED-optimized colors.",
    icon: "🌙",
    tag: "planned",
  },
  {
    id: "csv-import",
    title: "CSV / Bank Statement Import",
    description: "Import transactions directly from your bank's CSV export.",
    icon: "📊",
    tag: "considering",
  },
  {
    id: "multi-currency",
    title: "Multi-Currency Wallets",
    description: "Track expenses across multiple currencies with live conversion.",
    icon: "💱",
    tag: "considering",
  },
  {
    id: "whatsapp-bot",
    title: "WhatsApp Expense Bot",
    description: "Log expenses by sending a WhatsApp message. No app needed.",
    icon: "💬",
    tag: "under-review",
  },
  {
    id: "budget-templates",
    title: "Budget Templates",
    description: "One-click monthly budgets based on your lifestyle and income.",
    icon: "📋",
    tag: "considering",
  },
  {
    id: "spending-alerts-sms",
    title: "SMS Spending Alerts",
    description: "Get a text message when you exceed any budget category.",
    icon: "📱",
    tag: "under-review",
  },
  {
    id: "investment-tracking",
    title: "Investment Portfolio Tracker",
    description: "Track stocks, mutual funds, and SIPs alongside your budget.",
    icon: "📈",
    tag: "considering",
  },
  {
    id: "tax-reports",
    title: "Tax-Friendly Reports",
    description: "Export reports formatted for annual tax filing and ITR.",
    icon: "🧾",
    tag: "under-review",
  },
  {
    id: "shared-budgets",
    title: "Shared Budgets for Couples",
    description: "Real-time budget sharing with a partner or roommate.",
    icon: "💑",
    tag: "considering",
  },
];

// ── Coach Mark IDs ─────────────────────────────────────────────────────────────

export const COACH_MARK_IDS = {
  TRACKER_QUICK_ADD: "tracker-quick-add",
  GOALS_CREATE: "goals-create",
  INSIGHTS_AI: "insights-ai-panel",
  BUDGET_CATEGORIES: "budget-categories",
} as const;

// ── Onboarding Checklist IDs ───────────────────────────────────────────────────

export const CHECKLIST_IDS = {
  SET_BUDGET: "set-first-budget",
  LOG_EXPENSE: "log-first-expense",
  CREATE_GOAL: "create-first-goal",
  VIEW_INSIGHTS: "view-insights",
} as const;

// ── Store ─────────────────────────────────────────────────────────────────────

interface FeedbackState {
  // NPS
  sessionCount: number;
  npsLastAskedAt: string | null;
  npsSubmittedAt: string | null;

  // CSAT
  csatHistory: Array<{ context: string; rating: number; timestamp: string }>;

  // Feature votes
  featureVotes: Record<string, string>; // featureId → votedAt ISO string

  // Coach marks
  dismissedCoachMarks: string[];

  // What's New
  lastSeenVersion: string;

  // Onboarding checklist
  checklistItems: Record<string, string>; // checklistId → completedAt ISO string
  checklistDismissed: boolean;

  // Stored feedback entries
  feedbackEntries: FeedbackEntry[];

  // Actions
  incrementSession: () => void;
  markNPSShown: () => void;
  recordNPSSubmission: () => void;
  recordCSAT: (context: string, rating: number) => void;
  toggleFeatureVote: (featureId: string) => void;
  dismissCoachMark: (id: string) => void;
  resetCoachMarks: () => void;
  setLastSeenVersion: (version: string) => void;
  completeChecklistItem: (id: string) => void;
  dismissChecklist: () => void;
  addFeedbackEntry: (entry: Omit<FeedbackEntry, "id" | "timestamp">) => void;
}

export const useFeedbackStore = create<FeedbackState>()(
  persist(
    (set) => ({
      sessionCount: 0,
      npsLastAskedAt: null,
      npsSubmittedAt: null,
      csatHistory: [],
      featureVotes: {},
      dismissedCoachMarks: [],
      lastSeenVersion: "",
      checklistItems: {},
      checklistDismissed: false,
      feedbackEntries: [],

      incrementSession: () =>
        set((s) => ({ sessionCount: s.sessionCount + 1 })),

      markNPSShown: () =>
        set({ npsLastAskedAt: new Date().toISOString() }),

      recordNPSSubmission: () =>
        set({
          npsSubmittedAt: new Date().toISOString(),
          npsLastAskedAt: new Date().toISOString(),
        }),

      recordCSAT: (context, rating) =>
        set((s) => ({
          csatHistory: [
            ...s.csatHistory,
            { context, rating, timestamp: new Date().toISOString() },
          ],
        })),

      toggleFeatureVote: (featureId) =>
        set((s) => {
          const updated = { ...s.featureVotes };
          if (updated[featureId]) {
            delete updated[featureId];
          } else {
            updated[featureId] = new Date().toISOString();
          }
          return { featureVotes: updated };
        }),

      dismissCoachMark: (id) =>
        set((s) => ({
          dismissedCoachMarks: s.dismissedCoachMarks.includes(id)
            ? s.dismissedCoachMarks
            : [...s.dismissedCoachMarks, id],
        })),

      resetCoachMarks: () => set({ dismissedCoachMarks: [] }),

      setLastSeenVersion: (version) => set({ lastSeenVersion: version }),

      completeChecklistItem: (id) =>
        set((s) => ({
          checklistItems: { ...s.checklistItems, [id]: new Date().toISOString() },
        })),

      dismissChecklist: () => set({ checklistDismissed: true }),

      addFeedbackEntry: (entry) =>
        set((s) => ({
          feedbackEntries: [
            {
              ...entry,
              id: `fb_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
              timestamp: new Date().toISOString(),
            },
            ...s.feedbackEntries.slice(0, 49), // keep last 50
          ],
        })),
    }),
    {
      name: "spend-sense-feedback-v1",
    }
  )
);

// ── Selectors ─────────────────────────────────────────────────────────────────

/** Returns true if NPS should show: 3+ sessions and not asked in last 30 days */
export function shouldShowNPS(state: FeedbackState): boolean {
  if (state.sessionCount < 3) return false;
  if (!state.npsLastAskedAt) return true;
  const last = new Date(state.npsLastAskedAt).getTime();
  const thirtyDays = 30 * 24 * 60 * 60 * 1000;
  return Date.now() - last > thirtyDays;
}

/** Returns true if a CSAT for this context has been shown in the last 7 days */
export function wasCSATShownRecently(
  state: FeedbackState,
  context: string
): boolean {
  const sevenDays = 7 * 24 * 60 * 60 * 1000;
  return state.csatHistory.some(
    (e) =>
      e.context === context &&
      Date.now() - new Date(e.timestamp).getTime() < sevenDays
  );
}
