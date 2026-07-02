import { motion } from "framer-motion";
import { Heart, ChevronRight, Zap, Clock, CheckCircle2 } from "lucide-react";
import {
  useFeedbackStore,
  FEATURE_REQUESTS,
  type FeatureRequest,
} from "@/hooks/useFeedbackStore";
import { Analytics } from "@/lib/analytics";

const TAG_CONFIG: Record<
  FeatureRequest["tag"],
  { label: string; classes: string; Icon: typeof Zap }
> = {
  planned: {
    label: "Planned",
    classes: "bg-blue-50 text-blue-600 border-blue-200",
    Icon: Zap,
  },
  considering: {
    label: "Considering",
    classes: "bg-amber-50 text-amber-600 border-amber-200",
    Icon: Clock,
  },
  "under-review": {
    label: "Under Review",
    classes: "bg-violet-50 text-violet-600 border-violet-200",
    Icon: ChevronRight,
  },
  shipped: {
    label: "Shipped ✓",
    classes: "bg-green-50 text-green-600 border-green-200",
    Icon: CheckCircle2,
  },
};

interface FeatureCardProps {
  feature: FeatureRequest;
  voted: boolean;
  voteCount: number;
  onToggle: () => void;
}

function FeatureCard({ feature, voted, voteCount, onToggle }: FeatureCardProps) {
  const tag = TAG_CONFIG[feature.tag];
  const TagIcon = tag.Icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-start gap-4 p-4 rounded-2xl border transition-all duration-200 group ${
        voted
          ? "border-primary/30 bg-primary/4 shadow-sm"
          : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/8"
      }`}
    >
      {/* Emoji */}
      <span className="text-2xl shrink-0 mt-0.5">{feature.icon}</span>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-1.5">
        <div className="flex items-start gap-2 flex-wrap">
          <p className="font-semibold text-sm text-gray-800 leading-snug">
            {feature.title}
          </p>
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${tag.classes}`}
          >
            <TagIcon className="h-2.5 w-2.5" />
            {tag.label}
          </span>
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">
          {feature.description}
        </p>
      </div>

      {/* Vote button */}
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.93 }}
        onClick={onToggle}
        aria-label={voted ? "Remove vote" : "Vote for this feature"}
        className={`shrink-0 flex flex-col items-center gap-1 px-3 py-2 rounded-xl border transition-all ${
          voted
            ? "bg-primary/10 border-primary/30 text-primary"
            : "bg-white/5 border-white/10 text-muted-foreground hover:border-primary/30 hover:text-primary hover:bg-primary/5"
        }`}
      >
        <Heart
          className={`h-4 w-4 transition-all ${
            voted ? "fill-primary text-primary scale-110" : ""
          }`}
        />
        <span className="text-[10px] font-bold tabular-nums">{voteCount}</span>
      </motion.button>
    </motion.div>
  );
}

/**
 * FeatureRequestBoard — embedded in the Settings "Feedback" tab.
 *
 * Votes are stored locally in useFeedbackStore. A future backend endpoint
 * can aggregate and persist these server-side.
 */
export function FeatureRequestBoard() {
  const { featureVotes, toggleFeatureVote } = useFeedbackStore();

  const handleToggle = (featureId: string) => {
    const wasVoted = !!featureVotes[featureId];
    toggleFeatureVote(featureId);
    Analytics.featureVoteToggled(featureId, wasVoted ? "unvote" : "vote");
  };

  // Simulate community votes (stable per feature, based on id hash)
  const communityBase = (id: string): number => {
    let hash = 0;
    for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) >>> 0;
    return 12 + (hash % 89);
  };

  // Sort: voted first, then by community count descending
  const sorted = [...FEATURE_REQUESTS].sort((a, b) => {
    const aVoted = featureVotes[a.id] ? 1 : 0;
    const bVoted = featureVotes[b.id] ? 1 : 0;
    if (aVoted !== bVoted) return bVoted - aVoted;
    return communityBase(b.id) - communityBase(a.id);
  });

  const totalVotes = Object.keys(featureVotes).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h3 className="font-display font-bold text-lg text-foreground">
            Feature Requests
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            Vote for features you'd love to see next. Your votes shape our roadmap.
          </p>
        </div>
        {totalVotes > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20">
            <Heart className="h-3.5 w-3.5 fill-primary text-primary" />
            <span className="text-xs font-bold text-primary">
              {totalVotes} vote{totalVotes !== 1 ? "s" : ""} cast
            </span>
          </div>
        )}
      </div>

      {/* Feature cards */}
      <motion.div layout className="space-y-2.5">
        {sorted.map((feature) => {
          const userVoted = !!featureVotes[feature.id];
          const base = communityBase(feature.id);
          const voteCount = base + (userVoted ? 1 : 0);
          return (
            <FeatureCard
              key={feature.id}
              feature={feature}
              voted={userVoted}
              voteCount={voteCount}
              onToggle={() => handleToggle(feature.id)}
            />
          );
        })}
      </motion.div>

      {/* Suggest your own */}
      <div className="rounded-2xl border border-dashed border-primary/30 bg-primary/4 px-5 py-4 flex items-center gap-4">
        <span className="text-2xl">💡</span>
        <div className="flex-1">
          <p className="font-semibold text-sm text-gray-800">
            Have an idea we missed?
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Use the feedback widget to submit a feature request — we read every one.
          </p>
        </div>
      </div>
    </div>
  );
}
