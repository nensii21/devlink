import React, { useState } from "react";
import { OrganizationHeader } from "./OrganizationHeader";
import { OrganizationApiTokens } from "./OrganizationApiTokens";
import { OrganizationAuditLogs } from "./OrganizationAuditLogs";
import { OrganizationMembers } from "./OrganizationMembers";
import { TypoHeading } from "@/components/shared/Typography";

interface OrganizationProfileProps {
  organizationData: {
    name: string;
    logo_url?: string;
    banner_url?: string;
    location?: string;
    website?: string;
    description?: string;
    hiring: boolean;
    technologies?: string[];
    socialLinks?: {
      twitter?: string;
      linkedin?: string;
      github?: string;
    };
    activityFeed?: {
      id: string;
      type: string;
      content: string;
      date: string;
    }[];
  };
  orgId: string;
}

export const OrganizationProfile: React.FC<OrganizationProfileProps> = ({
  organizationData,
  orgId,
}) => {
  const [activeTab, setActiveTab] = useState<
    "about" | "members" | "team" | "projects" | "hiring" | "tokens" | "audit" | "activity"
  >("about");

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <OrganizationHeader
        name={organizationData.name}
        logoUrl={organizationData.logo_url}
        bannerUrl={organizationData.banner_url}
        location={organizationData.location}
        website={organizationData.website}
        isHiring={organizationData.hiring}
        socialLinks={organizationData.socialLinks}
      />

      {/* Tabs */}
      <div className="mb-6 flex gap-6 overflow-x-auto border-b border-border">
        {(
          ["about", "members", "team", "projects", "hiring", "tokens", "audit", "activity"] as const
        ).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 text-sm font-medium capitalize border-b-2 transition-colors shrink-0 ${
              activeTab === tab
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab === "tokens"
              ? "API Tokens"
              : tab === "audit"
                ? "Audit Logs"
                : tab === "activity"
                  ? "Activity Feed"
                  : tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="rounded-xl border border-border bg-card p-6">
        {activeTab === "about" && (
          <div>
            <TypoHeading as="h2">About Us</TypoHeading>
            <p className="mb-6 leading-relaxed text-foreground">
              {organizationData.description || "No description provided."}
            </p>
            {organizationData.technologies && organizationData.technologies.length > 0 && (
              <div className="mt-6">
                <TypoHeading as="h3" className="mb-3 text-sm font-semibold text-muted-foreground">
                  Technologies We Use
                </TypoHeading>
                <div className="flex flex-wrap gap-2">
                  {organizationData.technologies.map((tech) => (
                    <span
                      key={tech}
                      className="rounded-full border border-border bg-muted px-3 py-1 text-xs text-muted-foreground"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "members" && <OrganizationMembers orgId={orgId} />}

        {activeTab === "team" && (
          <div>
            <TypoHeading as="h2">Team Members</TypoHeading>
            <p className="text-sm text-muted-foreground">
              Showing team members connected to {organizationData.name}.
            </p>
          </div>
        )}

        {activeTab === "projects" && (
          <div>
            <TypoHeading as="h2">Projects</TypoHeading>
            <p className="text-sm text-muted-foreground">
              Projects built or maintained by {organizationData.name}.
            </p>
          </div>
        )}

        {activeTab === "hiring" && (
          <div>
            <TypoHeading as="h2">Open Roles</TypoHeading>
            {organizationData.hiring ? (
              <p className="text-sm text-foreground">
                We are actively recruiting talent! Apply below.
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">We are not actively hiring right now.</p>
            )}
          </div>
        )}

        {activeTab === "tokens" && <OrganizationApiTokens orgId={orgId} />}

        {activeTab === "audit" && <OrganizationAuditLogs orgId={orgId} />}

        {activeTab === "activity" && (
          <div>
            <TypoHeading as="h2">Activity Feed</TypoHeading>
            <div className="mt-6 space-y-4">
              {organizationData.activityFeed && organizationData.activityFeed.length > 0 ? (
                organizationData.activityFeed.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex flex-col gap-1 rounded-lg border border-border bg-muted/50 p-4"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-indigo-400 capitalize">
                        {activity.type}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(activity.date).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-sm text-foreground">{activity.content}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No recent activity found.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
