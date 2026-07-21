import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  Search,
  Users2,
  FolderKanban,
  Building2,
  Hash,
  Flame,
  ArrowRight,
  Loader2,
  CornerDownLeft,
} from "lucide-react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { useDebounce } from "@/hooks/useDebounce";
import { searchService } from "@/services";
import type {
  SearchUser,
  SearchProject,
  SearchOrganization,
  SearchSkill,
  SearchFlare,
} from "@/api/modules/search";

interface GlobalSearchPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const CATEGORY_ICONS = {
  user: Users2,
  project: FolderKanban,
  organization: Building2,
  skill: Hash,
  flare: Flame,
} as const;

export function GlobalSearchPalette({ open, onOpenChange }: GlobalSearchPaletteProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 250);

  // Reset the input whenever the dialog closes.
  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  const { data, isFetching, isError } = useQuery({
    queryKey: ["global-search", debouncedQuery],
    queryFn: () => searchService.all(debouncedQuery),
    enabled: debouncedQuery.trim().length >= 1,
    staleTime: 30_000,
  });

  const groups = useMemo(() => {
    if (!data?.results) return null;
    return data.results;
  }, [data]);

  const goTo = (path: string) => {
    onOpenChange(false);
    navigate({ to: path });
  };

  const isEmpty =
    groups &&
    groups.users.length === 0 &&
    groups.projects.length === 0 &&
    groups.organizations.length === 0 &&
    groups.skills.length === 0 &&
    groups.flares.length === 0;

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput
        placeholder="Search developers, projects, skills…"
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {/* ----- Loading ----- */}
        {isFetching && (
          <div className="flex items-center justify-center gap-2 py-6 text-sm text-muted-foreground">
            <Loader2 size={14} className="animate-spin" />
            Searching…
          </div>
        )}

        {/* ----- Error ----- */}
        {isError && !isFetching && (
          <CommandEmpty>Something went wrong. Please try again.</CommandEmpty>
        )}

        {/* ----- Empty state ----- */}
        {!isFetching && !isError && isEmpty && debouncedQuery.trim().length >= 1 && (
          <CommandEmpty>No results for “{debouncedQuery}”. Try a different keyword.</CommandEmpty>
        )}

        {/* ----- Initial hint (no query yet) ----- */}
        {!debouncedQuery.trim() && (
          <div className="py-6 text-center text-sm text-muted-foreground">
            <Search size={20} className="mx-auto mb-2 opacity-40" />
            Start typing to search across the entire platform.
          </div>
        )}

        {/* ----- Results ----- */}
        {!isFetching && groups && !isEmpty && (
          <>
            {groups.users.length > 0 && (
              <CommandGroup heading="Developers">
                {groups.users.slice(0, 6).map((u) => (
                  <UserItem key={u.id} user={u} query={debouncedQuery} onSelect={goTo} />
                ))}
              </CommandGroup>
            )}
            {groups.projects.length > 0 && (
              <>
                {groups.users.length > 0 && <CommandSeparator />}
                <CommandGroup heading="Projects">
                  {groups.projects.slice(0, 6).map((p) => (
                    <ProjectItem key={p.id} project={p} onSelect={goTo} />
                  ))}
                </CommandGroup>
              </>
            )}
            {groups.organizations.length > 0 && (
              <>
                {(groups.users.length > 0 || groups.projects.length > 0) && <CommandSeparator />}
                <CommandGroup heading="Organizations">
                  {groups.organizations.slice(0, 6).map((o) => (
                    <OrgItem key={o.id} org={o} onSelect={goTo} />
                  ))}
                </CommandGroup>
              </>
            )}
            {groups.skills.length > 0 && (
              <>
                {(groups.users.length > 0 ||
                  groups.projects.length > 0 ||
                  groups.organizations.length > 0) && <CommandSeparator />}
                <CommandGroup heading="Skills">
                  {groups.skills.slice(0, 8).map((s) => (
                    <SkillItem key={s.id} skill={s} onSelect={goTo} />
                  ))}
                </CommandGroup>
              </>
            )}
            {groups.flares.length > 0 && (
              <>
                {(groups.users.length > 0 ||
                  groups.projects.length > 0 ||
                  groups.organizations.length > 0 ||
                  groups.skills.length > 0) && <CommandSeparator />}
                <CommandGroup heading="Flares">
                  {groups.flares.slice(0, 5).map((f) => (
                    <FlareItem key={f.id} flare={f} onSelect={goTo} />
                  ))}
                </CommandGroup>
              </>
            )}

            <CommandSeparator />
            <CommandGroup>
              <CommandItem
                onSelect={() => goTo(`/search?q=${encodeURIComponent(debouncedQuery)}`)}
                className="text-muted-foreground"
              >
                <ArrowRight size={16} />
                <span>View all results for “{debouncedQuery}”</span>
                <CornerDownLeft size={12} className="ml-auto opacity-50" />
              </CommandItem>
            </CommandGroup>
          </>
        )}
      </CommandList>
    </CommandDialog>
  );
}

