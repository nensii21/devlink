import { createFileRoute, notFound, Link, useNavigate } from "@tanstack/react-router";
import { Card, TagChip, Avatar, Skeleton } from "@/components/shared/primitives";
import { builders, currentUser, projects } from "@/mocks/seed";
import { MapPin, Calendar, Link as LinkIcon, MessageCircle, Sparkles, Pencil, RotateCw } from "lucide-react";
import { toast } from "sonner";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { profileSummaryApi, type ProfileSummaryResponse } from "@/api";
import { cn } from "@/lib/utils";

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
        id: currentUser.id,
      }
    : builders.find((x) => x.handle === username);
  if (!b) throw notFound();

  // Profile summary state
  const [summary, setSummary] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedSummary, setEditedSummary] = useState("");

  const summaryMutation = useMutation({
    mutationFn: () => profileSummaryApi.generate(b.id),
    onSuccess: (data: ProfileSummaryResponse) => {
      setSummary(data.summary);
      setEditedSummary(data.summary);
      toast.success("Profile summary generated!");
    },
    onError: () => {
      toast.error("Failed to generate summary. Please try again.");
    },
  });

  const handleEdit = () => {
    setEditedSummary(summary || "");
    setIsEditing(true);
  };

  const handleSave = () => {
    setSummary(editedSummary);
    setIsEditing(false);
    toast.success("Summary updated!");
  };

  const handleCancel = () => {
    setEditedSummary(summary || "");
    setIsEditing(false);
  };

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

      {/* AI Profile Summary Section */}
      <Card className="p-4">
        <div className="flex items-center justify-between gap-3">
          <p className="text-[13px] font-semibold text-foreground flex items-center gap-2">
            <Sparkles size={14} className="text-primary" />
            AI Profile Summary
          </p>
          {summary && !isEditing && (
            <div className="flex items-center gap-1">
              <button
                onClick={handleEdit}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              >
                <Pencil size={12} /> Edit
              </button>
              <button
                onClick={() => summaryMutation.mutate()}
                disabled={summaryMutation.isPending}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted/50 hover:text-foreground disabled:opacity-50"
              >
                <RotateCw size={12} className={summaryMutation.isPending ? "animate-spin" : ""} /> Regenerate
              </button>
            </div>
          )}
          {!summary && !summaryMutation.isPending && (
            <button
              onClick={() => summaryMutation.mutate()}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-[11px] font-semibold text-primary-foreground hover:opacity-90"
            >
              <Sparkles size={12} /> Generate Summary
            </button>
          )}
        </div>

        {summaryMutation.isPending && (
          <div className="mt-3 space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        )}

        {summary && !summaryMutation.isPending && (
          <div className="mt-3">
            {isEditing ? (
              <div className="space-y-2">
                <textarea
                  value={editedSummary}
                  onChange={(e) => setEditedSummary(e.target.value)}
                  maxLength={500}
                  rows={4}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-[13px] text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 resize-none"
                />
                <div className="flex items-center justify-between">
                  <p className={cn(
                    "text-[11px]",
                    editedSummary.length > 450 ? "text-orange-500" : "text-muted-foreground"
                  )}>
                    {editedSummary.length}/500 characters
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleCancel}
                      className="rounded-md px-3 py-1.5 text-[11px] text-muted-foreground hover:bg-muted/50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      className="rounded-md bg-primary px-3 py-1.5 text-[11px] font-semibold text-primary-foreground hover:opacity-90"
                    >
                      Save
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-[13px] text-foreground leading-relaxed">{summary}</p>
            )}
          </div>
        )}

        {!summary && !summaryMutation.isPending && !summaryMutation.isError && (
          <p className="mt-2 text-[12px] text-muted-foreground">
            Generate an AI-powered professional summary based on your profile, skills, and activity.
          </p>
        )}

        {summaryMutation.isError && (
          <p className="mt-2 text-[12px] text-destructive">
            Failed to generate summary. Please try again.
          </p>
        )}
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
