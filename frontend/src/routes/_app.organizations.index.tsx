import { useState, useMemo, useEffect } from "react";
import { TypoHeading } from "@/components/shared/Typography";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Search, Bookmark, Users, Briefcase, PlusCircle, Clock, CheckCircle2, ChevronRight } from "lucide-react";
import { useSavedSearches } from "@/stores/useSavedSearches";
import { SaveSearchDialog } from "@/components/shared/SaveSearchDialog";

export const Route = createFileRoute("/_app/organizations/")({
  validateSearch: (search: Record<string, unknown>): { q?: string } => ({
    q: typeof search.q === "string" ? search.q : undefined,
  }),
  component: OrganizationsListPage,
});

const mockOrgs = [
  {
    id: "devlink-org",
    name: "DevLink",
    description: "The developer portfolio & project collaboration network for modern creators.",
    logo: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=80&h=80&fit=crop&auto=format",
    verified: true,
    hiring: true,
    members_count: 12,
    projects_count: 5,
    open_roles_count: 3,
    recent_activity: "Launched DevLink v2 portfolio builder 2 days ago",
  },
  {
    id: "vercel",
    name: "Vercel",
    description: "Vercel provides the developer experience and infrastructure to build, deploy, and scale.",
    logo: "https://images.unsplash.com/photo-1618401471353-b98aedd07871?w=80&h=80&fit=crop&auto=format",
    verified: true,
    hiring: false,
    members_count: 145,
    projects_count: 32,
    open_roles_count: 0,
    recent_activity: "Released Next.js 15 with Turbopack updates yesterday",
  },
  {
    id: "supabase",
    name: "Supabase",
    description: "The open source Firebase alternative. Build production-grade backends in minutes.",
    logo: "https://images.unsplash.com/photo-1607799279861-4dd421887fb3?w=80&h=80&fit=crop&auto=format",
    verified: true,
    hiring: true,
    members_count: 68,
    projects_count: 15,
    open_roles_count: 5,
    recent_activity: "Shipped Supabase Vector v0.2 index upgrades last week",
  },
  {
    id: "linear",
    name: "Linear",
    description: "Linear helps teams manage software development, design, and product roadmaps.",
    logo: "https://images.unsplash.com/photo-1551434678-e076c223a692?w=80&h=80&fit=crop&auto=format",
    verified: true,
    hiring: false,
    members_count: 42,
    projects_count: 8,
    open_roles_count: 2,
    recent_activity: "Added custom status cycle tracking workflows 3 days ago",
  },
  {
    id: "clerk",
    name: "Clerk",
    description: "More than authentication. Complete user management & sign-in for React and Next.js.",
    logo: "https://images.unsplash.com/photo-1620121692029-d088224ddc74?w=80&h=80&fit=crop&auto=format",
    verified: false,
    hiring: true,
    members_count: 24,
    projects_count: 4,
    open_roles_count: 1,
    recent_activity: "Integrated Clerk SDK with SvelteKit 1.0 support",
  },
  {
    id: "tailwind",
    name: "Tailwind Labs",
    description: "Creators of Tailwind CSS, Tailwind UI, and Refactoring UI. Building the future of CSS.",
    logo: "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?w=80&h=80&fit=crop&auto=format",
    verified: true,
    hiring: false,
    members_count: 9,
    projects_count: 6,
    open_roles_count: 0,
    recent_activity: "Announced Tailwind CSS v4.0 Alpha compiler rewrite",
  }
];

