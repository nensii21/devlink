import React, { useState, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { UserAvatar } from "@/components/user-avatar";
import { TypoCaption, TypoSection, TypoCard } from "@/components/shared/Typography";
import { toast } from "sonner";
import { postsApi } from "@/api/modules/posts";
import {
  Image as ImageIcon,
  GitBranch,
  FolderKanban,
  BarChart2,
  Bold,
  Italic,
  Code,
  Link as LinkIcon,
  List,
  Quote,
  X,
  Globe,
  Users,
  Lock,
  Plus,
  Trash2,
  Sparkles,
  Send,
  Loader2,
  Star,
  Tag,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface RepositoryOption {
  id: string;
  name: string;
  url: string;
  stars: number;
  language: string;
}

export interface ProjectOption {
  id: string;
  title: string;
  tech_stack: string[];
}

export const MOCK_USER_REPOS: RepositoryOption[] = [
  { id: "r1", name: "devlink/core", url: "https://github.com/nensii21/devlink", stars: 1240, language: "TypeScript" },
  { id: "r2", name: "devlink/ai-matching-engine", url: "https://github.com/nensii21/ai-matching", stars: 450, language: "Python" },
  { id: "r3", name: "devlink/ui-kit", url: "https://github.com/nensii21/ui-kit", stars: 310, language: "TypeScript" },
  { id: "r4", name: "devlink/fastapi-backend", url: "https://github.com/nensii21/fastapi-backend", stars: 290, language: "Python" },
];

export const MOCK_USER_PROJECTS: ProjectOption[] = [
  { id: "p1", title: "AI-Powered Builder Platform", tech_stack: ["React", "TypeScript", "FastAPI", "WebSockets"] },
  { id: "p2", title: "Real-time Collaboration Workspace", tech_stack: ["Next.js", "TailwindCSS", "PostgreSQL"] },
  { id: "p3", title: "Open-Source Portfolio Generator", tech_stack: ["Vue.js", "Node.js", "Docker"] },
];

export interface FeedComposerProps {
  userAvatar?: string;
  userName?: string;
  userHandle?: string;
  onPostCreated?: () => void;
  className?: string;
}

export function FeedComposer({
  userAvatar,
  userName = "Developer",
  userHandle = "@builder",
  onPostCreated,
  className,
}: FeedComposerProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [content, setContent] = useState("");
  const [audience, setAudience] = useState<"public" | "connections" | "only_me">("public");
  
  // Attachments state
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);
  const [showMediaInput, setShowMediaInput] = useState(false);
  const [tempMediaInput, setTempMediaInput] = useState("");
  
  const [attachedRepo, setAttachedRepo] = useState<RepositoryOption | null>(null);
  const [showRepoPicker, setShowRepoPicker] = useState(false);

  const [attachedProject, setAttachedProject] = useState<ProjectOption | null>(null);
  const [showProjectPicker, setShowProjectPicker] = useState(false);

  // Poll State
  const [showPollCreator, setShowPollCreator] = useState(false);
  const [pollQuestion, setPollQuestion] = useState("");
  const [pollOptions, setPollOptions] = useState<string[]>(["", ""]);
  const [pollDays, setPollDays] = useState<number>(7);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Markdown Formatting Helpers
  const insertMarkdown = (prefix: string, suffix: string = "") => {
    if (!textareaRef.current) return;
    const textarea = textareaRef.current;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = content.substring(start, end) || "text";
    const newText = content.substring(0, start) + prefix + selectedText + suffix + content.substring(end);
    setContent(newText);
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + prefix.length, start + prefix.length + selectedText.length);
    }, 0);
  };

  const handleAddPollOption = () => {
    if (pollOptions.length >= 6) return;
    setPollOptions([...pollOptions, ""]);
  };

  const handleRemovePollOption = (index: number) => {
    if (pollOptions.length <= 2) return;
    setPollOptions(pollOptions.filter((_, i) => i !== index));
  };

  const handleUpdatePollOption = (index: number, val: string) => {
    const next = [...pollOptions];
    next[index] = val;
    setPollOptions(next);
  };

  const handleCreatePost = async () => {
    if (!content.trim() && !mediaUrl && !attachedRepo && !attachedProject && !pollQuestion.trim()) {
      toast.error("Please add text or an attachment to your post.");
      return;
    }

    setIsSubmitting(true);
    try {
      const validPollOptions = pollOptions.filter((o) => o.trim().length > 0);
      const pollPayload =
        showPollCreator && pollQuestion.trim() && validPollOptions.length >= 2
          ? {
              question: pollQuestion.trim(),
              options: validPollOptions,
              expires_in_days: pollDays,
            }
          : undefined;

      await postsApi.create({
        content: content.trim(),
        image: mediaUrl || undefined,
        repository: attachedRepo
          ? {
              id: attachedRepo.id,
              name: attachedRepo.name,
              url: attachedRepo.url,
              stars: attachedRepo.stars,
              language: attachedRepo.language,
            }
          : undefined,
        project: attachedProject
          ? {
              id: attachedProject.id,
              title: attachedProject.title,
              tech_stack: attachedProject.tech_stack,
            }
          : undefined,
        poll: pollPayload,
      });

      toast.success("Post published successfully!");
      // Reset composer state
      setContent("");
      setMediaUrl(null);
      setShowMediaInput(false);
      setAttachedRepo(null);
      setAttachedProject(null);
      setShowPollCreator(false);
      setPollQuestion("");
      setPollOptions(["", ""]);
      setModalOpen(false);
      if (onPostCreated) onPostCreated();
    } catch (err: any) {
      toast.error(err.message || "Failed to publish post.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={cn("w-full rounded-2xl border border-border bg-card p-4 shadow-sm", className)}>
      {/* LinkedIn-style Trigger Card */}
      <div className="flex items-center gap-3">
        <UserAvatar src={userAvatar} name={userName} size="md" />
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="flex-1 rounded-full border border-border bg-surface hover:bg-muted/60 px-4 py-2.5 text-left text-sm text-muted-foreground transition-all duration-200 cursor-pointer shadow-2xs"
        >
          Start a post, share a project, or create a poll...
        </button>
      </div>

      {/* Action Buttons Row */}
      <div className="mt-3.5 pt-3 border-t border-border/50 flex flex-wrap items-center justify-between gap-1 text-xs font-medium text-muted-foreground">
        <button
          type="button"
          onClick={() => {
            setShowMediaInput(true);
            setModalOpen(true);
          }}
          className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-surface hover:text-foreground transition-colors cursor-pointer"
        >
          <ImageIcon size={18} className="text-sky-500" />
          <span>Media</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setShowRepoPicker(true);
            setModalOpen(true);
          }}
          className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-surface hover:text-foreground transition-colors cursor-pointer"
        >
          <GitBranch size={18} className="text-emerald-500" />
          <span>Repository</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setShowProjectPicker(true);
            setModalOpen(true);
          }}
          className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-surface hover:text-foreground transition-colors cursor-pointer"
        >
          <FolderKanban size={18} className="text-purple-500" />
          <span>Project</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setShowPollCreator(true);
            setModalOpen(true);
          }}
          className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-surface hover:text-foreground transition-colors cursor-pointer"
        >
          <BarChart2 size={18} className="text-amber-500" />
          <span>Poll</span>
        </button>
      </div>

      {/* Expanded LinkedIn-like Composer Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="sm:max-w-2xl p-0 gap-0 overflow-hidden bg-card border border-border shadow-xl rounded-2xl">
          <DialogHeader className="p-4 border-b border-border flex flex-row items-center justify-between">
            <DialogTitle className="text-base font-semibold flex items-center gap-2">
              <Sparkles size={18} className="text-primary" /> Create Post
            </DialogTitle>
          </DialogHeader>

          <div className="p-4 space-y-4 max-h-[75vh] overflow-y-auto">
            {/* User Header & Audience Selector */}
            <div className="flex items-center gap-3">
              <UserAvatar src={userAvatar} name={userName} size="md" />
              <div>
                <TypoCard className="text-sm font-semibold text-foreground">{userName}</TypoCard>
                <div className="flex items-center gap-2 mt-0.5">
                  <select
                    value={audience}
                    onChange={(e) => setAudience(e.target.value as any)}
                    className="flex items-center gap-1 rounded-full border border-border bg-surface px-2.5 py-0.5 text-xs text-muted-foreground font-medium outline-none cursor-pointer hover:border-primary/50"
                  >
                    <option value="public">🌐 Anyone (Public)</option>
                    <option value="connections">👥 Connections Only</option>
                    <option value="only_me">🔒 Only Me</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Markdown Formatting Toolbar */}
            <div className="flex items-center gap-1 p-1.5 rounded-lg border border-border/60 bg-surface/50 text-muted-foreground">
              <button
                type="button"
                onClick={() => insertMarkdown("**", "**")}
                title="Bold"
                className="p-1.5 rounded hover:bg-muted hover:text-foreground transition-colors"
              >
                <Bold size={15} />
              </button>
              <button
                type="button"
                onClick={() => insertMarkdown("*", "*")}
                title="Italic"
                className="p-1.5 rounded hover:bg-muted hover:text-foreground transition-colors"
              >
                <Italic size={15} />
              </button>
              <button
                type="button"
                onClick={() => insertMarkdown("`", "`")}
                title="Code"
                className="p-1.5 rounded hover:bg-muted hover:text-foreground transition-colors"
              >
                <Code size={15} />
              </button>
              <div className="h-4 w-px bg-border mx-1" />
              <button
                type="button"
                onClick={() => insertMarkdown("[", "](https://)")}
                title="Link"
                className="p-1.5 rounded hover:bg-muted hover:text-foreground transition-colors"
              >
                <LinkIcon size={15} />
              </button>
              <button
                type="button"
                onClick={() => insertMarkdown("- ")}
                title="Bullet List"
                className="p-1.5 rounded hover:bg-muted hover:text-foreground transition-colors"
              >
                <List size={15} />
              </button>
              <button
                type="button"
                onClick={() => insertMarkdown("> ")}
                title="Quote"
                className="p-1.5 rounded hover:bg-muted hover:text-foreground transition-colors"
              >
                <Quote size={15} />
              </button>
            </div>

            {/* Content Textarea */}
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="What do you want to share with the builder community? Use #hashtags or markdown..."
              className="w-full min-h-[140px] resize-none bg-transparent text-sm leading-relaxed text-foreground placeholder:text-muted-foreground outline-none border-none p-1"
            />

            {/* Media Attachment Action Input */}
            {showMediaInput && (
              <div className="rounded-xl border border-border bg-surface p-3 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold text-foreground">
                  <span className="flex items-center gap-1.5"><ImageIcon size={14} className="text-sky-500" /> Image / Video URL</span>
                  <button type="button" onClick={() => setShowMediaInput(false)} className="text-muted-foreground hover:text-foreground">
                    <X size={14} />
                  </button>
                </div>
                <div className="flex gap-2">
                  <input
                    type="url"
                    value={tempMediaInput}
                    onChange={(e) => setTempMediaInput(e.target.value)}
                    placeholder="Paste image or video link (e.g. https://images.unsplash.com/...)"
                    className="flex-1 rounded-lg border border-border bg-card px-3 py-1.5 text-xs outline-none focus:ring-1 focus:ring-primary"
                  />
                  <Button
                    size="sm"
                    onClick={() => {
                      if (tempMediaInput.trim()) {
                        setMediaUrl(tempMediaInput.trim());
                        setTempMediaInput("");
                        setShowMediaInput(false);
                      }
                    }}
                    className="h-8 text-xs"
                  >
                    Attach
                  </Button>
                </div>
              </div>
            )}

            {/* Media Preview Card */}
            {mediaUrl && (
              <div className="relative rounded-xl overflow-hidden border border-border bg-surface max-h-56 flex items-center justify-center">
                <img src={mediaUrl} alt="Attached Media" className="object-cover max-h-56 w-full" />
                <button
                  type="button"
                  onClick={() => setMediaUrl(null)}
                  className="absolute top-2 right-2 rounded-full bg-black/70 p-1 text-white hover:bg-black"
                >
                  <X size={14} />
                </button>
              </div>
            )}

            {/* Repository Picker & Preview */}
            {showRepoPicker && !attachedRepo && (
              <div className="rounded-xl border border-border bg-surface p-3 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold text-foreground">
                  <span className="flex items-center gap-1.5"><GitBranch size={14} className="text-emerald-500" /> Select Repository</span>
                  <button type="button" onClick={() => setShowRepoPicker(false)} className="text-muted-foreground hover:text-foreground">
                    <X size={14} />
                  </button>
                </div>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {MOCK_USER_REPOS.map((repo) => (
                    <button
                      key={repo.id}
                      type="button"
                      onClick={() => {
                        setAttachedRepo(repo);
                        setShowRepoPicker(false);
                      }}
                      className="w-full flex items-center justify-between p-2 rounded-lg border border-border/50 bg-card hover:bg-muted text-left transition-colors"
                    >
                      <div>
                        <div className="text-xs font-semibold text-foreground">{repo.name}</div>
                        <div className="text-[11px] text-muted-foreground">{repo.language}</div>
                      </div>
                      <span className="flex items-center gap-1 text-xs text-amber-500">
                        <Star size={12} className="fill-current" /> {repo.stars}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {attachedRepo && (
              <div className="flex items-center justify-between rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
                    <GitBranch size={18} />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-foreground">{attachedRepo.name}</div>
                    <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                      <span>{attachedRepo.language}</span>
                      <span>•</span>
                      <span className="flex items-center gap-0.5 text-amber-500 font-medium">
                        <Star size={11} className="fill-current" /> {attachedRepo.stars}
                      </span>
                    </div>
                  </div>
                </div>
                <button type="button" onClick={() => setAttachedRepo(null)} className="text-muted-foreground hover:text-foreground p-1">
                  <X size={14} />
                </button>
              </div>
            )}

            {/* Project Picker & Preview */}
            {showProjectPicker && !attachedProject && (
              <div className="rounded-xl border border-border bg-surface p-3 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold text-foreground">
                  <span className="flex items-center gap-1.5"><FolderKanban size={14} className="text-purple-500" /> Attach DevLink Project</span>
                  <button type="button" onClick={() => setShowProjectPicker(false)} className="text-muted-foreground hover:text-foreground">
                    <X size={14} />
                  </button>
                </div>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {MOCK_USER_PROJECTS.map((proj) => (
                    <button
                      key={proj.id}
                      type="button"
                      onClick={() => {
                        setAttachedProject(proj);
                        setShowProjectPicker(false);
                      }}
                      className="w-full flex items-center justify-between p-2 rounded-lg border border-border/50 bg-card hover:bg-muted text-left transition-colors"
                    >
                      <div>
                        <div className="text-xs font-semibold text-foreground">{proj.title}</div>
                        <div className="text-[11px] text-muted-foreground">{proj.tech_stack.join(" • ")}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {attachedProject && (
              <div className="flex items-center justify-between rounded-xl border border-purple-500/30 bg-purple-500/5 p-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-purple-500/10 text-purple-500">
                    <FolderKanban size={18} />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-foreground">{attachedProject.title}</div>
                    <div className="flex flex-wrap gap-1 mt-0.5">
                      {attachedProject.tech_stack.map((tech) => (
                        <span key={tech} className="rounded bg-surface px-1.5 py-0.5 text-[10px] text-muted-foreground border border-border/50">
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <button type="button" onClick={() => setAttachedProject(null)} className="text-muted-foreground hover:text-foreground p-1">
                  <X size={14} />
                </button>
              </div>
            )}

            {/* Poll Creator Component */}
            {showPollCreator && (
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3.5 space-y-3">
                <div className="flex items-center justify-between text-xs font-semibold text-foreground">
                  <span className="flex items-center gap-1.5"><BarChart2 size={14} className="text-amber-500" /> Create a Poll</span>
                  <button type="button" onClick={() => setShowPollCreator(false)} className="text-muted-foreground hover:text-foreground">
                    <X size={14} />
                  </button>
                </div>

                <input
                  type="text"
                  value={pollQuestion}
                  onChange={(e) => setPollQuestion(e.target.value)}
                  placeholder="Ask a question (e.g., Which backend framework do you prefer?)"
                  className="w-full rounded-lg border border-border bg-card px-3 py-1.5 text-xs outline-none focus:ring-1 focus:ring-amber-500"
                />

                <div className="space-y-2">
                  {pollOptions.map((opt, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={opt}
                        onChange={(e) => handleUpdatePollOption(i, e.target.value)}
                        placeholder={`Option ${i + 1}`}
                        className="flex-1 rounded-lg border border-border bg-card px-3 py-1.5 text-xs outline-none focus:ring-1 focus:ring-amber-500"
                      />
                      {pollOptions.length > 2 && (
                        <button
                          type="button"
                          onClick={() => handleRemovePollOption(i)}
                          className="text-muted-foreground hover:text-destructive p-1"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-between pt-1">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleAddPollOption}
                    disabled={pollOptions.length >= 6}
                    className="h-7 text-xs gap-1"
                  >
                    <Plus size={12} /> Add Option
                  </Button>

                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>Duration:</span>
                    <select
                      value={pollDays}
                      onChange={(e) => setPollDays(Number(e.target.value))}
                      className="rounded-md border border-border bg-card px-2 py-1 text-xs outline-none"
                    >
                      <option value={1}>1 Day</option>
                      <option value={3}>3 Days</option>
                      <option value={7}>7 Days</option>
                      <option value={14}>14 Days</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Modal Footer Controls */}
          <div className="p-4 border-t border-border bg-surface/30 flex items-center justify-between">
            <div className="flex items-center gap-1 text-muted-foreground">
              <button
                type="button"
                onClick={() => setShowMediaInput(!showMediaInput)}
                title="Attach Image / Video"
                className="p-2 rounded-lg hover:bg-muted hover:text-sky-500 transition-colors"
              >
                <ImageIcon size={18} />
              </button>
              <button
                type="button"
                onClick={() => setShowRepoPicker(!showRepoPicker)}
                title="Attach Repository"
                className="p-2 rounded-lg hover:bg-muted hover:text-emerald-500 transition-colors"
              >
                <GitBranch size={18} />
              </button>
              <button
                type="button"
                onClick={() => setShowProjectPicker(!showProjectPicker)}
                title="Attach Project"
                className="p-2 rounded-lg hover:bg-muted hover:text-purple-500 transition-colors"
              >
                <FolderKanban size={18} />
              </button>
              <button
                type="button"
                onClick={() => setShowPollCreator(!showPollCreator)}
                title="Create Poll"
                className="p-2 rounded-lg hover:bg-muted hover:text-amber-500 transition-colors"
              >
                <BarChart2 size={18} />
              </button>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground">{content.length} / 3000</span>
              <Button
                onClick={handleCreatePost}
                disabled={isSubmitting || (!content.trim() && !mediaUrl && !attachedRepo && !attachedProject && !pollQuestion.trim())}
                className="gap-1.5 rounded-full px-5 text-xs font-semibold"
              >
                {isSubmitting ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                <span>Post</span>
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default FeedComposer;
