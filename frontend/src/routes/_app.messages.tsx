import { createFileRoute, Link, Outlet, useMatch } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { messagesService } from "@/services";
import { Card, Avatar, EmptyState } from "@/components/shared/primitives";
import {
  MessageSquareDashed,
  Search,
  X,
  Pin,
  Archive,
  BellOff,
  MoreVertical,
  Plus,
  Volume2,
  Mail,
  MailOpen,
  ArchiveRestore,
} from "lucide-react";
import { useState, useEffect, createContext, useContext } from "react";
import { TypoCaption } from "@/components/shared/Typography";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { currentUser } from "@/mocks/seed";
import { NotificationCenter } from "@/components/shared/NotificationCenter";

// Context to share conversation settings with the thread details panel
export interface ConversationSettingsContextType {
  pinnedIds: string[];
  archivedIds: string[];
  mutedIds: string[];
  manualUnreadIds: string[];
  togglePin: (id: string) => void;
  toggleArchive: (id: string) => void;
  toggleMute: (id: string) => void;
  toggleManualUnread: (id: string) => void;
}

export const ConversationSettingsContext = createContext<ConversationSettingsContextType | null>(null);

export function useConversationSettings() {
  const context = useContext(ConversationSettingsContext);
  if (!context) {
    throw new Error("useConversationSettings must be used within a ConversationSettingsProvider");
  }
  return context;
}

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

  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<"all" | "unread" | "pinned" | "archived">("all");
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);

  // Local storage flags for Pin, Archive, Mute, and Manual Unread
  const [pinnedIds, setPinnedIds] = useState<string[]>([]);
  const [archivedIds, setArchivedIds] = useState<string[]>([]);
  const [mutedIds, setMutedIds] = useState<string[]>([]);
  const [manualUnreadIds, setManualUnreadIds] = useState<string[]>([]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        setPinnedIds(JSON.parse(localStorage.getItem("devlink_pinned_convs") || "[]"));
        setArchivedIds(JSON.parse(localStorage.getItem("devlink_archived_convs") || "[]"));
        setMutedIds(JSON.parse(localStorage.getItem("devlink_muted_convs") || "[]"));
        setManualUnreadIds(JSON.parse(localStorage.getItem("devlink_unread_convs") || "[]"));
      } catch (e) {
        console.error("Failed to load conversation settings from localStorage", e);
      }
    }
  }, []);

  const togglePin = (id: string) => {
    const next = pinnedIds.includes(id)
      ? pinnedIds.filter((x) => x !== id)
      : [...pinnedIds, id];
    setPinnedIds(next);
    localStorage.setItem("devlink_pinned_convs", JSON.stringify(next));
    toast.success(pinnedIds.includes(id) ? "Conversation unpinned" : "Conversation pinned");
    setActiveMenuId(null);
  };

  const toggleArchive = (id: string) => {
    const next = archivedIds.includes(id)
      ? archivedIds.filter((x) => x !== id)
      : [...archivedIds, id];
    setArchivedIds(next);
    localStorage.setItem("devlink_archived_convs", JSON.stringify(next));
    toast.success(archivedIds.includes(id) ? "Conversation unarchived" : "Conversation archived");
    setActiveMenuId(null);
  };

  const toggleMute = (id: string) => {
    const next = mutedIds.includes(id)
      ? mutedIds.filter((x) => x !== id)
      : [...mutedIds, id];
    setMutedIds(next);
    localStorage.setItem("devlink_muted_convs", JSON.stringify(next));
    toast.success(mutedIds.includes(id) ? "Notifications unmuted" : "Notifications muted");
    setActiveMenuId(null);
  };

  const toggleManualUnread = (id: string) => {
    const next = manualUnreadIds.includes(id)
      ? manualUnreadIds.filter((x) => x !== id)
      : [...manualUnreadIds, id];
    setManualUnreadIds(next);
    localStorage.setItem("devlink_unread_convs", JSON.stringify(next));
    toast.success(manualUnreadIds.includes(id) ? "Marked as read" : "Marked as unread");
    setActiveMenuId(null);
  };

  // Close menus on click outside
  useEffect(() => {
    if (!activeMenuId) return;
    const handler = () => setActiveMenuId(null);
    window.addEventListener("click", handler);
    return () => window.removeEventListener("click", handler);
  }, [activeMenuId]);

  const isConversationActive = useMatch({
    from: "/_app/messages/$conversationId",
    shouldThrow: false,
  });

  // Category counts
  const allCount = data.filter((c) => !archivedIds.includes(c.id)).length;
  const unreadCount = data.filter(
    (c) => !archivedIds.includes(c.id) && (c.unread > 0 || manualUnreadIds.includes(c.id))
  ).length;
  const pinnedCount = data.filter((c) => pinnedIds.includes(c.id) && !archivedIds.includes(c.id)).length;
  const archivedCount = data.filter((c) => archivedIds.includes(c.id)).length;

  // Real filtering logic
  const filteredConversations = data.filter((c) => {
    const matchesSearch =
      c.with.name.toLowerCase().includes(query.toLowerCase()) ||
      (c.preview && c.preview.toLowerCase().includes(query.toLowerCase()));

    if (!matchesSearch) return false;

    if (activeFilter === "pinned") {
      return pinnedIds.includes(c.id) && !archivedIds.includes(c.id);
    }
    if (activeFilter === "archived") {
      return archivedIds.includes(c.id);
    }
    if (activeFilter === "unread") {
      return (c.unread > 0 || manualUnreadIds.includes(c.id)) && !archivedIds.includes(c.id);
    }

    // Default "all"
    return !archivedIds.includes(c.id);
  });

  // Separate pinned and normal conversations for displaying
  const showPinnedSection = activeFilter === "all" || activeFilter === "unread";
  const pinnedConversations = showPinnedSection
    ? filteredConversations.filter((c) => pinnedIds.includes(c.id))
    : [];
  const normalConversations = showPinnedSection
    ? filteredConversations.filter((c) => !pinnedIds.includes(c.id))
    : filteredConversations;

  return (
    <ConversationSettingsContext.Provider
      value={{
        pinnedIds,
        archivedIds,
        mutedIds,
        manualUnreadIds,
        togglePin,
        toggleArchive,
        toggleMute,
        toggleManualUnread,
      }}
    >
      <div className="grid gap-0 lg:gap-4 lg:grid-cols-[340px_minmax(0,1fr)] h-full lg:h-[calc(100vh-8rem)] overflow-hidden">
        {/* Left Side: Conversation List Card */}
        <Card
          className={cn(
            "flex flex-col h-full overflow-hidden border-0 lg:border border-border bg-card rounded-none lg:rounded-2xl shadow-none lg:shadow-xs",
            isConversationActive && "hidden lg:flex"
          )}
        >
          {/* Compact Header Mobile-only */}
          <div className="flex md:hidden items-center justify-between px-4 pt-4 pb-2 border-b border-border bg-card shrink-0">
            <h1 className="text-xl font-extrabold text-foreground tracking-tight">Messages</h1>
            <div className="flex items-center gap-1.5">
              <NotificationCenter />
              <Link
                to="/profile/$username"
                params={{ username: currentUser.handle }}
                className="p-1 shrink-0 rounded-full hover:bg-muted transition-colors"
              >
                <Avatar src={currentUser.avatar} alt={currentUser.name} size={30} />
              </Link>
            </div>
          </div>

          {/* Desktop/Tablet Header */}
          <div className="hidden md:flex px-4 pt-4 pb-2 items-center justify-between shrink-0">
            <h2 className="text-lg font-bold text-foreground tracking-tight">Messages</h2>
            <div className="flex items-center gap-2">
              <button
                className="p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground rounded-md transition-colors"
                title="New conversation"
                onClick={() => toast.info("Search builders to start a chat")}
              >
                <Plus size={16} />
              </button>
            </div>
          </div>

          {/* Search bar */}
          <div className="px-4 py-2 shrink-0">
            <div className="flex h-11 items-center gap-2 rounded-xl border border-border bg-surface px-3.5 focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all">
              <Search size={15} className="text-muted-foreground shrink-0" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search conversations..."
                className="w-full bg-transparent text-[13px] outline-none placeholder:text-muted-foreground"
              />
              {query && (
                <button
                  onClick={() => setQuery("")}
                  className="text-muted-foreground hover:text-foreground p-1"
                >
                  <X size={14} />
                </button>
              )}
            </div>
          </div>

          {/* Filters */}
          <div className="px-4 py-2 border-b border-border shrink-0">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1.5 scrollbar-none">
              <button
                onClick={() => setActiveFilter("all")}
                className={cn(
                  "px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors border cursor-pointer select-none",
                  activeFilter === "all"
                    ? "bg-primary border-primary text-primary-foreground font-bold"
                    : "bg-surface border-border text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                )}
              >
                All {allCount > 0 && <span className="ml-1 opacity-75">{allCount}</span>}
              </button>
              <button
                onClick={() => setActiveFilter("unread")}
                className={cn(
                  "px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors border cursor-pointer select-none",
                  activeFilter === "unread"
                    ? "bg-primary border-primary text-primary-foreground font-bold"
                    : "bg-surface border-border text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                )}
              >
                Unread {unreadCount > 0 && <span className="ml-1 opacity-75">{unreadCount}</span>}
              </button>
              <button
                onClick={() => setActiveFilter("pinned")}
                className={cn(
                  "px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors border cursor-pointer select-none",
                  activeFilter === "pinned"
                    ? "bg-primary border-primary text-primary-foreground font-bold"
                    : "bg-surface border-border text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                )}
              >
                Pinned {pinnedCount > 0 && <span className="ml-1 opacity-75">{pinnedCount}</span>}
              </button>
              <button
                onClick={() => setActiveFilter("archived")}
                className={cn(
                  "px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors border cursor-pointer select-none",
                  activeFilter === "archived"
                    ? "bg-primary border-primary text-primary-foreground font-bold"
                    : "bg-surface border-border text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                )}
              >
                Archived {archivedCount > 0 && <span className="ml-1 opacity-75">{archivedCount}</span>}
              </button>
            </div>
          </div>

          {/* Conversations list container */}
          <div className="flex-1 overflow-y-auto min-h-0 divide-y divide-border/40">
            {filteredConversations.length === 0 ? (
              <div className="p-8 my-auto">
                <EmptyState
                  title={query ? "No matches found" : "No conversations"}
                  desc={
                    query
                      ? "Try searching for another name or message content."
                      : activeFilter === "archived"
                      ? "Archived conversations will appear here."
                      : "No conversations found."
                  }
                  icon={MessageSquareDashed}
                />
              </div>
            ) : (
              <div className="divide-y divide-border/45">
                {/* Pinned Section */}
                {pinnedConversations.length > 0 && (
                  <div className="pb-2">
                    <div className="px-4 pt-3 pb-1 text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1 select-none">
                      <Pin size={10} className="text-primary shrink-0 rotate-45" />
                      Pinned Chats
                    </div>
                    <ul>
                      {pinnedConversations.map((c) => (
                        <ConversationRow
                          key={c.id}
                          c={c}
                          isMuted={mutedIds.includes(c.id)}
                          isPinned={true}
                          isManualUnread={manualUnreadIds.includes(c.id)}
                          activeMenuId={activeMenuId}
                          setActiveMenuId={setActiveMenuId}
                          togglePin={togglePin}
                          toggleArchive={toggleArchive}
                          toggleMute={toggleMute}
                          toggleManualUnread={toggleManualUnread}
                        />
                      ))}
                    </ul>
                  </div>
                )}

                {/* Normal Section */}
                {normalConversations.length > 0 && (
                  <div>
                    {pinnedConversations.length > 0 && (
                      <div className="px-4 pt-3 pb-1 text-[10px] font-bold text-muted-foreground uppercase tracking-wider select-none">
                        All Conversations
                      </div>
                    )}
                    <ul>
                      {normalConversations.map((c) => (
                        <ConversationRow
                          key={c.id}
                          c={c}
                          isMuted={mutedIds.includes(c.id)}
                          isPinned={pinnedIds.includes(c.id)}
                          isManualUnread={manualUnreadIds.includes(c.id)}
                          activeMenuId={activeMenuId}
                          setActiveMenuId={setActiveMenuId}
                          togglePin={togglePin}
                          toggleArchive={toggleArchive}
                          toggleMute={toggleMute}
                          toggleManualUnread={toggleManualUnread}
                        />
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Archived conversations bottom entry */}
          {activeFilter !== "archived" && archivedCount > 0 && (
            <button
              onClick={() => setActiveFilter("archived")}
              className="w-full flex items-center justify-between border-t border-border px-4 py-3.5 text-xs text-muted-foreground hover:bg-muted/30 hover:text-foreground transition-colors font-medium mt-auto shrink-0 cursor-pointer select-none"
            >
              <span className="flex items-center gap-2">
                <Archive size={14} className="text-muted-foreground" />
                Archived Conversations
              </span>
              <span className="rounded-full bg-muted border border-border px-1.5 py-0.5 text-[10px] font-bold">
                {archivedCount}
              </span>
            </button>
          )}
        </Card>

        {/* Right Side: Active Chat / Empty State */}
        {isConversationActive ? (
          <div className="h-full overflow-hidden">
            <Outlet />
          </div>
        ) : (
          <Card className={cn("flex flex-col items-center justify-center p-8 bg-card border-border h-full", !isConversationActive && "hidden lg:flex")}>
            <EmptyState
              title="Select a conversation"
              desc="Choose a chat on the left or search builders to start a new conversation."
              icon={MessageSquareDashed}
            />
          </Card>
        )}
      </div>
    </ConversationSettingsContext.Provider>
  );
}

interface RowProps {
  c: any;
  isMuted: boolean;
  isPinned: boolean;
  isManualUnread: boolean;
  activeMenuId: string | null;
  setActiveMenuId: (id: string | null) => void;
  togglePin: (id: string) => void;
  toggleArchive: (id: string) => void;
  toggleMute: (id: string) => void;
  toggleManualUnread: (id: string) => void;
}

function ConversationRow({
  c,
  isMuted,
  isPinned,
  isManualUnread,
  activeMenuId,
  setActiveMenuId,
  togglePin,
  toggleArchive,
  toggleMute,
  toggleManualUnread,
}: RowProps) {
  const hasUnread = c.unread > 0 || isManualUnread;
  const { archivedIds } = useConversationSettings();
  const isArchived = archivedIds.includes(c.id);

  return (
    <li className="relative group">
      <Link
        to="/messages/$conversationId"
        params={{ conversationId: c.id }}
        className="flex items-center gap-3 px-4 py-3.5 min-h-[72px] hover:bg-muted/30 transition-all cursor-pointer relative"
        activeProps={{ className: "bg-primary-soft/40 border-l-2 border-primary pl-[14px]" }}
      >
        <Avatar src={c.with.avatar} alt={c.with.name} size={40} online={c.with.online} />
        
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-1 mb-0.5">
            <p className={cn("truncate text-[13px] text-foreground transition-all", hasUnread ? "font-bold text-foreground" : "font-medium text-foreground/80")}>
              {c.with.name}
            </p>
            <TypoCaption className="text-[10px] whitespace-nowrap shrink-0">{c.ago}</TypoCaption>
          </div>
          <div className="flex items-center justify-between gap-2">
            <p className={cn("truncate text-xs", hasUnread ? "font-semibold text-foreground/95" : "text-muted-foreground")}>
              {c.preview === "Typing…" ? (
                <span className="text-success font-medium animate-pulse">Typing...</span>
              ) : (
                c.preview
              )}
            </p>
            <div className="flex items-center gap-1 shrink-0">
              {isPinned && <Pin size={11} className="text-primary shrink-0 rotate-45" />}
              {isMuted && <BellOff size={11} className="text-muted-foreground shrink-0" />}
              {hasUnread && (
                <span className="h-4 min-w-4 px-1 rounded-full bg-primary text-[9px] font-bold text-primary-foreground flex items-center justify-center shrink-0">
                  {c.unread > 0 ? c.unread : 1}
                </span>
              )}
            </div>
          </div>
        </div>
      </Link>

      {/* Hover action menu trigger */}
      <div className="absolute right-3 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setActiveMenuId(activeMenuId === c.id ? null : c.id);
          }}
          className="p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground rounded-md border border-border bg-card shadow-xs cursor-pointer"
          title="Actions"
        >
          <MoreVertical size={13} />
        </button>

        {activeMenuId === c.id && (
          <div className="absolute right-0 mt-1 w-44 rounded-xl border border-border bg-card shadow-lg py-1.5 text-xs text-foreground z-20 animate-in fade-in slide-in-from-top-1 duration-150">
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                togglePin(c.id);
              }}
              className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-muted text-left"
            >
              <Pin size={12} className="rotate-45" />
              {isPinned ? "Unpin Chat" : "Pin Chat"}
            </button>
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                toggleManualUnread(c.id);
              }}
              className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-muted text-left"
            >
              {hasUnread ? <MailOpen size={12} /> : <Mail size={12} />}
              {hasUnread ? "Mark as Read" : "Mark as Unread"}
            </button>
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                toggleMute(c.id);
              }}
              className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-muted text-left"
            >
              <BellOff size={12} />
              {isMuted ? "Unmute Notifications" : "Mute Notifications"}
            </button>
            <div className="h-px bg-border my-1" />
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                toggleArchive(c.id);
              }}
              className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-muted text-left"
            >
              {isArchived ? <ArchiveRestore size={12} /> : <Archive size={12} />}
              {isArchived ? "Unarchive Chat" : "Archive Chat"}
            </button>
          </div>
        )}
      </div>
    </li>
  );
}
