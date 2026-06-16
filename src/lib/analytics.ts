/**
 * analytics.ts — PostHog wrapper for Spend Sense
 *
 * All calls are no-ops when VITE_POSTHOG_KEY is not set, so local development
 * and test environments are unaffected.
 *
 * Privacy guarantees:
 * - No PII is ever sent (no names, emails, or financial figures).
 * - User IDs are hashed before being passed to PostHog.
 * - autocapture is disabled — only explicit track() calls fire events.
 */

// Dynamic import so PostHog is only bundled when the key is present.
let posthog: typeof import("posthog-js").default | null = null;

const KEY = import.meta.env.VITE_POSTHOG_KEY as string | undefined;
const HOST = (import.meta.env.VITE_POSTHOG_HOST as string | undefined) ?? "https://us.i.posthog.com";

/** Initialise PostHog. Call once at app startup (before routes render). */
export async function initAnalytics(): Promise<void> {
  if (!KEY) return;
  try {
    const mod = await import("posthog-js");
    posthog = mod.default;
    posthog.init(KEY, {
      api_host: HOST,
      autocapture: false,          // manual tracking only
      capture_pageview: false,     // we fire page views manually
      capture_pageleave: false,
      disable_session_recording: true,
      persistence: "localStorage", // no cookies
      loaded: (ph) => {
        if (import.meta.env.DEV) {
          ph.opt_out_capturing(); // never send events in dev unless KEY is set
        }
      },
    });
    // Re-opt-in if key is explicitly provided (overrides dev opt-out)
    if (KEY) posthog.opt_in_capturing();
  } catch {
    // PostHog unavailable — silently continue
    posthog = null;
  }
}

/** Hash a string (user ID) to avoid sending PII. */
async function sha256Short(text: string): Promise<string> {
  try {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return Array.from(new Uint8Array(buf))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("")
      .slice(0, 16);
  } catch {
    return "anon";
  }
}

/** Track a page view. Call on every route change. */
export function trackPageView(path: string): void {
  posthog?.capture("$pageview", { $current_url: path });
}

/** Associate subsequent events with a hashed user identity. */
export async function identifyUser(rawId: string): Promise<void> {
  if (!posthog) return;
  const hashed = await sha256Short(rawId);
  posthog.identify(`user_${hashed}`);
}

/** Clear identity on logout. */
export function resetUser(): void {
  posthog?.reset();
}

/** Fire a named analytics event with optional safe properties. */
export function track(event: string, properties?: Record<string, string | number | boolean>): void {
  posthog?.capture(event, properties);
}

// ── Pre-defined event helpers ─────────────────────────────────────────────────

export const Analytics = {
  onboardingCompleted: (userType: string) =>
    track("onboarding_completed", { user_type: userType }),

  expenseAdded: (categorySlug: string) =>
    track("expense_added", { category: categorySlug }),

  goalCreated: () => track("goal_created"),

  budgetSet: (month: string) => track("budget_set", { month }),

  reportExported: (format: "csv" | "pdf") =>
    track("report_exported", { format }),

  insightViewed: (type: string) =>
    track("insight_viewed", { insight_type: type }),

  feedbackSubmitted: (rating: number, category: string) =>
    track("feedback_submitted", { rating, category }),

  bugReported: (severity: string) =>
    track("bug_reported", { severity }),

  betaBannerDismissed: () => track("beta_banner_dismissed"),

  // ── Phase 16: Feedback & Iteration ──────────────────────────────────────

  /** NPS score submitted (0–10). Segment: promoter 9-10, passive 7-8, detractor 0-6 */
  npsSubmitted: (score: number, followUp?: string) =>
    track("nps_submitted", {
      score,
      segment: score >= 9 ? "promoter" : score >= 7 ? "passive" : "detractor",
      has_comment: followUp ? followUp.length > 0 : false,
    }),

  /** Contextual CSAT rating after a key action */
  csatSubmitted: (rating: number, context: string) =>
    track("csat_submitted", { rating, context }),

  /** User upvoted or withdrew a vote on a feature request */
  featureVoteToggled: (featureId: string, action: "vote" | "unvote") =>
    track("feature_vote_toggled", { feature_id: featureId, action }),

  /** User dismissed a coach mark spotlight */
  coachMarkDismissed: (markId: string) =>
    track("coach_mark_dismissed", { mark_id: markId }),

  /** What's New modal was viewed for a given version */
  whatsNewViewed: (version: string) =>
    track("whats_new_viewed", { version }),

  /** Onboarding checklist item completed */
  checklistItemCompleted: (itemId: string) =>
    track("checklist_item_completed", { item_id: itemId }),
} as const;