function OrganizationsListPage() {
  const search = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const [q, setQ] = useState(search.q || "");
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const saveSearch = useSavedSearches((s) => s.saveSearch);

  useEffect(() => {
    if (search.q !== undefined) {
      setQ(search.q);
    }
  }, [search.q]);

  useEffect(() => {
    const handler = setTimeout(() => {
      navigate({
        search: (prev: any) => ({ ...prev, q: q || undefined }),
        replace: true,
      });
    }, 300);
    return () => clearTimeout(handler);
  }, [q, navigate]);

  const filteredOrgs = useMemo(() => {
    const query = q.toLowerCase();
    return mockOrgs.filter(
      (org) =>
        org.name.toLowerCase().includes(query) || org.description.toLowerCase().includes(query),
    );
  }, [q]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <TypoHeading as="h1">Organizations</TypoHeading>
          <p className="text-gray-400 mt-1">
            Discover startups, open-source orgs, and teams building awesome products.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-6">
        <div className="relative min-w-0 flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search organizations..."
            className="w-full rounded-md border border-gray-800 bg-gray-900/40 py-[7px] pl-9 pr-3 text-[13px] text-gray-100 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50"
          />
        </div>
        <button
          onClick={() => setSaveDialogOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-800 bg-gray-900/40 px-2.5 py-[7px] text-[12px] font-medium text-gray-400 transition-colors hover:text-gray-100 hover:border-gray-700"
        >
          <Bookmark size={13} />
          Save Search
        </button>
      </div>

      <SaveSearchDialog
        open={saveDialogOpen}
        onOpenChange={setSaveDialogOpen}
        onSave={(name) => {
          saveSearch({
            name,
            type: "Organizations",
            query: q,
          } as any);
        }}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredOrgs.map((org) => (
          <div
            key={org.id}
            className="flex flex-col justify-between p-5 rounded-xl border border-gray-800 bg-gray-900/40 hover:border-indigo-500/50 hover:bg-gray-800/45 hover:shadow-lg hover:shadow-indigo-500/5 transition-all duration-300 h-full group"
          >
            <div>
              {/* Header row: Logo, Name, Verified badge, Hiring badge */}
              <div className="flex gap-3 items-start">
                {org.logo ? (
                  <img
                    src={org.logo}
                    alt={`${org.name} logo`}
                    className="h-11 w-11 rounded-lg object-cover bg-gray-800 shrink-0 border border-gray-800 group-hover:border-indigo-500/30 transition-colors"
                  />
                ) : (
                  <div className="h-11 w-11 rounded-lg bg-indigo-600/10 text-indigo-400 border border-indigo-500/10 flex items-center justify-center font-bold text-base shrink-0">
                    {org.name.slice(0, 2).toUpperCase()}
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <h2 className="text-[14px] font-semibold text-gray-100 truncate group-hover:text-white transition-colors">
                      {org.name}
                    </h2>
                    {org.verified && (
                      <CheckCircle2 size={13} className="text-indigo-400 shrink-0 fill-indigo-400/10" />
                    )}
                  </div>
                  {org.hiring && (
                    <span className="inline-flex mt-1 text-[9px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold uppercase tracking-wider">
                      Hiring
                    </span>
                  )}
                </div>
              </div>

              {/* Description */}
              <p className="text-gray-400 text-[12.5px] leading-relaxed mt-4 mb-4 line-clamp-2">
                {org.description}
              </p>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-2 py-3 border-y border-gray-800/60 text-[11px] text-gray-400">
                <div className="flex flex-col items-center text-center">
                  <Users size={12} className="text-gray-500 mb-1" />
                  <span className="font-semibold text-gray-200">{org.members_count}</span>
                  <span className="text-[10px] text-gray-500">Members</span>
                </div>
                <div className="flex flex-col items-center text-center border-x border-gray-800/60">
                  <Briefcase size={12} className="text-gray-500 mb-1" />
                  <span className="font-semibold text-gray-200">{org.projects_count}</span>
                  <span className="text-[10px] text-gray-500">Projects</span>
                </div>
                <div className="flex flex-col items-center text-center">
                  <PlusCircle size={12} className="text-gray-500 mb-1" />
                  <span className="font-semibold text-gray-200">{org.open_roles_count || 0}</span>
                  <span className="text-[10px] text-gray-500">Open Roles</span>
                </div>
              </div>

              {/* Recent Activity */}
              {org.recent_activity && (
                <div className="flex gap-1.5 items-start mt-3.5 text-[11px] text-gray-400 leading-snug italic">
                  <Clock size={11} className="text-gray-500 shrink-0 mt-0.5" />
                  <span className="line-clamp-1">{org.recent_activity}</span>
                </div>
              )}
            </div>

            {/* View Profile Action */}
            <Link
              to="/organizations/$orgId"
              params={{ orgId: org.id }}
              className="mt-5 w-full inline-flex items-center justify-center gap-1.5 rounded-lg bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 px-3 py-2 text-[12px] font-semibold transition-all hover:bg-indigo-600 hover:text-white hover:border-indigo-500"
            >
              <span>View Profile</span>
              <ChevronRight size={13} className="group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
