import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { notificationsService } from "@/services";
import { Card } from "@/components/shared/primitives";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/notifications")({
  head: () => ({
    meta: [
      { title: "Notifications — DevLink" },
      { name: "description", content: "All your DevLink notifications in one place." },
    ],
  }),
  component: NotificationsPage,
});

function NotificationsPage() {
  const { data = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: notificationsService.list,
  });
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-bold tracking-tight text-foreground">Notifications</h1>
          <p className="text-[13px] text-muted-foreground">Stay on top of what's happening.</p>
        </div>
        <button className="rounded-md border border-border bg-surface px-3 py-1.5 text-[12px] font-medium text-foreground hover:bg-muted">
          Mark all read
        </button>
      </div>
      <Card>
        <ul className="divide-y divide-border">
          {data.map((n) => (
            <li
              key={n.id}
              className={cn("flex items-center gap-3 px-4 py-3", n.unread && "bg-primary-soft/30")}
            >
              <span
                className={cn(
                  "h-2 w-2 shrink-0 rounded-full",
                  n.unread ? "bg-primary" : "bg-transparent",
                )}
              />
              <p className="min-w-0 flex-1 text-[13px] text-foreground">{n.text}</p>
              <span className="text-[11px] text-muted-foreground">{n.ago}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
