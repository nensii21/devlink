import { createFileRoute, notFound } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Card, Avatar } from "@/components/shared/primitives";
import { BioCard, SkillsCard, TechStackCard, ExperienceCard, EducationCard, SocialLinksCard, ResumeUploadCard } from "@/components/profile";
import { builders, currentUser, projects, type Builder, type ProfileSkill } from "@/mocks/seed";
import { MapPin, Calendar, Link as LinkIcon } from "lucide-react";
import { validateBio, validateHeadline, validateProfileUrls, validateSkillEntry, validateSkillList } from "@/lib/validation/profile";
import { updateCurrentUserProfile, type ProfilePayload } from "@/services/profile";

export const Route = createFileRoute("/_app/profile/$username")({
  head: ({ params }) => ({
    meta: [
      { title: `@${params.username} — DevLink` },
      { name: "description", content: `${params.username}'s DevLink profile: skills, projects and activity.` },
    ],
  }),
  component: ProfilePage,
});

type ProfileFormValues = {
  headline: string;
  bio: string;
  location: string;
  timezone: string;
  website: string;
  resumeUrl: string;
  portfolioUrl: string;
  githubUrl: string;
  linkedinUrl: string;
  role: string;
  experienceLevel: string;
  company: string;
  profileSkills: ProfileSkill[];
  techStack: string[];
};

function mapBuilderToFormValues(builder: Builder): ProfileFormValues {
  return {
    headline: builder.headline ?? "",
    bio: builder.bio ?? "",
    location: builder.location ?? "",
    timezone: builder.timezone ?? "",
    website: builder.website ?? "",
    resumeUrl: builder.resumeUrl ?? "",
    portfolioUrl: builder.portfolioUrl ?? "",
    githubUrl: builder.githubUrl ?? "",
    linkedinUrl: builder.linkedinUrl ?? "",
    role: builder.role ?? "",
    experienceLevel: builder.experienceLevel ?? "",
    company: builder.company ?? "",
    profileSkills:
      builder.profileSkills?.length
        ? builder.profileSkills.map((skill) => ({ ...skill, level: skill.level ?? "Intermediate", yearsOfExperience: skill.yearsOfExperience ?? 0 }))
        : builder.skills.map((skill) => ({ name: skill, level: "Intermediate", category: "general" })),
    techStack: builder.techStack ?? [],
  };
}

function buildUpdatedBuilder(builder: Builder, values: ProfileFormValues): Builder {
  return {
    ...builder,
    headline: values.headline || undefined,
    bio: values.bio || undefined,
    location: values.location || undefined,
    timezone: values.timezone || undefined,
    website: values.website || undefined,
    resumeUrl: values.resumeUrl || undefined,
    portfolioUrl: values.portfolioUrl || undefined,
    githubUrl: values.githubUrl || undefined,
    linkedinUrl: values.linkedinUrl || undefined,
    role: values.role || undefined,
    experienceLevel: values.experienceLevel || undefined,
    company: values.company || undefined,
    profileSkills: values.profileSkills.map((skill) => ({
      name: skill.name,
      level: skill.level || "Intermediate",
      category: skill.category || "general",
      yearsOfExperience: skill.yearsOfExperience ?? 0,
    })),
    techStack: values.techStack.filter(Boolean),
    skills: values.profileSkills.map((skill) => skill.name),
  };
}

