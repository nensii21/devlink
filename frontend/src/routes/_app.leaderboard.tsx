import { useState, useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Trophy,
  Award,
  Medal,
  Crown,
  Sparkles,
  Zap,
  CheckCircle,
  GitPullRequest,
  FolderCheck,
  HeartHandshake,
  MessageSquare,
  UserCheck,
  Flame,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, EmptyState } from "@/components/shared/primitives";
import { UserAvatar } from "@/components/user-avatar";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { reputationApi, type LeaderboardEntry, type ReputationSummary } from "@/api";
import { TypoSection, TypoCaption, TypoCard, TypoHeading } from "@/components/shared/Typography";

export const Route = createFileRoute("/_app/leaderboard")({
  head: () => ({
    meta: [
      { title: "Community Leaderboard & Reputation — DevLink" },
      {
        name: "description",
        content: "Track community reputation scores, rank tiers, and top contributors.",
      },
    ],
  }),
  component: LeaderboardPage,
});

const ACTION_POINTS_LABEL: Record<string, { label: string; points: number; icon: any }> = {
  merged_pull_request: { label: "Merged Pull Request", points: 50, icon: GitPullRequest },
  completed_project: { label: "Completed Project", points: 100, icon: FolderCheck },
  community_contribution: { label: "Community Contribution", points: 25, icon: HeartHandshake },
  helpful_discussion: { label: "Helpful Discussion", points: 15, icon: MessageSquare },
  profile_completion: { label: "Profile Completion", points: 10, icon: UserCheck },
  mentor_recognition: { label: "Mentor Recognition", points: 30, icon: Award },
};

