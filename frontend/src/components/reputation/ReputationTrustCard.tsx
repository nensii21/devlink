import React, { useState } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  GitPullRequest,
  CheckSquare,
  MessageSquare,
  ThumbsUp,
  Award,
  Sparkles,
  Heart,
} from "lucide-react";
import { TrustScoreBadge } from "./TrustScoreBadge";

export interface TrustBreakdownData {
  collaborations_points: number;
  pull_requests_points: number;
  completed_projects_points: number;
  feedback_points: number;
  endorsements_points: number;
  verification_points: number;
}

export interface ReputationTrustCardProps {
  userId?: string;
  username?: string;
  reputationScore?: number;
  trustScore?: number;
  trustLevel?: string;
  rankTier?: string;
  isVerified?: boolean;
  breakdown?: TrustBreakdownData;
  onEndorse?: (skillOrReason: string, note?: string) => Promise<void>;
  isSelf?: boolean;
}

export function ReputationTrustCard({
  userId,
  username = "Developer",
  reputationScore = 240,
  trustScore = 48,
  trustLevel = "Verified Contributor 🛡️",
  rankTier = "Builder 🥇",
  isVerified = true,
  breakdown = {
    collaborations_points: 60,
    pull_requests_points: 100,
    completed_projects_points: 100,
    feedback_points: 40,
    endorsements_points: 30,
    verification_points: 40,
  },
  onEndorse,
  isSelf = false,
}: ReputationTrustCardProps) {
  const [isEndorseModalOpen, setIsEndorseModalOpen] = useState(false);
  const [skillInput, setSkillInput] = useState("");
  const [noteInput, setNoteInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  const calculatedTrust = trustScore || Math.min(100, Math.round((reputationScore / 500) * 100));

  const handleEndorseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!skillInput.trim() || !onEndorse) return;
    try {
      setIsSubmitting(true);
      await onEndorse(skillInput.trim(), noteInput.trim() || undefined);
      setSuccessMsg(`Successfully endorsed ${username}!`);
      setTimeout(() => {
        setIsEndorseModalOpen(false);
        setSuccessMsg("");
        setSkillInput("");
        setNoteInput("");
      }, 1500);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const metrics = [
    {
      title: "Successful Collaborations",
      points: breakdown.collaborations_points,
      icon: <Sparkles className="h-4 w-4 text-emerald-400" />,
      weight: "+30 pts each",
    },
    {
      title: "Merged Pull Requests",
      points: breakdown.pull_requests_points,
      icon: <GitPullRequest className="h-4 w-4 text-purple-400" />,
      weight: "+50 pts each",
    },
    {
      title: "Completed Projects",
      points: breakdown.completed_projects_points,
      icon: <CheckSquare className="h-4 w-4 text-blue-400" />,
      weight: "+100 pts each",
    },
    {
      title: "Community Feedback",
      points: breakdown.feedback_points,
      icon: <MessageSquare className="h-4 w-4 text-amber-400" />,
      weight: "+20 pts each",
    },
    {
      title: "Peer Endorsements",
      points: breakdown.endorsements_points,
      icon: <ThumbsUp className="h-4 w-4 text-pink-400" />,
      weight: "+15 pts each",
    },
    {
      title: "Account Verification",
      points: breakdown.verification_points,
      icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
      weight: isVerified ? "Verified (+40 pts)" : "Unverified (0 pts)",
    },
  ];

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-foreground">Reputation & Trust Score</h3>
            <TrustScoreBadge
              trustScore={calculatedTrust}
              trustLevel={trustLevel}
              isVerified={isVerified}
              size="md"
            />
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Calculated from verified collaborations, code contributions, project completions, and peer reviews.
          </p>
        </div>
        {!isSelf && onEndorse && (
          <button
            onClick={() => setIsEndorseModalOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
          >
            <Heart className="h-3.5 w-3.5" />
            Endorse Builder
          </button>
        )}
      </div>

      {/* Trust Meter Gauge */}
      <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-lg border border-border bg-muted/40 p-4 flex flex-col justify-center items-center text-center">
          <span className="text-3xl font-black text-primary">{calculatedTrust}%</span>
          <span className="mt-1 text-xs font-medium text-muted-foreground">Normalized Trust Index</span>
          <div className="w-full bg-secondary h-2 rounded-full mt-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-500 via-emerald-500 to-amber-500 h-full transition-all duration-500"
              style={{ width: `${calculatedTrust}%` }}
            />
          </div>
        </div>

        <div className="rounded-lg border border-border bg-muted/40 p-4 flex flex-col justify-center items-center text-center">
          <span className="text-2xl font-bold text-foreground">{reputationScore}</span>
          <span className="mt-1 text-xs font-medium text-muted-foreground">Total Reputation Points</span>
          <span className="mt-2 text-xs font-semibold text-amber-500">{rankTier}</span>
        </div>

        <div className="rounded-lg border border-border bg-muted/40 p-4 flex flex-col justify-center items-center text-center">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="h-5 w-5 text-emerald-500" />
            <span className="text-sm font-semibold text-foreground">{trustLevel}</span>
          </div>
          <span className="mt-2 text-xs text-muted-foreground">
            {isVerified ? "✅ Verified Identity & Portfolio" : "⚠️ Identity verification pending"}
          </span>
        </div>
      </div>

      {/* Criteria Breakdown Grid */}
      <div className="mt-6">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Score Breakdown Criteria
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {metrics.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between rounded-md border border-border bg-background p-3">
              <div className="flex items-center gap-2.5">
                {item.icon}
                <div>
                  <p className="text-xs font-medium text-foreground">{item.title}</p>
                  <p className="text-[10px] text-muted-foreground">{item.weight}</p>
                </div>
              </div>
              <span className="text-xs font-bold text-primary">+{item.points}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Endorse Modal */}
      {isEndorseModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-2xl">
            <h3 className="text-base font-bold text-foreground">Endorse {username}</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Endorse this developer for their technical skills or successful collaboration (+15 reputation points).
            </p>

            {successMsg ? (
              <div className="mt-4 rounded-md bg-emerald-500/10 p-3 text-xs text-emerald-400 border border-emerald-500/30">
                {successMsg}
              </div>
            ) : (
              <form onSubmit={handleEndorseSubmit} className="mt-4 space-y-3">
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1">
                    Skill or Reason for Endorsement *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. React, System Architecture, Code Quality"
                    value={skillInput}
                    onChange={(e) => setSkillInput(e.target.value)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-foreground mb-1">
                    Optional Endorsement Note
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Write a brief note highlighting their contribution..."
                    value={noteInput}
                    onChange={(e) => setNoteInput(e.target.value)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsEndorseModalOpen(false)}
                    className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || !skillInput.trim()}
                    className="rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
                  >
                    {isSubmitting ? "Submitting..." : "Submit Endorsement"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
