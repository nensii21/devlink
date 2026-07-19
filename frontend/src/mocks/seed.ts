// Realistic seed data for DevLink — used by all mock services.
// Replace mock services with an HTTP client later; shapes are stable.

export type ID = string;

export interface Skill {
  name: string;
}
export interface Builder {
  id: ID;
  name: string;
  handle: string;
  role: string;
  avatar: string;
  country: string;
  yearsExp: number;
  matchScore: number;
  skills: string[];
  online: boolean;
  bio: string;
}
export interface Project {
  id: ID;
  name: string;
  description: string;
  stack: string[];
  owner: string;
  members: number;
  stars: number;
  views: number;
  forks: number;
  progress: number;
  status: "recruiting" | "in-progress" | "completed" | "archived";
  icon: string;
  language?: string;
  difficulty?: "beginner" | "intermediate" | "advanced";
  remote?: boolean;
  paid?: boolean;
  openSource?: boolean;
  ai?: boolean;
  web?: boolean;
  mobile?: boolean;
  backend?: boolean;
  frontend?: boolean;
}
export interface Activity {
  id: ID;
  kind: "join" | "accept" | "commit" | "merge" | "follow" | "repo" | "hackathon" | "ai";
  text: string;
  highlight?: string;
  ago: string;
}
export interface BuilderRequest {
  id: ID;
  builder: Builder;
}
export interface InviteRequest {
  id: ID;
  project: string;
  role: string;
  dueDays: number;
  by: string;
  icon: string;
  color: string;
}
export interface Flare {
  id: ID;
  author: Builder;
  content: string;
  tags: string[];
  likes: number;
  comments: number;
  ago: string;
}
export interface Conversation {
  id: ID;
  with: Builder;
  preview: string;
  ago: string;
  unread: number;
}
export interface Message {
  id: ID;
  from: ID;
  text: string;
  at: string;
}
export interface Notification {
  id: ID;
  kind: "apply" | "comment" | "invite" | "match" | "hackathon";
  text: string;
  ago: string;
  unread: boolean;
}
export interface Hackathon {
  id: ID;
  name: string;
  theme: string;
  startsIn: number;
  prize: string;
  teamSize: string;
  registered: boolean;
}
export interface Deadline {
  id: ID;
  project: string;
  milestone: string;
  dueDays: number;
  severity: "danger" | "warning" | "info";
}

const AV = (seed: string) =>
  `https://api.dicebear.com/9.x/notionists-neutral/svg?seed=${encodeURIComponent(seed)}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf`;

export const builders: Builder[] = [
  {
    id: "b1",
    name: "Priya Sharma",
    handle: "priya_dev",
    role: "Frontend Developer",
    avatar: AV("Priya"),
    country: "India",
    yearsExp: 3,
    matchScore: 92,
    skills: ["React", "Next.js", "TypeScript"],
    online: true,
    bio: "Loves accessible UIs and design systems.",
  },
  {
    id: "b2",
    name: "Rahul Verma",
    handle: "rahul_v",
    role: "Full Stack Developer",
    avatar: AV("Rahul"),
    country: "India",
    yearsExp: 4,
    matchScore: 89,
    skills: ["Node.js", "MongoDB", "Express"],
    online: true,
    bio: "Builds end-to-end features fast.",
  },
  {
    id: "b3",
    name: "Ankit Singh",
    handle: "ankit_be",
    role: "Backend Developer",
    avatar: AV("Ankit"),
    country: "India",
    yearsExp: 2,
    matchScore: 87,
    skills: ["Python", "FastAPI", "PostgreSQL"],
    online: false,
    bio: "APIs, queues and Postgres tuning.",
  },
  {
    id: "b4",
    name: "Sneha Iyer",
    handle: "sneha_ux",
    role: "UI/UX Designer",
    avatar: AV("Sneha"),
    country: "India",
    yearsExp: 3,
    matchScore: 94,
    skills: ["Figma", "Adobe XD"],
    online: true,
    bio: "Product design for early-stage teams.",
  },
  {
    id: "b5",
    name: "Vikram Mehta",
    handle: "vikram_fs",
    role: "Full Stack Dev",
    avatar: AV("Vikram"),
    country: "India",
    yearsExp: 4,
    matchScore: 93,
    skills: ["MERN", "Next.js"],
    online: false,
    bio: "Ships side-projects on weekends.",
  },
  {
    id: "b6",
    name: "Aditya Rao",
    handle: "aditya_m",
    role: "Mobile Developer",
    avatar: AV("Aditya"),
    country: "India",
    yearsExp: 3,
    matchScore: 91,
    skills: ["Flutter", "Firebase"],
    online: true,
    bio: "Cross-platform mobile since 2021.",
  },
  {
    id: "b7",
    name: "Sarah Chen",
    handle: "sarah_c",
    role: "ML Engineer",
    avatar: AV("Sarah"),
    country: "US",
    yearsExp: 5,
    matchScore: 88,
    skills: ["Python", "PyTorch", "AWS"],
    online: true,
    bio: "Recsys, embeddings, evals.",
  },
  {
    id: "b8",
    name: "Alex Johnson",
    handle: "alex_j",
    role: "DevOps",
    avatar: AV("Alex"),
    country: "UK",
    yearsExp: 6,
    matchScore: 86,
    skills: ["Kubernetes", "Terraform"],
    online: false,
    bio: "Infra as code, cost optimization.",
  },
];

