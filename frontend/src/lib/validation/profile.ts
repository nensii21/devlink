export interface ProfileValidationErrors {
  [key: string]: string;
}

export function isValidUrl(value?: string | null): boolean {
  if (!value) return true;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export function isValidHeadlineLength(value?: string | null): boolean {
  return (value ?? "").trim().length <= 150;
}

export function isValidBioLength(value?: string | null): boolean {
  return (value ?? "").length <= 1000;
}

export function validateProfileUrls(values: {
  website?: string | null;
  portfolioUrl?: string | null;
  githubUrl?: string | null;
  linkedinUrl?: string | null;
}): ProfileValidationErrors {
  const errors: ProfileValidationErrors = {};

  if (values.website && !isValidUrl(values.website)) {
    errors.website = "Please enter a valid URL.";
  }
  if (values.portfolioUrl && !isValidUrl(values.portfolioUrl)) {
    errors.portfolioUrl = "Please enter a valid URL.";
  }
  if (values.githubUrl && !isValidUrl(values.githubUrl)) {
    errors.githubUrl = "Please enter a valid URL.";
  }
  if (values.linkedinUrl && !isValidUrl(values.linkedinUrl)) {
    errors.linkedinUrl = "Please enter a valid URL.";
  }

  return errors;
}

export function validateHeadline(value?: string | null): string | undefined {
  if (!isValidHeadlineLength(value)) {
    return "Headline cannot exceed 150 characters.";
  }
  return undefined;
}

export function validateBio(value?: string | null): string | undefined {
  if (!isValidBioLength(value)) {
    return "Bio cannot exceed 1000 characters.";
  }
  return undefined;
}

export function validateSkillEntry(name: string, level: string, existingSkills: Array<{ name: string }>, currentName?: string): string | undefined {
  const normalizedName = name.trim().toLowerCase();
  const hasDuplicate = existingSkills.some((skill) => skill.name.trim().toLowerCase() === normalizedName && skill.name.trim().toLowerCase() !== (currentName ?? "").trim().toLowerCase());

  if (!name.trim()) {
    return "Skill name is required.";
  }
  if (!level) {
    return "Please select a skill level.";
  }
  if (hasDuplicate) {
    return "Skill already exists in your list.";
  }
  return undefined;
}

export function validateSkillList(skills: Array<{ name: string }>): string | undefined {
  if (skills.length === 0) {
    return undefined;
  }

  const seen = new Set<string>();
  for (const skill of skills) {
    const normalized = skill.name.trim().toLowerCase();
    if (!normalized) {
      return "Each skill needs a name.";
    }
    if (seen.has(normalized)) {
      return "Duplicate skill entries are not allowed.";
    }
    seen.add(normalized);
  }

  return undefined;
}
