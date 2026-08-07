import React from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { APP_LOGO } from "@/lib/logo";
import { motion } from "framer-motion";
import { Sparkles, Users2, MessageSquare, Trophy, Github, ArrowRight, Check } from "lucide-react";
import {
  Sun,
  Moon,
  X,
  Menu,
  HelpCircle,
  Shield,
  CreditCard,
  ChevronDown,
  CheckCircle2,
  Zap,
  ArrowUpRight,
  Lock,
} from "lucide-react";
import { AnimatePresence } from "framer-motion";
import { useTheme } from "@/hooks/useTheme";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

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
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const faqs = [
    {
      question: "Is DevLink free to use?",
      answer:
        "Yes. You can start using DevLink for free to discover builders, create projects, and collaborate with your team.",
    },
    {
      question: "How does AI matching work?",
      answer:
        "Our AI recommends collaborators by analyzing skills, interests, project history, and availability to help you build balanced teams.",
    },
    {
      question: "Can I invite my team?",
      answer:
        "Yes. You can collaborate with teammates, manage projects together, and communicate in one shared workspace.",
    },
    {
      question: "Which authentication methods are supported?",
      answer:
        "You can sign in securely using GitHub, with support for additional authentication methods as the platform grows.",
    },
    {
      question: "How is my data protected?",
      answer:
        "Your account data is handled securely, and privacy is a priority. Sensitive information is protected using industry-standard security practices.",
    },
  ];
  const [billingCycle, setBillingCycle] = React.useState<"monthly" | "yearly">("yearly");
  const [openFaq, setOpenFaq] = React.useState<number | null>(0);
  const [activeSection, setActiveSection] = React.useState("features");

  React.useEffect(() => {
    document.documentElement.style.scrollBehavior = "smooth";

    const sections = ["features", "pricing"];

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { threshold: 0.5 },
    );

    sections.forEach((id) => {
      const section = document.getElementById(id);
      if (section) observer.observe(section);
    });

    return () => {
      observer.disconnect();
      document.documentElement.style.scrollBehavior = "";
    };
  }, []);

  const primaryBtnClass =
    "inline-flex items-center justify-center gap-1.5 rounded-xl bg-primary px-5 py-3 text-[14px] font-semibold text-primary-foreground shadow-[0_4px_12px_rgba(5,183,215,0.25)] transition-all duration-300 hover:bg-primary/95 hover:shadow-[0_6px_20px_rgba(5,183,215,0.4)] hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] cursor-pointer";
  const secondaryBtnClass =
    "inline-flex items-center justify-center gap-1.5 rounded-xl border border-border bg-surface px-5 py-3 text-[14px] font-medium text-foreground transition-all duration-300 hover:bg-muted hover:border-foreground/10 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] cursor-pointer";

  React.useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }

    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-20 border-b border-border bg-surface/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2">
            <img src={APP_LOGO} alt="" className="h-9 w-9 rounded-md" />
            <span className="text-[20px] font-bold tracking-tight text-foreground">DevLink</span>
          </Link>
          <nav className="ml-6 hidden items-center gap-5 text-[13px] font-medium text-muted-foreground md:flex">
            <a
              href="#features"
              className={
                activeSection === "features"
                  ? "text-foreground font-semibold"
                  : "hover:text-foreground text-muted-foreground"
              }
            >
              Features
            </a>
            <Link to="/builders" className="hover:text-foreground">
              Builders
            </Link>
            <a
              href="#pricing"
              className={
                activeSection === "pricing"
                  ? "text-foreground font-semibold"
                  : "hover:text-foreground text-muted-foreground"
              }
            >
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
            <button
              type="button"
              className="md:hidden rounded-md p-2 hover:bg-muted"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>

            <div className="hidden md:flex items-center gap-2">
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
        </div>
      </header>
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.2 }}
            className="md:hidden border-b border-border bg-surface"
          >
            <div className="flex flex-col px-4 py-4 space-y-3">
              <a
                href="#features"
                className={
                  activeSection === "features"
                    ? "text-sm font-semibold text-foreground"
                    : "text-sm text-muted-foreground"
                }
                onClick={() => setMobileMenuOpen(false)}
              >
                Features
              </a>

              <Link
                to="/builders"
                className="text-sm text-foreground"
                onClick={() => setMobileMenuOpen(false)}
              >
                Builders
              </Link>

              <a
                href="#pricing"
                className={
                  activeSection === "pricing"
                    ? "text-sm font-semibold text-foreground"
                    : "text-sm text-muted-foreground"
                }
                onClick={() => setMobileMenuOpen(false)}
              >
                Pricing
              </a>

              <Link
                to="/auth"
                onClick={() => setMobileMenuOpen(false)}
                className="rounded-md border border-border px-3 py-2 text-center"
              >
                Sign In
              </Link>

              <Link
                to="/auth"
                onClick={() => setMobileMenuOpen(false)}
                className="rounded-md bg-primary px-3 py-2 text-center text-primary-foreground"
              >
                Get Started
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <section className="border-b border-border bg-gradient-to-b from-background to-surface/20">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:py-16">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="grid gap-12 lg:grid-cols-12 lg:items-center"
          >
            {/* Left Column: Heading, description, CTA, Trust indicators */}
            <div className="lg:col-span-6 flex flex-col justify-center text-center lg:text-left">
              <span className="inline-flex w-fit mx-auto lg:mx-0 items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-[12px] font-medium text-muted-foreground mb-6">
                <Sparkles size={12} className="text-primary" /> AI-powered team matching · in beta
              </span>
              <h1 className="text-[36px] font-extrabold leading-tight tracking-tight text-foreground sm:text-[48px] lg:text-[50px]">
                Where builders connect, <span className="text-primary">collaborate</span> and ship.
              </h1>
              <p className="mt-4 text-[15px] text-muted-foreground leading-relaxed max-w-xl mx-auto lg:mx-0">
                Match with teammates by skills and vibe, run projects with real-time messaging, and
                enter hackathons together — all in one clean workspace.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-3">
                <Link to="/auth" className={primaryBtnClass}>
                  Start free <ArrowRight size={15} />
                </Link>
                <Link to="/auth" className={secondaryBtnClass}>
                  <Github size={15} /> Continue with GitHub
                </Link>
              </div>
              
              {/* Trust Indicators */}
              <div className="mt-6 flex flex-wrap items-center justify-center lg:justify-start gap-x-5 gap-y-2 text-[12px] text-muted-foreground font-medium border-t border-border/40 pt-4">
                <span className="flex items-center gap-1">
                  <Check size={14} className="text-success" /> Free for hobbyists
                </span>
                <span className="flex items-center gap-1">
                  <Check size={14} className="text-success" /> No credit card required
                </span>
                <span className="flex items-center gap-1">
                  <Check size={14} className="text-success" /> 10k+ developers
                </span>
              </div>
            </div>

            {/* Right Column: Dashboard preview (above the fold) */}
            <div className="lg:col-span-6 relative w-full flex justify-center lg:justify-end">
              {/* Decorative background glow behind preview */}
              <div className="absolute inset-0 -m-8 bg-primary/5 rounded-full blur-[100px] pointer-events-none" />
              
              <div className="w-full max-w-lg rounded-2xl border border-border bg-surface shadow-2xl overflow-hidden relative">
                {/* Mock Window Header */}
                <div className="bg-muted/50 border-b border-border px-4 py-3 flex items-center justify-between">
                  <div className="flex gap-1.5">
                    <span className="h-3 w-3 rounded-full bg-[#ff5f56]" />
                    <span className="h-3 w-3 rounded-full bg-[#ffbd2e]" />
                    <span className="h-3 w-3 rounded-full bg-[#27c93f]" />
                  </div>
                  <span className="text-[11px] font-medium text-muted-foreground tracking-tight select-none">app.devlink.com</span>
                  <div className="w-12" /> {/* Spacing spacer */}
                </div>
                
                {/* Mock Window Body */}
                <div className="flex h-[320px] bg-background text-[13px] text-foreground relative">
                  {/* Mock Sidebar */}
                  <div className="w-[50px] border-r border-border bg-surface flex flex-col items-center py-4 gap-5 shrink-0">
                    <img src={APP_LOGO} alt="" className="h-6 w-6 rounded-md" />
                    <div className="flex flex-col gap-4 items-center w-full mt-2">
                      <span className="h-8 w-8 rounded-lg bg-primary-soft text-primary flex items-center justify-center"><Users2 size={16} /></span>
                      <span className="h-8 w-8 rounded-lg text-muted-foreground hover:bg-muted flex items-center justify-center"><MessageSquare size={16} /></span>
                      <span className="h-8 w-8 rounded-lg text-muted-foreground hover:bg-muted flex items-center justify-center"><Trophy size={16} /></span>
                      <span className="h-8 w-8 rounded-lg text-muted-foreground hover:bg-muted flex items-center justify-center"><Sparkles size={16} /></span>
                    </div>
                  </div>
                  
                  {/* Mock Main Content Area */}
                  <div className="flex-1 p-4 flex flex-col gap-4 overflow-hidden relative">
                    <div className="flex items-center justify-between border-b border-border pb-2">
                      <h4 className="font-bold text-foreground text-[14px]">Workspace Dashboard</h4>
                      <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full font-medium">Dev Mode</span>
                    </div>
                    
                    {/* Mock Active Project Card */}
                    <div className="rounded-xl border border-border bg-surface p-3 shadow-sm flex flex-col gap-2 shrink-0">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-foreground">Project: EduGrade-System</span>
                        <span className="text-[10px] bg-success-soft text-success px-2 py-0.5 rounded-full font-bold">Active</span>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-muted-foreground mt-1">
                        <span>Frontend Phase</span>
                        <span>85% Completed</span>
                      </div>
                      <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-primary rounded-full" style={{ width: '85%' }} />
                      </div>
                      <div className="flex gap-1.5 mt-1">
                        <span className="h-5 w-5 rounded-full bg-primary-soft text-primary text-[10px] font-bold flex items-center justify-center border border-border">AR</span>
                        <span className="h-5 w-5 rounded-full bg-secondary text-foreground text-[10px] font-bold flex items-center justify-center border border-border">PM</span>
                        <span className="h-5 w-5 rounded-full border border-dashed border-border text-muted-foreground text-[10px] font-bold flex items-center justify-center border border-border">+</span>
                      </div>
                    </div>
                    
                    {/* Mock AI Match Popup */}
                    <div className="rounded-xl border border-primary/20 bg-primary-soft/10 p-3 flex flex-col gap-1 shadow-sm shrink-0">
                      <span className="text-[10px] font-bold text-primary tracking-wider uppercase">AI Match Recommendation</span>
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-foreground">Alex Rivera (React Lead)</span>
                        <span className="text-[11px] font-bold text-success bg-success-soft/20 px-2 py-0.5 rounded-full">98% Match</span>
                      </div>
                    </div>
                    
                    {/* Mock Floating Message Bubble */}
                    <div className="absolute bottom-4 right-4 bg-primary text-primary-foreground rounded-xl px-3 py-2 shadow-lg flex flex-col max-w-[200px] border border-primary/20 animate-bounce-slow">
                      <span className="text-[10px] opacity-75 font-semibold">Alex Rivera</span>
                      <span className="text-[11px] leading-tight mt-0.5">"Hey! Let's team up for the next hackathon?"</span>
                    </div>
                  </div>
                </div>
              </div>
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

      <section
        id="pricing"
        className="border-b border-border py-24 relative overflow-hidden bg-gradient-to-b from-background via-surface/30 to-background"
      >
        {/* Subtle decorative background blur */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />

        <div className="mx-auto max-w-5xl px-4 sm:px-6 relative z-10">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl">
              Simple, transparent pricing
            </h2>
            <p className="mt-5 text-lg text-muted-foreground leading-relaxed">
              Start for free, upgrade when you need more power. No hidden fees.
            </p>
          </div>

          <div className="mt-12 flex justify-center">
            <div className="relative flex items-center rounded-full bg-surface border border-border p-1.5 shadow-sm">
              <button
                type="button"
                onClick={() => setBillingCycle("monthly")}
                className={`relative w-36 rounded-full py-2.5 text-[15px] font-semibold transition-colors duration-200 ease-in-out ${
                  billingCycle === "monthly"
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {billingCycle === "monthly" && (
                  <motion.div
                    layoutId="billingCycle"
                    className="absolute inset-0 rounded-full bg-background shadow-sm border border-border/50"
                    initial={false}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                )}
                <span className="relative z-10">Monthly</span>
              </button>
              <button
                type="button"
                onClick={() => setBillingCycle("yearly")}
                className={`relative w-36 rounded-full py-2.5 text-[15px] font-semibold transition-colors duration-200 ease-in-out ${
                  billingCycle === "yearly"
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {billingCycle === "yearly" && (
                  <motion.div
                    layoutId="billingCycle"
                    className="absolute inset-0 rounded-full bg-background shadow-sm border border-border/50"
                    initial={false}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                )}
                <span className="relative z-10">Yearly</span>
                <span className="absolute -top-3.5 -right-3 rounded-full bg-primary px-2.5 py-0.5 text-[11px] font-bold text-primary-foreground shadow-sm animate-pulse">
                  Save 20%
                </span>
              </button>
            </div>
          </div>

          <div className="mx-auto mt-14 grid max-w-5xl gap-8 lg:grid-cols-2 lg:items-center">
            {[
              {
                name: "Hobby",
                desc: "Perfect for students and solo developers building side projects.",
                price: "$0",
                period: "forever",
                cta: "Get Started Free",
                perks: [
                  "Up to 3 active projects",
                  "Basic AI matching",
                  "Community feed access",
                  "Standard support",
                ],
              },
              {
                name: "Pro",
                desc: "For professionals and teams who need more power and priority.",
                price: billingCycle === "yearly" ? "$12" : "$15",
                period: "per user/month",
                cta: "Upgrade to Pro",
                featured: true,
                recommended: true,
                perks: [
                  "Unlimited projects",
                  "Priority AI matching & insights",
                  "Team analytics dashboard",
                  "Priority 24/7 support",
                  "Custom domain support",
                ],
              },
            ].map((p) => (
              <div
                key={p.name}
                className={`relative flex flex-col rounded-[2rem] border p-8 transition-all duration-300 ${
                  p.featured
                    ? "border-primary/50 bg-background shadow-[0_0_40px_-15px_rgba(var(--primary),0.3)] ring-1 ring-primary/20 scale-100 lg:scale-105 z-10 lg:p-10"
                    : "border-border bg-surface/50 hover:bg-surface hover:shadow-md lg:p-8"
                }`}
              >
                {p.recommended && (
                  <div className="absolute -top-4 left-0 right-0 mx-auto w-fit rounded-full bg-gradient-to-r from-primary to-primary/80 px-4 py-1.5 text-center text-[13px] font-bold text-primary-foreground shadow-md flex items-center gap-1.5">
                    <Zap size={14} className="fill-current" /> Most Popular
                  </div>
                )}
                <div className="mb-6">
                  <h3
                    className={`text-2xl font-bold ${p.featured ? "text-primary" : "text-foreground"}`}
                  >
                    {p.name}
                  </h3>
                  <p className="mt-2 text-[15px] text-muted-foreground leading-relaxed">{p.desc}</p>
                </div>

                <div className="mb-6 flex items-baseline gap-2">
                  <span className="text-6xl font-extrabold tracking-tight text-foreground">
                    {p.price}
                  </span>
                  <span className="text-[15px] font-medium text-muted-foreground">{p.period}</span>
                </div>

                <Link
                  to="/auth"
                  className={`mb-8 inline-flex w-full items-center justify-center rounded-xl px-6 py-4 text-[16px] font-bold transition-all duration-200 group ${
                    p.featured
                      ? "bg-primary text-primary-foreground hover:bg-primary/90 hover:shadow-lg hover:-translate-y-0.5"
                      : "border border-border bg-background text-foreground hover:bg-muted hover:border-foreground/20"
                  }`}
                >
                  {p.cta}
                  <ArrowRight
                    size={18}
                    className={`ml-2 transition-transform duration-200 ${p.featured ? "group-hover:translate-x-1" : ""}`}
                  />
                </Link>

                <div className="flex-1">
                  <p className="mb-5 text-[15px] font-semibold text-foreground">What's included:</p>
                  <ul className="space-y-4 text-[15px] text-muted-foreground">
                    {p.perks.map((perk) => (
                      <li key={perk} className="flex items-start gap-3">
                        <CheckCircle2
                          className={`h-5 w-5 shrink-0 ${p.featured ? "text-primary" : "text-foreground/40"}`}
                        />
                        <span className="leading-snug">{perk}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>

          {/* Trust / Billing Info */}
          <div className="mt-16 flex flex-wrap items-center justify-center gap-6 sm:gap-12 text-sm text-muted-foreground font-medium">
            <div className="flex items-center gap-2">
              <Shield size={18} className="text-success" />
              <span>Cancel anytime</span>
            </div>
            <div className="flex items-center gap-2">
              <Lock size={18} className="text-primary" />
              <span>Secure payments</span>
            </div>
            <div className="flex items-center gap-2">
              <CreditCard size={18} className="text-foreground/50" />
              <span>No credit card for Hobby</span>
            </div>
          </div>

          {/* Feature Comparison */}
          <div className="mt-32 max-w-4xl mx-auto">
            <div className="text-center mb-10">
              <h3 className="text-3xl font-bold text-foreground">Compare plans</h3>
              <p className="mt-3 text-muted-foreground">Find the perfect plan for your needs.</p>
            </div>
            <div className="overflow-x-auto rounded-2xl border border-border bg-surface">
              <table className="w-full text-left text-sm text-foreground">
                <thead className="bg-background/50 border-b border-border">
                  <tr>
                    <th className="px-6 py-5 font-semibold">Features</th>
                    <th className="px-6 py-5 font-semibold text-center w-1/4">Hobby</th>
                    <th className="px-6 py-5 font-semibold text-center w-1/4 bg-primary/5 text-primary">
                      Pro
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {[
                    { feature: "Active Projects", hobby: "Up to 3", pro: "Unlimited" },
                    { feature: "AI Matching", hobby: "Basic", pro: "Priority + Insights" },
                    { feature: "Team Members", hobby: "Up to 5", pro: "Unlimited" },
                    { feature: "Analytics", hobby: "Basic", pro: "Advanced Dashboard" },
                    { feature: "Support", hobby: "Community", pro: "24/7 Priority" },
                    { feature: "Custom Domain", hobby: "-", pro: "Included" },
                  ].map((row, i) => (
                    <tr key={i} className="hover:bg-muted/50 transition-colors">
                      <td className="px-6 py-4 font-medium">{row.feature}</td>
                      <td className="px-6 py-4 text-center text-muted-foreground">
                        {row.hobby === "-" ? <span className="opacity-30">-</span> : row.hobby}
                      </td>
                      <td className="px-6 py-4 text-center font-medium bg-primary/5">{row.pro}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* FAQ Section */}
          <div className="mt-32 max-w-3xl mx-auto">
            <div className="text-center mb-10">
              <h3 className="text-3xl font-bold text-foreground">Frequently asked questions</h3>
            </div>
            <div className="space-y-4">
              {[
                {
                  q: "Can I upgrade or downgrade my plan later?",
                  a: "Absolutely. You can upgrade or downgrade your plan at any time. Prorated charges or credits will automatically be applied to your account.",
                },
                {
                  q: "What payment methods do you accept?",
                  a: "We accept all major credit cards including Visa, Mastercard, and American Express. Payments are securely processed through Stripe.",
                },
                {
                  q: "Is there a discount for yearly billing?",
                  a: "Yes! When you choose the yearly billing option, you automatically receive a 20% discount compared to the monthly plan.",
                },
                {
                  q: "Do I need a credit card for the Hobby plan?",
                  a: "No, the Hobby plan is completely free forever. We only require payment details when you decide to upgrade to Pro.",
                },
              ].map((faq, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-border bg-surface overflow-hidden transition-all duration-200"
                >
                  <button
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className="flex w-full items-center justify-between px-6 py-5 text-left font-semibold text-foreground hover:bg-muted/50"
                  >
                    <span>{faq.q}</span>
                    <ChevronDown
                      size={20}
                      className={`text-muted-foreground transition-transform duration-200 ${openFaq === i ? "rotate-180" : ""}`}
                    />
                  </button>
                  <AnimatePresence>
                    {openFaq === i && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div className="px-6 pb-5 pt-0 text-[15px] text-muted-foreground leading-relaxed border-t border-border mt-2 pt-4">
                          {faq.a}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-border bg-background">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
          <div className="text-center">
            <h2 className="text-[28px] font-bold tracking-tight text-foreground">
              Frequently Asked Questions
            </h2>
            <p className="mt-2 text-[14px] text-muted-foreground">
              Everything you need to know about DevLink.
            </p>
          </div>

          <Accordion
            type="single"
            collapsible
            className="mt-10 w-full rounded-md border border-border bg-card px-4"
          >
            {faqs.map((faq, index) => (
              <AccordionItem key={index} value={`item-${index}`}>
                <AccordionTrigger>{faq.question}</AccordionTrigger>
                <AccordionContent>
                  <p className="text-sm text-muted-foreground">{faq.answer}</p>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      <footer className="border-t border-border bg-surface py-3">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-2 sm:flex-row sm:text-left">
          <div className="flex items-center gap-2">
            <img src={APP_LOGO} alt="Devlink Logo" className="h-12 w-12 rounded" />
            <span className="text-[20px] font-bold text-foreground ">DevLink</span>
            <span className="text-[11px] text-muted-foreground opacity-70">
              © {new Date().getFullYear()}
            </span>
          </div>
          <div className="flex items-center gap-5 text-[16px] text-muted-foreground">
            {[
              { label: "GitHub", href: "https://github.com/nensii21/devlink" },
              { label: "Privacy Policy", href: "#" },
              { label: "Terms", href: "#" },
              { label: "Contact", href: "#" },
            ].map((item) => (
              <a
                key={item.label}
                href={item.href}
                target={item.href.startsWith("http") ? "_blank" : undefined}
                rel={item.href.startsWith("http") ? "noopener noreferrer" : undefined}
                className="hover:text-primary hover:underline"
              >
                {item.label}
              </a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
