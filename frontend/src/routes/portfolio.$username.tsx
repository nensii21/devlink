import { createFileRoute, notFound, Link } from "@tanstack/react-router";
import React, { useState, useEffect } from "react";
import {
  MapPin,
  Calendar,
  Link as LinkIcon,
  Github,
  Twitter,
  Linkedin,
  Briefcase,
  Mail,
  Send,
  Settings,
  Sparkles,
  X,
  ChevronRight,
  Check,
  Award,
  Eye,
  MessageSquare,
  Heart,
  Globe,
  ArrowLeft,
  Terminal,
  LayoutGrid,
} from "lucide-react";
import { toast } from "sonner";
import { builders, currentUser, projects as allProjects, flares as allFlares } from "@/mocks/seed";

export const Route = createFileRoute("/portfolio/$username")({
  head: ({ params }) => ({
    meta: [
      { title: `@${params.username}'s Public Portfolio — DevLink` },
      {
        name: "description",
        content: `Browse projects, skills, and get in touch with @${params.username}.`,
      },
    ],
  }),
  component: PortfolioPage,
});

interface PortfolioPrefs {
  theme: "modern" | "warm" | "cyberpunk" | "glass" | "slate";
  accent: "violet" | "emerald" | "amber" | "rose" | "cyan";
  showProjects: boolean;
  showFlares: boolean;
  showContact: boolean;
}

const accentConfig = {
  violet: {
    text: "text-violet-500 dark:text-violet-450",
    bg: "bg-violet-600 dark:bg-violet-500",
    hoverBg: "hover:bg-violet-750 dark:hover:bg-violet-600",
    border: "border-violet-500/30",
    ring: "focus:ring-violet-500",
    glow: "shadow-violet-500/20",
    badge: "bg-violet-500/10 text-violet-600 dark:text-violet-400 border-violet-550/20",
    hex: "#8b5cf6",
  },
  emerald: {
    text: "text-emerald-500 dark:text-emerald-450",
    bg: "bg-emerald-600 dark:bg-emerald-500",
    hoverBg: "hover:bg-emerald-750 dark:hover:bg-emerald-600",
    border: "border-emerald-500/30",
    ring: "focus:ring-emerald-500",
    glow: "shadow-emerald-500/20",
    badge: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-550/20",
    hex: "#10b981",
  },
  amber: {
    text: "text-amber-600 dark:text-amber-450",
    bg: "bg-amber-600 dark:bg-amber-500",
    hoverBg: "hover:bg-amber-750 dark:hover:bg-amber-600",
    border: "border-amber-500/30",
    ring: "focus:ring-amber-500",
    glow: "shadow-amber-500/20",
    badge: "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-550/20",
    hex: "#d97706",
  },
  rose: {
    text: "text-rose-500 dark:text-rose-450",
    bg: "bg-rose-600 dark:bg-rose-500",
    hoverBg: "hover:bg-rose-750 dark:hover:bg-rose-600",
    border: "border-rose-500/30",
    ring: "focus:ring-rose-500",
    glow: "shadow-rose-500/20",
    badge: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-550/20",
    hex: "#f43f5e",
  },
  cyan: {
    text: "text-cyan-600 dark:text-cyan-455",
    bg: "bg-cyan-600 dark:bg-cyan-500",
    hoverBg: "hover:bg-cyan-750 dark:hover:bg-cyan-600",
    border: "border-cyan-500/30",
    ring: "focus:ring-cyan-500",
    glow: "shadow-cyan-500/20",
    badge: "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-550/20",
    hex: "#0891b2",
  },
};