function ProfilePage() {
  const { username } = Route.useParams();
  const me = username === currentUser.handle;
  const initialProfile = useMemo<Builder | null>(() => {
    if (me) {
      return {
        ...builders[0],
        id: currentUser.id,
        name: currentUser.name,
        handle: currentUser.handle,
        avatar: currentUser.avatar,
        bio: "Product engineer. Ships fast, sleeps sometimes.",
        role: "Full Stack Developer",
        headline: "Building dependable product experiences across the stack",
        location: "Bengaluru, India",
        timezone: "IST (UTC+5:30)",
        website: "https://devlink.io",
        resumeUrl: "",
        portfolioUrl: "https://devlink.io/portfolio",
        githubUrl: "https://github.com/devlink",
        linkedinUrl: "https://linkedin.com/company/devlink",
        experienceLevel: "Senior",
        company: "DevLink",
        profileSkills: [
          { name: "React", level: "Advanced", category: "frontend", yearsOfExperience: 4 },
          { name: "Next.js", level: "Advanced", category: "frontend", yearsOfExperience: 3 },
          { name: "TypeScript", level: "Expert", category: "frontend", yearsOfExperience: 5 },
          { name: "Node.js", level: "Intermediate", category: "backend", yearsOfExperience: 2 },
          { name: "Docker", level: "Intermediate", category: "devops", yearsOfExperience: 2 },
        ],
        techStack: ["React", "Next.js", "TypeScript", "Node.js", "Docker"],
        education: [{ school: "IIT Delhi", degree: "B.Tech in Computer Science", years: "2017–2021" }],
      };
    }
    return builders.find((x) => x.handle === username) ?? null;
  }, [me, username]);

  const [profile, setProfile] = useState<Builder | null>(initialProfile);
  const [isEditing, setIsEditing] = useState(false);
  const [formValues, setFormValues] = useState<ProfileFormValues>(() => mapBuilderToFormValues(initialProfile ?? builders[0]));
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setProfile(initialProfile);
    setFormValues(mapBuilderToFormValues(initialProfile ?? builders[0]));
  }, [initialProfile]);

  if (!profile) throw notFound();

  const isOwnProfile = currentUser.id === profile.id || username === currentUser.handle;

  const handleFieldChange = (field: keyof Pick<ProfileFormValues, "headline" | "bio" | "location" | "timezone" | "website" | "portfolioUrl" | "githubUrl" | "linkedinUrl" | "role" | "experienceLevel" | "company">, value: string) => {
    setFormValues((prev) => ({ ...prev, [field]: value }));
    setFormErrors((prev) => ({ ...prev, [field]: "" }));
  };

  const handleSkillChange = (index: number, field: "name" | "level" | "category" | "yearsOfExperience", value: string | number) => {
    setFormValues((prev) => ({
      ...prev,
      profileSkills: prev.profileSkills.map((skill, skillIndex) => (skillIndex === index ? { ...skill, [field]: value } : skill)),
    }));
    setFormErrors((prev) => ({ ...prev, [`skill-${index}`]: "" }));
  };

  const handleAddSkill = () => {
    setFormValues((prev) => ({
      ...prev,
      profileSkills: [...prev.profileSkills, { name: "", level: "Intermediate", category: "general", yearsOfExperience: 0 }],
    }));
  };

  const handleRemoveSkill = (index: number) => {
    setFormValues((prev) => ({
      ...prev,
      profileSkills: prev.profileSkills.filter((_, skillIndex) => skillIndex !== index),
    }));
  };

  const handleTechStackChange = (value: string) => {
    setFormValues((prev) => ({
      ...prev,
      techStack: value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    }));
  };

  const startEditing = () => {
    setIsEditing(true);
    setFormErrors({});
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setFormValues(mapBuilderToFormValues(profile));
    setFormErrors({});
  };

  const validateForm = () => {
    const nextErrors: Record<string, string> = {};
    const headlineError = validateHeadline(formValues.headline);
    const bioError = validateBio(formValues.bio);
    const urlErrors = validateProfileUrls({
      website: formValues.website,
      portfolioUrl: formValues.portfolioUrl,
      githubUrl: formValues.githubUrl,
      linkedinUrl: formValues.linkedinUrl,
    });

    if (headlineError) nextErrors.headline = headlineError;
    if (bioError) nextErrors.bio = bioError;
    Object.assign(nextErrors, urlErrors);

    const skillListError = validateSkillList(formValues.profileSkills);
    if (skillListError) nextErrors.skills = skillListError;

    formValues.profileSkills.forEach((skill, index) => {
      const skillError = validateSkillEntry(skill.name, skill.level ?? "", formValues.profileSkills.filter((_, skillIndex) => skillIndex !== index), skill.name);
      if (skillError) nextErrors[`skill-${index}`] = skillError;
    });

    setFormErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      toast.error("Please fix the highlighted fields before saving.");
      return;
    }

    setIsSaving(true);
    try {
      const payload: ProfilePayload = {
        headline: formValues.headline || null,
        bio: formValues.bio || null,
        location: formValues.location || null,
        timezone: formValues.timezone || null,
        website: formValues.website || null,
        portfolio_url: formValues.portfolioUrl || null,
        github_url: formValues.githubUrl || null,
        linkedin_url: formValues.linkedinUrl || null,
        role: formValues.role || null,
        experience_level: formValues.experienceLevel || null,
        company: formValues.company || null,
      };

      await updateCurrentUserProfile(payload);
      const updatedProfile = buildUpdatedBuilder(profile, formValues);
      setProfile(updatedProfile);
      setIsEditing(false);
      setFormErrors({});
      toast.success("Profile updated successfully.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to update profile right now.";
      setFormErrors((prev) => ({ ...prev, form: message }));
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div className="flex flex-wrap items-start gap-5">
            <Avatar src={profile.avatar} alt={profile.name} size={96} online={profile.online} />
            <div className="min-w-0 flex-1">
              <h1 className="text-[22px] font-bold text-foreground">{profile.name}</h1>
              <p className="text-[13px] text-muted-foreground">@{profile.handle} · {profile.role}</p>
              <p className="mt-2 text-[13px] text-foreground">{profile.bio}</p>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-[12px] text-muted-foreground">
                <span className="inline-flex items-center gap-1"><MapPin size={12} /> {profile.country}</span>
                <span className="inline-flex items-center gap-1"><Calendar size={12} /> Joined 2024</span>
                <span className="inline-flex items-center gap-1"><LinkIcon size={12} /> devlink.io/{profile.handle}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!me && (
              <button className="rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90">
                Follow
              </button>
            )}
            {isOwnProfile && (
              isEditing ? (
                <>
                  <button
                    type="button"
                    onClick={cancelEditing}
                    className="rounded-md border border-border bg-background px-3 py-2 text-[13px] font-semibold text-foreground hover:bg-muted"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleSave}
                    disabled={isSaving}
                    className="rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {isSaving ? "Saving..." : "Save"}
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={startEditing}
                  className="rounded-md border border-border bg-background px-3 py-2 text-[13px] font-semibold text-foreground hover:bg-muted"
                >
                  Edit Profile
                </button>
              )
            )}
          </div>
        </div>
      </Card>

      {formErrors.form ? <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">{formErrors.form}</p> : null}

      <div className="grid gap-4 xl:grid-cols-3">
        <BioCard
          headline={isEditing ? undefined : profile.headline}
          bio={isEditing ? undefined : profile.bio}
          location={isEditing ? undefined : profile.location}
          timezone={isEditing ? undefined : profile.timezone}
          editable={isEditing}
          formValues={formValues}
          errors={formErrors}
          onFieldChange={handleFieldChange}
        />
        <ExperienceCard
          role={isEditing ? undefined : profile.role}
          company={isEditing ? undefined : profile.company}
          experienceLevel={isEditing ? undefined : profile.experienceLevel}
          editable={isEditing}
          formValues={{ role: formValues.role, company: formValues.company, experienceLevel: formValues.experienceLevel }}
          errors={formErrors}
          onFieldChange={handleFieldChange}
        />
        <SkillsCard
          skills={isEditing ? [] : profile.profileSkills ?? []}
          editable={isEditing}
          formValues={formValues.profileSkills}
          skillErrors={Object.entries(formErrors).filter(([key]) => key.startsWith("skill-") || key === "skills").map(([, message]) => message)}
          onSkillChange={handleSkillChange}
          onAddSkill={handleAddSkill}
          onRemoveSkill={handleRemoveSkill}
        />
        <TechStackCard
          skills={isEditing ? [] : profile.profileSkills ?? []}
          techStack={isEditing ? undefined : profile.techStack}
          editable={isEditing}
          formValues={formValues.techStack}
          error={formErrors.techStack}
          onTechStackChange={handleTechStackChange}
        />
        <SocialLinksCard
          githubUrl={isEditing ? undefined : profile.githubUrl}
          linkedinUrl={isEditing ? undefined : profile.linkedinUrl}
          portfolioUrl={isEditing ? undefined : profile.portfolioUrl}
          website={isEditing ? undefined : profile.website}
          editable={isEditing}
          formValues={{
            githubUrl: formValues.githubUrl,
            linkedinUrl: formValues.linkedinUrl,
            portfolioUrl: formValues.portfolioUrl,
            website: formValues.website,
          }}
          errors={formErrors}
          onFieldChange={handleFieldChange}
        />
        <ResumeUploadCard resumeUrl={profile.resumeUrl} editable={isOwnProfile && isEditing} />
        <EducationCard education={profile.education ?? []} />
        <Card className="p-4 xl:col-span-3">
          <p className="text-[13px] font-semibold text-foreground">Projects</p>
          <ul className="mt-3 divide-y divide-border">
            {projects.slice(0, 4).map((p) => (
              <li key={p.id} className="flex items-center gap-3 py-2">
                <span className="grid h-8 w-8 place-items-center rounded-md bg-muted text-lg">{p.icon}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-semibold text-foreground">{p.name}</p>
                  <p className="truncate text-[11px] text-muted-foreground">{p.stack.join(" · ")}</p>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
