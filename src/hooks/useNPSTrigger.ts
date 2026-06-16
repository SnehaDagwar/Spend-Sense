import { useEffect } from "react";
import { useFeedbackStore, shouldShowNPS } from "./useFeedbackStore";

/**
 * useNPSTrigger
 *
 * Increments the session counter on first call per browser session (uses
 * sessionStorage to detect "new session" without blowing away localStorage).
 * Returns whether the NPS survey should be shown right now.
 */
export function useNPSTrigger() {
  const { sessionCount, npsLastAskedAt, incrementSession, markNPSShown } =
    useFeedbackStore();

  useEffect(() => {
    const SEEN_KEY = "ss_session_counted";
    if (!sessionStorage.getItem(SEEN_KEY)) {
      sessionStorage.setItem(SEEN_KEY, "1");
      incrementSession();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const state = useFeedbackStore.getState();
  const show = shouldShowNPS(state);

  return { shouldShowNPS: show, markNPSShown };
}
