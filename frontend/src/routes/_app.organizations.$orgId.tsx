import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { OrganizationProfile } from "../features/organizations/components/OrganizationProfile";
import { organizationsApi } from "../api/modules/organizations";

export const Route = createFileRoute("/_app/organizations/$orgId")({
  component: OrganizationProfilePage,
});

const FALLBACK_ORG_DATA = {
  name: "DevLink",
  logo_url: "",
  banner_url: "",
  location: "Remote",
  website: "https://github.com/nensii21/devlink",
  description: "The developer portfolio & project collaboration network.",
  hiring: true,
};

function OrganizationProfilePage() {
  const { orgId } = Route.useParams();

  const { data: org, isLoading } = useQuery({
    queryKey: ["organizations", orgId],
    queryFn: () => organizationsApi.get(orgId),
    retry: false,
  });

  if (isLoading) {
    return <div className="max-w-6xl mx-auto px-4 py-8 text-gray-400">Loading organization...</div>;
  }

  const organizationData = org
    ? {
        name: org.name,
        logo_url: org.logo_url ?? "",
        banner_url: org.banner_url ?? "",
        location: org.location ?? undefined,
        website: org.website ?? undefined,
        description: org.description ?? undefined,
        hiring: org.hiring,
      }
    : FALLBACK_ORG_DATA;

  return <OrganizationProfile organizationData={organizationData} orgId={orgId} />;
}
