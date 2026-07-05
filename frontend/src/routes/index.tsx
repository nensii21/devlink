import { createFileRoute, Link } from "@tanstack/react-router";
import { APP_LOGO } from "@/lib/logo";
import { useTheme } from "@/hooks/useTheme";
import { motion } from "framer-motion";
import {
  Sparkles,
  Users2,
  MessageSquare,
  Trophy,
  Github,
  ArrowRight,
  Check,
  Moon,
  Sun,
} from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "DevLink — Find your next collaborator" },
      {
        name: "description",
        content:
          "DevLink is a developer collaboration platform. Match with builders using AI, run projects together, chat in real time, and win hackathons.",
      },
      { property: "og:title", content: "DevLink — Find your next collaborator" },
      {
        property: "og:description",
        content: "AI-powered matching, projects, messaging and hackathons in one place.",
      },
    ],
  }),
  component: Landing,
});

function Landing() {
  const { isDark, toggleTheme } = useTheme();
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-20 border-b border-border bg-surface/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2">
            <img src={APP_LOGO} alt="" className="h-7 w-7 rounded-md" />
            <span className="text-[16px] font-bold tracking-tight text-foreground">DevLink</span>
          </Link>
          <nav className="ml-6 hidden items-center gap-5 text-[13px] font-medium text-muted-foreground md:flex">
            <a href="#features" className="hover:text-foreground">
              Features
            </a>
            <a href="#builders" className="hover:text-foreground">
              Builders
            </a>
            <a href="#pricing" className="hover:text-foreground">
              Pricing
            </a>
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
              title={isDark ? "Switch to light mode" : "Switch to dark mode"}
              className="grid h-9 w-9 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <Link
              to="/auth"
              className="rounded-md px-3 py-1.5 text-[13px] font-medium text-foreground hover:bg-muted"
            >
              Sign in
            </Link>
            <Link
              to="/auth"
              className="rounded-md bg-primary px-3 py-1.5 text-[13px] font-semibold text-primary-foreground hover:opacity-90"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      <section className="border-b border-border">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24 text-center">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-[12px] font-medium text-muted-foreground">
              <Sparkles size={12} className="text-primary" /> AI-powered team matching · in beta
            </span>
            <h1 className="mx-auto mt-6 max-w-3xl text-[36px] font-bold leading-tight tracking-tight text-foreground sm:text-[52px]">
              Where builders connect, <span className="text-primary">collaborate</span> and ship.
            </h1>
            <p className="mx-auto mt-4 max-w-xl text-[15px] text-muted-foreground">
              Match with teammates by skills and vibe, run projects with real-time messaging, and
              enter hackathons together — all in one clean workspace.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link
                to="/auth"
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-[14px] font-semibold text-primary-foreground hover:opacity-90"
              >
                Start free <ArrowRight size={14} />
              </Link>
              <Link
                to="/auth"
                className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-4 py-2 text-[14px] font-medium text-foreground hover:bg-muted"
              >
                <Github size={14} /> Continue with GitHub
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <section id="features" className="border-b border-border">
        <div className="mx-auto grid max-w-6xl gap-4 px-4 py-16 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
          {[
            {
              icon: Sparkles,
              title: "AI matches",
              desc: "Rank teammates by skill, availability and past work.",
            },
            {
              icon: Users2,
              title: "Builder profiles",
              desc: "One profile, everywhere. Skills, stack, contributions.",
            },
            {
              icon: MessageSquare,
              title: "Real-time chat",
              desc: "Threaded conversations with your team, in-app.",
            },
            {
              icon: Trophy,
              title: "Hackathons",
              desc: "Discover jams, form teams, ship in a weekend.",
            },
          ].map((f) => (
            <div key={f.title} className="rounded-md border border-border bg-card p-5">
              <span className="grid h-9 w-9 place-items-center rounded-md bg-primary-soft text-primary">
                <f.icon size={16} />
              </span>
              <p className="mt-3 text-[15px] font-semibold text-foreground">{f.title}</p>
              <p className="mt-1 text-[13px] text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="pricing" className="border-b border-border">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <div className="text-center">
            <h2 className="text-[28px] font-bold tracking-tight text-foreground">
              Free while you're building.
            </h2>
            <p className="mt-2 text-[14px] text-muted-foreground">
              Upgrade when your team grows. No credit card required.
            </p>
          </div>
          <div className="mx-auto mt-8 grid max-w-3xl gap-4 sm:grid-cols-2">
            {[
              {
                name: "Free",
                price: "$0",
                perks: ["Up to 3 projects", "AI matching", "Community feed"],
              },
              {
                name: "Pro",
                price: "$12/mo",
                perks: ["Unlimited projects", "Priority AI", "Team analytics", "Priority support"],
                featured: true,
              },
            ].map((p) => (
              <div
                key={p.name}
                className={`rounded-md border p-5 ${p.featured ? "border-primary bg-primary-soft/40" : "border-border bg-card"}`}
              >
                <p className="text-[13px] font-semibold text-muted-foreground">{p.name}</p>
                <p className="mt-1 text-[28px] font-bold text-foreground">{p.price}</p>
                <ul className="mt-4 space-y-1.5 text-[13px] text-foreground">
                  {p.perks.map((perk) => (
                    <li key={perk} className="flex items-center gap-2">
                      <Check size={14} className="text-success" /> {perk}
                    </li>
                  ))}
                </ul>
                <Link
                  to="/auth"
                  className={`mt-5 inline-flex w-full items-center justify-center rounded-md px-3 py-2 text-[13px] font-semibold ${
                    p.featured
                      ? "bg-primary text-primary-foreground hover:opacity-90"
                      : "border border-border bg-surface text-foreground hover:bg-muted"
                  }`}
                >
                  Get started
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-border bg-surface">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-6 sm:px-6">
          <div className="flex items-center gap-2">
            <img src={APP_LOGO} alt="" className="h-6 w-6 rounded" />
            <span className="text-[13px] font-semibold text-foreground">DevLink</span>
            <span className="text-[12px] text-muted-foreground">© {new Date().getFullYear()}</span>
          </div>
          <div className="flex items-center gap-5 text-[12px] text-muted-foreground">
            {["Privacy", "Security", "Terms", "Status"].map((l) => (
              <a key={l} href="#" className="hover:text-primary hover:underline">
                {l}
              </a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
