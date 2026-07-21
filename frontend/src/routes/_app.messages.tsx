import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { messagesService } from "@/services";
import { Card, Avatar } from "@/components/shared/primitives";
import { MessageSquare } from "lucide-react";

export const Route = createFileRoute("/_app/messages")({
  head: () => ({
    meta: [
      { title: "Messages — DevLink" },
      { name: "description", content: "Chat with teammates and builders in real time." },
    ],
  }),
  component: MessagesIndex,
});

function MessagesIndex() {
  const { data = [] } = useQuery({
    queryKey: ["conversations"],
    queryFn: messagesService.conversations,
  });
  return (
    <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
      <Card className="lg:h-[calc(100vh-8rem)] lg:overflow-y-auto">
        <div className="border-b border-border px-4 py-3">
          <p className="text-[14px] font-semibold text-foreground">Conversations</p>
        </div>
        <ul className="divide-y divide-border">
          {data.map((c) => (
            <li key={c.id}>
              <Link
                to="/messages/$conversationId"
                params={{ conversationId: c.id }}
                className="flex items-center gap-3 px-4 py-3 hover:bg-muted/50"
              >
                <Avatar src={c.with.avatar} alt={c.with.name} size={40} online={c.with.online} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-semibold text-foreground">
                    {c.with.name}
                  </p>
                  <p className="truncate text-[12px] text-muted-foreground">{c.preview}</p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className="text-[11px] text-muted-foreground">{c.ago}</span>
                  {c.unread > 0 && (
                    <span className="rounded-full bg-primary px-1.5 text-[10px] font-semibold text-primary-foreground">
                      {c.unread}
                    </span>
                  )}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </Card>
      <Card className="grid place-items-center p-4 text-center">
        <div>
          <MessageSquare size={32} className="mx-auto text-muted-foreground" />
          <p className="mt-3 text-[14px] font-semibold text-foreground">Select a conversation</p>
          <p className="mt-1 text-[12px] text-muted-foreground">
            Choose a chat on the left to start messaging.
          </p>
        </div>
      </Card>
    </div>
  );
}
