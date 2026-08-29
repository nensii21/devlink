import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/shared/primitives";
import { useState } from "react";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";
import { AnimatedPage } from "@/components/shared/AnimatedPage";
import {
  mockHackathons, mockTeams, mockSubmissions, mockJudges,
  mockAwards, mockActivities, mockInsights, mockHackathonSummary,
} from "@/features/hackathon/service";
import {
  HackathonCard, TeamCard, SubmissionCard, JudgeCard,
  AwardCard, InsightCard,
} from "@/features/hackathon/components/HackathonCards";
import {
  SubmissionScoresRadar, PrizePie, ParticipationBar, ScoreComparison,
} from "@/features/hackathon/components/HackathonCharts";
import { formatNumber, formatCurrency, formatRelativeTime } from "@/features/hackathon/types";

export const Route = createFileRoute("/_app/hackathon-dashboard")({
  head: () => ({
    meta: [
      { title: "Hackathons — DevLink" },
      {
        name: "description",
        content: "Join hackathons, form teams, submit projects, and compete for prizes.",
      },
    ],
  }),
  component: HackathonDashboardPage,
});

const tabs = [
  { id: "overview", label: "📊 Overview" },
  { id: "hackathons", label: "🏆 Hackathons" },
  { id: "teams", label: "👥 Teams" },
  { id: "submissions", label: "🚀 Submissions" },
  { id: "judging", label: "⚖️ Judging" },
  { id: "awards", label: "🏅 Awards" },
];

function HackathonDashboardPage() {
  const [activeTab, setActiveTab] = useState("overview");
  const summary = mockHackathonSummary;

  return (
    <AnimatedPage>
      <div className="min-h-screen p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <TypoHeading level={2} className="text-3xl font-bold text-foreground mb-2">
              🏆 Hackathon Dashboard
            </TypoHeading>
            <TypoCaption className="text-muted-foreground text-base">
              Join hackathons, form teams, submit projects, and compete for prizes
            </TypoCaption>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-200 ${
                  activeTab === tab.id
                    ? "bg-primary text-primary-foreground shadow-md"
                    : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* ===== OVERVIEW TAB ===== */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="p-4 text-center">
                  <TypoCaption className="text-muted-foreground">Active</TypoCaption>
                  <p className="text-2xl font-bold text-red-500">{summary.activeHackathons}</p>
                </Card>
                <Card className="p-4 text-center">
                  <TypoCaption className="text-muted-foreground">Teams</TypoCaption>
                  <p className="text-2xl font-bold text-primary">{summary.teamsFormed}</p>
                </Card>
                <Card className="p-4 text-center">
                  <TypoCaption className="text-muted-foreground">Submissions</TypoCaption>
                  <p className="text-2xl font-bold text-foreground">{summary.submissions}</p>
                </Card>
                <Card className="p-4 text-center">
                  <TypoCaption className="text-muted-foreground">Total Prizes</TypoCaption>
                  <p className="text-2xl font-bold text-yellow-500">{formatCurrency(summary.totalPrizes)}</p>
                </Card>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ParticipationBar hackathons={mockHackathons} title="Hackathon Participation" />
                {mockSubmissions[0] && (
                  <SubmissionScoresRadar submission={mockSubmissions[0]} title="Top Submission Scores" />
                )}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {mockHackathons[0] && (
                  <PrizePie hackathon={mockHackathons[0]} title="Prize Distribution — Build Sprint" />
                )}
                {mockSubmissions.length > 0 && (
                  <ScoreComparison submissions={mockSubmissions} title="Score Comparison" />
                )}
              </div>

              <TypoHeading level={4} className="text-lg font-semibold text-foreground">📋 Recent Activity</TypoHeading>
              <Card className="p-4">
                <div className="space-y-3">
                  {mockActivities.slice(0, 4).map(act => (
                    <div key={act.id} className="flex items-center gap-3">
                      <span className="w-2 h-2 rounded-full bg-primary flex-shrink-0" />
                      <div className="flex-1">
                        <TypoCaption className="text-foreground text-xs">{act.message}</TypoCaption>
                      </div>
                      <TypoCaption className="text-muted-foreground text-[10px] flex-shrink-0">{formatRelativeTime(act.timestamp)}</TypoCaption>
                    </div>
                  ))}
                </div>
              </Card>

              <TypoHeading level={4} className="text-lg font-semibold text-foreground">💡 Insights</TypoHeading>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mockInsights.map(insight => (
                  <InsightCard key={insight.id} insight={insight} />
                ))}
              </div>
            </div>
          )}

          {/* ===== HACKATHONS TAB ===== */}
          {activeTab === "hackathons" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {mockHackathons.map(h => (
                  <HackathonCard key={h.id} hackathon={h} />
                ))}
              </div>
            </div>
          )}

          {/* ===== TEAMS TAB ===== */}
          {activeTab === "teams" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {mockTeams.map(team => (
                  <TeamCard key={team.id} team={team} />
                ))}
              </div>
            </div>
          )}

          {/* ===== SUBMISSIONS TAB ===== */}
          {activeTab === "submissions" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mockSubmissions.map(sub => (
                  <SubmissionCard key={sub.id} submission={sub} />
                ))}
              </div>
            </div>
          )}

          {/* ===== JUDGING TAB ===== */}
          {activeTab === "judging" && (
            <div className="space-y-6">
              <TypoHeading level={4} className="text-lg font-semibold text-foreground">Judges Panel</TypoHeading>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {mockJudges.map(judge => (
                  <JudgeCard key={judge.id} judge={judge} />
                ))}
              </div>

              <TypoHeading level={4} className="text-lg font-semibold text-foreground">Score Breakdown</TypoHeading>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {mockSubmissions.map(sub => (
                  <SubmissionScoresRadar key={sub.id} submission={sub} title={`${sub.title} — Score Radar`} />
                ))}
              </div>
            </div>
          )}

          {/* ===== AWARDS TAB ===== */}
          {activeTab === "awards" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {mockAwards.map(award => (
                  <AwardCard key={award.id} award={award} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AnimatedPage>
  );
}
