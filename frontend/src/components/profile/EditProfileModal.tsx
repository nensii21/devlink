import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, User, Plus, X } from "lucide-react";

import { usersApi, type UserProfileUpdateData } from "@/api/modules/users";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface EditProfileModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialData: {
    firstName: string;
    lastName: string;
    username: string;
    headline?: string;
    bio?: string;
    location?: string;
    website?: string;
    profileImage?: string;
    githubUrl?: string;
    linkedinUrl?: string;
    twitterUrl?: string;
    portfolioUrl?: string;
    role?: string;
    experienceLevel?: string;
    company?: string;
    skills?: string[];
  };
  onSuccess?: (updatedData: any) => void;
}

export function EditProfileModal({
  open,
  onOpenChange,
  initialData,
  onSuccess,
}: EditProfileModalProps) {
  const queryClient = useQueryClient();

  const [firstName, setFirstName] = useState(initialData.firstName || "");
  const [lastName, setLastName] = useState(initialData.lastName || "");
  const [username, setUsername] = useState(initialData.username || "");
  const [headline, setHeadline] = useState(initialData.headline || "");
  const [bio, setBio] = useState(initialData.bio || "");
  const [location, setLocation] = useState(initialData.location || "");
  const [website, setWebsite] = useState(initialData.website || "");
  const [profileImage, setProfileImage] = useState(initialData.profileImage || "");
  const [githubUrl, setGithubUrl] = useState(initialData.githubUrl || "");
  const [linkedinUrl, setLinkedinUrl] = useState(initialData.linkedinUrl || "");
  const [twitterUrl, setTwitterUrl] = useState(initialData.twitterUrl || "");
  const [portfolioUrl, setPortfolioUrl] = useState(initialData.portfolioUrl || "");
  const [role, setRole] = useState(initialData.role || "");
  const [experienceLevel, setExperienceLevel] = useState(initialData.experienceLevel || "Intermediate");
  const [company, setCompany] = useState(initialData.company || "");
  const [skills, setSkills] = useState<string[]>(initialData.skills || []);
  const [newSkillInput, setNewSkillInput] = useState("");

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (open) {
      setFirstName(initialData.firstName || "");
      setLastName(initialData.lastName || "");
      setUsername(initialData.username || "");
      setHeadline(initialData.headline || "");
      setBio(initialData.bio || "");
      setLocation(initialData.location || "");
      setWebsite(initialData.website || "");
      setProfileImage(initialData.profileImage || "");
      setGithubUrl(initialData.githubUrl || "");
      setLinkedinUrl(initialData.linkedinUrl || "");
      setTwitterUrl(initialData.twitterUrl || "");
      setPortfolioUrl(initialData.portfolioUrl || "");
      setRole(initialData.role || "");
      setExperienceLevel(initialData.experienceLevel || "Intermediate");
      setCompany(initialData.company || "");
      setSkills(initialData.skills || []);
      setValidationErrors({});
    }
  }, [open, initialData]);

  const handleAddSkill = () => {
    const trimmed = newSkillInput.trim();
    if (trimmed && !skills.includes(trimmed)) {
      setSkills([...skills, trimmed]);
      setNewSkillInput("");
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setSkills(skills.filter((s) => s !== skillToRemove));
  };

  const validate = (): boolean => {
    const errors: Record<string, string> = {};

    if (!firstName.trim()) errors.firstName = "First name is required";
    if (!lastName.trim()) errors.lastName = "Last name is required";
    if (!username.trim()) {
      errors.username = "Username is required";
    } else if (username.length < 3) {
      errors.username = "Username must be at least 3 characters";
    } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      errors.username = "Username can only contain letters, numbers, and underscores";
    }

    const isValidUrl = (url: string) => {
      if (!url) return true;
      try {
        new URL(url.startsWith("http") ? url : `https://${url}`);
        return true;
      } catch {
        return false;
      }
    };

    if (website && !isValidUrl(website)) errors.website = "Enter a valid website URL";
    if (githubUrl && !isValidUrl(githubUrl)) errors.githubUrl = "Enter a valid GitHub URL";
    if (linkedinUrl && !isValidUrl(linkedinUrl)) errors.linkedinUrl = "Enter a valid LinkedIn URL";
    if (twitterUrl && !isValidUrl(twitterUrl)) errors.twitterUrl = "Enter a valid Twitter/X URL";
    if (portfolioUrl && !isValidUrl(portfolioUrl)) errors.portfolioUrl = "Enter a valid Portfolio URL";

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const updateMutation = useMutation({
    mutationFn: async () => {
      const formatUrl = (url: string) => {
        if (!url) return undefined;
        return url.startsWith("http") ? url : `https://${url}`;
      };

      const payload: UserProfileUpdateData = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        username: username.trim(),
        headline: headline.trim() || undefined,
        bio: bio.trim() || undefined,
        location: location.trim() || undefined,
        website: formatUrl(website.trim()),
        profile_image: formatUrl(profileImage.trim()),
        github_url: formatUrl(githubUrl.trim()),
        linkedin_url: formatUrl(linkedinUrl.trim()),
        twitter_url: formatUrl(twitterUrl.trim()),
        portfolio_url: formatUrl(portfolioUrl.trim()),
        role: role.trim() || undefined,
        experience_level: experienceLevel || undefined,
        company: company.trim() || undefined,
        skills,
      };

      return await usersApi.updateProfile(payload);
    },
    onSuccess: (updated) => {
      toast.success("Profile updated successfully!");
      queryClient.invalidateQueries({ queryKey: ["user"] });
      queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      onOpenChange(false);
      if (onSuccess) {
        const updateObj = typeof updated === "object" && updated !== null ? updated : {};
        onSuccess({ ...updateObj, firstName, lastName, username, bio, location, role, skills });
      }
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || err?.message || "Failed to update profile";
      toast.error(detail);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      updateMutation.mutate();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <User className="h-5 w-5 text-primary" />
            Edit Profile Information
          </DialogTitle>
          <DialogDescription>
            Update your public profile information, bio, skills, and social links.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          <Tabs defaultValue="basic" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="basic" className="text-xs">
                Basic Info
              </TabsTrigger>
              <TabsTrigger value="details" className="text-xs">
                Bio & Role
              </TabsTrigger>
              <TabsTrigger value="skills" className="text-xs">
                Skills
              </TabsTrigger>
              <TabsTrigger value="social" className="text-xs">
                Social Links
              </TabsTrigger>
            </TabsList>

            {/* TAB 1: BASIC INFO */}
            <TabsContent value="basic" className="space-y-4 pt-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="first-name">First Name *</Label>
                  <Input
                    id="first-name"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="e.g. Jane"
                  />
                  {validationErrors.firstName && (
                    <p className="text-xs text-destructive">{validationErrors.firstName}</p>
                  )}
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="last-name">Last Name *</Label>
                  <Input
                    id="last-name"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder="e.g. Doe"
                  />
                  {validationErrors.lastName && (
                    <p className="text-xs text-destructive">{validationErrors.lastName}</p>
                  )}
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="edit-username">Username Handle *</Label>
                <Input
                  id="edit-username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. janedoe"
                />
                {validationErrors.username && (
                  <p className="text-xs text-destructive">{validationErrors.username}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="profile-image-url">Profile Picture URL</Label>
                <Input
                  id="profile-image-url"
                  value={profileImage}
                  onChange={(e) => setProfileImage(e.target.value)}
                  placeholder="https://example.com/avatar.jpg"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="headline">Headline / One-liner</Label>
                <Input
                  id="headline"
                  value={headline}
                  onChange={(e) => setHeadline(e.target.value)}
                  placeholder="e.g. Senior Full-Stack Engineer @ DevLink"
                />
              </div>
            </TabsContent>

            {/* TAB 2: BIO & ROLE */}
            <TabsContent value="details" className="space-y-4 pt-4">
              <div className="space-y-1.5">
                <Label htmlFor="bio">Bio</Label>
                <Textarea
                  id="bio"
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  rows={4}
                  placeholder="Tell the DevLink community about your journey, interests, and accomplishments..."
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="role">Current Role / Title</Label>
                  <Input
                    id="role"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    placeholder="e.g. Frontend Developer"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="company">Company / Organization</Label>
                  <Input
                    id="company"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    placeholder="e.g. Acme Corp"
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="e.g. San Francisco, CA"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="experience-level">Experience Level</Label>
                  <select
                    id="experience-level"
                    value={experienceLevel}
                    onChange={(e) => setExperienceLevel(e.target.value)}
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:ring-primary focus:border-primary"
                  >
                    <option value="Beginner">Beginner (0-1 yrs)</option>
                    <option value="Junior">Junior (1-3 yrs)</option>
                    <option value="Intermediate">Intermediate (3-5 yrs)</option>
                    <option value="Senior">Senior (5+ yrs)</option>
                    <option value="Lead">Lead / Staff</option>
                  </select>
                </div>
              </div>
            </TabsContent>

            {/* TAB 3: SKILLS */}
            <TabsContent value="skills" className="space-y-4 pt-4">
              <div className="space-y-1.5">
                <Label>Skills & Tech Stack</Label>
                <div className="flex gap-2">
                  <Input
                    value={newSkillInput}
                    onChange={(e) => {
                      setNewSkillInput(e.target.value);
                      if (validationErrors.skills) {
                        setValidationErrors((prev) => {
                          const next = { ...prev };
                          delete next.skills;
                          return next;
                        });
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        const trimmed = newSkillInput.trim();
                        if (!trimmed) return;
                        if (skills.some((s) => s.toLowerCase() === trimmed.toLowerCase())) {
                          setValidationErrors((prev) => ({
                            ...prev,
                            skills: `"${trimmed}" is already in your skills list.`,
                          }));
                          return;
                        }
                        setSkills([...skills, trimmed]);
                        setNewSkillInput("");
                      }
                    }}
                    placeholder="Add a skill (e.g. React, Python, Docker)"
                  />
                  <Button
                    type="button"
                    onClick={() => {
                      const trimmed = newSkillInput.trim();
                      if (!trimmed) return;
                      if (skills.some((s) => s.toLowerCase() === trimmed.toLowerCase())) {
                        setValidationErrors((prev) => ({
                          ...prev,
                          skills: `"${trimmed}" is already in your skills list.`,
                        }));
                        return;
                      }
                      setSkills([...skills, trimmed]);
                      setNewSkillInput("");
                    }}
                    variant="secondary"
                  >
                    <Plus className="h-4 w-4 mr-1" /> Add
                  </Button>
                </div>
                {validationErrors.skills && (
                  <p className="text-xs text-destructive mt-1">{validationErrors.skills}</p>
                )}
              </div>

              <div className="space-y-2 pt-2 max-h-60 overflow-y-auto">
                {skills.length === 0 ? (
                  <p className="text-xs text-muted-foreground italic">No skills added yet.</p>
                ) : (
                  skills.map((skill, index) => (
                    <div
                      key={`${skill}-${index}`}
                      className="flex items-center justify-between gap-2 p-2 rounded-md bg-muted/40 border border-border text-xs"
                    >
                      <span className="font-medium text-foreground">{skill}</span>
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => {
                            if (index === 0) return;
                            const next = [...skills];
                            const temp = next[index - 1];
                            next[index - 1] = next[index];
                            next[index] = temp;
                            setSkills(next);
                          }}
                          disabled={index === 0}
                          className="p-1 rounded text-muted-foreground hover:bg-muted disabled:opacity-30 cursor-pointer"
                          title="Move Up"
                        >
                          ↑
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            if (index === skills.length - 1) return;
                            const next = [...skills];
                            const temp = next[index + 1];
                            next[index + 1] = next[index];
                            next[index] = temp;
                            setSkills(next);
                          }}
                          disabled={index === skills.length - 1}
                          className="p-1 rounded text-muted-foreground hover:bg-muted disabled:opacity-30 cursor-pointer"
                          title="Move Down"
                        >
                          ↓
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemoveSkill(skill)}
                          className="p-1 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 cursor-pointer ml-1"
                          title="Remove"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </TabsContent>

            {/* TAB 4: SOCIAL LINKS */}
            <TabsContent value="social" className="space-y-4 pt-4">
              <div className="space-y-1.5">
                <Label htmlFor="website-url">Personal Website</Label>
                <Input
                  id="website-url"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  placeholder="https://yourwebsite.com"
                />
                {validationErrors.website && (
                  <p className="text-xs text-destructive">{validationErrors.website}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="github-url">GitHub URL</Label>
                <Input
                  id="github-url"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/username"
                />
                {validationErrors.githubUrl && (
                  <p className="text-xs text-destructive">{validationErrors.githubUrl}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="linkedin-url">LinkedIn URL</Label>
                <Input
                  id="linkedin-url"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  placeholder="https://linkedin.com/in/username"
                />
                {validationErrors.linkedinUrl && (
                  <p className="text-xs text-destructive">{validationErrors.linkedinUrl}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="twitter-url">Twitter / X URL</Label>
                <Input
                  id="twitter-url"
                  value={twitterUrl}
                  onChange={(e) => setTwitterUrl(e.target.value)}
                  placeholder="https://x.com/username"
                />
                {validationErrors.twitterUrl && (
                  <p className="text-xs text-destructive">{validationErrors.twitterUrl}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="portfolio-url">Portfolio URL</Label>
                <Input
                  id="portfolio-url"
                  value={portfolioUrl}
                  onChange={(e) => setPortfolioUrl(e.target.value)}
                  placeholder="https://portfolio.dev"
                />
                {validationErrors.portfolioUrl && (
                  <p className="text-xs text-destructive">{validationErrors.portfolioUrl}</p>
                )}
              </div>
            </TabsContent>
          </Tabs>

          <DialogFooter className="pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving Changes...
                </>
              ) : (
                "Save Profile"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
