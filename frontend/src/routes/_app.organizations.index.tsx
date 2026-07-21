import { createFileRoute, Link } from '@tanstack/react-router';

export const Route = createFileRoute('/_app/organizations/')({
  component: OrganizationsListPage,
});

function OrganizationsListPage() {
  const mockOrgs = [
    {
      id: 'devlink-org',
      name: 'DevLink',
      description: 'The developer portfolio & project collaboration network.',
      hiring: true,
      members_count: 12,
      projects_count: 5,
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Organizations</h1>
          <p className="text-gray-400 mt-1">
            Discover startups, open-source orgs, and teams building awesome products.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {mockOrgs.map((org) => (
          <Link
            key={org.id}
            to="/organizations/$orgId"
            params={{ orgId: org.id }}
            className="block p-6 rounded-xl border border-gray-800 bg-gray-900/40 hover:border-indigo-500/50 hover:bg-gray-800/40 transition-all cursor-pointer"
          >
            <div className="flex justify-between items-start mb-3">
              <h2 className="text-xl font-semibold text-white hover:text-indigo-400 transition-colors">
                {org.name}
              </h2>
              {org.hiring && (
                <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  Hiring
                </span>
              )}
            </div>
            <p className="text-gray-300 text-sm mb-4">{org.description}</p>
            <div className="flex gap-4 text-xs text-gray-400">
              <span>{org.members_count} Members</span>
              <span>•</span>
              <span>{org.projects_count} Projects</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
