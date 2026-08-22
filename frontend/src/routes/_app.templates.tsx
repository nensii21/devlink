import { useState, useEffect } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  LayoutTemplate,
  Search,
  Plus,
  Star,
  Copy,
  ExternalLink,
  Github,
  Filter,
  Sparkles,
  CheckCircle,
  Code2,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, EmptyState } from "@/components/shared/primitives";
import { UserAvatar } from "@/components/user-avatar";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { toast } from "sonner";
import { projectTemplatesApi, type ProjectTemplate } from "@/api";
import { TypoSection, TypoCaption, TypoHeading } from "@/components/shared/Typography";

export const Route = createFileRoute("/_app/templates")({
  head: () => ({
    meta: [
      { title: "Project Templates Marketplace — DevLink" },
      {
        name: "description",
        content: "Discover, share, and clone reusable project templates and blueprints.",
      },
    ],
  }),
  component: TemplatesPage,
});

const CATEGORIES = [
  { id: "all", label: "All Templates" },
  { id: "web-app", label: "Web Apps" },
  { id: "mobile-app", label: "Mobile Apps" },
  { id: "ai-ml", label: "AI / ML" },
  { id: "cli-tool", label: "CLI Tools" },
  { id: "backend-service", label: "Backend Services" },
  { id: "library", label: "Libraries" },
];