function PortfolioPage() {
  const { username } = Route.useParams();
  const me = username === currentUser.handle;

  // Find builder details
  const b =
    builders.find((x) => x.handle === username) ||
    (me
      ? {
          id: "me",
          name: currentUser.name,
          handle: currentUser.handle,
          role: "Full Stack Developer",
          avatar: currentUser.avatar,
          country: "India",
          yearsExp: 3,
          matchScore: 96,
          skills: ["React", "Next.js", "TypeScript", "Node.js", "Python", "TailwindCSS"],
          online: true,
          bio: "Product engineer. Ships fast, sleeps sometimes. Love crafting delightful UX.",
        }
      : null);

  if (!b) throw notFound();

  // Get matching projects and flares
  const userProjects = allProjects.filter((p) => p.owner === b.name || p.owner === b.handle);
  const displayProjects =
    userProjects.length > 0
      ? userProjects
      : allProjects.filter((p) => p.stack.some((skill) => b.skills.includes(skill))).slice(0, 4);

  const displayFlares = allFlares.filter(
    (f) => f.author.handle === b.handle || f.author.name === b.name,
  );

  // States
  const [prefs, setPrefs] = useState<PortfolioPrefs>(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem(`devlink-portfolio-prefs-${username}`);

        if (stored) {
          return JSON.parse(stored);
        }
      } catch (error) {
        console.debug(" Failed to load portfolio preferences :", error);
      }
    }
    return {
      theme: "modern",
      accent: "violet",
      showProjects: true,
      showFlares: true,
      showContact: true,
    };
  });

  const [customizerOpen, setCustomizerOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    role: "recruiter",
    message: "",
    budget: "",
  });
  const [submitting, setSubmitting] = useState(false);

  // Read config from URL query parameters (useful for preview links)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const urlTheme = params.get("theme") as PortfolioPrefs["theme"];
      const urlAccent = params.get("accent") as PortfolioPrefs["accent"];
      const urlProjects = params.get("projects");
      const urlFlares = params.get("flares");
      const urlContact = params.get("contact");

      if (urlTheme || urlAccent || urlProjects || urlFlares || urlContact) {
        setPrefs((prev) => ({
          ...prev,
          theme: urlTheme || prev.theme,
          accent: urlAccent || prev.accent,
          showProjects: urlProjects !== null ? urlProjects === "true" : prev.showProjects,
          showFlares: urlFlares !== null ? urlFlares === "true" : prev.showFlares,
          showContact: urlContact !== null ? urlContact === "true" : prev.showContact,
        }));
      }
    }
  }, []);

  const handleSaveDefault = () => {
    localStorage.setItem(`devlink-portfolio-prefs-${username}`, JSON.stringify(prefs));
    toast.success("Theme preferences saved as your personal default!");
  };

  const handleCopyLink = () => {
    const url = `${window.location.origin}/portfolio/${username}?theme=${prefs.theme}&accent=${prefs.accent}&projects=${prefs.showProjects}&flares=${prefs.showFlares}&contact=${prefs.showContact}`;
    navigator.clipboard.writeText(url);
    toast.success("Customized portfolio link copied to clipboard!");
  };

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.message) {
      toast.error("Please fill in all required fields.");
      return;
    }
    setSubmitting(true);
    setTimeout(() => {
      const budgetText = formData.budget ? ` (Project Budget: $${formData.budget})` : "";
      const newNotification = {
        id: `noti-${Date.now()}`,
        kind: "invite" as const,
        text: `💼 Recruitment Inquirer "${formData.name}" sent a portfolio message: "${formData.message}"${budgetText}. Reply to ${formData.email}.`,
        ago: "Just now",
        unread: true,
      };

      try {
        const stored = localStorage.getItem("devlink-notifications");
        const currentNotis = stored ? JSON.parse(stored) : [];
        localStorage.setItem(
          "devlink-notifications",
          JSON.stringify([newNotification, ...currentNotis]),
        );
      } catch (error) {
        console.debug("Failed to save notification :", error);
      }

      toast.success("Your message has been sent to " + b.name + "!");
      setFormData({ name: "", email: "", role: "recruiter", message: "", budget: "" });
      setSubmitting(false);
    }, 1200);
  };

  const activeAccent = accentConfig[prefs.accent];

  // ==========================================
  // RENDER THEME STYLES
  // ==========================================

  // Theme 1: Modern Neon (Dark)
  const renderModernNeon = () => (
    <div className="min-h-screen bg-[#07090e] text-slate-100 font-sans relative overflow-hidden pb-20">
      {/* Glow auras */}
      <div
        className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full filter blur-[120px] opacity-10 pointer-events-none"
        style={{ backgroundColor: activeAccent.hex }}
      />
      <div
        className="absolute bottom-[20%] right-[-10%] w-[600px] h-[600px] rounded-full filter blur-[150px] opacity-[0.08] pointer-events-none"
        style={{ backgroundColor: activeAccent.hex }}
      />

      {/* Decorative Grid Lines */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0f172a_1px,transparent_1px),linear-gradient(to_bottom,#0f172a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-30 pointer-events-none" />

      <header className="border-b border-slate-800 bg-[#07090e]/80 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link
            to="/dashboard"
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-100 transition-colors"
          >
            <ArrowLeft size={14} /> Back to DevLink
          </Link>
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full ${activeAccent.badge} border`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
              Available for hire
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 pt-12 space-y-16 relative z-10">
        {/* Profile Card */}
        <section className="flex flex-col md:flex-row gap-8 items-center md:items-start text-center md:text-left bg-slate-900/40 border border-slate-800/80 p-8 rounded-2xl backdrop-blur-md">
          <div className="relative shrink-0">
            <img
              src={b.avatar}
              alt={b.name}
              className="w-28 h-28 rounded-2xl border-2 border-slate-700 bg-slate-800"
            />
            <div
              className={`absolute -bottom-1 -right-1 w-5 h-5 rounded-full border-4 border-[#07090e] bg-success`}
            />
          </div>
          <div className="space-y-4 flex-1">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                {b.name}
              </h1>
              <p className={`text-base font-semibold mt-1 ${activeAccent.text}`}>{b.role}</p>
              <div className="flex flex-wrap justify-center md:justify-start items-center gap-4 mt-3 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <MapPin size={13} /> {b.country}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar size={13} /> Active Builder
                </span>
                <span className="flex items-center gap-1">
                  <Globe size={13} /> devlink.io/portfolio/{b.handle}
                </span>
              </div>
            </div>
            <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">{b.bio}</p>
            <div className="flex justify-center md:justify-start items-center gap-2 pt-2">
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer"
                className="p-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-300 hover:text-white rounded-lg transition-colors"
              >
                <Github size={16} />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noreferrer"
                className="p-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-300 hover:text-white rounded-lg transition-colors"
              >
                <Twitter size={16} />
              </a>
              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noreferrer"
                className="p-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-300 hover:text-white rounded-lg transition-colors"
              >
                <Linkedin size={16} />
              </a>
            </div>
          </div>
        </section>

        {/* Skills Section */}
        <section className="space-y-4">
          <h2
            className="text-lg font-bold tracking-tight border-l-2 pl-3"
            style={{ borderColor: activeAccent.hex }}
          >
            Skills & Tech Stack
          </h2>
          <div className="flex flex-wrap gap-2">
            {b.skills.map((s) => (
              <span
                key={s}
                className={`px-3 py-1 rounded-lg text-xs font-semibold bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-colors`}
              >
                {s}
              </span>
            ))}
          </div>
        </section>

        {/* Projects Section */}
        {prefs.showProjects && (
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2
                className="text-lg font-bold tracking-tight border-l-2 pl-3"
                style={{ borderColor: activeAccent.hex }}
              >
                Featured Projects
              </h2>
              <span className="text-xs text-slate-400">
                Total Projects ({displayProjects.length})
              </span>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {displayProjects.map((p) => (
                <article
                  key={p.id}
                  className="p-6 bg-slate-900/30 border border-slate-800/80 rounded-xl hover:-translate-y-1 hover:border-slate-700 transition-all duration-300 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-2xl">{p.icon}</span>
                      <span
                        className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${activeAccent.badge}`}
                      >
                        {p.status}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-slate-100 mt-4">{p.name}</h3>
                    <p className="text-xs text-slate-400 mt-2 line-clamp-2 leading-relaxed">
                      {p.description}
                    </p>
                  </div>
                  <div className="mt-6 pt-4 border-t border-slate-800/60">
                    <div className="flex flex-wrap gap-1">
                      {p.stack.slice(0, 3).map((tech) => (
                        <span
                          key={tech}
                          className="text-[10px] text-slate-300 bg-slate-800 px-2 py-0.5 rounded"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        {/* Flares Section */}
        {prefs.showFlares && displayFlares.length > 0 && (
          <section className="space-y-4">
            <h2
              className="text-lg font-bold tracking-tight border-l-2 pl-3"
              style={{ borderColor: activeAccent.hex }}
            >
              Latest Dev Thoughts
            </h2>
            <div className="space-y-3">
              {displayFlares.map((f) => (
                <div
                  key={f.id}
                  className="p-5 bg-slate-900/20 border border-slate-850 rounded-xl space-y-3"
                >
                  <p className="text-xs text-slate-300 leading-relaxed">{f.content}</p>
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1">
                        <Heart size={11} /> {f.likes} likes
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageSquare size={11} /> {f.comments} replies
                      </span>
                    </div>
                    <span>{f.ago}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Contact Form */}
        {prefs.showContact && (
          <section className="bg-slate-900/50 border border-slate-800/80 p-8 rounded-2xl space-y-6">
            <div className="text-center md:text-left">
              <h2 className="text-xl font-bold tracking-tight">Hire or Message {b.name}</h2>
              <p className="text-xs text-slate-400 mt-1">
                Fill out this secure form. Your inquiry will arrive directly in their DevLink
                notification inbox.
              </p>
            </div>
            <form onSubmit={handleContactSubmit} className="space-y-4 max-w-2xl mx-auto md:mx-0">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">
                    Your Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full text-xs bg-slate-950 border border-slate-800 rounded-lg p-2.5 focus:outline-none focus:border-slate-600 transition-colors"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">
                    Your Email *
                  </label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full text-xs bg-slate-950 border border-slate-800 rounded-lg p-2.5 focus:outline-none focus:border-slate-600 transition-colors"
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">
                    Hiring Role
                  </label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full text-xs bg-slate-950 border border-slate-800 rounded-lg p-2.5 focus:outline-none focus:border-slate-600 transition-colors"
                  >
                    <option value="recruiter">Full-time Opportunity</option>
                    <option value="freelance">Freelance Contract</option>
                    <option value="collab">Hackathon / Open Source Teamup</option>
                    <option value="other">General / Hello</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">
                    Budget Est. (USD, Optional)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g. 5000"
                    value={formData.budget}
                    onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                    className="w-full text-xs bg-slate-950 border border-slate-800 rounded-lg p-2.5 focus:outline-none focus:border-slate-600 transition-colors"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-400 uppercase">
                  Message *
                </label>
                <textarea
                  rows={4}
                  required
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full text-xs bg-slate-950 border border-slate-800 rounded-lg p-2.5 focus:outline-none focus:border-slate-600 transition-colors resize-none"
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className={`w-full sm:w-auto px-5 py-2.5 rounded-lg text-xs font-semibold text-white flex items-center justify-center gap-1.5 transition-all ${submitting ? "opacity-80 cursor-not-allowed" : activeAccent.bg + " " + activeAccent.hoverBg}`}
              >
                <Send size={12} /> {submitting ? "Sending..." : "Submit Inquiry"}
              </button>
            </form>
          </section>
        )}
      </main>
    </div>
  );

  // Theme 2: Minimalist Warm (Light)
  const renderMinimalistWarm = () => (
    <div
      className="min-h-screen bg-[#f7f5f0] text-[#2c2a27] font-serif pb-20 border-t-8"
      style={{ borderTopColor: activeAccent.hex }}
    >
      <header className="border-b border-[#e2dec9] bg-[#f7f5f0]/80 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-3xl mx-auto px-4 py-6 flex items-center justify-between font-sans">
          <Link
            to="/dashboard"
            className="flex items-center gap-1.5 text-xs text-stone-500 hover:text-stone-900 transition-colors"
          >
            <ArrowLeft size={14} /> Back to DevLink
          </Link>
          <span className="text-[10px] uppercase font-bold tracking-widest border border-stone-800 px-2 py-0.5 rounded">
            PORTFOLIO PREVIEW
          </span>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 pt-16 space-y-20">
        {/* Profile Card */}
        <section className="space-y-6">
          <div className="flex flex-col items-center md:items-start md:flex-row gap-6">
            <img
              src={b.avatar}
              alt={b.name}
              className="w-24 h-24 rounded-full border border-stone-400 bg-stone-100 filter grayscale"
            />
            <div className="text-center md:text-left space-y-2">
              <h1 className="text-4xl font-normal tracking-tight font-serif text-[#1c1a18]">
                {b.name}
              </h1>
              <p
                className={`text-sm font-sans font-semibold tracking-wider uppercase ${activeAccent.text}`}
              >
                {b.role}
              </p>
              <div className="flex flex-wrap justify-center md:justify-start gap-4 text-xs font-sans text-stone-600 mt-2">
                <span>📍 {b.country}</span>
                <span>✨ 2026 ECSoc</span>
                <span>🌐 {b.handle}</span>
              </div>
            </div>
          </div>
          <div className="border-t border-b border-stone-300 py-6 my-2">
            <p className="text-base italic font-serif leading-relaxed text-[#403c37] max-w-2xl">
              {b.bio}
            </p>
          </div>
          <div className="flex justify-center md:justify-start items-center gap-3 pt-2 font-sans text-xs">
            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 text-stone-600 hover:text-stone-950 hover:underline"
            >
              <Github size={14} /> GitHub
            </a>
            <span>·</span>
            <a
              href="https://twitter.com"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 text-stone-600 hover:text-stone-950 hover:underline"
            >
              <Twitter size={14} /> Twitter
            </a>
            <span>·</span>
            <a
              href="https://linkedin.com"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 text-stone-600 hover:text-stone-950 hover:underline"
            >
              <Linkedin size={14} /> LinkedIn
            </a>
          </div>
        </section>

        {/* Skills Section */}
        <section className="space-y-4">
          <h2 className="text-xs uppercase tracking-widest font-sans font-bold text-stone-400">
            Core Expertise
          </h2>
          <div className="flex flex-wrap gap-x-6 gap-y-3 font-sans text-sm">
            {b.skills.map((s) => (
              <span key={s} className="text-stone-800 hover:underline cursor-pointer">
                {s}
              </span>
            ))}
          </div>
        </section>

        {/* Projects Section */}
        {prefs.showProjects && (
          <section className="space-y-6">
            <h2 className="text-xs uppercase tracking-widest font-sans font-bold text-stone-400">
              Selected Works
            </h2>
            <div className="space-y-8">
              {displayProjects.map((p) => (
                <div
                  key={p.id}
                  className="grid md:grid-cols-3 gap-4 border-b border-stone-200 pb-6 last:border-0"
                >
                  <div className="md:col-span-1">
                    <span className="text-xl mb-1 block">{p.icon}</span>
                    <h3 className="text-base font-bold text-[#1c1a18]">{p.name}</h3>
                    <p
                      className={`text-[10px] font-sans font-bold uppercase tracking-wider mt-1 ${activeAccent.text}`}
                    >
                      {p.status}
                    </p>
                  </div>
                  <div className="md:col-span-2 space-y-4">
                    <p className="text-sm leading-relaxed text-stone-600 font-serif">
                      {p.description}
                    </p>
                    <div className="flex flex-wrap gap-2 font-sans text-[11px]">
                      {p.stack.map((tech) => (
                        <span
                          key={tech}
                          className="px-2 py-0.5 bg-stone-200 rounded text-stone-700"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Contact Form */}
        {prefs.showContact && (
          <section className="border-t-2 border-stone-300 pt-10 space-y-6">
            <div className="space-y-1">
              <h2 className="text-xl font-bold tracking-tight">Initiate Inquiry</h2>
              <p className="text-xs font-sans text-stone-500">
                Reach out for collaborations, full-time engineering placement, or consulting
                projects.
              </p>
            </div>
            <form onSubmit={handleContactSubmit} className="space-y-4 font-sans text-xs">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="font-bold text-stone-700 uppercase">Your Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-[#f4f2ea] border border-stone-300 rounded p-2.5 focus:outline-none focus:border-stone-800 transition-colors"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-stone-700 uppercase">Your Email Address</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full bg-[#f4f2ea] border border-stone-300 rounded p-2.5 focus:outline-none focus:border-stone-800 transition-colors"
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="font-bold text-stone-700 uppercase">Role Type</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full bg-[#f4f2ea] border border-stone-300 rounded p-2.5 focus:outline-none focus:border-stone-800 transition-colors"
                  >
                    <option value="recruiter">Full-time Offer</option>
                    <option value="freelance">Freelance Consulting</option>
                    <option value="collab">Co-founding Project</option>
                    <option value="other">Message / Greeting</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-stone-700 uppercase">Project Budget (USD)</label>
                  <input
                    type="number"
                    placeholder="e.g. 5000"
                    value={formData.budget}
                    onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                    className="w-full bg-[#f4f2ea] border border-stone-300 rounded p-2.5 focus:outline-none focus:border-stone-800 transition-colors"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="font-bold text-stone-700 uppercase">Correspondence Details</label>
                <textarea
                  rows={4}
                  required
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full bg-[#f4f2ea] border border-stone-300 rounded p-2.5 focus:outline-none focus:border-stone-800 transition-colors resize-none"
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className={`w-full sm:w-auto px-6 py-3 border border-stone-800 font-bold uppercase tracking-wider hover:bg-stone-900 hover:text-white transition-colors duration-250 cursor-pointer`}
              >
                {submitting ? "Sending..." : "Submit Dispatch"}
              </button>
            </form>
          </section>
        )}
      </main>
    </div>
  );

  // Theme 3: Cyberpunk Grid
  const renderCyberpunk = () => (
    <div className="min-h-screen bg-black text-[#00ff66] font-mono pb-20 relative select-none">
      {/* Scanline effect */}
      <div className="absolute inset-0 bg-[linear-gradient(to_bottom,rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%)] bg-[size:100%_4px] pointer-events-none z-50" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(0,255,102,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(0,255,102,0.03)_1px,transparent_1px)] bg-[size:2rem_2rem] pointer-events-none" />

      <header className="border-b border-[#00ff66] bg-black sticky top-0 z-30">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link
            to="/dashboard"
            className="text-xs text-[#00ff66] hover:text-[#ff00ea] transition-colors flex items-center gap-1"
          >
            &lt;= DEVLINK_MAIN_SHELL
          </Link>
          <span className="text-xs animate-pulse text-[#ff00ea]">SYS_ONLINE // HOST:PORTFOLIO</span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 pt-12 space-y-16">
        {/* Profile Card */}
        <section className="border-2 border-[#00ff66] p-6 shadow-[6px_6px_0px_rgba(0,255,102,0.2)] bg-black relative">
          <div className="absolute top-2 right-2 text-[10px] text-[#ff00ea] uppercase tracking-wider">
            [ BUILDER_ID: {b.id.toUpperCase()} ]
          </div>
          <div className="flex flex-col sm:flex-row gap-6 items-center sm:items-start text-center sm:text-left">
            <img
              src={b.avatar}
              alt={b.name}
              className="w-24 h-24 border-2 border-[#00ff66] bg-[#111]"
            />
            <div className="space-y-3">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-[#00ff66]">
                  {b.name.toUpperCase()}
                </h1>
                <p className="text-xs mt-1 text-[#ff00ea]">&gt;&gt; {b.role.toUpperCase()}</p>
                <div className="flex flex-wrap justify-center sm:justify-start gap-4 text-[10px] text-[#00ff66]/80 mt-2">
                  <span>LOC: {b.country.toUpperCase()}</span>
                  <span>SCORE: {b.matchScore}%</span>
                  <span>NET: devlink.io/{b.handle}</span>
                </div>
              </div>
              <p className="text-xs leading-relaxed text-[#00ff66]/90 border-l border-[#ff00ea] pl-3 py-1">
                {b.bio}
              </p>
            </div>
          </div>
        </section>

        {/* Skills Section */}
        <section className="space-y-4">
          <h2 className="text-sm font-bold text-[#ff00ea] uppercase">[ // CORE_SKILLS ]</h2>
          <div className="flex flex-wrap gap-2">
            {b.skills.map((s) => (
              <span
                key={s}
                className="px-2 py-1 text-xs border border-[#00ff66] hover:bg-[#00ff66] hover:text-black transition-colors duration-150 cursor-crosshair"
              >
                [{s.toUpperCase()}]
              </span>
            ))}
          </div>
        </section>

        {/* Projects Section */}
        {prefs.showProjects && (
          <section className="space-y-6">
            <h2 className="text-sm font-bold text-[#ff00ea] uppercase">[ // GRID_PROJECTS ]</h2>
            <div className="grid gap-6 md:grid-cols-2">
              {displayProjects.map((p) => (
                <div
                  key={p.id}
                  className="border border-[#00ff66] p-6 shadow-[4px_4px_0px_rgba(0,255,102,0.15)] hover:shadow-[6px_6px_0px_rgba(255,0,234,0.3)] hover:border-[#ff00ea] transition-all bg-black flex flex-col justify-between"
                >
                  <div>
                    <div className="flex justify-between items-center text-[10px]">
                      <span>{p.icon} DATA_NODE</span>
                      <span className="text-[#ff00ea] border border-[#ff00ea] px-1">
                        {p.status}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-[#00ff66] mt-4">
                      {p.name.toUpperCase()}
                    </h3>
                    <p className="text-xs text-[#00ff66]/70 mt-2 line-clamp-3 leading-relaxed">
                      {p.description}
                    </p>
                  </div>
                  <div className="mt-6 pt-4 border-t border-[#00ff66]/20 text-[10px] flex flex-wrap gap-2 text-[#00ff66]/90">
                    {p.stack.map((tech) => (
                      <span key={tech}>#{tech.toUpperCase()}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Contact Form */}
        {prefs.showContact && (
          <section className="border-2 border-[#00ff66] p-6 shadow-[6px_6px_0px_rgba(0,255,102,0.2)] bg-black space-y-6">
            <div>
              <h2 className="text-sm font-bold text-[#ff00ea] uppercase">
                [ // TERMINAL_COMMUNICATIONS ]
              </h2>
              <p className="text-[10px] text-[#00ff66]/80 mt-1">
                ESTABLISH PORTFOLIO CONGESTION TUNNEL TO HOST DIRECTLY.
              </p>
            </div>
            <form onSubmit={handleContactSubmit} className="space-y-4 text-xs">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="font-bold text-[#ff00ea] block">ID_NAME *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-black border border-[#00ff66] text-[#00ff66] p-2 focus:outline-none focus:border-[#ff00ea] focus:ring-1 focus:ring-[#ff00ea]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-[#ff00ea] block">INBOX_EMAIL *</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full bg-black border border-[#00ff66] text-[#00ff66] p-2 focus:outline-none focus:border-[#ff00ea] focus:ring-1 focus:ring-[#ff00ea]"
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="font-bold text-[#ff00ea] block">REQUEST_ROLE</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full bg-black border border-[#00ff66] text-[#00ff66] p-2 focus:outline-none focus:border-[#ff00ea]"
                  >
                    <option value="recruiter">FULL_TIME_HIRE</option>
                    <option value="freelance">CONTRACT_FREELANCE</option>
                    <option value="collab">COLLAB_MISSION</option>
                    <option value="other">GEN_ALERT</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-[#ff00ea] block">BUDGET_VAL (USD)</label>
                  <input
                    type="number"
                    placeholder="e.g. 5000"
                    value={formData.budget}
                    onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                    className="w-full bg-black border border-[#00ff66] text-[#00ff66] p-2 focus:outline-none focus:border-[#ff00ea] focus:ring-1 focus:ring-[#ff00ea]"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="font-bold text-[#ff00ea] block">PAYLOAD_MESSAGE *</label>
                <textarea
                  rows={4}
                  required
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full bg-black border border-[#00ff66] text-[#00ff66] p-2 focus:outline-none focus:border-[#ff00ea] resize-none"
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-[#00ff66] hover:bg-[#ff00ea] hover:text-black text-black font-bold py-2.5 transition-colors cursor-pointer"
              >
                {submitting ? "[ UPLOADING_TRANSMISSION... ]" : "[ EXECUTE_SEND ]"}
              </button>
            </form>
          </section>
        )}
      </main>
    </div>
  );

  // Theme 4: Glassmorphic Mesh
  const renderGlass = () => (
    <div className="min-h-screen bg-[#070514] text-white pb-20 relative overflow-hidden font-sans">
      {/* Background glowing blurred gradients */}
      <div className="absolute top-[10%] left-[-15%] w-[450px] h-[450px] rounded-full mix-blend-screen filter blur-[100px] opacity-25 animate-pulse bg-gradient-to-tr from-violet-600 to-indigo-600 pointer-events-none" />
      <div className="absolute bottom-[20%] right-[-15%] w-[550px] h-[550px] rounded-full mix-blend-screen filter blur-[120px] opacity-20 bg-gradient-to-tr from-cyan-500 to-emerald-500 pointer-events-none" />
      <div className="absolute top-[50%] left-[30%] w-[350px] h-[350px] rounded-full mix-blend-screen filter blur-[90px] opacity-15 bg-gradient-to-tr from-rose-500 to-purple-600 pointer-events-none" />

      <header className="border-b border-white/10 bg-[#070514]/30 backdrop-blur-xl sticky top-0 z-30">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link
            to="/dashboard"
            className="text-xs text-white/60 hover:text-white transition-colors flex items-center gap-1"
          >
            <ArrowLeft size={14} /> Back to dashboard
          </Link>
          <span className="text-[10px] font-bold tracking-widest bg-white/10 px-2 py-0.5 rounded-full border border-white/20">
            SECURE PORTFOLIO
          </span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 pt-12 space-y-16 relative z-10">
        {/* Profile Card */}
        <section className="bg-white/5 border border-white/15 p-8 rounded-2xl backdrop-blur-xl shadow-[0_8px_32px_0_rgba(0,0,0,0.37)] flex flex-col md:flex-row gap-8 items-center md:items-start text-center md:text-left">
          <div className="relative shrink-0">
            <img
              src={b.avatar}
              alt={b.name}
              className="w-28 h-28 rounded-full border-2 border-white/20 bg-white/10"
            />
            <div
              className={`absolute -bottom-1 -right-1 w-5 h-5 rounded-full border-4 border-[#070514] bg-success`}
            />
          </div>
          <div className="space-y-4 flex-1">
            <div>
              <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-white to-white/60 bg-clip-text text-transparent">
                {b.name}
              </h1>
              <p className={`text-base font-semibold mt-1 ${activeAccent.text}`}>{b.role}</p>
              <div className="flex flex-wrap justify-center md:justify-start gap-4 text-xs text-white/60 mt-2">
                <span>📍 {b.country}</span>
                <span>🔥 Match Score: {b.matchScore}%</span>
                <span>🌐 devlink.io/{b.handle}</span>
              </div>
            </div>
            <p className="text-sm text-white/80 max-w-2xl leading-relaxed">{b.bio}</p>
            <div className="flex justify-center md:justify-start items-center gap-3 pt-2">
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer"
                className="p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white rounded-full transition-all"
              >
                <Github size={15} />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noreferrer"
                className="p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white rounded-full transition-all"
              >
                <Twitter size={15} />
              </a>
              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noreferrer"
                className="p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white rounded-full transition-all"
              >
                <Linkedin size={15} />
              </a>
            </div>
          </div>
        </section>

        {/* Skills Section */}
        <section className="space-y-4">
          <h2 className="text-base font-bold tracking-tight">Expertise</h2>
          <div className="flex flex-wrap gap-2">
            {b.skills.map((s) => (
              <span
                key={s}
                className="px-3.5 py-1.5 rounded-full text-xs bg-white/5 border border-white/10 backdrop-blur-md text-white/90 hover:bg-white/10 transition-colors"
              >
                {s}
              </span>
            ))}
          </div>
        </section>

        {/* Projects Section */}
        {prefs.showProjects && (
          <section className="space-y-6">
            <h2 className="text-base font-bold tracking-tight">Featured Operations</h2>
            <div className="grid gap-6 md:grid-cols-2">
              {displayProjects.map((p) => (
                <div
                  key={p.id}
                  className="p-6 bg-white/5 border border-white/10 hover:border-white/20 rounded-2xl backdrop-blur-md shadow-lg hover:-translate-y-1 transition-all duration-300 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-2xl">{p.icon}</span>
                      <span
                        className={`text-[9px] uppercase font-bold tracking-widest px-2.5 py-1 rounded-full bg-white/10 border border-white/20 ${activeAccent.text}`}
                      >
                        {p.status}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-white mt-4">{p.name}</h3>
                    <p className="text-xs text-white/70 mt-2 line-clamp-2 leading-relaxed">
                      {p.description}
                    </p>
                  </div>
                  <div className="mt-6 pt-4 border-t border-white/10 flex flex-wrap gap-1">
                    {p.stack.slice(0, 3).map((tech) => (
                      <span
                        key={tech}
                        className="text-[10px] text-white/90 bg-white/5 px-2 py-0.5 rounded border border-white/5"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Contact Form */}
        {prefs.showContact && (
          <section className="bg-white/5 border border-white/10 p-8 rounded-3xl backdrop-blur-xl space-y-6">
            <div>
              <h2 className="text-lg font-bold tracking-tight">Connect Channels</h2>
              <p className="text-xs text-white/60 mt-1">
                Submit hiring inquiries or collaboration request tokens directly to {b.name}.
              </p>
            </div>
            <form onSubmit={handleContactSubmit} className="space-y-4 text-xs">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="font-semibold text-white/70 uppercase">Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 focus:border-white/30 rounded-xl p-3 focus:outline-none transition-all text-white"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-white/70 uppercase">Email *</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 focus:border-white/30 rounded-xl p-3 focus:outline-none transition-all text-white"
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="font-semibold text-white/70 uppercase">Inquiry Type</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 focus:outline-none text-white [&>option]:bg-[#070514]"
                  >
                    <option value="recruiter">Employment</option>
                    <option value="freelance">Freelance Contract</option>
                    <option value="collab">Collaboration</option>
                    <option value="other">General Inbox</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-white/70 uppercase">Budget (USD)</label>
                  <input
                    type="number"
                    placeholder="e.g. 5000"
                    value={formData.budget}
                    onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 focus:border-white/30 rounded-xl p-3 focus:outline-none transition-all text-white"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="font-semibold text-white/70 uppercase">Detailed Memo *</label>
                <textarea
                  rows={4}
                  required
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 focus:border-white/30 rounded-xl p-3 focus:outline-none transition-all resize-none text-white"
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className={`w-full sm:w-auto px-6 py-3 rounded-xl font-bold transition-all bg-white text-[#070514] hover:bg-white/90 flex items-center justify-center gap-1.5 cursor-pointer`}
              >
                <Send size={12} /> {submitting ? "Transmitting..." : "Send Secure Message"}
              </button>
            </form>
          </section>
        )}
      </main>
    </div>
  );

  // Theme 5: Slate Professional
  const renderSlate = () => (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans pb-20">
      <header className="border-b border-slate-900 bg-slate-950/80 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link
            to="/dashboard"
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1.5"
          >
            <ArrowLeft size={14} /> Return to App
          </Link>
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md ${activeAccent.badge}`}
            >
              Active Portfolio
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 pt-12 space-y-16">
        {/* Profile Card */}
        <section className="bg-slate-900 border border-slate-800 p-8 rounded-xl flex flex-col md:flex-row gap-8 items-center md:items-start text-center md:text-left shadow-lg">
          <div className="shrink-0">
            <img
              src={b.avatar}
              alt={b.name}
              className="w-24 h-24 rounded-lg border border-slate-700 bg-slate-950"
            />
          </div>
          <div className="space-y-4 flex-1">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">{b.name}</h1>
              <p className={`text-sm font-semibold mt-0.5 ${activeAccent.text}`}>{b.role}</p>
              <div className="flex flex-wrap justify-center md:justify-start gap-4 text-xs text-slate-400 mt-2">
                <span>📍 {b.country}</span>
                <span>🚀 Exp: {b.yearsExp} Years</span>
                <span>🌐 @{b.handle}</span>
              </div>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">{b.bio}</p>
            <div className="flex justify-center md:justify-start items-center gap-3 pt-2">
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer"
                className="text-slate-400 hover:text-white transition-colors"
              >
                <Github size={16} />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noreferrer"
                className="text-slate-400 hover:text-white transition-colors"
              >
                <Twitter size={16} />
              </a>
              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noreferrer"
                className="text-slate-400 hover:text-white transition-colors"
              >
                <Linkedin size={16} />
              </a>
            </div>
          </div>
        </section>

        {/* Skills Section */}
        <section className="space-y-4 bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
            Stack Expertise
          </h2>
          <div className="flex flex-wrap gap-2">
            {b.skills.map((s) => (
              <span
                key={s}
                className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-xs text-slate-300"
              >
                {s}
              </span>
            ))}
          </div>
        </section>

        {/* Projects Section */}
        {prefs.showProjects && (
          <section className="space-y-6">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
              Featured Projects
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              {displayProjects.map((p) => (
                <div
                  key={p.id}
                  className="p-6 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl transition-all flex flex-col justify-between shadow-sm"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{p.icon}</span>
                        <h3 className="text-sm font-bold text-white">{p.name}</h3>
                      </div>
                      <span
                        className={`text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-950 border border-slate-800 ${activeAccent.text}`}
                      >
                        {p.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-3 line-clamp-2 leading-relaxed">
                      {p.description}
                    </p>
                  </div>
                  <div className="mt-6 pt-4 border-t border-slate-800 flex flex-wrap gap-1.5 text-[10px] text-slate-300">
                    {p.stack.slice(0, 3).map((tech) => (
                      <span key={tech} className="bg-slate-950 px-2 py-0.5 rounded">
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Contact Form */}
        {prefs.showContact && (
          <section className="bg-slate-900 border border-slate-800 p-8 rounded-xl space-y-6">
            <div>
              <h2 className="text-lg font-bold tracking-tight text-white">Contact & Hire</h2>
              <p className="text-xs text-slate-400 mt-1">
                Submit inquiries directly to {b.name}. Leads are delivered to their DevLink
                dashboard.
              </p>
            </div>
            <form onSubmit={handleContactSubmit} className="space-y-4 text-xs">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Your Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded p-2.5 focus:outline-none focus:border-slate-700 transition-colors text-white"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Your Email *</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded p-2.5 focus:outline-none focus:border-slate-700 transition-colors text-white"
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Topic</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded p-2.5 focus:outline-none text-white"
                  >
                    <option value="recruiter">Full-time Contract</option>
                    <option value="freelance">Freelance Build</option>
                    <option value="collab">Hackathon Project</option>
                    <option value="other">General Inbox</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Budget Est. (USD)</label>
                  <input
                    type="number"
                    placeholder="e.g. 5000"
                    value={formData.budget}
                    onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded p-2.5 focus:outline-none focus:border-slate-700 transition-colors text-white"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Message details *</label>
                <textarea
                  rows={4}
                  required
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2.5 focus:outline-none focus:border-slate-700 transition-colors resize-none text-white"
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className={`w-full sm:w-auto px-5 py-2.5 rounded text-xs font-semibold text-white flex items-center justify-center gap-1.5 transition-colors cursor-pointer ${submitting ? "opacity-80 cursor-not-allowed" : activeAccent.bg + " " + activeAccent.hoverBg}`}
              >
                <Send size={12} /> {submitting ? "Sending..." : "Submit Inquiry"}
              </button>
            </form>
          </section>
        )}
      </main>
    </div>
  );

  return (
    <div className="relative">
      {/* Floating Customizer Button */}
      {me && (
        <button
          onClick={() => setCustomizerOpen(true)}
          className="fixed bottom-6 right-6 z-40 bg-primary hover:scale-105 active:scale-95 text-white font-bold p-4 rounded-full shadow-[0_4px_20px_rgba(5,183,215,0.4)] flex items-center gap-2 transition-all cursor-pointer"
        >
          <Settings size={18} />
          <span className="text-xs">Customize Portfolio</span>
        </button>
      )}

      {/* Render selected theme */}
      {prefs.theme === "modern" && renderModernNeon()}
      {prefs.theme === "warm" && renderMinimalistWarm()}
      {prefs.theme === "cyberpunk" && renderCyberpunk()}
      {prefs.theme === "glass" && renderGlass()}
      {prefs.theme === "slate" && renderSlate()}

      {/* Floating Customizer Drawer */}
      {customizerOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden font-sans">
          {/* Overlay */}
          <div
            onClick={() => setCustomizerOpen(false)}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />

          <div className="absolute inset-y-0 right-0 max-w-full flex">
            <div className="w-screen max-w-sm bg-slate-900 text-white border-l border-slate-800 p-6 flex flex-col justify-between shadow-2xl">
              <div className="space-y-6 overflow-y-auto pr-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold flex items-center gap-1.5">
                    <Sparkles size={16} className="text-primary animate-pulse" /> Portfolio
                    Customizer
                  </h3>
                  <button
                    onClick={() => setCustomizerOpen(false)}
                    className="p-1 text-slate-400 hover:text-white rounded-lg animate-fade-in"
                  >
                    <X size={18} />
                  </button>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">
                  Design how other people see your profile. Your selection will auto-load when they
                  visit your public url.
                </p>

                {/* Theme selection */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                    1. Layout Template
                  </span>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { key: "modern", label: "Modern Neon" },
                      { key: "warm", label: "Minimalist Warm" },
                      { key: "cyberpunk", label: "Cyberpunk Console" },
                      { key: "glass", label: "Glassmorphism" },
                      { key: "slate", label: "Slate Pro" },
                    ].map((item) => (
                      <button
                        key={item.key}
                        onClick={() =>
                          setPrefs({ ...prefs, theme: item.key as PortfolioPrefs["theme"] })
                        }
                        className={`text-xs p-3 rounded-lg border text-left flex flex-col justify-between h-18 transition-all ${prefs.theme === item.key ? "border-primary bg-primary-soft/10 text-primary font-bold shadow-md" : "border-slate-800 bg-slate-950 hover:border-slate-700 text-slate-300"}`}
                      >
                        <span className="text-[10px] uppercase opacity-75">Theme</span>
                        <span>{item.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Accent selection */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                    2. Accent Color
                  </span>
                  <div className="flex items-center gap-3">
                    {(Object.keys(accentConfig) as Array<keyof typeof accentConfig>).map((c) => (
                      <button
                        key={c}
                        onClick={() => setPrefs({ ...prefs, accent: c })}
                        className={`w-6 h-6 rounded-full border-2 transition-all flex items-center justify-center ${prefs.accent === c ? "border-white scale-110 shadow-lg" : "border-transparent opacity-80 hover:opacity-100"}`}
                        style={{ backgroundColor: accentConfig[c].hex }}
                      >
                        {prefs.accent === c && <Check size={12} className="text-white" />}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Toggle Visibility */}
                <div className="space-y-3 pt-2">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                    3. Display Sections
                  </span>
                  <div className="space-y-2.5">
                    <label className="flex items-center justify-between text-xs text-slate-300 cursor-pointer">
                      <span>Show Portfolio Projects</span>
                      <input
                        type="checkbox"
                        checked={prefs.showProjects}
                        onChange={(e) => setPrefs({ ...prefs, showProjects: e.target.checked })}
                        className="rounded border-slate-800 bg-slate-950 text-primary focus:ring-primary w-4 h-4"
                      />
                    </label>
                    <label className="flex items-center justify-between text-xs text-slate-300 cursor-pointer">
                      <span>Show Dev Thoughts / Flares</span>
                      <input
                        type="checkbox"
                        checked={prefs.showFlares}
                        onChange={(e) => setPrefs({ ...prefs, showFlares: e.target.checked })}
                        className="rounded border-slate-800 bg-slate-950 text-primary focus:ring-primary w-4 h-4"
                      />
                    </label>
                    <label className="flex items-center justify-between text-xs text-slate-300 cursor-pointer">
                      <span>Show Direct Hire Lead Form</span>
                      <input
                        type="checkbox"
                        checked={prefs.showContact}
                        onChange={(e) => setPrefs({ ...prefs, showContact: e.target.checked })}
                        className="rounded border-slate-800 bg-slate-950 text-primary focus:ring-primary w-4 h-4"
                      />
                    </label>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-2 pt-6 border-t border-slate-800">
                <button
                  onClick={handleSaveDefault}
                  className="w-full bg-primary hover:opacity-90 text-white font-bold py-2.5 rounded-lg text-xs transition-opacity cursor-pointer"
                >
                  Save as Default Template
                </button>
                <button
                  onClick={handleCopyLink}
                  className="w-full border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white font-semibold py-2.5 rounded-lg text-xs transition-all cursor-pointer"
                >
                  Copy Shareable URL
                </button>
                <button
                  onClick={() => {
                    setCustomizerOpen(false);
                    // navigate to profile
                    window.history.back();
                  }}
                  className="w-full text-center text-[11px] text-slate-500 hover:text-slate-400 hover:underline block pt-2 cursor-pointer"
                >
                  Return to Dashboard profile
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
