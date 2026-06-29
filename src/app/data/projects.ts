import { Project } from "../types/project";
import { BUILDERS } from "./builders";

export const PROJECTS: Project[] = [
  {
    id: 1,
    title: "AI Startup Platform",
    founder: BUILDERS[5],
    desc: "AI-powered platform that helps non-technical founders define, validate, and ship SaaS ideas end-to-end. Think Notion meets an AI co-founder.",
    skills: ["React", "Python", "FastAPI", "OpenAI"],
    teamSize: 3,
    maxTeam: 5,
    stage: "MVP",
    remote: true,
    apps: 12,
    featured: true,
    cover:
      "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=600&h=200&fit=crop&auto=format",
    rolesNeeded: ["Frontend Developer", "AI Engineer"],
  },
  {
    id: 2,
    title: "Open Source Analytics",
    founder: BUILDERS[0],
    desc: "Privacy-first, self-hosted analytics alternative to Mixpanel. Zero tracking of your users. Open source from day one.",
    skills: ["Go", "React", "ClickHouse", "Docker"],
    teamSize: 2,
    maxTeam: 4,
    stage: "Early",
    remote: true,
    apps: 8,
    featured: true,
    cover:
      "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&h=200&fit=crop&auto=format",
    rolesNeeded: ["React Developer", "UI Designer"],
  },
  {
    id: 3,
    title: "SaaS Productivity App",
    founder: BUILDERS[4],
    desc: "All-in-one async workspace for distributed teams — tasks, docs, and decisions in one focused product. No fluff.",
    skills: ["Next.js", "TypeScript", "Node.js", "PostgreSQL"],
    teamSize: 4,
    maxTeam: 6,
    stage: "Beta",
    remote: true,
    apps: 18,
    featured: false,
    cover:
      "https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&h=200&fit=crop&auto=format",
    rolesNeeded: ["Backend Engineer", "Product Designer"],
  },
];