import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { flaresService } from "@/services";
import { Card, TagChip, Avatar } from "@/components/shared/primitives";
import { Markdown } from "@/components/shared/Markdown";
import { MarkdownEditor } from "@/components/shared/MarkdownEditor";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { Heart, MessageCircle, Send, Flame } from "lucide-react";
import { useState, useCallback } from "react";
import { currentUser, builders } from "@/mocks/seed";
import type { Flare } from "@/mocks/seed";
import { toast } from "sonner";
import { useToggleLike, useLikedFlares } from "@/hooks/useLike";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/flares")({
  head: () => ({
    meta: [
      { title: "Flares — DevLink Community" },
      { name: "description", content: "Community feed of updates, tips and asks from builders." },
    ],
  }),
  component: FlaresPage,
});

function FlareCard({ flare }: { flare: Flare }) {
  const { data: likedMap } = useLikedFlares();
  const toggleLike = useToggleLike(flare.id);
  const isLiked = likedMap?.[flare.id] ?? false;

  return (
    <Card className="p-4">
      <div className="flex items-start gap-3">
        <Avatar
          src={flare.author.avatar}
          alt={flare.author.name}
          size={40}
          online={flare.author.online}
        />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-[13px] font-semibold text-foreground">{flare.author.name}</p>
            <p className="text-[12px] text-muted-foreground">
              @{flare.author.handle} · {flare.ago}
            </p>
          </div>
          <div className="mt-2">
            <Markdown content={flare.content} />
          </div>
          <div className="mt-2 flex flex-wrap gap-1">
            {flare.tags.map((t) => (
              <TagChip key={t}>#{t}</TagChip>
            ))}
          </div>
          <div className="mt-3 flex items-center justify-between gap-4 text-[12px] text-muted-foreground">
            <div className="flex items-center gap-4">
              <button
                className={cn(
                  "inline-flex items-center gap-1 transition-colors",
                  isLiked ? "text-destructive" : "hover:text-destructive",
                )}
                onClick={() => toggleLike.mutate()}
                disabled={toggleLike.isPending}
                aria-label={isLiked ? "Unlike this flare" : "Like this flare"}
                aria-pressed={isLiked}
              >
                <Heart size={12} className={isLiked ? "fill-current" : ""} /> {flare.likes}
              </button>
              <button className="inline-flex items-center gap-1 hover:text-primary">
                <MessageCircle size={12} /> {flare.comments}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

function FlaresPage() {
  const { data = [] } = useQuery({ queryKey: ["flares"], queryFn: flaresService.list });
  const [content, setContent] = useState("");
  const [localFlares, setLocalFlares] = useState<Flare[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const feed = [...localFlares, ...data];

  const handlePost = useCallback(async () => {
    if (!content.trim() || submitting) return;
    setSubmitting(true);
    try {
      await new Promise((r) => setTimeout(r, 600));
      const newFlare: Flare = {
        id: `local-${Date.now()}`,
        author: {
          ...builders[0],
          name: currentUser.name,
          handle: currentUser.handle,
          avatar: currentUser.avatar,
        },
        content,
        tags: Array.from(new Set(content.match(/#(\w+)/g)?.map((t) => t.slice(1)) ?? [])),
        likes: 0,
        comments: 0,
        ago: "just now",
      };
      setLocalFlares((prev) => [newFlare, ...prev]);
      toast.success("Flare posted");
      setContent("");
    } finally {
      setSubmitting(false);
    }
  }, [content, submitting]);

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
      <div className="space-y-4">
        <Card className="p-4">
          <div className="flex items-start gap-3">
            <Avatar src={currentUser.avatar} alt={currentUser.name} size={40} />
            <div className="min-w-0 flex-1">
              <MarkdownEditor
                value={content}
                onChange={setContent}
                placeholder="Share an update, a tip, or ask the community…"
                rows={3}
              />
              <div className="mt-2 flex items-center justify-between">
                <p className="text-[11px] text-muted-foreground">Markdown supported</p>
                <LoadingButton
                  disabled={!content.trim()}
                  loading={submitting}
                  loadingText="Posting..."
                  onClick={handlePost}
                  size="sm"
                  className="inline-flex items-center gap-1.5"
                >
                  <Send size={12} /> Post
                </LoadingButton>
              </div>
            </div>
          </div>
        </Card>

        {feed.map((f) => (
          <FlareCard key={f.id} flare={f} />
        ))}
      </div>

      <aside className="space-y-4">
        <Card className="p-4">
          <p className="flex items-center gap-1.5 text-[13px] font-semibold text-foreground">
            <Flame size={14} className="text-warning" /> Trending tags
          </p>
          <div className="mt-3 flex flex-wrap gap-1">
            {[
              "react",
              "typescript",
              "ml",
              "designsystems",
              "postgres",
              "webgpu",
              "wasm",
              "rust",
            ].map((t) => (
              <TagChip key={t}>#{t}</TagChip>
            ))}
          </div>
        </Card>
        <Card className="p-4">
          <p className="text-[13px] font-semibold text-foreground">Community guidelines</p>
          <p className="mt-2 text-[12px] text-muted-foreground">
            Be kind, credit sources, no spam. Ship generously.
          </p>
        </Card>
      </aside>
    </div>
  );
}
