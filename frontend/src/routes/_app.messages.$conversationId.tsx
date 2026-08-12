import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { messagesService } from "@/services";
import { Card, Avatar, Skeleton } from "@/components/shared/primitives";
import { LoadingButton } from "@/components/shared/LoadingButton";
import {
  ArrowLeft,
  Send,
  Sparkles,
  Paperclip,
  File,
  Download,
  Image,
  FileText,
  FileArchive,
  Code,
  Clock,
  X,
  Check,
  CheckCheck,
} from "lucide-react";
import { useState, useCallback, useEffect, useRef } from "react";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { builders, conversations } from "@/mocks/seed";
import { cn } from "@/lib/utils";
import { conversationStartersApi, type ConversationStarterResponse } from "@/api";
import { useAuth } from "@/contexts/auth-context";
import { useChatWebSocket } from "@/hooks/useChatWebSocket";
import { toast } from "sonner";
import { TypoCaption } from "@/components/shared/Typography";

export const Route = createFileRoute("/_app/messages/$conversationId")({
  head: () => ({ meta: [{ title: "Chat — DevLink" }] }),
  component: Thread,
});

function Thread() {
  const { conversationId } = Route.useParams();
  const existingConversation = conversations.find((c) => c.id === conversationId);
  const contact =
    existingConversation?.with ?? builders.find((builder) => builder.id === conversationId);
  const conv =
    existingConversation ?? (contact ? { id: conversationId, with: contact } : conversations[0]);
  const { data = [] } = useQuery({
    queryKey: ["thread", conversationId],
    queryFn: () => messagesService.thread(conversationId),
  });
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // File sharing & progress states
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [attachment, setAttachment] = useState<{
    url: string;
    name: string;
    size: number;
    mime_type: string;
    type: string;
  } | null>(null);

  // Conversation starters state
  const [starters, setStarters] = useState<ConversationStarterResponse | null>(null);
  const [startersError, setStartersError] = useState<string | null>(null);
  const conversationIdRef = useRef(conversationId);

  const startersMutation = useMutation({
    mutationFn: () => conversationStartersApi.generate(conversationId),
    onSuccess: (data) => {
      if (conversationIdRef.current !== conversationId) return;
      setStarters(data);
      setStartersError(null);
    },
    onError: (err) => {
      if (conversationIdRef.current !== conversationId) return;
      setStartersError(err instanceof Error ? err.message : "Failed to load suggestions");
    },
  });

  // Reset starters & attachment when switching conversations
  useEffect(() => {
    conversationIdRef.current = conversationId;
    setStarters(null);
    setStartersError(null);
    setAttachment(null);
    setUploadProgress(0);
    setUploading(false);
  }, [conversationId]);
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Use the websocket hook for real-time messaging and typing
  const { isConnected, typingUsers, broadcastMessage, broadcastTyping } = useChatWebSocket(
    conversationId,
    user?.id || "",
    useCallback(
      (msg: unknown) => {
        queryClient.invalidateQueries({ queryKey: ["thread", conversationId] });
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
      },
      [queryClient, conversationId],
    ),
    useCallback(
      (msg: unknown) => {
        queryClient.invalidateQueries({ queryKey: ["thread", conversationId] });
      },
      [queryClient, conversationId],
    ),
  );

  const themTyping = typingUsers.length > 0;
  const lastTypingPingRef = useRef<number>(0);

  const notifyTyping = useCallback(() => {
    const now = Date.now();
    if (now - lastTypingPingRef.current < 1000) return;
    lastTypingPingRef.current = now;
    fetch(`/api/messages/conversation/${conversationId}/typing`, {
      method: "POST",
      credentials: "include",
    }).catch(() => {});
  }, [conversationId]);

  const clearTyping = useCallback(() => {
    fetch(`/api/messages/conversation/${conversationId}/typing`, {
      method: "DELETE",
      credentials: "include",
    }).catch(() => {});
  }, [conversationId]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setText(e.target.value);
      notifyTyping();
    },
    [notifyTyping],
  );

  useEffect(() => {
    return () => {
      clearTyping();
    };
  }, [clearTyping]);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      toast.error("File exceeds maximum size limit of 10MB");
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    const apiBase = import.meta.env.VITE_API_BASE_URL;
    if (apiBase) {
      const formData = new FormData();
      formData.append("file", file);

      try {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${apiBase}/api/media/upload-attachment`, true);
        xhr.withCredentials = true;

        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const pct = Math.round((event.loaded / event.total) * 100);
            setUploadProgress(pct);
          }
        };

        xhr.onload = () => {
          if (xhr.status === 201) {
            const res = JSON.parse(xhr.responseText);
            const isImage = file.type.startsWith("image/");
            setAttachment({
              url: res.url,
              name: res.filename,
              size: res.size,
              mime_type: res.mime_type,
              type: isImage ? "image" : "file",
            });
            toast.success("Attachment uploaded successfully");
          } else {
            toast.error("Attachment upload failed");
          }
          setUploading(false);
        };

        xhr.onerror = () => {
          toast.error("Attachment upload failed");
          setUploading(false);
        };

        xhr.send(formData);
      } catch (err) {
        console.error("Upload error", err);
        toast.error("Failed to upload file");
        setUploading(false);
      }
    } else {
      // Mock progress offline
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        setUploadProgress(progress);
        if (progress >= 100) {
          clearInterval(interval);
          setUploading(false);
          const isImage = file.type.startsWith("image/");
          setAttachment({
            url: isImage ? URL.createObjectURL(file) : "#",
            name: file.name,
            size: file.size,
            mime_type: file.type || "application/octet-stream",
            type: isImage ? "image" : "file",
          });
          toast.success("File uploaded (Mock)");
        }
      }, 100);
    }
  };

  const clearAttachment = () => {
    setAttachment(null);
    setUploadProgress(0);
    setUploading(false);
  };

  const handleSend = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if ((!text.trim() && !attachment) || submitting) return;
      setSubmitting(true);
      clearTyping();
      try {
        await messagesService.send(conversationId, text, attachment || undefined);
        setText("");
        setAttachment(null);
        broadcastMessage(text || `Shared an attachment: ${attachment?.name}`);

        queryClient.invalidateQueries({ queryKey: ["thread", conversationId] });
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
      } catch (err) {
        console.error("Failed to send message", err);
      } finally {
        setSubmitting(false);
      }
    },
    [text, submitting, clearTyping, conversationId, broadcastMessage, queryClient, attachment],
  );

  return (
    <Card className="flex flex-col lg:h-[calc(100vh-8rem)]">
      <div className="flex items-center gap-3 border-b border-border px-4 py-3">
        <Link to="/messages" className="lg:hidden">
          <ArrowLeft size={16} className="text-muted-foreground" />
        </Link>
        <Avatar src={conv.with.avatar} alt={conv.with.name} size={36} online={conv.with.online} />
        <div>
          <p className="text-[13px] font-semibold text-foreground">{conv.with.name}</p>
          <TypoCaption as="p">
            {conv.with.online ? "Online" : "Offline"}
          </TypoCaption>
        </div>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {data.length === 0 && (
          <div className="space-y-4">
            <TypoCaption as="p">
              No messages yet — say hello 👋
            </TypoCaption>

            {!starters && !startersMutation.isPending && !startersError && (
              <button
                onClick={() => startersMutation.mutate()}
                className="mx-auto flex items-center gap-2 rounded-md border border-border bg-surface px-4 py-2 text-[12px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              >
                <Sparkles size={14} />
                Get conversation starters
              </button>
            )}

            {startersMutation.isPending && (
              <div className="space-y-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-3/4" />
              </div>
            )}

            {startersError && (
              <div className="space-y-2">
                <p className="text-center text-[12px] text-destructive">{startersError}</p>
                <button
                  onClick={() => {
                    setStartersError(null);
                    startersMutation.mutate();
                  }}
                  className="mx-auto flex items-center gap-2 rounded-md border border-border bg-surface px-4 py-2 text-[12px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                >
                  <Sparkles size={14} />
                  Try again
                </button>
              </div>
            )}

            {starters && (
              <div className="space-y-2">
                <TypoCaption as="p">
                  Suggestions for {starters.target_user_name}
                </TypoCaption>
                {starters.suggestions.map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => setText(suggestion.text)}
                    className="flex w-full items-center justify-between gap-2 rounded-md border border-border bg-surface px-3 py-2 text-left text-[13px] text-foreground hover:bg-muted/50"
                  >
                    <span>{suggestion.text}</span>
                    <TypoCaption>
                      {Math.round(suggestion.confidence * 100)}%
                    </TypoCaption>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        {data.map((m: any) => (
          <div key={m.id} className={cn("flex", m.from === "me" ? "justify-end" : "justify-start")}>
            <div
              className={cn(
                "max-w-[75%] rounded-md px-3 py-2 text-[13px] space-y-2",
                m.from === "me"
                  ? "bg-primary text-primary-foreground"
                  : "border border-border bg-surface text-foreground",
              )}
            >
              {/* Clickable Image Attachment */}
              {m.attachment_url && m.type === "image" && (
                <div className="rounded overflow-hidden max-w-sm border border-black/5 bg-black/5">
                  <a href={m.attachment_url} target="_blank" rel="noopener noreferrer">
                    <img
                      src={m.attachment_url}
                      alt={m.attachment_name || "Shared image"}
                      className="max-h-60 object-contain hover:opacity-90 transition-opacity"
                    />
                  </a>
                </div>
              )}

              {/* Specialized File Attachment Card */}
              {m.attachment_url && m.type === "file" && (
                <div
                  className={cn(
                    "flex items-center gap-3 p-2 rounded-md border text-xs min-w-[200px]",
                    m.from === "me"
                      ? "bg-primary-dark/20 border-primary-foreground/10"
                      : "bg-muted/30 border-border",
                  )}
                >
                  <div className="p-2 bg-primary/10 rounded text-primary shrink-0">
                    {(() => {
                      const name = m.attachment_name?.toLowerCase() || "";
                      if (
                        name.endsWith(".zip") ||
                        name.endsWith(".tar") ||
                        name.endsWith(".rar") ||
                        name.endsWith(".gz")
                      ) {
                        return <FileArchive size={18} />;
                      }
                      if (name.endsWith(".pdf")) {
                        return <FileText size={18} />;
                      }
                      if (
                        name.endsWith(".json") ||
                        name.endsWith(".js") ||
                        name.endsWith(".ts") ||
                        name.endsWith(".py") ||
                        name.endsWith(".html") ||
                        name.endsWith(".css") ||
                        name.endsWith(".go")
                      ) {
                        return <Code size={18} />;
                      }
                      return <File size={18} />;
                    })()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium truncate">{m.attachment_name}</p>
                    <p
                      className={cn(
                        "text-[10px]",
                        m.from === "me" ? "text-primary-foreground/75" : "text-muted-foreground",
                      )}
                    >
                      {m.attachment_size ? formatFileSize(m.attachment_size) : "Unknown size"}
                    </p>
                  </div>
                  <a
                    href={m.attachment_url}
                    download={m.attachment_name}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 hover:bg-black/10 rounded text-inherit transition-colors"
                    title="Download file"
                  >
                    <Download size={14} />
                  </a>
                </div>
              )}

              {m.text && <p className="whitespace-pre-wrap">{m.text}</p>}

                <div
                  className={cn(
                    "mt-1 flex items-center justify-end gap-1 text-[10px]",
                    m.from === "me" ? "text-primary-foreground/70" : "text-muted-foreground",
                  )}
                >
                  <span>{m.at}</span>
                  {m.from === "me" && (
                    <span className="inline-flex">
                      {m.read_at ? (
                        <CheckCheck className="w-3 h-3 text-blue-400" />
                      ) : m.delivered_at ? (
                        <CheckCheck className="w-3 h-3 opacity-70" />
                      ) : (
                        <Check className="w-3 h-3 opacity-70" />
                      )}
                    </span>
                  )}
                </div>
            </div>
          </div>
        ))}

        {themTyping && (
          <div className="flex justify-start">
            <div className="max-w-[75%] rounded-md border border-border bg-surface px-3 py-2">
              <TypingIndicator />
            </div>
          </div>
        )}
      </div>

      {themTyping && (
        <div className="px-4 pt-1">
          <TypingIndicator label={`${conv.with.name} is typing`} />
        </div>
      )}

      {/* Uploading progress bar */}
      {uploading && (
        <div className="px-4 py-2 bg-muted/30 border-t border-border flex items-center justify-between gap-4">
          <TypoCaption>
            <Clock size={12} className="animate-spin text-primary" /> Uploading file...
          </TypoCaption>
          <div className="flex-1 max-w-xs h-1.5 bg-primary/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <span className="text-xs font-semibold text-primary">{uploadProgress}%</span>
        </div>
      )}

      {/* Attachment preview banner */}
      {attachment && (
        <div className="px-4 py-2 bg-muted/40 border-t border-border flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-primary/10 rounded text-primary">
              {attachment.type === "image" ? <Image size={14} /> : <File size={14} />}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-foreground truncate max-w-[200px] sm:max-w-md">
                {attachment.name}
              </p>
              <TypoCaption as="p">{formatFileSize(attachment.size)}</TypoCaption>
            </div>
          </div>
          <button
            onClick={clearAttachment}
            className="p-1 text-muted-foreground hover:text-foreground rounded hover:bg-muted transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      )}

      <form onSubmit={handleSend} className="flex items-center gap-2 border-t border-border p-3">
        <input
          type="file"
          id="chat-file-upload"
          className="hidden"
          onChange={handleFileChange}
          disabled={uploading}
          accept=".png,.jpg,.jpeg,.webp,.gif,.pdf,.zip,.tar,.gz,.rar,.json,.js,.ts,.py,.go,.cpp,.cs,.html,.css,.docx,.doc,.txt,.xlsx,.xls,.pptx,.ppt"
        />
        <button
          type="button"
          onClick={() => document.getElementById("chat-file-upload")?.click()}
          disabled={uploading || submitting}
          className="p-2 hover:bg-muted text-muted-foreground hover:text-foreground rounded-md transition-colors"
          title="Attach file (Image, PDF, ZIP, code, doc)"
        >
          <Paperclip size={16} />
        </button>

        <input
          value={text}
          onChange={handleInputChange}
          placeholder={attachment ? "Add a message or hit send..." : "Type a message…"}
          className="min-w-0 flex-1 rounded-md border border-border bg-surface px-3 py-2 text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
        />
        <LoadingButton
          type="submit"
          loading={submitting}
          loadingText=""
          disabled={(!text.trim() && !attachment) || uploading}
          className="inline-flex items-center gap-1"
        >
          <Send size={14} /> Send
        </LoadingButton>
      </form>
    </Card>
  );
}
