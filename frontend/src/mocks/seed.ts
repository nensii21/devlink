// Realistic seed data for DevLink — used by all mock services.
// Replace mock services with an HTTP client later; shapes are stable.

export type ID = string;

export type UserRole = "Developer" | "Founder" | "Designer" | "AI Engineer" | "Mentor";

export interface ProfileSkill {
  name: string;
  level?: string;
  category?: string;
  yearsOfExperience?: number;
}

export interface Skill {
  name: string;
}
export interface Builder {
  id: ID;
  name: string;
  handle: string;
  role: UserRole;
  avatar: string;
  country: string;
  yearsExp: number;
  matchScore: number;
  skills: string[];
  badges: string[];
  interests: string[];
  online: boolean;
  headline?: string;
  bio?: string;
  location?: string;
  timezone?: string;
  website?: string;
  resumeUrl?: string;
  portfolioUrl?: string;
  githubUrl?: string;
  linkedinUrl?: string;
  twitterUrl?: string;
  experienceLevel?: string;
  company?: string;
  profileSkills?: { name: string; level?: string; category?: string; yearsOfExperience?: number }[];
  techStack?: string[];
  lastActiveAt: string | null;
  publicEmail?: string;
  verified?: boolean;
  premium?: boolean;
  contributions?: number;
  followers?: number;
  following?: number;
  experience?: {
    company: string;
    role: string;
    duration: string;
  }[];
  education?: {
    school: string;
    degree: string;
    duration: string;
  }[];
  language?: string[];
  activityTimeline?: {
    title: string;
    date: string;
  }[];
  collaborationStatus?: string;
}
export interface Project {
  id: ID;
  name: string;
  description: string;
  stack: string[];
  owner: string;
  owner_id?: string;
  ownerId?: string;
  members: number;
  stars: number;
  views: number;
  forks: number;
  progress: number;
  status: "recruiting" | "in-progress" | "completed" | "archived";
  icon: string;
  language?: string;
  difficulty?: "Beginner" | "Intermediate" | "Advanced";
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
  status?: string;
  publish_at?: string;
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
  type?: string;
  attachment_url?: string;
  attachment_name?: string;
  attachment_size?: number;
  mime_type?: string;
  sender_id?: string;
  is_edited?: boolean;
  is_deleted?: boolean;
  is_sent?: boolean;
  is_pinned?: boolean;
  scheduled_for?: string;
  read_at?: string;
  pinned_by_id?: string;
  pinned_at?: string;
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
  description: string;
  theme: string;
  starts_at: string;
  ends_at: string;
  min_team_size: number;
  max_team_size: number;
  prize: string;
  status: string;
  is_published: boolean;
  created_by: string;
  website_url?: string;
  created_at: string;
  updated_at: string;
}

