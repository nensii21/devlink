import { useState } from "react";
import { createFileRoute, notFound } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { hackathonsService } from "@/services";
import { Card, TagChip, Skeleton } from "@/components/shared/primitives";
import { Trophy, Users2, Calendar, ExternalLink, CheckCircle2 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BackButton } from "@/components/shared/BackButton";
import { RegisterDialog } from "@/components/hackathons/RegisterDialog";
import { TeamsTab } from "@/components/hackathons/TeamsTab";
import { SubmissionsTab } from "@/components/hackathons/SubmissionsTab";
import { LeaderboardTab } from "@/components/hackathons/LeaderboardTab";
import { cn } from "@/lib/utils";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

type Tab = "overview" | "teams" | "submissions" | "leaderboard";

function getInitialTab(): Tab {
  if (typeof window === "undefined") return "overview";
  const tab = new URLSearchParams(window.location.search).get("tab");
  if (tab === "overview" || tab === "teams" || tab === "submissions" || tab === "leaderboard")
    return tab;
  return "overview";
}

export const Route = createFileRoute("/_app/hackathons/$hackathonId")({
  head: () => ({
    meta: [
      { title: "Hackathon — DevLink" },
      { name: "description", content: "View hackathon details on DevLink." },
    ],
  }),
  component: HackathonDetail,
});

function HackathonDetail() {
  const { hackathonId } = Route.useParams();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>(getInitialTab);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [registered, setRegistered] = useState(() => hackathonsService.isRegistered(hackathonId));

  const { data: hackathon, isLoading } = useQuery({
    queryKey: ["hackathon", hackathonId],
    queryFn: () => hackathonsService.get(hackathonId),
  });

  const { data: teams = [] } = useQuery({
    queryKey: ["hackathon-teams", hackathonId],
    queryFn: () => hackathonsService.getTeams(hackathonId),
    enabled: !!hackathonId,
  });

  function handleTabChange(value: string) {
    setTab(value as Tab);
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.set("tab", value);
      window.history.replaceState({}, "", url.toString());
    }
  }

  function handleRegistered() {
    setRegistered(true);
    setRegisterOpen(false);
    queryClient.invalidateQueries({ queryKey: ["hackathon", hackathonId] });
  }

  if (isLoading) {
    return (
      <div className="space-y-4" role="status" aria-busy="true">
        <Skeleton className="h-5 w-32" />
        <Card className="p-4">
          <div className="flex flex-wrap items-start gap-5">
            <Skeleton className="h-24 w-24 shrink-0 rounded-full" />
            <div className="min-w-0 flex-1">
              <Skeleton className="h-7 w-40" />
              <Skeleton className="h-4 w-32" />
              <Skeleton className="mt-2 h-4 w-64" />
              <Skeleton className="mt-2 h-3 w-28" />
            </div>
          </div>
        </Card>
        <div className="grid gap-3 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-4">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="mt-2 h-9 w-16" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!hackathon) throw notFound();

  const formatDate = (d: string) =>
    new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

  const canRegister =
    !registered && hackathon.status !== "completed" && hackathon.status !== "cancelled";

  return (
    <div className="space-y-4">
      <BackButton to="/hackathons" label="Back to hackathons" />

      <Card className="p-4">
        <div className="flex flex-wrap items-start gap-5">
          <span className="grid h-24 w-24 shrink-0 place-items-center rounded-full bg-muted text-4xl">
            🏆
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <TypoHeading as="h1">{hackathon.name}</TypoHeading>
              <TagChip
                className={cn(
                  hackathon.status === "registration_open"
                    ? "border-success/30 bg-success/10 text-success"
                    : hackathon.status === "in_progress"
                      ? "border-primary/30 bg-primary/10 text-primary"
                      : hackathon.status === "judging"
                        ? "border-warning/30 bg-warning/10 text-warning"
                        : hackathon.status === "completed"
                          ? "border-success/30 bg-success/10 text-success"
                          : "border-border bg-muted text-muted-foreground",
                )}
              >
                {hackathon.status.replace(/_/g, " ")}
              </TagChip>
            </div>
            {hackathon.theme && <TypoCaption as="p">{hackathon.theme}</TypoCaption>}
            <p className="mt-2 text-[13px] text-foreground line-clamp-3">{hackathon.description}</p>
            <div className="mt-3 flex flex-wrap gap-3 text-[12px] text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <Calendar size={12} /> {formatDate(hackathon.starts_at)} —{" "}
                {formatDate(hackathon.ends_at)}
              </span>
              <span className="inline-flex items-center gap-1">
                <Users2 size={12} /> {hackathon.min_team_size}–{hackathon.max_team_size} per team
              </span>
              {hackathon.prize && (
                <TagChip className="border-warning/30 bg-warning/10 text-warning">
                  {hackathon.prize}
                </TagChip>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {registered ? (
              <span className="inline-flex items-center gap-1.5 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-[13px] font-semibold text-success">
                <CheckCircle2 size={14} /> Registered
              </span>
            ) : canRegister ? (
              <button
                onClick={() => setRegisterOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90"
              >
                Register
              </button>
            ) : null}
            {hackathon.website_url && (
              <a
                href={hackathon.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-[13px] font-medium text-foreground hover:bg-muted"
              >
                <ExternalLink size={13} /> Website
              </a>
            )}
          </div>
        </div>
      </Card>

      <div className="grid gap-3 lg:grid-cols-3">
        <Card className="p-4">
          <p className="text-[13px] font-semibold text-foreground">Status</p>
          <p className="mt-2 text-[24px] font-bold capitalize text-foreground">
            {hackathon.status.replace(/_/g, " ")}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-[13px] font-semibold text-foreground">Teams</p>
          <p className="mt-2 text-[24px] font-bold text-foreground">{teams.length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-[13px] font-semibold text-foreground">Team Size</p>
          <p className="mt-2 text-[24px] font-bold text-foreground">
            {hackathon.min_team_size}–{hackathon.max_team_size}
          </p>
        </Card>
      </div>

      <Tabs value={tab} onValueChange={handleTabChange}>
        <TabsList className="overflow-x-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="teams">
            Teams
            {teams.length > 0 && (
              <span className="ml-1.5 rounded-full bg-primary/15 px-1.5 py-0.5 text-[10px] font-bold text-primary">
                {teams.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="submissions">Submissions</TabsTrigger>
          <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Card className="p-4">
            <p className="text-[13px] font-semibold text-foreground">About</p>
            <TypoCaption as="p">{hackathon.description}</TypoCaption>
          </Card>
          {hackathon.website_url && (
            <Card className="mt-3 p-4">
              <a
                href={hackathon.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-[13px] font-medium text-primary hover:underline"
              >
                <ExternalLink size={14} /> Visit website
              </a>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="teams">
          <TeamsTab hackathonId={hackathonId} maxTeamSize={hackathon.max_team_size} />
        </TabsContent>

        <TabsContent value="submissions">
          <SubmissionsTab hackathonId={hackathonId} teams={teams} />
        </TabsContent>

        <TabsContent value="leaderboard">
          <LeaderboardTab hackathonId={hackathonId} />
        </TabsContent>
      </Tabs>

      <RegisterDialog
        hackathonId={hackathonId}
        hackathonName={hackathon.name}
        open={registerOpen}
        onOpenChange={setRegisterOpen}
        onRegistered={handleRegistered}
      />
    </div>
  );
}
