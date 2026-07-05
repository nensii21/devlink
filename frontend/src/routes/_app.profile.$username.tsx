import { createFileRoute, notFound } from "@tanstack/react-router";
import { Card, Avatar } from "@/components/shared/primitives";
import { BioCard, SkillsCard, TechStackCard, ExperienceCard, EducationCard, SocialLinksCard } from "@/components/profile";
import { builders, currentUser, projects } from "@/mocks/seed";
import { MapPin, Calendar, Link as LinkIcon } from "lucide-react";

export const Route = createFileRoute("/_app/profile/$username")({
  head: ({ params }) => ({
    meta: [
      { title: `@${params.username} — DevLink` },
      { name: "description", content: `${params.username}'s DevLink profile: skills, projects and activity.` },
    ],
  }),
  component: ProfilePage,
});

function ProfilePage() {
  const { username } = Route.useParams();
  const me = username === currentUser.handle;
  const b = me
    ? {
        ...builders[0],
        name: currentUser.name,
        handle: currentUser.handle,
        avatar: currentUser.avatar,
        bio: "Product engineer. Ships fast, sleeps sometimes.",
        role: "Full Stack Developer",
        headline: "Building dependable product experiences across the stack",
        location: "Bengaluru, India",
        timezone: "IST (UTC+5:30)",
        website: "https://devlink.io",
        portfolioUrl: "https://devlink.io/portfolio",
        githubUrl: "https://github.com/devlink",
        linkedinUrl: "https://linkedin.com/company/devlink",
        experienceLevel: "Senior",
        company: "DevLink",
        profileSkills: [
          { name: "React", level: "Advanced", category: "frontend", yearsOfExperience: 4 },
          { name: "Next.js", level: "Advanced", category: "frontend", yearsOfExperience: 3 },
          { name: "TypeScript", level: "Expert", category: "frontend", yearsOfExperience: 5 },
          { name: "Node.js", level: "Intermediate", category: "backend", yearsOfExperience: 2 },
          { name: "Docker", level: "Intermediate", category: "devops", yearsOfExperience: 2 },
        ],
        techStack: ["React", "Next.js", "TypeScript", "Node.js", "Docker"],
        education: [{ school: "IIT Delhi", degree: "B.Tech in Computer Science", years: "2017–2021" }],
      }
    : builders.find((x) => x.handle === username);
  if (!b) throw notFound();

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <div className="flex flex-wrap items-start gap-5">
          <Avatar src={b.avatar} alt={b.name} size={96} online={b.online} />
          <div className="min-w-0 flex-1">
            <h1 className="text-[22px] font-bold text-foreground">{b.name}</h1>
            <p className="text-[13px] text-muted-foreground">@{b.handle} · {b.role}</p>
            <p className="mt-2 text-[13px] text-foreground">{b.bio}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-[12px] text-muted-foreground">
              <span className="inline-flex items-center gap-1"><MapPin size={12} /> {b.country}</span>
              <span className="inline-flex items-center gap-1"><Calendar size={12} /> Joined 2024</span>
              <span className="inline-flex items-center gap-1"><LinkIcon size={12} /> devlink.io/{b.handle}</span>
            </div>
          </div>
          {!me && (
            <button className="rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90">
              Follow
            </button>
          )}
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-3">
        <BioCard headline={b.headline} bio={b.bio} location={b.location} timezone={b.timezone} />
        <ExperienceCard role={b.role} company={b.company} experienceLevel={b.experienceLevel} />
        <SkillsCard skills={b.profileSkills ?? []} />
        <TechStackCard skills={b.profileSkills ?? []} techStack={b.techStack} />
        <SocialLinksCard githubUrl={b.githubUrl} linkedinUrl={b.linkedinUrl} portfolioUrl={b.portfolioUrl} website={b.website} />
        <EducationCard education={b.education ?? []} />
        <Card className="p-4 xl:col-span-3">
          <p className="text-[13px] font-semibold text-foreground">Projects</p>
          <ul className="mt-3 divide-y divide-border">
            {projects.slice(0, 4).map((p) => (
              <li key={p.id} className="flex items-center gap-3 py-2">
                <span className="grid h-8 w-8 place-items-center rounded-md bg-muted text-lg">{p.icon}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-semibold text-foreground">{p.name}</p>
                  <p className="truncate text-[11px] text-muted-foreground">{p.stack.join(" · ")}</p>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