export interface HackathonTeam {
  id: ID;
  hackathon_id: string;
  name: string;
  description?: string;
  created_by: string;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface HackathonSubmission {
  id: ID;
  hackathon_id: string;
  team_id: string;
  submitted_by: string;
  title: string;
  description: string;
  repo_url?: string;
  demo_url?: string;
  status: "draft" | "submitted" | "in_review" | "accepted" | "rejected";
  created_at: string;
  updated_at: string;
}

export interface HackathonLeaderboardEntry {
  rank: number;
  team_id: string;
  team_name: string;
  submission_title: string;
  avg_score: number;
  judge_count: number;
}
export interface Deadline {
  id: ID;
  project: string;
  milestone: string;
  dueDays: number;
  severity: "danger" | "warning" | "info";
}

export interface OrganizationMember {
  id: ID;
  name: string;
  role: string;
  department: string;
  avatar: string;
  joinedAt: string;
}

export interface OrganizationOpening {
  id: ID;
  title: string;
  location: string;
  type: "Full-time" | "Part-time" | "Contract";
  description?: string;
}

export interface OrganizationProject {
  id: ID;
  name: string;
  category: string;
  description: string;
  website?: string;
  repoUrl?: string;
  members?: number;
}

export interface OrganizationStats {
  projects: number;
  members: number;
  activeUsers: number;
  satisfaction: number;
}

export interface OrganizationBanner {
  id: ID;
  name: string;
  tagline: string;
  logoUrl: string;
  color: string;
}

export interface ActivityItem {
  id: ID;
  type: "join" | "project" | "hire" | "update";
  title: string;
  description: string;
  ago: string;
  icon: string;
}

const AV = (seed: string) =>
  `https://api.dicebear.com/9.x/notionists-neutral/svg?seed=${encodeURIComponent(seed)}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf`;

const ago = (minutes: number) => new Date(Date.now() - minutes * 60_000).toISOString();

export const builders: Builder[] = [
  {
    id: "b1",
    name: "Priya Sharma",
    handle: "priya_dev",
    role: "Developer",
    avatar: AV("Priya"),
    country: "India",
    yearsExp: 3,
    matchScore: 92,
    skills: ["React", "Next.js", "TypeScript"],
    profileSkills: [
      { name: "TypeScript", level: "Expert", category: "Languages", yearsOfExperience: 4 },
      { name: "React", level: "Expert", category: "Frameworks", yearsOfExperience: 4 },
      { name: "Next.js", level: "Advanced", category: "Frameworks", yearsOfExperience: 3 },
      { name: "PostgreSQL", level: "Intermediate", category: "Databases", yearsOfExperience: 2 },
      { name: "AWS", level: "Intermediate", category: "Cloud", yearsOfExperience: 2 },
      { name: "Docker", level: "Advanced", category: "DevOps", yearsOfExperience: 3 },
      { name: "Tailwind CSS", level: "Expert", category: "Design", yearsOfExperience: 4 },
    ],
    badges: ["Top Contributor", "Social Butterfly"],
    online: true,
    bio: "Loves accessible UIs and design systems.",
    collaborationStatus: "reviewing_pr",
    interests: ["Web Dev", "Design Systems", "AI"],
    lastActiveAt: ago(1),
    publicEmail: "priya@example.com",
    verified: true,
    contributions: 842,
    followers: 238,
    following: 124,
    language: ["English", "Hindi"],
    experience: [
      {
        company: "Google",
        role: "Frontend Engineer",
        duration: "2023- Present",
      },
      {
        company: "StartupX",
        role: "React Developer",
        duration: "2021-2023",
      },
    ],
    education: [
      {
        school: "IIT Delhi",
        degree: "B.Tech Computer Science",
        duration: "2017-2021",
      },
    ],
    activityTimeline: [
      {
        title: "Joined DevLink",
        date: "Jan 2024",
      },
      {
        title: "Created AI Chatbot",
        date: "Mar 2024",
      },
      {
        title: "Reached 200 Followers",
        date: "Jul 2024",
      },
    ],
  },
  {
    id: "b2",
    name: "Rahul Verma",
    handle: "rahul_v",
    role: "Developer",
    avatar: AV("Rahul"),
    country: "India",
    yearsExp: 4,
    matchScore: 89,
    skills: ["Node.js", "MongoDB", "Express"],
    badges: ["Active Developer"],
    online: true,
    bio: "Builds end-to-end features fast.",
    collaborationStatus: "coding",
    interests: ["Backend", "Web Dev"],
    lastActiveAt: ago(3),
  },
  {
    id: "b3",
    name: "Ankit Singh",
    handle: "ankit_be",
    role: "Developer",
    avatar: AV("Ankit"),
    country: "India",
    yearsExp: 2,
    matchScore: 87,
    skills: ["Python", "FastAPI", "PostgreSQL"],
    badges: ["Project Owner", "Active Developer"],
    online: false,
    bio: "APIs, queues and Postgres tuning.",
    collaborationStatus: "looking_for_project",
    interests: ["Backend", "AI"],
    lastActiveAt: ago(120),
  },
  {
    id: "b4",
    name: "Sneha Iyer",
    handle: "sneha_ux",
    role: "Designer",
    avatar: AV("Sneha"),
    country: "India",
    yearsExp: 3,
    matchScore: 94,
    skills: ["Figma", "Adobe XD"],
    badges: ["Social Butterfly"],
    online: true,
    bio: "Product design for early-stage teams.",
    interests: ["Design Systems", "Web Dev"],
    lastActiveAt: ago(5),
  },
  {
    id: "b5",
    name: "Vikram Mehta",
    handle: "vikram_fs",
    role: "Developer",
    avatar: AV("Vikram"),
    country: "India",
    yearsExp: 4,
    matchScore: 93,
    skills: ["MERN", "Next.js"],
    badges: ["Top Contributor", "Project Owner"],
    online: false,
    bio: "Ships side-projects on weekends.",
    interests: ["Web Dev", "Frontend"],
    lastActiveAt: ago(1440),
  },
  {
    id: "b6",
    name: "Aditya Rao",
    handle: "aditya_m",
    role: "Developer",
    avatar: AV("Aditya"),
    country: "India",
    yearsExp: 3,
    matchScore: 91,
    skills: ["Flutter", "Firebase"],
    badges: ["Active Developer"],
    online: true,
    bio: "Cross-platform mobile since 2021.",
    interests: ["Mobile", "Web Dev"],
    lastActiveAt: ago(10),
  },
  {
    id: "b7",
    name: "Sarah Chen",
    handle: "sarah_c",
    role: "AI Engineer",
    avatar: AV("Sarah"),
    country: "US",
    yearsExp: 5,
    matchScore: 88,
    skills: ["Python", "PyTorch", "AWS"],
    badges: ["Top Contributor", "Social Butterfly"],
    online: true,
    bio: "Recsys, embeddings, evals.",
    interests: ["AI", "Backend"],
    lastActiveAt: ago(30),
  },
  {
    id: "b8",
    name: "Alex Johnson",
    handle: "alex_j",
    role: "Developer",
    avatar: AV("Alex"),
    country: "UK",
    yearsExp: 6,
    matchScore: 86,
    skills: ["Kubernetes", "Terraform"],
    badges: ["Project Owner"],
    online: false,
    bio: "Infra as code, cost optimization.",
    interests: ["Backend", "AI"],
    lastActiveAt: null,
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
    difficulty: "Intermediate",
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
    difficulty: "Advanced",
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
    difficulty: "Advanced",
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
    difficulty: "Advanced",
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
    difficulty: "Beginner",
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
    difficulty: "Intermediate",
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
    description:
      "Build AI-powered tools that drive social impact. Use machine learning, NLP, or computer vision to solve real-world problems.",
    theme: "Social impact",
    starts_at: "2025-09-15T09:00:00Z",
    ends_at: "2025-09-17T18:00:00Z",
    min_team_size: 2,
    max_team_size: 5,
    prize: "$25k",
    status: "registration_open",
    is_published: true,
    created_by: "u1",
    created_at: "2025-08-01T00:00:00Z",
    updated_at: "2025-08-01T00:00:00Z",
  },
  {
    id: "h2",
    name: "DevLink Winter Jam",
    description:
      "A weekend hackathon for the DevLink community. Ship something cool, win prizes, and meet fellow developers.",
    theme: "Any theme",
    starts_at: "2025-12-10T09:00:00Z",
    ends_at: "2025-12-12T18:00:00Z",
    min_team_size: 1,
    max_team_size: 4,
    prize: "$10k",
    status: "draft",
    is_published: false,
    created_by: "u1",
    created_at: "2025-11-01T00:00:00Z",
    updated_at: "2025-11-01T00:00:00Z",
  },
  {
    id: "h3",
    name: "Chain Builders",
    description:
      "Build the next generation of decentralized applications. Focus on DeFi, NFTs, DAOs, or blockchain infrastructure.",
    theme: "Web3",
    starts_at: "2026-01-20T09:00:00Z",
    ends_at: "2026-01-22T18:00:00Z",
    min_team_size: 1,
    max_team_size: 5,
    prize: "$50k",
    status: "completed",
    is_published: true,
    created_by: "u2",
    created_at: "2025-12-15T00:00:00Z",
    updated_at: "2026-01-23T00:00:00Z",
  },
];

export const hackathonTeams: HackathonTeam[] = [
  {
    id: "ht1",
    hackathon_id: "h1",
    name: "Neural Nexus",
    description: "Building an AI tool to help NGOs manage volunteer coordination.",
    created_by: "u1",
    member_count: 3,
    created_at: "2025-08-10T10:00:00Z",
    updated_at: "2025-08-10T10:00:00Z",
  },
  {
    id: "ht2",
    hackathon_id: "h1",
    name: "Green Coders",
    description: "Using computer vision to detect and classify waste for recycling.",
    created_by: "u2",
    member_count: 2,
    created_at: "2025-08-11T14:00:00Z",
    updated_at: "2025-08-11T14:00:00Z",
  },
  {
    id: "ht3",
    hackathon_id: "h1",
    name: "AccessAI",
    description: "AI-powered accessibility tools for visually impaired users.",
    created_by: "u3",
    member_count: 4,
    created_at: "2025-08-12T09:00:00Z",
    updated_at: "2025-08-12T09:00:00Z",
  },
  {
    id: "ht4",
    hackathon_id: "h3",
    name: "DeFi Degen Squad",
    description: "A yield aggregator with gas optimization on Ethereum L2.",
    created_by: "u2",
    member_count: 3,
    created_at: "2026-01-05T10:00:00Z",
    updated_at: "2026-01-05T10:00:00Z",
  },
  {
    id: "ht5",
    hackathon_id: "h3",
    name: "Zero Knowledge Labs",
    description: "ZK-proof based identity verification without exposing personal data.",
    created_by: "u4",
    member_count: 2,
    created_at: "2026-01-06T12:00:00Z",
    updated_at: "2026-01-06T12:00:00Z",
  },
];

export const hackathonSubmissions: HackathonSubmission[] = [
  {
    id: "hs1",
    hackathon_id: "h3",
    team_id: "ht4",
    submitted_by: "u2",
    title: "YieldMax Protocol",
    description:
      "A multi-strategy yield aggregator that automatically routes funds to the highest APY protocols on Arbitrum and Optimism, saving up to 40% on gas.",
    repo_url: "https://github.com/defidegen/yieldmax",
    demo_url: "https://yieldmax.demo.xyz",
    status: "accepted",
    created_at: "2026-01-21T20:00:00Z",
    updated_at: "2026-01-22T10:00:00Z",
  },
  {
    id: "hs2",
    hackathon_id: "h3",
    team_id: "ht5",
    submitted_by: "u4",
    title: "ZKident",
    description:
      "Privacy-preserving identity verification using zk-SNARKs. Prove you are over 18 or a citizen of a country without revealing your actual documents.",
    repo_url: "https://github.com/zklabs/zkident",
    demo_url: "https://zkident.vercel.app",
    status: "accepted",
    created_at: "2026-01-22T08:00:00Z",
    updated_at: "2026-01-22T14:00:00Z",
  },
];

export const hackathonLeaderboard: HackathonLeaderboardEntry[] = [
  {
    rank: 1,
    team_id: "ht5",
    team_name: "Zero Knowledge Labs",
    submission_title: "ZKident",
    avg_score: 94,
    judge_count: 3,
  },
  {
    rank: 2,
    team_id: "ht4",
    team_name: "DeFi Degen Squad",
    submission_title: "YieldMax Protocol",
    avg_score: 88,
    judge_count: 3,
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

export const organization = {
  id: "org1",
  name: "DevLink Labs",
  tagline: "Building the network for developers",
  logoUrl: "https://devlink.io/logo.svg",
  color: "from-primary-500 to-primary-600",
  members: 15,
  openPositions: 4,
  activeUsers: 3421,
  satisfaction: 97,
  team: [
    {
      id: "m1",
      name: "Nancy Patel",
      role: "Founder & CEO",
      department: "Executive",
      avatar: AV("Nancy"),
      joinedAt: "2022-01-15",
    },
    {
      id: "m2",
      name: "Rahul Verma",
      role: "Lead Developer",
      department: "Engineering",
      avatar: AV("Rahul"),
      joinedAt: "2022-03-20",
    },
    {
      id: "m3",
      name: "Ankit Singh",
      role: "Design Lead",
      department: "Design",
      avatar: AV("Ankit"),
      joinedAt: "2022-05-10",
    },
    {
      id: "m4",
      name: "Sneha Iyer",
      role: "Product Manager",
      department: "Product",
      avatar: AV("Sneha"),
      joinedAt: "2022-07-05",
    },
    {
      id: "m5",
      name: "Alex Johnson",
      role: "DevOps Engineer",
      department: "Engineering",
      avatar: AV("Alex"),
      joinedAt: "2023-01-10",
    },
  ],
  openings: [
    {
      id: "o1",
      title: "Senior Frontend Developer",
      location: "Remote",
      type: "Full-time",
    },
    {
      id: "o2",
      title: "UI/UX Designer",
      location: "San Francisco, CA",
      type: "Full-time",
    },
    {
      id: "o3",
      title: "DevOps Engineer",
      location: "New York, NY",
      type: "Contract",
    },
  ],
  projects: [
    {
      id: "p1",
      name: "DevLink Platform",
      category: "Web Application",
      description:
        "A network platform for developers to showcase their skills and connect with opportunities",
      website: "https://devlink.io",
      repoUrl: "https://github.com/devlink/platform",
    },
    {
      id: "p2",
      name: "Portfolio Builder",
      category: "Tool",
      description: "Customizable portfolio builder for developers",
      repoUrl: "https://github.com/devlink/portfolio-builder",
    },
    {
      id: "p3",
      name: "Flares API",
      category: "Backend",
      description: "API for creating and managing developer flares",
      repoUrl: "https://github.com/devlink/flares-api",
    },
  ],
  activity: [
    {
      id: "a1",
      type: "join",
      title: "Alex Johnson joined the team",
      description: "Started as DevOps Engineer",
      ago: "2 days ago",
      icon: "UserPlus",
    },
    {
      id: "a2",
      type: "project",
      title: "DevLink Platform v2.0 launched",
      description: "Major update with new features and improved performance",
      ago: "1 week ago",
      icon: "Globe",
    },
    {
      id: "a3",
      type: "hire",
      title: "Hiring Senior Frontend Developer",
      description: "Now hiring for remote position",
      ago: "3 days ago",
      icon: "Briefcase",
    },
  ],
};

export const currentUser = {
  id: "me",
  name: "Nancy Patel",
  handle: "nancy_dev",
  avatar: AV("Nancy"),
  premium: true,
  verified: true,
  profileSkills: [
    { name: "TypeScript", level: "Expert", category: "Languages", yearsOfExperience: 4 },
    { name: "React", level: "Expert", category: "Frameworks", yearsOfExperience: 4 },
    { name: "Python", level: "Advanced", category: "Languages", yearsOfExperience: 3 },
    { name: "FastAPI", level: "Advanced", category: "Frameworks", yearsOfExperience: 3 },
    { name: "PostgreSQL", level: "Intermediate", category: "Databases", yearsOfExperience: 2 },
    { name: "AWS", level: "Intermediate", category: "Cloud", yearsOfExperience: 2 },
    { name: "Docker", level: "Advanced", category: "DevOps", yearsOfExperience: 3 },
  ],
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

export interface QuickAction {
  id: ID;
  iconName: string;
  label: string;
  to: string;
}

export const quickActions: QuickAction[] = [
  { id: "qa1", iconName: "FolderPlus", label: "Continue current project", to: "/projects/p1" },
  { id: "qa2", iconName: "Users2", label: "Review applications", to: "/projects" },
  { id: "qa3", iconName: "Flame", label: "Publish flare", to: "/flares" },
  { id: "qa4", iconName: "UserPlus", label: "Invite recommended builder", to: "/builders" },
];
