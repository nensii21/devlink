import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { projectsService } from "@/services";
import { Card, TagChip, Avatar } from "@/components/shared/primitives";
import { ArrowLeft, Star, GitFork, Users2, Github, Copy, Check } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { builders, activity, currentUser } from "@/mocks/seed";
import { Markdown } from "@/components/shared/Markdown";
import { BackButton } from "@/components/shared/BackButton";

export const Route = createFileRoute("/_app/projects/$projectId")({
  head: ({ params }) => ({
    meta: [
      { title: `${params.projectId} — DevLink` },
      { name: "description", content: "Project details, members, activity and repositories." },
    ],
  }),
  component: ProjectDetail,
});

function ProjectDetail() {
  const { projectId } = Route.useParams();
  const { data: p, isLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsService.get(projectId),
  });
  const [tab, setTab] = useState<"overview" | "members" | "activity" | "repos">("overview");
  const [copied, setCopied] = useState(false);
  const isOwner = p?.owner === currentUser.name;

  const handleCopyInviteLink = async () => {
    const inviteLink = `${window.location.origin}/projects/${projectId}?invite=true`;

    await navigator.clipboard.writeText(inviteLink);
    setCopied(true);

    window.setTimeout(() => setCopied(false), 2000);
  };

  if (isLoading) return <Card className="h-96 animate-pulse" />;
  if (!p) throw notFound();

  const tabs = ["overview", "members", "activity", "repos"] as const;

  return (
    <div className="space-y-4">
      <BackButton to="/projects" label="Back to projects" />
      <Card className="p-5">
        <div className="flex items-start gap-4">
          <span className="grid h-14 w-14 shrink-0 place-items-center rounded-md bg-muted text-3xl">
            {p.icon}
          </span>
          <div className="min-w-0 flex-1">
            <h1 className="text-[22px] font-bold text-foreground">{p.name}</h1>
            <p className="mt-1 text-[13px] text-muted-foreground">{p.description}</p>
            <div className="mt-3 flex flex-wrap gap-1">
              {p.stack.map((s) => (
                <TagChip key={s}>{s}</TagChip>
              ))}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            {isOwner && (
              <button
                type="button"
                onClick={handleCopyInviteLink}
                className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-2 text-[12px] font-medium text-foreground transition-colors hover:bg-muted"
                aria-label="Copy project invitation link"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? "Copied!" : "Copy invite link"}
              </button>
            )}

            <div className="hidden gap-4 text-[12px] text-muted-foreground sm:flex">
              <span className="inline-flex items-center gap-1">
                <Star size={12} /> {p.stars}
              </span>
              <span className="inline-flex items-center gap-1">
                <GitFork size={12} /> {p.forks}
              </span>
              <span className="inline-flex items-center gap-1">
                <Users2 size={12} /> {p.members}
              </span>
            </div>
          </div>
        </div>
      </Card>

      <div className="flex items-center gap-1 border-b border-border">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "border-b-2 px-3 py-2 text-[13px] font-medium capitalize transition-colors",
              tab === t
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="p-4 lg:col-span-2">
            <p className="text-[13px] font-semibold text-foreground">About</p>
            <Markdown content={p.description} className="mt-2 text-muted-foreground" />
            <p className="mt-4 text-[13px] font-semibold text-foreground">Progress</p>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
              <div className="h-full bg-primary" style={{ width: `${p.progress}%` }} />
            </div>
            <p className="mt-1 text-[11px] text-muted-foreground">{p.progress}% complete</p>
          </Card>
          <Card className="p-4">
            <p className="text-[13px] font-semibold text-foreground">Owner</p>
            <p className="mt-2 text-[13px] text-muted-foreground">{p.owner}</p>
            <p className="mt-4 text-[13px] font-semibold text-foreground">Status</p>
            <p className="mt-1 text-[13px] capitalize text-muted-foreground">{p.status}</p>
          </Card>
        </div>
      )}
      {tab === "members" && (
        <Card>
          <ul className="divide-y divide-border">
            {builders.slice(0, p.members).map((b) => (
              <li key={b.id} className="flex items-center gap-3 px-4 py-3">
                <Avatar src={b.avatar} alt={b.name} size={36} online={b.online} />
                <div className="min-w-0 flex-1">
                  <p className="text-[13px] font-semibold text-foreground">{b.name}</p>
                  <p className="text-[12px] text-muted-foreground">{b.role}</p>
                </div>
                <TagChip>{b.matchScore}% match</TagChip>
              </li>
            ))}
          </ul>
        </Card>
      )}
      {tab === "activity" && (
        <Card>
          <ul className="divide-y divide-border">
            {activity.map((a) => (
              <li
                key={a.id}
                className="flex items-center gap-3 px-4 py-2.5 text-[13px] text-foreground"
              >
                {a.text} <span className="ml-auto text-[11px] text-muted-foreground">{a.ago}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
      {tab === "repos" && (
        <Card className="p-4">
          <div className="flex items-center gap-2 rounded-md border border-border p-3">
            <Github size={16} className="text-muted-foreground" />
            <span className="text-[13px] font-medium text-foreground">
              devlink/{p.name.toLowerCase().replace(/\s+/g, "-")}
            </span>
            <span className="ml-auto text-[11px] text-muted-foreground">main · updated 2h ago</span>
          </div>
        </Card>
      )}
    </div>
  );
}