function TemplatesPage() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [sortBy, setSortBy] = useState("popular");

  // Publish Modal State
  const [publishOpen, setPublishOpen] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newCategory, setNewCategory] = useState("web-app");
  const [newTechStack, setNewTechStack] = useState("");
  const [newFeatures, setNewFeatures] = useState("");
  const [newRepoUrl, setNewRepoUrl] = useState("");
  const [newDemoUrl, setNewDemoUrl] = useState("");

  // Clone Modal State
  const [cloneModalOpen, setCloneModalOpen] = useState(false);
  const [cloningTemplate, setCloningTemplate] = useState<ProjectTemplate | null>(null);
  const [clonedTitle, setClonedTitle] = useState("");
  const [cloning, setCloning] = useState(false);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const res = await projectTemplatesApi.listTemplates({
        search: search.trim() || undefined,
        category: selectedCategory !== "all" ? selectedCategory : undefined,
        sort_by: sortBy,
      });
      setTemplates(res.templates);
    } catch {
      toast.error("Failed to load project templates");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, [search, selectedCategory, sortBy]);

  const handleFavoriteToggle = async (templateId: string) => {
    try {
      const res = await projectTemplatesApi.toggleFavorite(templateId);
      setTemplates((prev) =>
        prev.map((t) =>
          t.id === templateId
            ? { ...t, is_favorited: res.is_favorited, stars_count: res.stars_count }
            : t,
        ),
      );
      toast.success(res.is_favorited ? "Added to favorites" : "Removed from favorites");
    } catch {
      toast.error("Please sign in to favorite templates");
    }
  };

  const handlePublish = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDescription.trim()) {
      toast.error("Title and description are required");
      return;
    }

    setPublishing(true);
    try {
      const stackList = newTechStack
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const featureList = newFeatures
        .split("\n")
        .map((f) => f.trim())
        .filter(Boolean);

      await projectTemplatesApi.createTemplate({
        title: newTitle,
        description: newDescription,
        category: newCategory,
        tech_stack: stackList,
        features: featureList,
        repository_url: newRepoUrl || undefined,
        demo_url: newDemoUrl || undefined,
      });

      toast.success("Project template published to marketplace!");
      setPublishOpen(false);
      setNewTitle("");
      setNewDescription("");
      setNewTechStack("");
      setNewFeatures("");
      setNewRepoUrl("");
      setNewDemoUrl("");
      fetchTemplates();
    } catch {
      toast.error("Failed to publish template. Please check input.");
    } finally {
      setPublishing(false);
    }
  };

  const handleCloneSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cloningTemplate) return;

    setCloning(true);
    try {
      const project = await projectTemplatesApi.cloneTemplate(cloningTemplate.id, {
        new_project_title: clonedTitle || undefined,
      });

      toast.success(`Cloned '${cloningTemplate.title}' as a new project!`);
      setCloneModalOpen(false);
      navigate({ to: "/projects/$projectId", params: { projectId: project.id } });
    } catch {
      toast.error("Failed to clone template");
    } finally {
      setCloning(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6 py-6 px-4 sm:px-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent p-6 rounded-2xl border border-primary/20">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold text-sm mb-1">
            <LayoutTemplate className="h-4 w-4" /> Templates Marketplace
          </div>
          <TypoHeading as="h1">Reusable Project Blueprints</TypoHeading>
          <TypoCaption as="p">
            Discover, share, and clone production-ready starters, fullstack templates, and
            scaffolding for your next build.
          </TypoCaption>
        </div>

        <Button
          onClick={() => setPublishOpen(true)}
          className="gap-2 shrink-0 self-start md:self-auto"
        >
          <Plus size={16} /> Publish Template
        </Button>
      </div>

      {/* Filter & Search Bar */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search templates, tech stack, features..."
              className="pl-9 text-sm"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-between sm:justify-end">
            <TypoCaption>
              <Filter size={13} /> Sort by:
            </TypoCaption>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="rounded-md border border-border bg-background px-3 py-1.5 text-xs text-foreground outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="popular">Most Popular</option>
              <option value="clones">Most Cloned</option>
              <option value="recent">Recently Added</option>
            </select>
          </div>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap ${
                selectedCategory === cat.id
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted/70 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Templates Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="h-64 rounded-xl border border-border bg-muted/20 animate-pulse p-5"
            />
          ))}
        </div>
      ) : templates.length === 0 ? (
        <EmptyState
          icon={LayoutTemplate}
          title="No templates found"
          desc="Try a different search, or publish the first template in this category."
          action={<Button onClick={() => setPublishOpen(true)} variant="outline" size="sm" className="gap-2"><Plus size={14} /> Publish template</Button>}
          className="rounded-2xl border border-dashed border-primary/20 bg-primary/5"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((tpl) => (
            <Card
              key={tpl.id}
              className="p-5 flex flex-col justify-between hover:border-primary/50 transition-all shadow-sm"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <Badge
                    variant="secondary"
                    className="capitalize text-[11px] font-medium bg-primary/10 text-primary hover:bg-primary/15"
                  >
                    {tpl.category.replace("-", " ")}
                  </Badge>
                  {tpl.is_featured && (
                    <Badge
                      variant="default"
                      className="bg-amber-500 hover:bg-amber-600 text-[10px] gap-1"
                    >
                      <Sparkles size={10} /> Featured
                    </Badge>
                  )}
                </div>

                <div>
                  <TypoSection>{tpl.title}</TypoSection>
                  <TypoCaption as="p">{tpl.description}</TypoCaption>
                </div>

                {/* Tech Stack Pills */}
                {tpl.tech_stack && tpl.tech_stack.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {tpl.tech_stack.slice(0, 4).map((tech) => (
                      <span
                        key={tech}
                        className="text-[10px] font-mono bg-muted px-2 py-0.5 rounded text-foreground/80"
                      >
                        {tech}
                      </span>
                    ))}
                    {tpl.tech_stack.length > 4 && (
                      <TypoCaption>+{tpl.tech_stack.length - 4} more</TypoCaption>
                    )}
                  </div>
                )}

                {/* Key Features */}
                {tpl.features && tpl.features.length > 0 && (
                  <ul className="text-xs text-muted-foreground space-y-1 pt-1 border-t border-border/50">
                    {tpl.features.slice(0, 2).map((feat, idx) => (
                      <li key={idx} className="flex items-center gap-1.5 truncate">
                        <CheckCircle size={12} className="text-emerald-500 shrink-0" />
                        <span className="truncate">{feat}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="pt-4 mt-4 border-t border-border flex items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleFavoriteToggle(tpl.id)}
                    className={`flex items-center gap-1 text-xs transition-colors ${
                      tpl.is_favorited
                        ? "text-amber-500 font-semibold"
                        : "text-muted-foreground hover:text-amber-500"
                    }`}
                    title={tpl.is_favorited ? "Remove favorite" : "Star template"}
                  >
                    <Star
                      size={14}
                      className={tpl.is_favorited ? "fill-amber-500 text-amber-500" : ""}
                    />
                    <span>{tpl.stars_count}</span>
                  </button>

                  <span
                    className="flex items-center gap-1 text-xs text-muted-foreground"
                    title="Total clones"
                  >
                    <Copy size={13} />
                    <span>{tpl.clones_count}</span>
                  </span>
                </div>

                <div className="flex items-center gap-1.5">
                  {tpl.repository_url && (
                    <a
                      href={tpl.repository_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 text-muted-foreground hover:text-foreground rounded-md hover:bg-muted transition-colors"
                      title="View Repository"
                    >
                      <Github size={15} />
                    </a>
                  )}

                  <Button
                    size="sm"
                    className="text-xs gap-1 h-8"
                    onClick={() => {
                      setCloningTemplate(tpl);
                      setClonedTitle(`${tpl.title} App`);
                      setCloneModalOpen(true);
                    }}
                  >
                    <Copy size={13} /> Clone
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Publish Template Dialog */}
      <Dialog open={publishOpen} onOpenChange={setPublishOpen}>
        <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg">
              <LayoutTemplate className="h-5 w-5 text-primary" /> Publish Project Template
            </DialogTitle>
            <DialogDescription>
              Share your project scaffolding or blueprint with the DevLink community.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handlePublish} className="space-y-4 py-2">
            <div>
              <Label className="text-xs font-semibold">Template Title *</Label>
              <Input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="e.g. Next.js 14 SaaS Starter with Stripe"
                required
                className="mt-1"
              />
            </div>

            <div>
              <Label className="text-xs font-semibold">Category *</Label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="w-full mt-1 rounded-md border border-border bg-background px-3 py-2 text-xs text-foreground"
              >
                <option value="web-app">Web App</option>
                <option value="mobile-app">Mobile App</option>
                <option value="ai-ml">AI / ML</option>
                <option value="cli-tool">CLI Tool</option>
                <option value="backend-service">Backend Service</option>
                <option value="library">Library</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <Label className="text-xs font-semibold">Description *</Label>
              <Textarea
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Brief summary of what this template includes and how it helps developers..."
                required
                rows={3}
                className="mt-1 text-xs"
              />
            </div>

            <div>
              <Label className="text-xs font-semibold">Tech Stack (comma-separated)</Label>
              <Input
                value={newTechStack}
                onChange={(e) => setNewTechStack(e.target.value)}
                placeholder="React, FastAPI, PostgreSQL, TailwindCSS"
                className="mt-1 text-xs"
              />
            </div>

            <div>
              <Label className="text-xs font-semibold">Key Features (one per line)</Label>
              <Textarea
                value={newFeatures}
                onChange={(e) => setNewFeatures(e.target.value)}
                placeholder="OAuth2 Authentication&#10;Stripe Subscription Billing&#10;Docker & CI/CD Pipelines"
                rows={3}
                className="mt-1 text-xs"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <Label className="text-xs font-semibold">Repository URL</Label>
                <Input
                  value={newRepoUrl}
                  onChange={(e) => setNewRepoUrl(e.target.value)}
                  placeholder="https://github.com/org/repo"
                  className="mt-1 text-xs"
                />
              </div>

              <div>
                <Label className="text-xs font-semibold">Demo URL</Label>
                <Input
                  value={newDemoUrl}
                  onChange={(e) => setNewDemoUrl(e.target.value)}
                  placeholder="https://demo.example.com"
                  className="mt-1 text-xs"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <Button type="button" variant="ghost" onClick={() => setPublishOpen(false)}>
                Cancel
              </Button>
              <LoadingButton type="submit" loading={publishing} loadingText="Publishing...">
                Publish Template
              </LoadingButton>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Clone Template Dialog */}
      <Dialog open={cloneModalOpen} onOpenChange={setCloneModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <Copy className="h-4 w-4 text-primary" /> Clone '{cloningTemplate?.title}'
            </DialogTitle>
            <DialogDescription className="text-xs">
              Create a new DevLink project initialized from this template.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleCloneSubmit} className="space-y-4 py-2">
            <div>
              <Label className="text-xs font-semibold">Project Title</Label>
              <Input
                value={clonedTitle}
                onChange={(e) => setClonedTitle(e.target.value)}
                placeholder="Enter name for your new project"
                required
                className="mt-1 text-xs"
              />
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setCloneModalOpen(false)}
              >
                Cancel
              </Button>
              <LoadingButton type="submit" size="sm" loading={cloning} loadingText="Cloning...">
                Clone & Launch Project
              </LoadingButton>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