function LeaderboardPage() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [mySummary, setMySummary] = useState<ReputationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [awardModalOpen, setAwardModalOpen] = useState(false);
  const [selectedAction, setSelectedAction] = useState("merged_pull_request");
  const [actionDesc, setActionDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [lbRes, myRes] = await Promise.all([
        reputationApi.getLeaderboard({ limit: 50 }),
        reputationApi.getMyReputation().catch(() => null),
      ]);

      if (lbRes) {
        setLeaderboard(lbRes.entries || []);
        setTotal(lbRes.total || 0);
      }
      if (myRes) {
        setMySummary(myRes);
      }
    } catch (err) {
      console.error("Failed to load leaderboard data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAwardSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await reputationApi.awardReputation({
        action: selectedAction,
        description: actionDesc || undefined,
      });
      toast.success("Reputation points awarded successfully!");
      setAwardModalOpen(false);
      setActionDesc("");
      fetchData();
    } catch (err) {
      toast.error("Failed to log reputation points.");
    } finally {
      setSubmitting(false);
    }
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) {
      return (
        <Badge className="bg-amber-500 text-white font-bold gap-1">
          <Crown size={12} /> #1 Gold
        </Badge>
      );
    }
    if (rank === 2) {
      return (
        <Badge className="bg-slate-400 text-white font-bold gap-1">
          <Medal size={12} /> #2 Silver
        </Badge>
      );
    }
    if (rank === 3) {
      return (
        <Badge className="bg-amber-700 text-white font-bold gap-1">
          <Award size={12} /> #3 Bronze
        </Badge>
      );
    }
    return <TypoCaption>#{rank}</TypoCaption>;
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent p-6 rounded-xl border border-primary/20">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Trophy className="h-6 w-6 text-primary animate-bounce" />
            <TypoHeading as="h1">Community Leaderboard & Reputation</TypoHeading>
          </div>
          <TypoCaption as="p">
            Earn reputation points for merging pull requests, completing projects, and helping
            fellow builders.
          </TypoCaption>
        </div>

        <Button onClick={() => setAwardModalOpen(true)} className="gap-2 shrink-0">
          <Plus size={16} /> Claim Reputation Points
        </Button>
      </div>

      {/* Grid: My Summary + Point System Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* User Reputation Score Card */}
        <Card className="p-5 flex flex-col justify-between border-l-4 border-l-primary">
          <div>
            <div className="flex items-center justify-between mb-3">
              <TypoCaption>My Reputation</TypoCaption>
              <Badge variant="outline" className="font-semibold text-xs">
                {mySummary?.rank_tier || "Novice 🥉"}
              </Badge>
            </div>
            <div className="flex items-baseline gap-2 mb-4">
              <span className="text-4xl font-extrabold text-foreground">
                {mySummary?.reputation_score || 0}
              </span>
              <TypoCaption>pts</TypoCaption>
            </div>
          </div>

          <div className="space-y-2">
            <TypoCard>Recent Log</TypoCard>
            {mySummary?.recent_logs && mySummary.recent_logs.length > 0 ? (
              <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                {mySummary.recent_logs.slice(0, 3).map((log) => (
                  <div
                    key={log.id}
                    className="flex items-center justify-between text-xs p-1.5 rounded bg-muted/40"
                  >
                    <span className="truncate max-w-[170px] text-foreground font-medium">
                      {log.description || log.action}
                    </span>
                    <span className="font-bold text-emerald-600 dark:text-emerald-400 shrink-0">
                      +{log.points}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={Award}
                title="Your reputation journey begins here"
                desc="Complete projects and help fellow builders to earn your first points."
                className="rounded-xl border border-dashed border-primary/20 bg-primary/5 py-7"
              />
            )}
          </div>
        </Card>

        {/* Reputation Sources Card */}
        <Card className="p-5 md:col-span-2">
          <TypoSection>
            <Sparkles className="h-4 w-4 text-amber-500" /> How to Earn Reputation Points
          </TypoSection>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
            {Object.entries(ACTION_POINTS_LABEL).map(([key, item]) => {
              const IconComp = item.icon;
              return (
                <div
                  key={key}
                  className="p-2.5 rounded-lg border border-border bg-card flex flex-col justify-between"
                >
                  <div className="flex items-center gap-1.5 mb-1 font-medium text-foreground">
                    <IconComp className="h-3.5 w-3.5 text-primary shrink-0" />
                    <span className="truncate">{item.label}</span>
                  </div>
                  <span className="font-bold text-primary text-sm">+{item.points} pts</span>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Leaderboard Table */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <TypoHeading as="h2">
              <Flame className="h-5 w-5 text-orange-500" /> Top Community Members
            </TypoHeading>
            <TypoCaption as="p">
              Showing {leaderboard.length} of {total} registered builders
            </TypoCaption>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-muted-foreground">
            Loading community leaderboard...
          </div>
        ) : leaderboard.length === 0 ? (
          <div className="py-12 text-center text-sm text-muted-foreground">
            No leaderboard entries found yet. Be the first to claim points!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border text-xs uppercase text-muted-foreground">
                  <th className="py-3 px-4 w-16">Rank</th>
                  <th className="py-3 px-4">Member</th>
                  <th className="py-3 px-4">Rank Tier</th>
                  <th className="py-3 px-4 text-right">Reputation Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {leaderboard.map((entry) => (
                  <tr key={entry.user_id} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3.5 px-4 font-semibold">{getRankBadge(entry.rank)}</td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        <UserAvatar
                          src={entry.avatar_url || undefined}
                          name={entry.full_name || entry.username}
                          className="h-8 w-8"
                        />
                        <div>
                          <p className="font-semibold text-foreground text-sm leading-tight">
                            {entry.full_name || entry.username}
                          </p>
                          <TypoCaption as="p">@{entry.username}</TypoCaption>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge variant="secondary" className="font-medium text-xs">
                        {entry.rank_tier}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <span className="font-extrabold text-foreground text-base">
                        {entry.reputation_score.toLocaleString()}
                      </span>
                      <TypoCaption>pts</TypoCaption>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Claim Reputation Modal */}
      <Dialog open={awardModalOpen} onOpenChange={setAwardModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-500" /> Claim Reputation Points
            </DialogTitle>
            <DialogDescription>
              Select your completed community activity to log reputation points.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleAwardSubmit} className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-foreground">Action Type</label>
              <Select value={selectedAction} onValueChange={setSelectedAction}>
                <SelectTrigger>
                  <SelectValue placeholder="Select activity" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(ACTION_POINTS_LABEL).map(([key, item]) => (
                    <SelectItem key={key} value={key}>
                      {item.label} (+{item.points} pts)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-foreground">
                Description / Reference (Optional)
              </label>
              <Input
                placeholder="e.g., Merged PR #868 in DevLink repo"
                value={actionDesc}
                onChange={(e) => setActionDesc(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setAwardModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Claiming..." : "Award Points"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
