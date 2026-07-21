import { createFileRoute } from '@tanstack/react-router';
import { OrganizationProfile } from '../features/organizations/components/OrganizationProfile';

export const Route = createFileRoute('/_app/organizations/$orgId')({
  component: OrganizationProfilePage,
});

function OrganizationProfilePage() {
  const { orgId } = Route.useParams();

  const mockOrgData = {
    name: 'DevLink',
    logo_url: '',
    banner_url: '',
    location: 'Remote',
    website: 'https://github.com/nensii21/devlink',
    description: 'The developer portfolio & project collaboration network.',
    hiring: true,
  };

  return <OrganizationProfile organizationData={mockOrgData} />;
}