export const projects: Project[] = [
  {
    id: "p1",
    name: "AI Chatbot",
    description: "Multi-agent customer support bot for SaaS.",
    stack: ["React", "Node.js", "MongoDB"],
    owner: "Nancy Patel",
    members: 4,
    stars: 24,
    views: 1042,
    forks: 12,
    progress: 75,
    status: "in-progress",
    icon: "🤖",
    language: "JavaScript",
    difficulty: "intermediate",
    remote: true,
    paid: true,
    openSource: false,
    ai: true,
    web: true,
    frontend: true,
    backend: true,
  },
  {
    id: "p2",
    name: "AI SaaS Platform",
    description: "Full-stack platform with billing and dashboards.",
    stack: ["Next.js", "Python", "PostgreSQL"],
    owner: "Nancy Patel",
    members: 6,
    stars: 18,
    views: 890,
    forks: 8,
    progress: 40,
    status: "in-progress",
    icon: "✨",
    language: "Python",
    difficulty: "advanced",
    remote: true,
    paid: true,
    openSource: false,
    ai: true,
    web: true,
    frontend: true,
    backend: true,
  },
  {
    id: "p3",
    name: "DevOps Dashboard",
    description: "K8s deploy monitoring with drift detection.",
    stack: ["Docker", "Kubernetes", "AWS"],
    owner: "Nancy Patel",
    members: 3,
    stars: 16,
    views: 521,
    forks: 6,
    progress: 60,
    status: "in-progress",
    icon: "🚀",
    language: "Go",
    difficulty: "advanced",
    remote: true,
    paid: false,
    openSource: false,
    ai: false,
    web: true,
    backend: true,
  },
  {
    id: "p4",
    name: "Blockchain Wallet",
    description: "Non-custodial multi-chain wallet.",
    stack: ["Solidity", "Web3", "React"],
    owner: "Nancy Patel",
    members: 5,
    stars: 14,
    views: 310,
    forks: 7,
    progress: 25,
    status: "recruiting",
    icon: "🪙",
    language: "TypeScript",
    difficulty: "advanced",
    remote: true,
    paid: false,
    openSource: true,
    ai: false,
    web: true,
    mobile: true,
    frontend: true,
  },
  {
    id: "p5",
    name: "React Component Library",
    description: "Accessible component library with docs.",
    stack: ["TypeScript", "Tailwind", "Storybook"],
    owner: "Nancy Patel",
    members: 2,
    stars: 12,
    views: 180,
    forks: 5,
    progress: 90,
    status: "in-progress",
    icon: "🧩",
    language: "TypeScript",
    difficulty: "beginner",
    remote: true,
    paid: false,
    openSource: true,
    ai: false,
    web: true,
    frontend: true,
  },
  {
    id: "p6",
    name: "Open Source CRM",
    description: "Lightweight CRM with pipelines and reports.",
    stack: ["React", "Node.js", "MongoDB"],
    owner: "Community",
    members: 8,
    stars: 240,
    views: 5040,
    forks: 96,
    progress: 100,
    status: "completed",
    icon: "📇",
    language: "JavaScript",
    difficulty: "intermediate",
    remote: false,
    paid: false,
    openSource: true,
    ai: false,
    web: true,
    frontend: true,
    backend: true,
  },
];

export const activity: Activity[] = [
  {
    id: "a1",
    kind: "join",
    text: "Alex joined your project",
    highlight: "AI Chatbot",
    ago: "2m ago",
  },
  { id: "a2", kind: "accept", text: "Sarah accepted your invitation", ago: "15m ago" },
  { id: "a3", kind: "commit", text: "Backend API development completed", ago: "1h ago" },
  { id: "a4", kind: "merge", text: "Frontend PR #24 merged", ago: "2h ago" },
  { id: "a5", kind: "follow", text: "New builder Rahul followed you", ago: "3h ago" },
  { id: "a6", kind: "repo", text: "Repository", highlight: "devlink/web", ago: "5h ago" },
  { id: "a7", kind: "hackathon", text: "You registered for Hackathon 2025", ago: "1d ago" },
  { id: "a8", kind: "ai", text: "AI suggested 3 new builders for you", ago: "1d ago" },
];

export const builderRequests: BuilderRequest[] = [
  { id: "r1", builder: builders[0] },
  { id: "r2", builder: builders[1] },
  { id: "r3", builder: builders[2] },
];

export const inviteRequests: InviteRequest[] = [
  {
    id: "i1",
    project: "Open Source CRM",
    role: "Backend Developer",
    dueDays: 3,
    by: "Alex",
    icon: "📇",
    color: "bg-info/10 text-info",
  },
  {
    id: "i2",
    project: "AI SaaS Platform",
    role: "ML Engineer",
    dueDays: 5,
    by: "Sarah",
    icon: "✨",
    color: "bg-primary/10 text-primary",
  },
  {
    id: "i3",
    project: "DevOps Dashboard",
    role: "DevOps Engineer",
    dueDays: 7,
    by: "Mike",
    icon: "🚀",
    color: "bg-warning/10 text-warning",
  },
];

