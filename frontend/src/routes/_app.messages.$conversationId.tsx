import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { messagesService } from "@/services";
import { Card, Avatar, Skeleton } from "@/components/shared/primitives";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { useConversationSettings } from "./_app.messages";
import {
  ArrowLeft,
  Send,
  Sparkles,
  Paperclip,
  File as FileIcon,
  Download,
  Image,
  FileText,
  FileArchive,
  Code,
  Clock,
  X,
  MoreVertical,
  Trash2,
  Pencil,
  Pin,
  PinOff,
  Check,
  CheckCheck,
  Mic,
  Square,
  CalendarClock,
  Phone,
  Video,
  Info,
  Smile,
  ExternalLink,
  Lock,
  Archive,
} from "lucide-react";
import { useState, useCallback, useEffect, useRef } from "react";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { builders, conversations } from "@/mocks/seed";
import { cn } from "@/lib/utils";
import { conversationStartersApi, type ConversationStarterResponse } from "@/api";
import { useAuth } from "@/contexts/auth-context";
import { useChatWebSocket } from "@/hooks/useChatWebSocket";
import { toast } from "sonner";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useIsMobile } from "@/hooks/use-mobile";

export const Route = createFileRoute("/_app/messages/$conversationId")({
  head: () => ({ meta: [{ title: "Chat — DevLink" }] }),
  component: Thread,
});