// ---------------------------------------------------------------------------
// Item renderers
// ---------------------------------------------------------------------------

function UserItem({
  user,
  query,
  onSelect,
}: {
  user: SearchUser;
  query: string;
  onSelect: (path: string) => void;
}) {
  const Icon = CATEGORY_ICONS.user;
  return (
    <CommandItem
      value={`user-${user.id}-${user.username}`}
      onSelect={() => onSelect(`/builders/${user.id}`)}
    >
      <Icon size={16} className="text-muted-foreground" />
      <img
        src={user.profile_image ?? ""}
        alt=""
        className="h-6 w-6 rounded-full border border-border bg-muted"
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-medium text-foreground">
          {user.first_name} {user.last_name}
        </p>
        <p className="truncate text-[11px] text-muted-foreground">
          @{user.username}
          {user.headline ? ` · ${user.headline}` : ""}
        </p>
      </div>
    </CommandItem>
  );
}

function ProjectItem({
  project,
  onSelect,
}: {
  project: SearchProject;
  onSelect: (path: string) => void;
}) {
  const Icon = CATEGORY_ICONS.project;
  return (
    <CommandItem
      value={`project-${project.id}-${project.title}`}
      onSelect={() => onSelect(`/projects/${project.id}`)}
    >
      <Icon size={16} className="text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-medium text-foreground">{project.title}</p>
        <p className="truncate text-[11px] text-muted-foreground">
          {project.tagline ?? project.description.slice(0, 60)}
        </p>
      </div>
      {project.is_featured && (
        <span className="rounded bg-primary-soft px-1.5 py-0.5 text-[10px] font-semibold text-primary">
          ★
        </span>
      )}
    </CommandItem>
  );
}

function OrgItem({ org, onSelect }: { org: SearchOrganization; onSelect: (path: string) => void }) {
  const Icon = CATEGORY_ICONS.organization;
  return (
    <CommandItem value={`org-${org.id}-${org.name}`} onSelect={() => onSelect(`/builders`)}>
      <Icon size={16} className="text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-medium text-foreground">{org.name}</p>
        <p className="truncate text-[11px] text-muted-foreground">
          {org.members_count} members
          {org.location ? ` · ${org.location}` : ""}
        </p>
      </div>
      {org.verified && <span className="text-[10px] font-semibold text-info">✓</span>}
    </CommandItem>
  );
}

function SkillItem({ skill, onSelect }: { skill: SearchSkill; onSelect: (path: string) => void }) {
  const Icon = CATEGORY_ICONS.skill;
  return (
    <CommandItem
      value={`skill-${skill.id}-${skill.name}`}
      onSelect={() => onSelect(`/search?q=${encodeURIComponent(skill.name)}`)}
    >
      <Icon size={16} className="text-muted-foreground" />
      <span className="text-[13px] font-medium text-foreground">{skill.name}</span>
      {skill.category && (
        <span className="ml-1 text-[11px] text-muted-foreground">{skill.category}</span>
      )}
    </CommandItem>
  );
}

function FlareItem({ flare, onSelect }: { flare: SearchFlare; onSelect: (path: string) => void }) {
  const Icon = CATEGORY_ICONS.flare;
  return (
    <CommandItem value={`flare-${flare.id}-${flare.title}`} onSelect={() => onSelect(`/flares`)}>
      <Icon size={16} className="text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-medium text-foreground">{flare.title}</p>
        <p className="truncate text-[11px] text-muted-foreground">{flare.role}</p>
      </div>
    </CommandItem>
  );
}