export const flares: Flare[] = [
  {
    id: "f1",
    author: builders[3],
    content:
      "Just shipped a component library refresh — new tokens, better a11y, half the CSS. AMA about migrating design systems.",
    tags: ["designsystems", "react"],
    likes: 128,
    comments: 22,
    ago: "1h ago",
  },
  {
    id: "f2",
    author: builders[6],
    content:
      "Wrote a small evaluator for embedding models. Cosine wasn't cutting it for our recall — dot-product + normalized inputs won.",
    tags: ["ml", "search"],
    likes: 87,
    comments: 14,
    ago: "3h ago",
  },
  {
    id: "f3",
    author: builders[1],
    content:
      "Anyone else notice Node 22 shaving ~10% off cold starts for our fastify APIs? Ran the same suite twice.",
    tags: ["node", "perf"],
    likes: 54,
    comments: 9,
    ago: "5h ago",
  },
];

export const conversations: Conversation[] = [
  { id: "c1", with: builders[0], preview: "Typing…", ago: "2m", unread: 2 },
  { id: "c2", with: builders[7], preview: "Can we schedule a call?", ago: "10m", unread: 0 },
  { id: "c3", with: builders[1], preview: "Project update: v2.0 released", ago: "1h", unread: 1 },
  { id: "c4", with: builders[6], preview: "Shared a file", ago: "2h", unread: 0 },
];

export const messages: Record<ID, Message[]> = {
  c1: [
    { id: "m1", from: "b1", text: "Hey! Loved the mocks you posted.", at: "10:02" },
    { id: "m2", from: "me", text: "Thanks 🙌 want to pair on the empty states?", at: "10:04" },
    { id: "m3", from: "b1", text: "Yes — send me the branch.", at: "10:05" },
  ],
};

export const notifications: Notification[] = [
  { id: "n1", kind: "apply", text: "Alex applied to your project", ago: "2m ago", unread: true },
  { id: "n2", kind: "comment", text: "Sarah commented on your post", ago: "15m ago", unread: true },
  { id: "n3", kind: "invite", text: "Your invitation was accepted", ago: "1h ago", unread: false },
  { id: "n4", kind: "match", text: "New builder matches found", ago: "3h ago", unread: false },
  {
    id: "n5",
    kind: "hackathon",
    text: "Hackathon deadline reminder",
    ago: "1d ago",
    unread: false,
  },
];

export const hackathons: Hackathon[] = [
  {
    id: "h1",
    name: "AI for Good 2025",
    theme: "Social impact",
    startsIn: 12,
    prize: "$25k",
    teamSize: "2–5",
    registered: true,
  },
  {
    id: "h2",
    name: "DevLink Winter Jam",
    theme: "Any theme",
    startsIn: 30,
    prize: "$10k",
    teamSize: "1–4",
    registered: false,
  },
  {
    id: "h3",
    name: "Chain Builders",
    theme: "Web3",
    startsIn: 45,
    prize: "$50k",
    teamSize: "1–5",
    registered: false,
  },
];

export const deadlines: Deadline[] = [
  { id: "d1", project: "AI Chatbot", milestone: "Backend API", dueDays: 2, severity: "danger" },
  {
    id: "d2",
    project: "DevOps Dashboard",
    milestone: "Deployment",
    dueDays: 5,
    severity: "warning",
  },
  {
    id: "d3",
    project: "Hackathon 2025",
    milestone: "Registration",
    dueDays: 7,
    severity: "warning",
  },
  { id: "d4", project: "Project Milestone", milestone: "v1.0", dueDays: 10, severity: "info" },
];

export const currentUser = {
  id: "me",
  name: "Nancy Patel",
  handle: "nancy_dev",
  avatar: AV("Nancy"),
  premium: true,
};

export const stats = [
  { key: "projects", label: "Projects", value: 12, icon: "folder", tint: "info" },
  { key: "builders", label: "Builders", value: 54, icon: "users", tint: "primary" },
  { key: "messages", label: "Messages", value: 21, icon: "message", tint: "primary" },
  { key: "invitations", label: "Invitations", value: 8, icon: "mail", tint: "warning" },
  { key: "connections", label: "Connections", value: 112, icon: "share", tint: "success" },
  { key: "views", label: "Profile Views", value: 489, icon: "eye", tint: "info" },
  { key: "contribs", label: "Weekly Contributions", value: 26, icon: "activity", tint: "success" },
  { key: "commits", label: "GitHub Commits", value: 54, icon: "github", tint: "foreground" },
  { key: "hackathons", label: "Hackathons", value: 4, icon: "trophy", tint: "warning" },
  { key: "ai", label: "AI Match Score", value: "96%", icon: "sparkles", tint: "primary" },
] as const;