function Thread() {
  const { conversationId } = Route.useParams();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Settings context
  const {
    pinnedIds,
    archivedIds,
    mutedIds,
    togglePin: toggleConvPin,
    toggleArchive: toggleConvArchive,
    toggleMute: toggleConvMute,
  } = useConversationSettings();

  // Device responsiveness
  const isMobile = useIsMobile();
  const isTablet = useMediaQuery("(min-width: 768px) and (max-width: 1199px)");
  const isLargeDesktop = useMediaQuery("(min-width: 1200px)");

  // UI state
  const [showDetails, setShowDetails] = useState(true);
  const [activeTab, setActiveTab] = useState<"details" | "files" | "links">("details");
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [showMobileHeaderMenu, setShowMobileHeaderMenu] = useState(false);

  // Notes state
  const [notes, setNotes] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem(`devlink_notes_${conversationId}`) || "";
    }
    return "";
  });

  useEffect(() => {
    if (typeof window !== "undefined") {
      setNotes(localStorage.getItem(`devlink_notes_${conversationId}`) || "");
    }
    // Default to hiding details panel on mobile and tablet, keeping visible on large desktop
    setShowDetails(isLargeDesktop);
  }, [conversationId, isLargeDesktop]);

  const handleNotesChange = (text: string) => {
    setNotes(text);
    localStorage.setItem(`devlink_notes_${conversationId}`, text);
  };

  const existingConversation = conversations.find((c) => c.id === conversationId);
  const contact =
    existingConversation?.with ?? builders.find((builder) => builder.id === conversationId);
  const conv =
    existingConversation ?? (contact ? { id: conversationId, with: contact } : conversations[0]);

  const { data = [] } = useQuery({
    queryKey: ["thread", conversationId],
    queryFn: () => messagesService.thread(conversationId),
  });

  const { data: pinned = [] } = useQuery({
    queryKey: ["pinned", conversationId],
    queryFn: () => messagesService.pinned(conversationId),
  });

  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Message scheduling
  const [scheduledFor, setScheduledFor] = useState<string>("");

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

  // Voice recording
  const [recording, setRecording] = useState(false);
  const [voiceUploading, setVoiceUploading] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Editing state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [menuFor, setMenuFor] = useState<string | null>(null);

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
    setScheduledFor("");
    setRecording(false);
    setEditingId(null);
    setMenuFor(null);
    setShowMobileHeaderMenu(false);
  }, [conversationId]);

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

  // --- Voice recording ---------------------------------------------------
  const uploadBlob = (blob: Blob, filename: string): Promise<string> => {
    const apiBase = import.meta.env.VITE_API_BASE_URL;
    if (!apiBase) {
      return Promise.resolve(URL.createObjectURL(blob));
    }
    const formData = new FormData();
    formData.append("file", new File([blob], filename, { type: blob.type }));
    return fetch(`${apiBase}/api/media/upload-attachment`, {
      method: "POST",
      credentials: "include",
      body: formData,
    })
      .then((res) => {
        if (!res.ok) throw new Error("Upload failed");
        return res.json();
      })
      .then((data) => data.url as string);
  };

  const toggleRecording = useCallback(async () => {
    if (recording) {
      mediaRecorderRef.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(audioChunksRef.current, { type: recorder.mimeType || "audio/webm" });
        audioChunksRef.current = [];
        setRecording(false);
        if (blob.size === 0) {
          toast.error("No audio captured");
          return;
        }
        setVoiceUploading(true);
        try {
          const url = await uploadBlob(blob, `voice-${Date.now()}.webm`);
          await messagesService.send(
            conversationId,
            "",
            {
              url,
              name: `voice-${Date.now()}.webm`,
              size: blob.size,
              mime_type: blob.type || "audio/webm",
              type: "voice",
            },
            null,
          );
          queryClient.invalidateQueries({ queryKey: ["thread", conversationId] });
          queryClient.invalidateQueries({ queryKey: ["conversations"] });
          toast.success("Voice message sent");
        } catch (err) {
          console.error("Failed to send voice message", err);
          toast.error("Failed to send voice message");
        } finally {
          setVoiceUploading(false);
        }
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
    } catch (err) {
      console.error("Microphone access denied", err);
      toast.error("Microphone access denied");
    }
  }, [recording, conversationId, queryClient]);

  // --- Edit / delete / pin ----------------------------------------------
  const startEdit = useCallback((m: { id: string; text: string }) => {
    setEditingId(m.id);
    setEditText(m.text);
    setMenuFor(null);
  }, []);

  const saveEdit = useCallback(async () => {
    if (!editingId || !editText.trim()) return;
    try {
      await messagesService.update(editingId, editText.trim());
      setEditingId(null);
      setEditText("");
      queryClient.invalidateQueries({ queryKey: ["thread", conversationId] });
      toast.success("Message updated");
    } catch (err) {
      console.error("Failed to update message", err);
      toast.error("Failed to update message");
    }
  }, [editingId, editText, queryClient, conversationId]);

  const deleteMessage = useCallback(
    async (messageId: string) => {
      try {
        await messagesService.remove(messageId);
        setMenuFor(null);
        queryClient.invalidateQueries({ queryKey: ["thread", conversationId] });
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
        toast.success("Message deleted");
      } catch (err) {
        console.error("Failed to delete message", err);
        toast.error("Failed to delete message");
      }
    },
    [queryClient, conversationId],
  );

  const togglePin = useCallback(
    async (m: { id: string; is_pinned?: boolean }) => {
      try {
        if (m.is_pinned) {
          await messagesService.unpin(m.id);
        } else {
          await messagesService.pin(m.id);
        }
        setMenuFor(null);
        queryClient.invalidateQueries({ queryKey: ["thread", conversationId] });
        queryClient.invalidateQueries({ queryKey: ["pinned", conversationId] });
      } catch (err) {
        console.error("Failed to pin message", err);
        toast.error("Failed to pin message");
      }
    },
    [queryClient, conversationId],
  );

  const handleSend = useCallback(
    async (e?: React.FormEvent) => {
      if (e) e.preventDefault();
      if ((!text.trim() && !attachment) || submitting) return;
      setSubmitting(true);
      clearTyping();
      try {
        await messagesService.send(
          conversationId,
          text,
          attachment || undefined,
          scheduledFor || null,
        );
        setText("");
        setAttachment(null);
        setScheduledFor("");
        broadcastMessage(text || `Shared an attachment: ${attachment?.name}`);
        if (scheduledFor) {
          toast.success(`Message scheduled for ${new Date(scheduledFor).toLocaleString()}`);
        }

        queryClient.invalidateQueries({ queryKey: ["thread", conversationId] });
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
      } catch (err) {
        console.error("Failed to send message", err);
      } finally {
        setSubmitting(false);
      }
    },
    [
      text,
      submitting,
      clearTyping,
      conversationId,
      broadcastMessage,
      queryClient,
      attachment,
      scheduledFor,
    ],
  );

  const popularEmojis = ["😊", "👍", "🙌", "❤️", "😂", "🔥", "🎉", "🚀", "😮", "😢", "✨", "💯", "👏", "💡"];

  const addEmoji = (emoji: string) => {
    setText((prev) => prev + emoji);
    setShowEmojiPicker(false);
  };

  // --- Dynamic data extraction from message history for details panel ---------------------
  const sharedImages = data
    .filter((m: any) => m.type === "image" && m.attachment_url)
    .map((m: any) => ({ url: m.attachment_url, name: m.attachment_name }));

  const sharedFiles = data
    .filter((m: any) => m.type === "file" && m.attachment_url)
    .map((m: any) => ({
      url: m.attachment_url,
      name: m.attachment_name,
      size: m.attachment_size,
      mime: m.mime_type,
    }));

  const linkRegex = /(https?:\/\/[^\s]+)/g;
  const sharedLinks: { url: string; title: string }[] = [];
  data.forEach((m: any) => {
    if (m.text) {
      const matches = m.text.match(linkRegex);
      if (matches) {
        matches.forEach((url: string) => {
          sharedLinks.push({ url, title: url.replace(/https?:\/\/(www\.)?/, "").split("/")[0] });
        });
      }
    }
  });

  // Fallbacks if empty for visual excellence
  const displayImages = sharedImages.length > 0 ? sharedImages : [
    { url: "https://images.unsplash.com/photo-1531403009284-440f080d1e12?w=200&auto=format&fit=crop&q=60", name: "dashboard-wireframe.png" },
    { url: "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?w=200&auto=format&fit=crop&q=60", name: "branding-guidelines.png" },
    { url: "https://images.unsplash.com/photo-1581291518633-83b4ebd1d83e?w=200&auto=format&fit=crop&q=60", name: "editor-interface.png" },
  ];

  const displayFiles = sharedFiles.length > 0 ? sharedFiles : [
    { name: "project-spec.pdf", size: 2516582, url: "#", type: "pdf" },
    { name: "api-endpoints.docx", size: 1258291, url: "#", type: "docx" },
    { name: "database-schema.fig", size: 5033164, url: "#", type: "fig" },
  ];

  const displayLinks = sharedLinks.length > 0 ? sharedLinks : [
    { url: "https://devlink.io/dashboard", title: "DevLink Dashboard" },
    { url: "https://github.com/zaaraf027-glitch/devlink", title: "GitHub Repository" },
    { url: "https://figma.com/file/devlink-ui", title: "Figma UI Kit" },
  ];

  // --- Message Grouping & Date Dividers Logic ------------------------------
  const parseMessageDate = (m: any): Date => {
    if (m.created_at) return new Date(m.created_at);
    if (m.at && m.at.includes(":")) {
      const [h, min] = m.at.split(":");
      const d = new Date();
      d.setHours(parseInt(h, 10), parseInt(min, 10), 0, 0);
      return d;
    }
    return new Date();
  };

  const getDateLabel = (date: Date): string => {
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return "Today";
    }
    if (date.toDateString() === yesterday.toDateString()) {
      return "Yesterday";
    }
    return date.toLocaleDateString([], { month: "long", day: "numeric", year: "numeric" });
  };

  // Group messages
  const groupedMessages: {
    senderId: string;
    isMe: boolean;
    senderName: string;
    avatar: string | null | undefined;
    online?: boolean;
    timeLabel: string;
    messages: any[];
  }[] = [];

  let currentGroup: typeof groupedMessages[0] | undefined = undefined;

  data.forEach((m: any) => {
    const msgDate = parseMessageDate(m);
    const mine = m.from === "me";
    const senderId = mine ? "me" : (m.sender_id || "them");
    const senderName = mine ? (user?.first_name || "Me") : (conv.with.name || "Teammate");
    const senderAvatar = mine ? ((user?.profile_image as string) || "") : conv.with.avatar;
    const timeLabel = msgDate.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    const shouldStartNewGroup =
      !currentGroup ||
      currentGroup.senderId !== senderId ||
      msgDate.getTime() - parseMessageDate(currentGroup.messages[currentGroup.messages.length - 1]).getTime() > 5 * 60 * 1000 ||
      msgDate.toDateString() !== parseMessageDate(currentGroup.messages[currentGroup.messages.length - 1]).toDateString();

    if (shouldStartNewGroup) {
      const newGroup = {
        senderId,
        isMe: mine,
        senderName,
        avatar: senderAvatar,
        online: mine ? undefined : conv.with.online,
        timeLabel,
        messages: [m],
      };
      currentGroup = newGroup;
      groupedMessages.push(newGroup);
    } else if (currentGroup) {
      currentGroup.messages.push(m);
    }
  });

  return (
    <div className="flex h-full w-full overflow-hidden relative">
      {/* ─── CHAT PANEL (Panel 2) ─────────────────────────────────────────── */}
      <Card className="flex flex-col flex-1 h-full min-w-0 bg-card border-0 lg:border border-border overflow-hidden rounded-none lg:rounded-2xl shadow-none lg:shadow-xs relative">
        {/* Active Chat Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-card shrink-0 select-none">
          <div className="flex items-center gap-2.5 min-w-0">
            <Link to="/messages" className="lg:hidden p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground rounded-lg transition-colors shrink-0">
              <ArrowLeft size={16} className="text-muted-foreground" />
            </Link>
            <Avatar src={conv.with.avatar} alt={conv.with.name} size={36} online={conv.with.online} className="shrink-0" />
            <div className="min-w-0">
              <p className="text-[13px] font-extrabold text-foreground truncate">{conv.with.name}</p>
              <div className="flex items-center gap-1 mt-0.5">
                <span className={cn("inline-block h-1.5 w-1.5 rounded-full shrink-0", conv.with.online ? "bg-success" : "bg-muted-foreground/45")} />
                <span className="text-[9px] text-muted-foreground font-bold uppercase tracking-wider leading-none">
                  {conv.with.online ? "Online" : "Offline"}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            {/* Desktop/Tablet Header Actions */}
            <div className="hidden sm:flex items-center gap-1 shrink-0">
              <button
                onClick={() => toast.info(`Starting voice call with ${conv.with.name}...`)}
                className="p-2 hover:bg-muted text-muted-foreground hover:text-foreground rounded-lg transition-colors"
                title="Voice call"
              >
                <Phone size={15} />
              </button>
              <button
                onClick={() => toast.info(`Starting video call with ${conv.with.name}...`)}
                className="p-2 hover:bg-muted text-muted-foreground hover:text-foreground rounded-lg transition-colors"
                title="Video call"
              >
                <Video size={15} />
              </button>
              <button
                onClick={() => setShowDetails(!showDetails)}
                className={cn(
                  "p-2 rounded-lg transition-colors",
                  showDetails
                    ? "bg-primary-soft text-primary"
                    : "hover:bg-muted text-muted-foreground hover:text-foreground"
                )}
                title="Toggle Details panel"
              >
                <Info size={15} />
              </button>
            </div>

            {/* Mobile-only Header Actions Dropdown */}
            <div className="sm:hidden relative shrink-0">
              <button
                onClick={() => setShowMobileHeaderMenu(!showMobileHeaderMenu)}
                className="p-2 hover:bg-muted text-muted-foreground hover:text-foreground rounded-lg transition-colors cursor-pointer"
                title="Actions"
              >
                <MoreVertical size={16} />
              </button>
              {showMobileHeaderMenu && (
                <>
                  <div className="fixed inset-0 z-30" onClick={() => setShowMobileHeaderMenu(false)} />
                  <div className="absolute right-0 mt-1.5 w-44 rounded-xl border border-border bg-card shadow-lg py-1.5 text-xs text-foreground z-40 animate-in fade-in slide-in-from-top-1 duration-150">
                    <button
                      onClick={() => {
                        setShowMobileHeaderMenu(false);
                        toast.info(`Starting voice call with ${conv.with.name}...`);
                      }}
                      className="w-full flex items-center gap-2.5 px-3.5 py-2 hover:bg-muted text-left"
                    >
                      <Phone size={13} /> Voice Call
                    </button>
                    <button
                      onClick={() => {
                        setShowMobileHeaderMenu(false);
                        toast.info(`Starting video call with ${conv.with.name}...`);
                      }}
                      className="w-full flex items-center gap-2.5 px-3.5 py-2 hover:bg-muted text-left"
                    >
                      <Video size={13} /> Video Call
                    </button>
                    <button
                      onClick={() => {
                        setShowMobileHeaderMenu(false);
                        setShowDetails(true); // Open Details drawer
                      }}
                      className="w-full flex items-center gap-2.5 px-3.5 py-2 hover:bg-muted text-left font-bold"
                    >
                      <Info size={13} /> View Details
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Pinned Messages Banner */}
        {pinned.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 border-b border-border bg-muted/20 px-4 py-2 shrink-0">
            <Pin size={11} className="text-primary shrink-0 rotate-45" />
            <span className="text-[11px] font-semibold text-foreground/80 mr-1 shrink-0">Pinned Messages:</span>
            {pinned.map((m) => (
              <div
                key={m.id}
                className="flex items-center gap-1 rounded-full border border-border bg-card px-2.5 py-0.5 text-[11px] text-muted-foreground shadow-xs animate-in fade-in zoom-in-95 duration-200"
              >
                <span className="max-w-[140px] truncate">
                  {m.from === "me" ? "You: " : ""}
                  {m.text || m.attachment_name || "Shared attachment"}
                </span>
                <button
                  onClick={() => togglePin(m)}
                  className="text-muted-foreground hover:text-foreground p-0.5"
                  title="Unpin message"
                >
                  <X size={10} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Message Scrolling Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0 bg-surface/30 flex flex-col">
          {data.length === 0 && (
            <div className="flex flex-col items-center justify-center py-6 px-4 max-w-xs mx-auto text-center my-auto space-y-3.5 animate-in fade-in duration-200 select-none">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-primary-soft text-primary shadow-2xs">
                <Sparkles size={20} />
              </div>
              <div>
                <p className="text-sm font-bold text-foreground">No messages yet</p>
                <p className="text-xs text-muted-foreground mt-0.5">Say hello and start collaborating! 👋</p>
              </div>

              {!starters && !startersMutation.isPending && !startersError && (
                <button
                  onClick={() => startersMutation.mutate()}
                  className="flex items-center gap-1.5 rounded-xl border border-border bg-card px-3.5 py-1.5 text-xs font-bold text-muted-foreground hover:bg-muted/40 hover:text-foreground shadow-2xs transition-colors cursor-pointer"
                >
                  <Sparkles size={12} className="text-primary" />
                  Get AI suggestions
                </button>
              )}

              {startersMutation.isPending && (
                <div className="w-full space-y-1.5">
                  <Skeleton className="h-8 w-full rounded-lg" />
                  <Skeleton className="h-8 w-full rounded-lg" />
                </div>
              )}

              {startersError && (
                <div className="space-y-1.5">
                  <p className="text-[11px] text-destructive">{startersError}</p>
                  <button
                    onClick={() => {
                      setStartersError(null);
                      startersMutation.mutate();
                    }}
                    className="rounded-lg border border-border bg-card px-2.5 py-1 text-[10px] font-semibold text-muted-foreground hover:bg-muted/50"
                  >
                    Try again
                  </button>
                </div>
              )}

              {starters && (
                <div className="w-full space-y-1.5 text-left animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <p className="text-[9px] font-extrabold text-muted-foreground uppercase tracking-wider px-1">Suggestions:</p>
                  {starters.suggestions.slice(0, 3).map((suggestion, i) => (
                    <button
                      key={i}
                      onClick={() => setText(suggestion.text)}
                      className="flex w-full items-center justify-between gap-2.5 rounded-xl border border-border bg-card px-2.5 py-1.5 text-xs text-foreground hover:bg-muted/40 shadow-2xs transition-all text-left cursor-pointer hover:border-primary/20"
                    >
                      <span className="truncate">{suggestion.text}</span>
                      <span className="text-[9px] text-primary bg-primary-soft font-bold px-1.5 py-0.5 rounded-full shrink-0">
                        {Math.round(suggestion.confidence * 100)}%
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {groupedMessages.map((group, groupIdx) => {
            const prevGroup = groupIdx > 0 ? groupedMessages[groupIdx - 1] : null;
            const currentDate = parseMessageDate(group.messages[0]);
            const prevDate = prevGroup ? parseMessageDate(prevGroup.messages[0]) : null;
            const showDateDivider = !prevDate || currentDate.toDateString() !== prevDate.toDateString();

            return (
              <div key={groupIdx} className="space-y-3">
                {/* Date Divider */}
                {showDateDivider && (
                  <div className="flex items-center justify-center my-5 select-none">
                    <div className="h-px bg-border/50 flex-1" />
                    <span className="px-3 text-[10px] font-bold text-muted-foreground uppercase tracking-wider bg-card border border-border/60 rounded-full py-0.5 shadow-xs mx-3 shrink-0">
                      {getDateLabel(currentDate)}
                    </span>
                    <div className="h-px bg-border/50 flex-1" />
                  </div>
                )}

                {/* Message Group Row */}
                <div className={cn("flex gap-3", group.isMe ? "justify-end" : "justify-start")}>
                  {/* Left avatar for incoming messages */}
                  {!group.isMe && (
                    <Avatar src={group.avatar} alt={group.senderName} size={32} online={group.online} className="mt-0.5 shrink-0" />
                  )}
                  
                  <div className={cn("flex flex-col max-w-[75%]", group.isMe ? "items-end" : "items-start")}>
                    {/* Header: Sender details */}
                    <div className="flex items-center gap-2 mb-1 px-1 select-none">
                      {!group.isMe && <span className="text-[11px] font-bold text-foreground/80">{group.senderName}</span>}
                      <span className="text-[9px] text-muted-foreground font-medium">{group.timeLabel}</span>
                    </div>

                    {/* Messages in Group */}
                    <div className="space-y-1.5 w-full">
                      {group.messages.map((m) => {
                        const isMessagePinned = m.is_pinned;
                        return (
                          <div
                            key={m.id}
                            className={cn(
                              "relative group rounded-2xl px-3.5 py-2 text-[13px] leading-relaxed shadow-xs flex flex-col gap-1 w-fit max-w-full border",
                              group.isMe
                                ? "bg-primary border-primary text-primary-foreground ml-auto rounded-tr-xs"
                                : "bg-card border-border text-foreground rounded-tl-xs"
                            )}
                          >
                            {/* Pin icon on bubble */}
                            {isMessagePinned && (
                              <Pin size={10} className="absolute -top-1 -right-1 text-amber-500 bg-card border border-border rounded-full p-0.5 h-4 w-4" />
                            )}

                            {/* Image Attachment inside bubble */}
                            {m.attachment_url && m.type === "image" && (
                              <div className="rounded-xl overflow-hidden border border-black/10 max-w-xs bg-muted mt-0.5">
                                <a href={m.attachment_url} target="_blank" rel="noopener noreferrer" className="block">
                                  <img
                                    src={m.attachment_url}
                                    alt={m.attachment_name || "Shared image"}
                                    className="max-h-56 w-full object-cover hover:opacity-90 transition-opacity"
                                  />
                                </a>
                              </div>
                            )}

                            {/* Voice playback inside bubble */}
                            {m.attachment_url && m.type === "voice" && (
                              <div className="mt-0.5 py-1 px-0.5 rounded-xl bg-black/5 flex items-center gap-2">
                                <audio controls src={m.attachment_url} className="h-8 max-w-[200px]" />
                              </div>
                            )}

                            {/* File Document Card inside bubble */}
                            {m.attachment_url && m.type === "file" && (
                              <div
                                className={cn(
                                  "flex items-center gap-3 p-2 rounded-xl border text-[11px] min-w-[200px] mt-0.5",
                                  group.isMe
                                    ? "bg-primary-dark/20 border-primary-foreground/10"
                                    : "bg-surface border-border"
                                )}
                              >
                                <div className="p-2 bg-primary/10 rounded-lg text-primary shrink-0">
                                  {(() => {
                                    const name = m.attachment_name?.toLowerCase() || "";
                                    if (
                                      name.endsWith(".zip") ||
                                      name.endsWith(".tar") ||
                                      name.endsWith(".rar") ||
                                      name.endsWith(".gz")
                                    ) {
                                      return <FileArchive size={16} />;
                                    }
                                    if (name.endsWith(".pdf")) {
                                      return <FileText size={16} />;
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
                                      return <Code size={16} />;
                                    }
                                    return <FileIcon size={16} />;
                                  })()}
                                </div>
                                <div className="min-w-0 flex-1 text-left">
                                  <p className="font-semibold truncate">{m.attachment_name}</p>
                                  <p className={cn("text-[9px] mt-0.5", group.isMe ? "text-primary-foreground/70" : "text-muted-foreground")}>
                                    {m.attachment_size ? formatFileSize(m.attachment_size) : "Unknown size"}
                                  </p>
                                </div>
                                <a
                                  href={m.attachment_url}
                                  download={m.attachment_name}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="p-1.5 hover:bg-black/10 rounded-md text-inherit transition-colors"
                                  title="Download"
                                >
                                  <Download size={13} />
                                </a>
                              </div>
                            )}

                            {/* Message text / editor */}
                            {editingId === m.id ? (
                              <div className="flex flex-col gap-2 min-w-[200px]">
                                <input
                                  value={editText}
                                  onChange={(e) => setEditText(e.target.value)}
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter") saveEdit();
                                    if (e.key === "Escape") setEditingId(null);
                                  }}
                                  autoFocus
                                  className="w-full rounded-lg border border-border bg-surface px-2.5 py-1 text-xs text-foreground outline-none focus:border-primary"
                                />
                                <div className="flex justify-end gap-2 text-[10px] font-semibold">
                                  <button onClick={() => setEditingId(null)} className={cn(group.isMe ? "text-primary-foreground/80 hover:text-primary-foreground" : "text-muted-foreground hover:text-foreground")}>
                                    Cancel
                                  </button>
                                  <button onClick={saveEdit} className="bg-primary-foreground/15 px-2 py-0.5 rounded hover:bg-primary-foreground/25 transition-colors">
                                    Save
                                  </button>
                                </div>
                              </div>
                            ) : (
                              m.text && <p className="whitespace-pre-wrap text-left">{m.text}</p>
                            )}

                            {/* Edited status */}
                            {m.is_edited && !m.is_deleted && (
                              <span className={cn("text-[8.5px] italic self-start leading-none mt-0.5", group.isMe ? "text-primary-foreground/60" : "text-muted-foreground")}>
                                (edited)
                              </span>
                            )}

                            {/* Delivered/Read checks */}
                            {group.isMe && (
                              <div className="flex items-center justify-end gap-0.5 text-primary-foreground/75 text-[9px] mt-0.5 select-none align-middle">
                                <span>{m.at}</span>
                                <span className="inline-flex items-center" title={m.read_at ? "Read" : "Delivered"}>
                                  {m.read_at ? <CheckCheck size={11} className="text-white" /> : <Check size={11} className="text-white/70" />}
                                </span>
                              </div>
                            )}

                            {/* Individual message action triggers (Edit / Delete / Pin) */}
                            {!m.is_deleted && (
                              <div className={cn(
                                "absolute top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity z-10 hidden sm:block pointer-events-auto",
                                group.isMe ? "-left-8" : "-right-8"
                              )}>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setMenuFor(menuFor === m.id ? null : m.id);
                                  }}
                                  className="p-1 hover:bg-muted text-muted-foreground hover:text-foreground rounded-md border border-border bg-card shadow-xs cursor-pointer"
                                  title="Actions"
                                >
                                  <MoreVertical size={12} />
                                </button>
                                {menuFor === m.id && (
                                  <>
                                    <div className="fixed inset-0 z-10" onClick={() => setMenuFor(null)} />
                                    <div className={cn(
                                      "absolute z-20 w-32 rounded-xl border border-border bg-card py-1 shadow-md text-[11.5px] text-foreground font-medium animate-in fade-in duration-100",
                                      group.isMe ? "left-0" : "right-0"
                                    )}>
                                      {group.isMe && m.text && (
                                        <button
                                          onClick={() => startEdit(m)}
                                          className="w-full flex items-center gap-1.5 px-2.5 py-1 hover:bg-muted text-left"
                                        >
                                          <Pencil size={11} /> Edit
                                        </button>
                                      )}
                                      {group.isMe && (
                                        <button
                                          onClick={() => deleteMessage(m.id)}
                                          className="w-full flex items-center gap-1.5 px-2.5 py-1 hover:bg-muted text-left text-destructive"
                                        >
                                          <Trash2 size={11} /> Delete
                                        </button>
                                      )}
                                      <button
                                        onClick={() => togglePin(m)}
                                        className="w-full flex items-center gap-1.5 px-2.5 py-1 hover:bg-muted text-left"
                                      >
                                        {m.is_pinned ? <PinOff size={11} /> : <Pin size={11} />}
                                        {m.is_pinned ? "Unpin" : "Pin"}
                                      </button>
                                    </div>
                                  </>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {themTyping && (
            <div className="flex justify-start gap-3 items-center select-none">
              <Avatar src={conv.with.avatar} alt={conv.with.name} size={32} online={conv.with.online} className="shrink-0" />
              <div className="max-w-[75%] rounded-2xl border border-border bg-card px-4 py-2 flex items-center gap-1 shadow-xs animate-pulse">
                <TypingIndicator />
                <span className="text-[10px] text-muted-foreground ml-1.5 font-medium">{conv.with.name} is typing...</span>
              </div>
            </div>
          )}
        </div>

        {/* Upload progress indicator */}
        {uploading && (
          <div className="px-4 py-2 bg-muted/40 border-t border-border flex items-center justify-between gap-4 shrink-0">
            <span className="text-xs text-muted-foreground flex items-center gap-1.5">
              <Clock size={12} className="animate-spin text-primary" /> Uploading files...
            </span>
            <div className="flex-1 max-w-xs h-1.5 bg-primary/10 rounded-full overflow-hidden">
              <div className="h-full bg-primary transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
            </div>
            <span className="text-[10px] font-bold text-primary">{uploadProgress}%</span>
          </div>
        )}

        {/* Voice uploading */}
        {voiceUploading && (
          <div className="px-4 py-2 bg-muted/40 border-t border-border flex items-center gap-2 shrink-0">
            <Clock size={12} className="animate-spin text-primary" />
            <span className="text-xs text-muted-foreground">Uploading audio message...</span>
          </div>
        )}

        {recording && (
          <div className="px-4 py-2 bg-destructive/15 border-t border-border flex items-center justify-between gap-4 shrink-0">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-destructive animate-pulse" />
              <span className="text-xs font-semibold text-destructive">Voice Recording active...</span>
            </div>
            <button
              onClick={toggleRecording}
              className="px-2.5 py-1 bg-destructive text-white rounded-lg text-[10px] font-bold hover:bg-destructive/95 active:scale-95 transition-all"
            >
              Stop & Send
            </button>
          </div>
        )}

        {/* Attachment preview banner */}
        {attachment && (
          <div className="px-4 py-2 bg-muted/50 border-t border-border flex items-center justify-between gap-4 shrink-0 animate-in slide-in-from-bottom-1 duration-200">
            <div className="flex items-center gap-2 min-w-0">
              <div className="p-1.5 bg-primary/10 rounded-lg text-primary shrink-0">
                {attachment.type === "image" ? <Image size={14} /> : <FileIcon size={14} />}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-foreground truncate max-w-[200px]">{attachment.name}</p>
                <p className="text-[9px] text-muted-foreground leading-none mt-0.5">{formatFileSize(attachment.size)}</p>
              </div>
            </div>
            <button onClick={clearAttachment} className="p-1 text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors">
              <X size={14} />
            </button>
          </div>
        )}

        {/* Composer Form Input */}
        <form onSubmit={handleSend} className="flex items-center gap-2 border-t border-border p-3 bg-card shrink-0 relative">
          <input
            type="file"
            id="chat-file-upload"
            className="hidden"
            onChange={handleFileChange}
            disabled={uploading}
            accept=".png,.jpg,.jpeg,.webp,.gif,.pdf,.zip,.tar,.gz,.rar,.json,.js,.ts,.py,.go,.cpp,.cs,.html,.css,.docx,.doc,.txt,.xlsx,.xls,.pptx,.ppt"
          />
          {/* File attachment trigger */}
          <button
            type="button"
            onClick={() => document.getElementById("chat-file-upload")?.click()}
            disabled={uploading || submitting || recording}
            className="p-2.5 hover:bg-muted text-muted-foreground hover:text-foreground rounded-lg transition-colors shrink-0 cursor-pointer"
            title="Attach file (Image, PDF, ZIP, code, doc)"
          >
            <Paperclip size={16} />
          </button>

          {/* Voice recorder - hidden on mobile, visible on sm and up */}
          <button
            type="button"
            onClick={toggleRecording}
            disabled={uploading || submitting}
            className={cn(
              "hidden sm:block p-2.5 rounded-lg transition-colors shrink-0",
              recording
                ? "bg-destructive/15 text-destructive"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
            title={recording ? "Stop recording" : "Record a voice message"}
          >
            {recording ? <Square size={16} /> : <Mic size={16} />}
          </button>

          {/* Emoji button */}
          <div className="relative shrink-0 flex items-center">
            <button
              type="button"
              onClick={() => setShowEmojiPicker(!showEmojiPicker)}
              className={cn(
                "p-2.5 rounded-lg transition-colors cursor-pointer",
                showEmojiPicker
                  ? "bg-primary-soft text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
              title="Add Emoji"
            >
              <Smile size={16} />
            </button>

            {/* Emoji popover */}
            {showEmojiPicker && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setShowEmojiPicker(false)} />
                <div className="absolute bottom-12 left-0 z-45 bg-card border border-border rounded-2xl shadow-lg p-2.5 w-60 grid grid-cols-5 gap-1.5 animate-in fade-in slide-in-from-bottom-2 duration-150">
                  {popularEmojis.map((emoji) => (
                    <button
                      key={emoji}
                      type="button"
                      onClick={() => addEmoji(emoji)}
                      className="text-lg p-1 hover:bg-muted rounded-lg active:scale-95 transition-all text-center cursor-pointer"
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          <input
            value={text}
            onChange={handleInputChange}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={attachment ? "Add a message or send..." : "Type a message…"}
            className="min-w-0 flex-1 rounded-xl border border-border bg-surface px-3 py-2 text-xs outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all h-10"
          />

          {scheduledFor && (
            <div className="hidden sm:flex items-center gap-1 rounded-lg border border-border bg-muted/40 px-2 py-1 text-[10px] text-muted-foreground shrink-0 select-none animate-in scale-95 duration-100">
              <CalendarClock size={11} className="text-primary shrink-0" />
              <span>
                {new Date(scheduledFor).toLocaleString([], {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
              <button type="button" onClick={() => setScheduledFor("")} className="ml-1 hover:text-foreground shrink-0">
                <X size={10} />
              </button>
            </div>
          )}

          <input
            type="datetime-local"
            value={scheduledFor}
            onChange={(e) => setScheduledFor(e.target.value)}
            className="hidden w-0 p-0"
            id="chat-schedule-input"
          />
          {/* Schedule button - hidden on mobile, visible on sm and up */}
          <button
            type="button"
            onClick={() =>
              (document.getElementById("chat-schedule-input") as HTMLInputElement | null)?.showPicker?.()
            }
            disabled={recording}
            className="hidden sm:block p-2.5 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors shrink-0"
            title="Schedule message"
          >
            <CalendarClock size={16} />
          </button>
          
          <LoadingButton
            type="submit"
            loading={submitting}
            loadingText=""
            disabled={(!text.trim() && !attachment) || uploading || recording}
            className="inline-flex items-center gap-1 px-3.5 py-2 shrink-0 rounded-xl h-10 text-xs font-bold"
          >
            <Send size={13} /> Send
          </LoadingButton>
        </form>
      </Card>

      {/* ─── DETAILS SIDE PANEL (Panel 3) ─────────────────────────────────── */}
      {showDetails && (
        <>
          {/* Mobile backdrop for drawer overlay */}
          {(isMobile || isTablet) && (
            <div
              className="fixed inset-0 bg-black/40 z-40 backdrop-blur-xs transition-opacity duration-300 animate-in fade-in"
              onClick={() => setShowDetails(false)}
            />
          )}

          <aside
            className={cn(
              "flex flex-col border-border bg-card shrink-0 h-full overflow-hidden transition-all duration-300 relative z-50",
              isMobile
                ? "fixed inset-0 w-full h-full shadow-none border-0 animate-in slide-in-from-bottom duration-300"
                : isTablet
                  ? "fixed top-0 right-0 h-full w-[320px] shadow-2xl border-l border-border animate-in slide-in-from-right duration-300"
                  : "w-[310px] border border-l ml-4 rounded-2xl"
            )}
            aria-label="Conversation details"
          >
            {/* Drawer Close / Header */}
            <div className="flex items-center justify-between border-b border-border px-4 py-3 shrink-0">
              <span className="text-[13px] font-bold text-foreground">Conversation Info</span>
              <button
                onClick={() => setShowDetails(false)}
                className="p-1 hover:bg-muted text-muted-foreground hover:text-foreground rounded-md transition-colors cursor-pointer"
                title="Close sidebar"
              >
                <X size={15} />
              </button>
            </div>

            {/* Contact quick header */}
            <div className="p-4 flex flex-col items-center text-center border-b border-border bg-muted/10 shrink-0">
              <Avatar src={conv.with.avatar} alt={conv.with.name} size={64} online={conv.with.online} />
              <h3 className="mt-2.5 text-[14px] font-bold text-foreground">{conv.with.name}</h3>
              <p className="text-[10px] font-bold text-primary bg-primary-soft px-2 py-0.5 rounded-full mt-1.5">
                {conv.with.role || "Developer"}
              </p>
            </div>

            {/* Tabs selectors */}
            <div className="flex border-b border-border text-[11.5px] font-bold text-muted-foreground shrink-0 select-none">
              <button
                onClick={() => setActiveTab("details")}
                className={cn(
                  "flex-1 py-2.5 text-center border-b-2 transition-all cursor-pointer",
                  activeTab === "details"
                    ? "border-primary text-primary"
                    : "border-transparent hover:text-foreground hover:bg-muted/10"
                )}
              >
                Details
              </button>
              <button
                onClick={() => setActiveTab("files")}
                className={cn(
                  "flex-1 py-2.5 text-center border-b-2 transition-all cursor-pointer",
                  activeTab === "files"
                    ? "border-primary text-primary"
                    : "border-transparent hover:text-foreground hover:bg-muted/10"
                )}
              >
                Files ({displayFiles.length})
              </button>
              <button
                onClick={() => setActiveTab("links")}
                className={cn(
                  "flex-1 py-2.5 text-center border-b-2 transition-all cursor-pointer",
                  activeTab === "links"
                    ? "border-primary text-primary"
                    : "border-transparent hover:text-foreground hover:bg-muted/10"
                )}
              >
                Links ({displayLinks.length})
              </button>
            </div>

            {/* Tab content area */}
            <div className="flex-1 overflow-y-auto p-4 min-h-0 [&::-webkit-scrollbar]:hidden">
              {activeTab === "details" && (
                <div className="space-y-5">
                  {/* About Section */}
                  <div className="space-y-3">
                    <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">About</h4>
                    <div className="space-y-2.5 text-xs text-foreground/80">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Local Time</span>
                        <span className="font-semibold">
                          {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                      <div className="flex flex-col gap-1.5">
                        <span className="text-muted-foreground text-left">Labels</span>
                        <div className="flex flex-wrap gap-1">
                          <span className="px-2 py-0.5 rounded bg-muted border border-border text-[9px] font-semibold text-muted-foreground">Client</span>
                          <span className="px-2 py-0.5 rounded bg-muted border border-border text-[9px] font-semibold text-muted-foreground">Design</span>
                          <span className="px-2 py-0.5 rounded bg-muted border border-border text-[9px] font-semibold text-muted-foreground">Frontend</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Notes Textarea */}
                  <div className="space-y-2">
                    <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Conversation Notes</h4>
                    <textarea
                      value={notes}
                      onChange={(e) => handleNotesChange(e.target.value)}
                      placeholder="Add custom notes about this builder or project tasks..."
                      className="w-full h-20 rounded-xl border border-border bg-surface p-2 text-xs outline-none focus:border-primary resize-none placeholder:text-muted-foreground"
                    />
                  </div>

                  {/* Shared Media Grid */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Shared Media</h4>
                      {displayImages.length > 3 && (
                        <button className="text-[9px] font-bold text-primary hover:underline">View all</button>
                      )}
                    </div>
                    <div className="grid grid-cols-3 gap-1.5">
                      {displayImages.slice(0, 3).map((img, i) => (
                        <div key={i} className="aspect-square rounded-lg overflow-hidden border border-border bg-muted group/media">
                          <img
                            src={img.url}
                            alt={img.name}
                            className="h-full w-full object-cover hover:scale-105 transition-transform duration-200 cursor-pointer"
                            onClick={() => window.open(img.url, "_blank")}
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Context Actions */}
                  <div className="space-y-2 pt-2 border-t border-border/80">
                    <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">Actions</h4>
                    <div className="space-y-1.5 text-xs font-semibold">
                      <button
                        onClick={() => toggleConvPin(conversationId)}
                        className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-muted transition-colors text-left text-foreground/80 cursor-pointer"
                      >
                        <Pin size={13} className="rotate-45" />
                        {pinnedIds.includes(conversationId) ? "Unpin Conversation" : "Pin Conversation"}
                      </button>
                      <button
                        onClick={() => toggleConvMute(conversationId)}
                        className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-muted transition-colors text-left text-foreground/80 cursor-pointer"
                      >
                        <Lock size={13} />
                        {mutedIds.includes(conversationId) ? "Unmute Notifications" : "Mute Notifications"}
                      </button>
                      <button
                        onClick={() => toggleConvArchive(conversationId)}
                        className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-muted transition-colors text-left text-foreground/80 cursor-pointer"
                      >
                        <Archive size={13} />
                        {archivedIds.includes(conversationId) ? "Unarchive Conversation" : "Archive Conversation"}
                      </button>
                      <div className="h-px bg-border/60 my-1" />
                      <button
                        onClick={() => {
                          if (confirm("Are you sure you want to clear this chat history? This cannot be undone.")) {
                            toast.success("Chat history cleared (Mock)");
                          }
                        }}
                        className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-red-500/10 hover:text-red-600 transition-colors text-left text-red-500 font-bold border border-transparent hover:border-red-500/20 cursor-pointer"
                      >
                        <Trash2 size={13} />
                        Clear Chat History
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "files" && (
                <div className="space-y-2">
                  <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">Shared Files</h4>
                  {displayFiles.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic p-2">No files shared yet.</p>
                  ) : (
                    <div className="space-y-2">
                      {displayFiles.map((file: any, i: number) => (
                        <div key={i} className="flex items-center gap-2.5 p-2 rounded-xl border border-border bg-card shadow-2xs hover:border-primary/20 transition-all">
                          <div className="p-1.5 bg-primary/10 rounded-lg text-primary shrink-0">
                            {file.name?.toLowerCase().endsWith(".zip") ? <FileArchive size={14} /> : <FileText size={14} />}
                          </div>
                          <div className="min-w-0 flex-1 text-left">
                            <p className="text-[11px] font-semibold text-foreground truncate" title={file.name}>
                              {file.name}
                            </p>
                            <p className="text-[9px] text-muted-foreground leading-none mt-0.5">
                              {file.size ? formatFileSize(file.size) : "2.4 MB"} · {file.name?.split(".").pop()?.toUpperCase() || "PDF"}
                            </p>
                          </div>
                          {file.url !== "#" && (
                            <a
                              href={file.url}
                              download={file.name}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-1.5 hover:bg-muted rounded-md text-muted-foreground hover:text-foreground shrink-0"
                            >
                              <Download size={13} />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === "links" && (
                <div className="space-y-2">
                  <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">Shared Links</h4>
                  {displayLinks.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic p-2">No links shared yet.</p>
                  ) : (
                    <div className="space-y-2">
                      {displayLinks.map((link, i) => (
                        <a
                          key={i}
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center justify-between gap-2.5 p-2.5 rounded-xl border border-border bg-card shadow-2xs hover:border-primary/20 hover:bg-muted/10 transition-all text-left group"
                        >
                          <div className="min-w-0">
                            <p className="text-[11.5px] font-semibold text-foreground truncate group-hover:text-primary transition-colors">
                              {link.title}
                            </p>
                            <p className="text-[9px] text-muted-foreground truncate leading-none mt-0.5">
                              {link.url.replace(/https?:\/\/(www\.)?/, "")}
                            </p>
                          </div>
                          <ExternalLink size={11} className="text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </aside>
        </>
      )}
    </div>
  );
}
