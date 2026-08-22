import { useState } from "react";
import { Card } from "@/components/shared/primitives";
import { useCollaborativeWorkspace } from "@/hooks/useCollaborativeWorkspace";
import {
  FileText,
  Plus,
  Radio,
  AlertTriangle,
  CheckCircle2,
  Users,
  Sparkles,
  CloudCheck,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { currentUser } from "@/mocks/seed";
import { TypoSection, TypoCaption } from "@/components/shared/Typography";

interface CollaborativeWorkspaceProps {
  projectId: string;
}

export function CollaborativeWorkspace({ projectId }: CollaborativeWorkspaceProps) {
  const {
    documents,
    activeDoc,
    activeDocId,
    cursors,
    hasConflict,
    conflictMessage,
    isSaving,
    isConnected,
    selectDocument,
    createDocument,
    updateContent,
    updateCursor,
    dismissConflict,
  } = useCollaborativeWorkspace(projectId, currentUser.id, currentUser.name);

  const [newDocTitle, setNewDocTitle] = useState("");
  const [showNewDocInput, setShowNewDocInput] = useState(false);

  const handleCreateDoc = async () => {
    if (!newDocTitle.trim()) return;
    await createDocument(newDocTitle.trim());
    setNewDocTitle("");
    setShowNewDocInput(false);
  };

  return (
    <div className="grid gap-4 lg:grid-cols-4">
      {/* Sidebar - Workspace Document List */}
      <Card className="p-4 lg:col-span-1 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-border pb-3 mb-3">
            <TypoSection>
              <FileText size={16} className="text-primary" />
              Workspace Docs
            </TypoSection>
            <button
              onClick={() => setShowNewDocInput(true)}
              className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary hover:bg-primary/20 transition-colors"
            >
              <Plus size={14} /> New
            </button>
          </div>

          {showNewDocInput && (
            <div className="mb-3 space-y-2 rounded-md border border-border p-2 bg-muted/20">
              <input
                type="text"
                placeholder="Document title..."
                value={newDocTitle}
                onChange={(e) => setNewDocTitle(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreateDoc()}
                className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                autoFocus
              />
              <div className="flex justify-end gap-1">
                <button
                  onClick={() => setShowNewDocInput(false)}
                  className="px-2 py-1 text-[11px] text-muted-foreground hover:text-foreground"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateDoc}
                  className="rounded-md bg-primary px-2.5 py-1 text-[11px] font-semibold text-primary-foreground"
                >
                  Save
                </button>
              </div>
            </div>
          )}

          <div className="space-y-1">
            {documents.length === 0 ? (
              <TypoCaption as="p">No documents yet.</TypoCaption>
            ) : (
              documents.map((doc) => (
                <button
                  key={doc.id}
                  onClick={() => selectDocument(doc.id)}
                  className={cn(
                    "w-full flex items-center justify-between rounded-md px-3 py-2 text-left text-xs font-medium transition-colors",
                    activeDocId === doc.id
                      ? "bg-primary/10 text-primary border border-primary/20"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )}
                >
                  <span className="truncate pr-2">{doc.title}</span>
                  <TypoCaption>v{doc.version}</TypoCaption>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Real-time Connection Status Indicator */}
        <div className="pt-3 border-t border-border mt-4 flex items-center justify-between text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <Radio
              size={12}
              className={cn("animate-pulse", isConnected ? "text-emerald-500" : "text-amber-500")}
            />
            {isConnected ? "Live Sync Active" : "Local Draft Mode"}
          </span>
          <span className="flex items-center gap-1">
            <Users size={12} />
            {Object.keys(cursors).length + 1} online
          </span>
        </div>
      </Card>

      {/* Main Workspace Editor */}
      <Card className="p-4 lg:col-span-3 space-y-4">
        {activeDoc ? (
          <>
            {/* Header / Meta Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
              <div className="flex-1 min-w-[200px]">
                <input
                  type="text"
                  value={activeDoc.title}
                  onChange={(e) => updateContent(activeDoc.content, e.target.value)}
                  className="w-full bg-transparent text-lg font-bold text-foreground focus:outline-none border-b border-transparent hover:border-border focus:border-primary transition-colors"
                  placeholder="Document Title"
                />
              </div>

              <div className="flex items-center gap-3">
                {/* Active Collaborators Presence */}
                <div className="flex items-center gap-1">
                  <div className="flex -space-x-2 overflow-hidden">
                    <img
                      src={currentUser.avatar}
                      alt={currentUser.name}
                      title={`${currentUser.name} (You)`}
                      className="inline-block h-7 w-7 rounded-full ring-2 ring-background object-cover"
                    />
                    {Object.values(cursors).map((c) => (
                      <span
                        key={c.userId}
                        title={`${c.username} is editing`}
                        className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground ring-2 ring-background"
                      >
                        {c.username.slice(0, 2).toUpperCase()}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Save Status Badge */}
                <TypoCaption>
                  {isSaving ? (
                    <>
                      <RefreshCw size={12} className="animate-spin text-primary" /> Saving...
                    </>
                  ) : (
                    <>
                      <CloudCheck size={12} className="text-emerald-500" /> Synced v
                      {activeDoc.version}
                    </>
                  )}
                </TypoCaption>
              </div>
            </div>

            {/* Conflict Alert Banner */}
            {hasConflict && (
              <div className="flex items-center justify-between rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-600 dark:text-amber-400">
                <div className="flex items-center gap-2">
                  <AlertTriangle size={16} className="shrink-0 text-amber-500" />
                  <span>
                    {conflictMessage ||
                      "Version conflict detected. Server changes merged automatically."}
                  </span>
                </div>
                <button
                  onClick={dismissConflict}
                  className="rounded px-2 py-1 text-[11px] font-semibold text-amber-600 dark:text-amber-300 hover:bg-amber-500/20 transition-colors"
                >
                  Dismiss
                </button>
              </div>
            )}

            {/* Live Collaborative Text Area */}
            <div className="relative min-h-[350px]">
              <textarea
                value={activeDoc.content}
                onChange={(e) => updateContent(e.target.value)}
                onSelect={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  updateCursor(target.selectionStart, target.selectionStart, target.selectionEnd);
                }}
                placeholder="Start typing project notes, architecture specs, or documentation..."
                className="w-full min-h-[350px] resize-y rounded-md border border-border bg-background p-3 text-sm font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary leading-relaxed"
              />
            </div>
          </>
        ) : (
          <div className="grid h-[350px] place-items-center text-center">
            <div>
              <Sparkles size={32} className="mx-auto text-muted-foreground opacity-50 mb-2" />
              <p className="text-sm font-medium text-foreground">Select or create a document</p>
              <TypoCaption as="p">Collaborate with your team members in real time.</TypoCaption>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
