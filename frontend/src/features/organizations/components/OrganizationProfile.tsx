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
  };
  orgId: string;
}

export const OrganizationProfile: React.FC<OrganizationProfileProps> = ({
  organizationData,
  orgId,
}) => {
  const [activeTab, setActiveTab] = useState<
    "about" | "members" | "team" | "projects" | "hiring" | "tokens" | "audit"
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
      />

      {/* Tabs */}
      <div className="flex border-b border-gray-800 mb-6 gap-6 overflow-x-auto">
        {(["about", "members", "team", "projects", "hiring", "tokens", "audit"] as const).map(
          (tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 text-sm font-medium capitalize border-b-2 transition-colors shrink-0 ${
                activeTab === tab
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              {tab === "tokens" ? "API Tokens" : tab === "audit" ? "Audit Logs" : tab}
            </button>
          ),
        )}
      </div>

      {/* Tab Content */}
      <div className="bg-gray-900/30 border border-gray-800 rounded-xl p-6">
        {activeTab === "about" && (
          <div>
            <TypoHeading as="h2">About Us</TypoHeading>
            <p className="text-gray-300 leading-relaxed">
              {organizationData.description || "No description provided."}
            </p>
          </div>
        )}

        {activeTab === "members" && <OrganizationMembers orgId={orgId} />}

        {activeTab === "team" && (
          <div>
            <TypoHeading as="h2">Team Members</TypoHeading>
            <p className="text-gray-400 text-sm">
              Showing team members connected to {organizationData.name}.
            </p>
          </div>
        )}

        {activeTab === "projects" && (
          <div>
            <TypoHeading as="h2">Projects</TypoHeading>
            <p className="text-gray-400 text-sm">
              Projects built or maintained by {organizationData.name}.
            </p>
          </div>
        )}

        {activeTab === "hiring" && (
          <div>
            <TypoHeading as="h2">Open Roles</TypoHeading>
            {organizationData.hiring ? (
              <p className="text-gray-300 text-sm">
                We are actively recruiting talent! Apply below.
              </p>
            ) : (
              <p className="text-gray-400 text-sm">We are not actively hiring right now.</p>
            )}
          </div>
        )}

        {activeTab === "tokens" && <OrganizationApiTokens orgId={orgId} />}

        {activeTab === "audit" && <OrganizationAuditLogs orgId={orgId} />}
      </div>
    </div>
  );
};
