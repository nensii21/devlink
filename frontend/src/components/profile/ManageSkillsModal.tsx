import React, { useState, useEffect, useMemo, useRef } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TagChip, Card } from "@/components/shared/primitives";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { skillsApi, type SkillItem, type SkillSearchResult } from "@/api/modules/skills";
import { usersApi } from "@/api/modules/users";
import {
  Plus,
  Trash2,
  ArrowUp,
  ArrowDown,
  Search,
  Sparkles,
  AlertCircle,
  Loader2,
  Check,
  Award,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const SKILL_CATEGORIES = [
  "Languages",
  "Frameworks",
  "Databases",
  "Cloud",
  "DevOps",
  "AI/ML",
  "Design",
  "Other",
] as const;

export const SKILL_LEVELS = [
  { value: "Beginner", label: "Beginner", color: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
  { value: "Intermediate", label: "Intermediate", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" },
  { value: "Advanced", label: "Advanced", color: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
  { value: "Expert", label: "Expert", color: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
] as const;

const POPULAR_SUGGESTIONS = [
  { name: "TypeScript", category: "Languages" },
  { name: "Python", category: "Languages" },
  { name: "JavaScript", category: "Languages" },
  { name: "React", category: "Frameworks" },
  { name: "Next.js", category: "Frameworks" },
  { name: "FastAPI", category: "Frameworks" },
  { name: "Node.js", category: "Frameworks" },
  { name: "PostgreSQL", category: "Databases" },
  { name: "MongoDB", category: "Databases" },
  { name: "Redis", category: "Databases" },
  { name: "Docker", category: "DevOps" },
  { name: "Kubernetes", category: "DevOps" },
  { name: "AWS", category: "Cloud" },
  { name: "GCP", category: "Cloud" },
  { name: "PyTorch", category: "AI/ML" },
  { name: "Tailwind CSS", category: "Design" },
  { name: "Figma", category: "Design" },
];

export interface ManageSkillsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialSkills?: SkillItem[];
  username?: string;
  onSuccess?: (skills: SkillItem[]) => void;
}

export function ManageSkillsModal({
  open,
  onOpenChange,
  initialSkills = [],
  username,
  onSuccess,
}: ManageSkillsModalProps) {
  const queryClient = useQueryClient();

  const [skills, setSkills] = useState<SkillItem[]>([]);
  const [skillNameInput, setSkillNameInput] = useState("");
  const [categoryInput, setCategoryInput] = useState<string>("Languages");
  const [levelInput, setLevelInput] = useState<string>("Intermediate");
  const [yearsInput, setYearsInput] = useState<number>(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [duplicateError, setDuplicateError] = useState<string | null>(null);

  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Sync initial skills when modal opens
  useEffect(() => {
    if (open) {
      setSkills(
        initialSkills.map((s) => ({
          ...s,
          level: s.level || "Intermediate",
          category: s.category || "Languages",
          years_of_experience: s.years_of_experience ?? s.yearsOfExperience ?? 1,
        })),
      );
      setSkillNameInput("");
      setDuplicateError(null);
      setShowSuggestions(false);
    }
  }, [open, initialSkills]);

  // Autocomplete skill search
  const { data: searchResults = [], isFetching: isSearching } = useQuery({
    queryKey: ["skills-search", searchQuery],
    queryFn: async () => {
      if (!searchQuery.trim()) return [];
      try {
        const res = await skillsApi.search(searchQuery.trim());
        return res;
      } catch {
        return [];
      }
    },
    enabled: searchQuery.trim().length >= 1,
  });

  // Filter popular suggestions
  const filteredPopular = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return POPULAR_SUGGESTIONS.filter((s) => {
      const matches = !query || s.name.toLowerCase().includes(query);
      const notAdded = !skills.some((added) => added.name.toLowerCase() === s.name.toLowerCase());
      return matches && notAdded;
    }).slice(0, 6);
  }, [searchQuery, skills]);

  // Close suggestions dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        searchContainerRef.current &&
        !searchContainerRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectSuggestion = (name: string, category?: string) => {
    setSkillNameInput(name);
    setSearchQuery(name);
    if (category) {
      setCategoryInput(category);
    }
    setShowSuggestions(false);
    setDuplicateError(null);
  };

  const handleAddSkill = () => {
    const trimmedName = skillNameInput.trim();
    if (!trimmedName) {
      setDuplicateError("Please enter a skill name.");
      return;
    }

    // Duplicate prevention: Case-insensitive check
    const isDuplicate = skills.some(
      (s) => s.name.toLowerCase() === trimmedName.toLowerCase(),
    );

    if (isDuplicate) {
      setDuplicateError(`"${trimmedName}" is already in your skills list.`);
      return;
    }

    const newSkill: SkillItem = {
      name: trimmedName,
      category: categoryInput,
      level: levelInput,
      years_of_experience: Number(yearsInput) || 0,
    };

    setSkills((prev) => [...prev, newSkill]);
    setSkillNameInput("");
    setSearchQuery("");
    setDuplicateError(null);
    setShowSuggestions(false);
    toast.success(`Added ${trimmedName}`);
  };

  const handleRemoveSkill = (index: number) => {
    const removed = skills[index];
    setSkills((prev) => prev.filter((_, i) => i !== index));
    if (removed) {
      toast.info(`Removed ${removed.name}`);
    }
  };

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    setSkills((prev) => {
      const next = [...prev];
      const temp = next[index - 1];
      next[index - 1] = next[index];
      next[index] = temp;
      return next;
    });
  };

  const handleMoveDown = (index: number) => {
    if (index === skills.length - 1) return;
    setSkills((prev) => {
      const next = [...prev];
      const temp = next[index + 1];
      next[index + 1] = next[index];
      next[index] = temp;
      return next;
    });
  };

  const handleUpdateSkillField = (
    index: number,
    field: "level" | "category" | "years_of_experience",
    value: any,
  ) => {
    setSkills((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: async () => {
      // 1. Update skill matrix backend
      await skillsApi.updateMyMatrix(skills);
      // 2. Also sync string array to user profile
      await usersApi.updateProfile({ skills: skills.map((s) => s.name) });
      return skills;
    },
    onSuccess: (savedSkills) => {
      toast.success("Skills updated successfully!");
      if (username) {
        queryClient.invalidateQueries({ queryKey: ["profile", username] });
      }
      queryClient.invalidateQueries({ queryKey: ["skills-matrix"] });
      queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      if (onSuccess) {
        onSuccess(savedSkills);
      }
      onOpenChange(false);
    },
    onError: (err: any) => {
      toast.error(err?.message || "Failed to save skills. Please try again.");
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col p-6 overflow-hidden">
        <DialogHeader className="pb-3 border-b border-border">
          <DialogTitle className="text-lg font-bold flex items-center gap-2 text-foreground">
            <Award className="h-5 w-5 text-primary" />
            Manage Skills
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Add, edit, remove, and reorder skills on your developer profile.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto space-y-6 py-4 pr-1">
          {/* Add Skill Form Section */}
          <div className="p-4 rounded-xl border border-border bg-muted/30 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                Add New Skill
              </span>
              <span className="text-[11px] text-muted-foreground">
                {skills.length} skills added
              </span>
            </div>

            <div className="grid gap-3 sm:grid-cols-12 items-end">
              {/* Skill Name & Autocomplete */}
              <div className="sm:col-span-5 relative" ref={searchContainerRef}>
                <Label className="text-xs text-muted-foreground mb-1 block">Skill Name</Label>
                <div className="relative">
                  <Input
                    placeholder="e.g. TypeScript, React, Docker"
                    value={skillNameInput}
                    onChange={(e) => {
                      setSkillNameInput(e.target.value);
                      setSearchQuery(e.target.value);
                      setShowSuggestions(true);
                      setDuplicateError(null);
                    }}
                    onFocus={() => setShowSuggestions(true)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddSkill();
                      }
                    }}
                    className="pr-8 text-sm"
                  />
                  {isSearching ? (
                    <Loader2 className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />
                  ) : (
                    <Search className="absolute right-2.5 top-2.5 h-4 w-4 text-muted-foreground/60 pointer-events-none" />
                  )}
                </div>

                {/* Autocomplete suggestions dropdown */}
                {showSuggestions && (searchResults.length > 0 || filteredPopular.length > 0) && (
                  <div className="absolute z-50 left-0 right-0 top-full mt-1 max-h-48 overflow-y-auto rounded-lg border border-border bg-popover shadow-xl p-1 text-sm">
                    {searchResults.length > 0 && (
                      <div className="p-1">
                        <div className="text-[10px] font-bold text-muted-foreground uppercase px-2 py-1">
                          Database Matches
                        </div>
                        {searchResults.map((item) => (
                          <button
                            key={item.id || item.name}
                            type="button"
                            onClick={() => handleSelectSuggestion(item.name, item.category)}
                            className="w-full text-left flex items-center justify-between px-2 py-1.5 rounded hover:bg-muted text-xs cursor-pointer"
                          >
                            <span className="font-medium text-foreground">{item.name}</span>
                            {item.category && (
                              <span className="text-[10px] text-muted-foreground bg-muted/60 px-1.5 py-0.5 rounded">
                                {item.category}
                              </span>
                            )}
                          </button>
                        ))}
                      </div>
                    )}

                    {filteredPopular.length > 0 && (
                      <div className="p-1 border-t border-border/50">
                        <div className="text-[10px] font-bold text-muted-foreground uppercase px-2 py-1 flex items-center gap-1">
                          <Sparkles size={10} className="text-amber-500" /> Popular Suggestions
                        </div>
                        {filteredPopular.map((s) => (
                          <button
                            key={s.name}
                            type="button"
                            onClick={() => handleSelectSuggestion(s.name, s.category)}
                            className="w-full text-left flex items-center justify-between px-2 py-1.5 rounded hover:bg-muted text-xs cursor-pointer"
                          >
                            <span className="font-medium text-foreground">{s.name}</span>
                            <span className="text-[10px] text-muted-foreground bg-muted/60 px-1.5 py-0.5 rounded">
                              {s.category}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Category */}
              <div className="sm:col-span-3">
                <Label className="text-xs text-muted-foreground mb-1 block">Category</Label>
                <Select value={categoryInput} onValueChange={setCategoryInput}>
                  <SelectTrigger className="text-xs h-9">
                    <SelectValue placeholder="Category" />
                  </SelectTrigger>
                  <SelectContent>
                    {SKILL_CATEGORIES.map((cat) => (
                      <SelectItem key={cat} value={cat} className="text-xs">
                        {cat}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Level */}
              <div className="sm:col-span-2">
                <Label className="text-xs text-muted-foreground mb-1 block">Level</Label>
                <Select value={levelInput} onValueChange={setLevelInput}>
                  <SelectTrigger className="text-xs h-9">
                    <SelectValue placeholder="Level" />
                  </SelectTrigger>
                  <SelectContent>
                    {SKILL_LEVELS.map((lvl) => (
                      <SelectItem key={lvl.value} value={lvl.value} className="text-xs">
                        {lvl.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Add Button */}
              <div className="sm:col-span-2">
                <Button
                  type="button"
                  onClick={handleAddSkill}
                  size="sm"
                  className="w-full h-9 gap-1.5 text-xs font-semibold"
                >
                  <Plus size={14} /> Add
                </Button>
              </div>
            </div>

            {duplicateError && (
              <div className="flex items-center gap-1.5 text-xs text-destructive bg-destructive/10 border border-destructive/20 p-2 rounded-md">
                <AlertCircle size={14} className="shrink-0" />
                <span>{duplicateError}</span>
              </div>
            )}
          </div>

          {/* Current Skills List (CRUD & Reorder) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                Your Skills List
              </span>
              <span className="text-xs text-muted-foreground">
                Reorder using arrows
              </span>
            </div>

            {skills.length === 0 ? (
              <div className="p-8 text-center rounded-xl border border-dashed border-border bg-card">
                <Award className="mx-auto h-8 w-8 text-muted-foreground/50 mb-2" />
                <p className="text-sm font-medium text-foreground">No skills added yet</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Type a skill name above and click "Add" to start building your skill matrix.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {skills.map((skill, index) => {
                  const levelObj =
                    SKILL_LEVELS.find(
                      (l) => l.value.toLowerCase() === (skill.level || "").toLowerCase(),
                    ) || SKILL_LEVELS[1];

                  return (
                    <div
                      key={`${skill.name}-${index}`}
                      className="group flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg border border-border bg-card hover:border-primary/40 transition-all shadow-xs"
                    >
                      {/* Skill info & Reorder Buttons */}
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        {/* Reorder Buttons */}
                        <div className="flex flex-col gap-0.5 shrink-0">
                          <button
                            type="button"
                            onClick={() => handleMoveUp(index)}
                            disabled={index === 0}
                            className="p-1 rounded text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-30 disabled:hover:bg-transparent cursor-pointer"
                            title="Move Up"
                          >
                            <ArrowUp size={12} />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleMoveDown(index)}
                            disabled={index === skills.length - 1}
                            className="p-1 rounded text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-30 disabled:hover:bg-transparent cursor-pointer"
                            title="Move Down"
                          >
                            <ArrowDown size={12} />
                          </button>
                        </div>

                        {/* Name and Category badge */}
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-semibold text-sm text-foreground">
                              {skill.name}
                            </span>
                            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border">
                              {skill.category || "Languages"}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Controls: Level Selector, Years, and Delete */}
                      <div className="flex items-center gap-2 shrink-0">
                        {/* Inline Category Change */}
                        <Select
                          value={skill.category || "Languages"}
                          onValueChange={(val) => handleUpdateSkillField(index, "category", val)}
                        >
                          <SelectTrigger className="h-8 text-xs w-28">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {SKILL_CATEGORIES.map((cat) => (
                              <SelectItem key={cat} value={cat} className="text-xs">
                                {cat}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        {/* Inline Level Change */}
                        <Select
                          value={skill.level || "Intermediate"}
                          onValueChange={(val) => handleUpdateSkillField(index, "level", val)}
                        >
                          <SelectTrigger className={cn("h-8 text-xs w-28 font-medium", levelObj.color)}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {SKILL_LEVELS.map((lvl) => (
                              <SelectItem key={lvl.value} value={lvl.value} className="text-xs">
                                {lvl.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        {/* Remove Button */}
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveSkill(index)}
                          className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                          title="Delete skill"
                        >
                          <Trash2 size={14} />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Footer actions */}
        <div className="pt-3 border-t border-border flex items-center justify-between gap-3">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
            disabled={saveMutation.isPending}
          >
            Cancel
          </Button>

          <Button
            type="button"
            size="sm"
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending}
            className="gap-2 font-semibold"
          >
            {saveMutation.isPending ? (
              <>
                <Loader2 size={14} className="animate-spin" /> Saving...
              </>
            ) : (
              <>
                <Check size={14} /> Save Changes
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
export default ManageSkillsModal;
