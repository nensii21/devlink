import { createFileRoute, notFound, Link, useNavigate } from "@tanstack/react-router";
import { Card, TagChip, Avatar } from "@/components/shared/primitives";
import { builders, currentUser, projects } from "@/mocks/seed";
import { MapPin, Calendar, Link as LinkIcon, MessageCircle } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/profile/$username")({
  head: ({ params }) => ({
    meta: [
      { title: `@${params.username} — DevLink` },
      {
        name: "description",
        content: `${params.username}'s DevLink profile: skills, projects and activity.`,
      },
    ],
  }),
  component: ProfilePage,
});

function ProfilePage() {
  const { username } = Route.useParams();
  const navigate = useNavigate();
  const me = username === currentUser.handle;
  const b = me
    ? {
        ...builders[0],
        name: currentUser.name,
        handle: currentUser.handle,
        avatar: currentUser.avatar,
        bio: "Product engineer. Ships fast, sleeps sometimes.",
        role: "Full Stack Developer",
      }
    : builders.find((x) => x.handle === username);
  if (!b) throw notFound();

  return (
    <div className="space-y-4">
      {me ? (
        <Card className="p-6 bg-gradient-to-r from-primary-soft via-transparent to-transparent border-primary/20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <span className="text-lg">🚀</span> Your Shareable Public Portfolio
              </h3>
              <p className="text-xs text-muted-foreground">
                Showcase your projects, skills, and flares with beautiful custom themes, custom
                layouts, and a direct contact form.
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Link
                to="/portfolio/$username"
                params={{ username: b.handle }}
                className="inline-flex items-center justify-center rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
              >
                View Portfolio
              </Link>
              <button
                onClick={() => {
                  const url = `${window.location.origin}/portfolio/${b.handle}`;
                  navigator.clipboard.writeText(url);
                  toast.success("Portfolio link copied to clipboard!");
                }}
                className="inline-flex items-center justify-center rounded-md border border-border bg-surface px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
              >
                Copy Link
              </button>
            </div>
          </div>
        </Card>
      ) : (
        <Card className="p-4 bg-muted/40">
          <div className="flex items-center justify-between gap-4">
            <p className="text-xs text-muted-foreground">
              Looking for a more polished, professional view of {b.name}'s work?
            </p>
            <Link
              to="/portfolio/$username"
              params={{ username: b.handle }}
              className="inline-flex items-center justify-center rounded-md border border-primary text-primary hover:bg-primary-soft px-3 py-1.5 text-xs font-semibold transition-colors"
            >
              View Public Portfolio
            </Link>
          </div>
        </Card>
      )}

      <Card className="p-6">
        <div className="flex flex-wrap items-start gap-5">
          <Avatar src={b.avatar} alt={b.name} size={96} online={b.online} />
          <div className="min-w-0 flex-1">
            <h1 className="text-[22px] font-bold text-foreground">{b.name}</h1>
            <p className="text-[13px] text-muted-foreground">
              @{b.handle} · {b.role}
            </p>
            <p className="mt-2 text-[13px] text-foreground">{b.bio}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-[12px] text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <MapPin size={12} /> {b.country}
              </span>
              <span className="inline-flex items-center gap-1">
                <Calendar size={12} /> Joined 2024
              </span>
              <span className="inline-flex items-center gap-1">
                <LinkIcon size={12} /> devlink.io/{b.handle}
              </span>
            </div>
          </div>
          {!me && (
            <button
              type="button"
              onClick={() =>
                navigate({
                  to: "/messages/$conversationId",
                  params: { conversationId: b.id },
                })
              }
              className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              <MessageCircle size={16} />
              Contact Developer
            </button>
          )}
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="p-4">
          <p className="text-[13px] font-semibold text-foreground">Skills</p>
          <div className="mt-3 flex flex-wrap gap-1">
            {b.skills.map((s) => (
              <TagChip key={s}>{s}</TagChip>
            ))}
          </div>
        </Card>
        <Card className="p-4 lg:col-span-2">
          <p className="text-[13px] font-semibold text-foreground">Projects</p>
          <ul className="mt-3 divide-y divide-border">
            {projects.slice(0, 4).map((p) => (
              <li key={p.id} className="flex items-center gap-3 py-2">
                <span className="grid h-8 w-8 place-items-center rounded-md bg-muted text-lg">
                  {p.icon}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-semibold text-foreground">{p.name}</p>
                  <p className="truncate text-[11px] text-muted-foreground">
                    {p.stack.join(" · ")}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
