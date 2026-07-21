import { useState } from "react";
import { createFileRoute, notFound } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { buildersService } from "@/services";
import { Card, TagChip, Avatar, EmptyState, Skeleton } from "@/components/shared/primitives";
import { LastActive } from "@/components/shared/LastActive";
import { FollowButton } from "@/components/shared/FollowButton";
import {
  MessageSquare,
  Users2,
  Star,
  GitFork,
  FolderOpen,
  Activity as ActivityIcon,
} from "lucide-react";
import { BackButton } from "@/components/shared/BackButton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { projects as allProjects, activity } from "@/mocks/seed";

type Tab = "overview" | "projects" | "skills" | "activity";

function getTabFromURL(): Tab {
  const params = new URLSearchParams(window.location.search);
  const tab = params.get("tab");
  if (tab === "overview" || tab === "projects" || tab === "skills" || tab === "activity")
    return tab;
  return "overview";
}

export const Route = createFileRoute("/_app/builders/$builderId")({
  head: ({ params }) => ({
    meta: [
      { title: `Builder — DevLink` },
      { name: "description", content: `Builder ${params.builderId} on DevLink.` },
    ],
  }),
  component: BuilderProfile,
});

function BuilderProfile() {
  const { builderId } = Route.useParams();
  const { data: b, isLoading } = useQuery({
    queryKey: ["builder", builderId],
    queryFn: () => buildersService.get(builderId),
  });
  const [tab, setTab] = useState<Tab>(getTabFromURL);

  const handleTabChange = (value: string) => {
    setTab(value as Tab);
    const url = new URL(window.location.href);
    url.searchParams.set("tab", value);
    window.history.replaceState({}, "", url.toString());
  };

  if (isLoading)
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
            <div className="flex gap-2">
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-8 w-28" />
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
        <div className="inline-flex h-9 items-center gap-1 rounded-lg bg-muted p-1">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-7 w-24" />
          ))}
        </div>
      </div>
    );
  if (!b) throw notFound();

  const builderProjects = allProjects.filter((p) => p.owner === b.name);

  return (
    <div className="space-y-4">
      <BackButton to="/builders" label="Back to builders" />
      <Card className="p-4">
        <div className="flex flex-wrap items-start gap-5">
          <Avatar src={b.avatar} alt={b.name} size={96} online={b.online} />
          <div className="min-w-0 flex-1">
            <h1 className="text-[22px] font-bold text-foreground">{b.name}</h1>
            <p className="text-[13px] text-muted-foreground">
              @{b.handle} · {b.role}
            </p>
            <p className="mt-2 text-[13px] text-foreground">{b.bio}</p>
            <div className="mt-2">
              <LastActive lastActiveAt={b.lastActiveAt} />
            </div>
          </div>
          <div className="flex gap-2">
            <FollowButton userId={b.id} />
            <button className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-[13px] font-medium text-foreground hover:bg-muted">
              <MessageSquare size={14} /> Message
            </button>
          </div>
        </div>
      </Card>
      <div className="grid gap-3 lg:grid-cols-3">
        <Card className="p-4">
          <p className="text-[13px] font-semibold text-foreground">Match Score</p>
          <p className="mt-2 text-[36px] font-bold text-success">{b.matchScore}%</p>
        </Card>
        <Card className="p-4">
          <p className="text-[13px] font-semibold text-foreground">Experience</p>
          <p className="mt-2 text-[36px] font-bold text-foreground">
            {b.yearsExp} <span className="text-[14px] font-medium text-muted-foreground">yrs</span>
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-[13px] font-semibold text-foreground">Location</p>
          <p className="mt-2 text-[20px] font-bold text-foreground">{b.country}</p>
        </Card>
      </div>

      <Tabs value={tab} onValueChange={handleTabChange}>
        <TabsList className="overflow-x-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="projects">Projects</TabsTrigger>
          <TabsTrigger value="skills">Skills</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="p-4">
              <p className="text-[13px] font-semibold text-foreground">Match Score</p>
              <p className="mt-2 text-[36px] font-bold text-success">{b.matchScore}%</p>
            </Card>
            <Card className="p-4">
              <p className="text-[13px] font-semibold text-foreground">Experience</p>
              <p className="mt-2 text-[36px] font-bold text-foreground">
                {b.yearsExp}{" "}
                <span className="text-[14px] font-medium text-muted-foreground">yrs</span>
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-[13px] font-semibold text-foreground">Location</p>
              <p className="mt-2 text-[20px] font-bold text-foreground">{b.country}</p>
            </Card>
          </div>
          <Card className="p-4 mt-4">
            <p className="text-[13px] font-semibold text-foreground">About</p>
            <p className="mt-2 text-[13px] text-muted-foreground">{b.bio}</p>
          </Card>
        </TabsContent>

        <TabsContent value="projects">
          {builderProjects.length === 0 ? (
            <Card className="p-8">
              <EmptyState
                title="No projects yet"
                desc="This builder hasn't created any projects."
                action={<FolderOpen size={20} className="text-muted-foreground" />}
              />
            </Card>
          ) : (
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {builderProjects.map((p) => (
                <a key={p.id} href={`/projects/${p.id}`} className="block">
                  <Card interactive className="p-4">
                    <div className="flex items-start gap-3">
                      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-muted text-xl">
                        {p.icon}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-[14px] font-semibold text-foreground">
                          {p.name}
                        </p>
                        <p className="mt-0.5 line-clamp-2 text-[12px] text-muted-foreground">
                          {p.description}
                        </p>
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-1">
                      {p.stack.map((s) => (
                        <TagChip key={s}>{s}</TagChip>
                      ))}
                    </div>
                    <div className="mt-3 flex items-center justify-between text-[11px] text-muted-foreground">
                      <span className="inline-flex items-center gap-1">
                        <Users2 size={12} /> {p.members}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Star size={12} /> {p.stars}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <GitFork size={12} /> {p.forks}
                      </span>
                    </div>
                  </Card>
                </a>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="skills">
          {b.skills.length === 0 ? (
            <Card className="p-8">
              <EmptyState
                title="No skills listed"
                desc="This builder hasn't added any skills yet."
              />
            </Card>
          ) : (
            <Card className="p-4">
              <p className="text-[13px] font-semibold text-foreground mb-3">Technical Skills</p>
              <div className="flex flex-wrap gap-2">
                {b.skills.map((s) => (
                  <TagChip key={s} className="px-2.5 py-1 text-[12px]">
                    {s}
                  </TagChip>
                ))}
              </div>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="activity">
          {activity.length === 0 ? (
            <Card className="p-8">
              <EmptyState
                title="No recent activity"
                desc="Nothing happened recently."
                action={<ActivityIcon size={20} className="text-muted-foreground" />}
              />
            </Card>
          ) : (
            <Card>
              <ul className="divide-y divide-border">
                {activity.map((a) => (
                  <li
                    key={a.id}
                    className="flex items-center gap-3 px-4 py-2.5 text-[13px] text-foreground"
                  >
                    {a.text}
                    {a.highlight && (
                      <span className="ml-1 font-medium text-primary">{a.highlight}</span>
                    )}
                    <span className="ml-auto shrink-0 text-[11px] text-muted-foreground">
                      {a.ago}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
