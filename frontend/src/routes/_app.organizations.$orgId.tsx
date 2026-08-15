import { createFileRoute } from "@tanstack/react-router";
import { OrganizationProfile } from "../features/organizations/components/OrganizationProfile";

export const Route = createFileRoute("/_app/organizations/$orgId")({
  component: OrganizationProfilePage,
});

function OrganizationProfilePage() {
  const { orgId } = Route.useParams();

  const mockOrgData = {
    name: "DevLink",
    logo_url: "",
    banner_url: "",
    location: "Remote",
    website: "https://github.com/nensii21/devlink",
    description: "The developer portfolio & project collaboration network.",
    hiring: true,
    technologies: ["React", "TypeScript", "Node.js", "PostgreSQL"],
    socialLinks: {
      twitter: "https://twitter.com/devlink",
      github: "https://github.com/nensii21/devlink",
      linkedin: "https://linkedin.com/company/devlink",
    },
    activityFeed: [
      {
        id: "1",
        type: "update",
        content: "We just released version 2.0 of DevLink! Check out the new features.",
        date: "2026-08-10T10:00:00Z",
      },
      {
        id: "2",
        type: "milestone",
        content: "Reached 10,000 active developers on our platform.",
        date: "2026-08-01T14:30:00Z",
      },
    ],
  };

  return <OrganizationProfile organizationData={mockOrgData} orgId={orgId} />;
}
