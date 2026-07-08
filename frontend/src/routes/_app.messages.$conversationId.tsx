import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { messagesService } from "@/services";
import { Card, Avatar } from "@/components/shared/primitives";
import { ArrowLeft, Send } from "lucide-react";
import { useState } from "react";
import { conversations } from "@/mocks/seed";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/messages/$conversationId")({
  head: () => ({ meta: [{ title: "Chat — DevLink" }] }),
  component: Thread,
});

function Thread() {
  const { conversationId } = Route.useParams();
  const conv = conversations.find((c) => c.id === conversationId) ?? conversations[0];
  const { data = [] } = useQuery({
    queryKey: ["thread", conversationId],
    queryFn: () => messagesService.thread(conversationId),
  });
  const [text, setText] = useState("");

  return (
    <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
      <Card className="hidden lg:block lg:h-[calc(100vh-8rem)] lg:overflow-y-auto">
        <div className="border-b border-border px-4 py-3">
          <p className="text-[14px] font-semibold text-foreground">Conversations</p>
        </div>
        <ul className="divide-y divide-border">
          {conversations.map((c) => (
            <li key={c.id}>
              <Link
                to="/messages/$conversationId"
                params={{ conversationId: c.id }}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 hover:bg-muted/50",
                  c.id === conversationId && "bg-muted/50",
                )}
              >
                <Avatar src={c.with.avatar} alt={c.with.name} size={36} online={c.with.online} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-semibold text-foreground">
                    {c.with.name}
                  </p>
                  <p className="truncate text-[12px] text-muted-foreground">{c.preview}</p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </Card>

      <Card className="flex flex-col lg:h-[calc(100vh-8rem)]">
        <div className="flex items-center gap-3 border-b border-border px-4 py-3">
          <Link to="/messages" className="lg:hidden">
            <ArrowLeft size={16} className="text-muted-foreground" />
          </Link>
          <Avatar src={conv.with.avatar} alt={conv.with.name} size={36} online={conv.with.online} />
          <div>
            <p className="text-[13px] font-semibold text-foreground">{conv.with.name}</p>
            <p className="text-[11px] text-muted-foreground">
              {conv.with.online ? "Online" : "Offline"}
            </p>
          </div>
        </div>

        <div className="flex-1 space-y-2 overflow-y-auto p-4">
          {data.length === 0 && (
            <p className="text-center text-[12px] text-muted-foreground">
              No messages yet — say hello 👋
            </p>
          )}
          {data.map((m) => (
            <div
              key={m.id}
              className={cn("flex", m.from === "me" ? "justify-end" : "justify-start")}
            >
              <div
                className={cn(
                  "max-w-[75%] rounded-md px-3 py-2 text-[13px]",
                  m.from === "me"
                    ? "bg-primary text-primary-foreground"
                    : "border border-border bg-surface text-foreground",
                )}
              >
                <p>{m.text}</p>
                <p
                  className={cn(
                    "mt-1 text-[10px]",
                    m.from === "me" ? "text-primary-foreground/70" : "text-muted-foreground",
                  )}
                >
                  {m.at}
                </p>
              </div>
            </div>
          ))}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            setText("");
          }}
          className="flex items-center gap-2 border-t border-border p-3"
        >
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type a message…"
            className="min-w-0 flex-1 rounded-md border border-border bg-surface px-3 py-2 text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
          <button className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90">
            <Send size={14} /> Send
          </button>
        </form>
      </Card>
    </div>
  );
}
