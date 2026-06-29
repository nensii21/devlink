import { Builder, CurrentUser } from "../types/user";
export const ME:CurrentUser = {
  name: "Nancy Wells",
  role: "Full-Stack Engineer",
  avatar:
    "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=80&h=80&fit=crop&auto=format",
  location: "San Francisco, CA",
};

export const BUILDERS:Builder[] = [
  {
    id: 1,
    name: "Marcus Rivera",
    role: "ML Engineer",
    avatar:
      "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&auto=format",
    skills: ["Python", "PyTorch", "LangChain", "FastAPI"],
    bio: "Turning research papers into production ML systems. Previously DeepMind. 6 shipped products.",
    location: "Austin, TX",
    available: true,
    online: false,
    xp: "5 years",
  },
  {
    id: 2,
    name: "Priya Nair",
    role: "Cloud Architect",
    avatar:
      "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=80&h=80&fit=crop&auto=format",
    skills: ["Kubernetes", "Terraform", "Go", "AWS"],
    bio: "Infrastructure that scales from 0 to millions. Open-source contributor. Remote-first.",
    location: "Remote",
    available: true,
    online: true,
    xp: "6 years",
  },
  {
    id: 3,
    name: "James Okafor",
    role: "Mobile Developer",
    avatar:
      "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=80&h=80&fit=crop&auto=format",
    skills: ["Swift", "Kotlin", "React Native", "Expo"],
    bio: "Crafting native mobile experiences with real attention to detail. Apps with 1M+ downloads.",
    location: "London, UK",
    available: false,
    online: true,
    xp: "4 years",
  },
  {
    id: 4,
    name: "Elena Volkov",
    role: "Product Designer",
    avatar:
      "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=80&h=80&fit=crop&auto=format",
    skills: ["Figma", "Framer", "Design Systems", "Prototyping"],
    bio: "Systems thinker. Ex-Notion design team. Obsessed with craft, clarity, and shipping.",
    location: "Berlin, Germany",
    available: true,
    online: false,
    xp: "7 years",
  },
  {
    id: 5,
    name: "Taro Yamamoto",
    role: "Backend Engineer",
    avatar:
      "https://images.unsplash.com/photo-1547425260-76bcadfb4f2c?w=80&h=80&fit=crop&auto=format",
    skills: ["Go", "Rust", "PostgreSQL", "gRPC"],
    bio: "High-performance systems at scale. OSS contributor. Strong opinions about observability.",
    location: "Tokyo, Japan",
    available: true,
    online: true,
    xp: "8 years",
  },
  {
    id: 6,
    name: "Aisha Kamara",
    role: "AI Engineer",
    avatar:
      "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=80&h=80&fit=crop&auto=format",
    skills: ["Python", "TensorFlow", "RAG", "Vector DBs"],
    bio: "Building the layer between LLMs and real products. YC alum. Previously Scale AI.",
    location: "New York, NY",
    available: false,
    online: true,
    xp: "4 years",
  },
];