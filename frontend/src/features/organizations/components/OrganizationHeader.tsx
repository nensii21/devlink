import { TypoHeading } from "@/components/shared/Typography";
import React from "react";
import { Twitter, Linkedin, Github } from "lucide-react";
import { sanitizeUrl } from "@/lib/utils";

interface OrganizationHeaderProps {
  name: string;
  logoUrl?: string;
  bannerUrl?: string;
  location?: string;
  website?: string;
  isHiring: boolean;
  isVerified?: boolean;
  onVerifyClick?: () => void;
  socialLinks?: {
    twitter?: string;
    linkedin?: string;
    github?: string;
  };
}

export const OrganizationHeader: React.FC<OrganizationHeaderProps> = ({
  name,
  logoUrl,
  bannerUrl,
  location,
  website,
  isHiring,
  isVerified = false,
  onVerifyClick,
  socialLinks,
}) => {
  return (
    <div className="relative mb-6 overflow-hidden rounded-xl border border-border bg-card">
      {/* Banner */}
      <div className="relative h-32 w-full bg-gradient-to-r from-primary/40 to-primary/10 sm:h-48">
        {bannerUrl && (
          <img src={bannerUrl} alt={`${name} banner`} className="w-full h-full object-cover" />
        )}
      </div>

      {/* Profile Details Bar */}
      <div className="p-6 pt-0 relative flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4">
        <div className="flex items-end gap-4 -mt-12 sm:-mt-16">
          {/* Logo */}
          <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-xl border-4 border-card bg-muted text-2xl font-bold text-foreground shadow-lg sm:h-32 sm:w-32">
            {logoUrl ? (
              <img src={logoUrl} alt={`${name} logo`} className="w-full h-full object-cover" />
            ) : (
              name.slice(0, 2).toUpperCase()
            )}
          </div>

          <div className="mb-2">
            <TypoHeading as="h1">
              {name}
              {isVerified && (
                <span
                  title="Verified Organization"
                  className="inline-flex items-center justify-center w-5 h-5 bg-blue-500 text-white rounded-full text-xs shadow-sm"
                >
                  ✓
                </span>
              )}
              {isHiring && (
                <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  Hiring
                </span>
              )}
            </TypoHeading>
            {location && <p className="text-sm text-muted-foreground">{location}</p>}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {!isVerified && onVerifyClick && (
            <button
              onClick={onVerifyClick}
              type="button"
              className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
            >
              Apply for Verification
            </button>
          )}

          {socialLinks?.twitter && sanitizeUrl(socialLinks.twitter) && (
 feature/account-deactivation-1306
            <a
              href={socialLinks.twitter}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-muted-foreground transition-colors hover:text-foreground"
            >
              <Twitter className="w-5 h-5" />
            </a>
          )}
          {socialLinks?.github && sanitizeUrl(socialLinks.github) && (
            <a
              href={socialLinks.github}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-muted-foreground transition-colors hover:text-foreground"
            >
              <Github className="w-5 h-5" />
            </a>
          )}
          {socialLinks?.linkedin && sanitizeUrl(socialLinks.linkedin) && (
            <a
              href={socialLinks.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-muted-foreground transition-colors hover:text-foreground"
            >
              <Linkedin className="w-5 h-5" />
            </a>
          )}

          {website && (

 main
            <a
              href={sanitizeUrl(socialLinks.twitter)}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-muted-foreground transition-colors hover:text-foreground"
            >
              <Twitter className="w-5 h-5" />
            </a>
          )}
          {socialLinks?.github && sanitizeUrl(socialLinks.github) && (
            <a
              href={sanitizeUrl(socialLinks.github)}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-muted-foreground transition-colors hover:text-foreground"
            >
              <Github className="w-5 h-5" />
            </a>
          )}
          {socialLinks?.linkedin && sanitizeUrl(socialLinks.linkedin) && (
            <a
              href={sanitizeUrl(socialLinks.linkedin)}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-muted-foreground transition-colors hover:text-foreground"
            >
              <Linkedin className="w-5 h-5" />
            </a>
          )}

          {website && sanitizeUrl(website) && (
            <a
              href={sanitizeUrl(website)}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              Visit Website
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
