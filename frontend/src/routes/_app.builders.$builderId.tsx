import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { buildersService } from "@/services";
import { Card, TagChip, Avatar } from "@/components/shared/primitives";
import { ArrowLeft, MessageSquare, UserPlus } from "lucide-react";
import { BackButton } from "@/components/shared/BackButton";

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
  if (isLoading) return <Card className="h-96 animate-pulse" />;
  if (!b) throw notFound();
  return (
    <div className="space-y-4">
      <BackButton to="/builders" label="Back to builders" />
      <Card className="p-6">
        <div className="flex flex-wrap items-start gap-5">
          <Avatar src={b.avatar} alt={b.name} size={96} online={b.online} />
          <div className="min-w-0 flex-1">
            <h1 className="text-[22px] font-bold text-foreground">{b.name}</h1>
            <p className="text-[13px] text-muted-foreground">
              @{b.handle} · {b.role}
            </p>
            <p className="mt-2 text-[13px] text-foreground">{b.bio}</p>
            <div className="mt-3 flex flex-wrap gap-1">
              {b.skills.map((s) => (
                <TagChip key={s}>{s}</TagChip>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90">
              <UserPlus size={14} /> Connect
            </button>
            <button className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-[13px] font-medium text-foreground hover:bg-muted">
              <MessageSquare size={14} /> Message
            </button>
          </div>
        </div>
      </Card>
      <div className="grid gap-4 lg:grid-cols-3">
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
    </div>
  );
}
