import { createFileRoute, Link } from "@tanstack/react-router";
import { Card, TagChip } from "@/components/shared/primitives";
import { projects, flares } from "@/mocks/seed";
import { Bookmark } from "lucide-react";

export const Route = createFileRoute("/_app/bookmarks")({
  head: () => ({
    meta: [
      { title: "Bookmarks — DevLink" },
      { name: "description", content: "Projects, builders and flares you've saved for later." },
    ],
  }),
  component: BookmarksPage,
});

function BookmarksPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-[22px] font-bold tracking-tight text-foreground">Bookmarks</h1>
        <p className="text-[13px] text-muted-foreground">Everything you've saved.</p>
      </div>
      <section>
        <p className="mb-2 text-[12px] font-semibold uppercase tracking-wider text-muted-foreground">
          Projects
        </p>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {projects.slice(0, 3).map((p) => (
            <Link key={p.id} to="/projects/$projectId" params={{ projectId: p.id }}>
              <Card interactive className="p-4">
                <div className="flex items-start gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-muted text-xl">
                    {p.icon}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[14px] font-semibold text-foreground">{p.name}</p>
                    <p className="mt-0.5 text-[12px] text-muted-foreground line-clamp-2">
                      {p.description}
                    </p>
                  </div>
                  <Bookmark size={14} className="text-primary" />
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {p.stack.map((s) => (
                    <TagChip key={s}>{s}</TagChip>
                  ))}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </section>
      <section>
        <p className="mb-2 text-[12px] font-semibold uppercase tracking-wider text-muted-foreground">
          Flares
        </p>
        <div className="space-y-2">
          {flares.slice(0, 2).map((f) => (
            <Card key={f.id} className="p-4">
              <p className="text-[13px] font-semibold text-foreground">{f.author.name}</p>
              <p className="mt-1 text-[13px] text-foreground">{f.content}</p>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
