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
  const [billingCycle, setBillingCycle] = React.useState<"monthly" | "yearly">("yearly");
  const [openFaq, setOpenFaq] = React.useState<number | null>(0);

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
            <a href="#features" className="hover:text-foreground">
              Features
            </a>
            <Link to="/builders" className="hover:text-foreground">
              Builders
            </Link>
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
                className="text-sm text-foreground"
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
                className="text-sm text-foreground"
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

      <section className="border-b border-border">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-24 text-center">
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
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
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

      <footer className="border-t border-border bg-surface py-3">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-2 sm:flex-row sm:text-left">
          <div className="flex items-center gap-2">
            <img src={APP_LOGO} alt="DevLink logo" className="h-12 w-12 rounded" />
            <span className="text-[20px] font-bold text-foreground">DevLink</span>
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
                aria-label={item.label}
                target={item.href.startsWith("http") ? "_blank" : undefined}
                rel={item.href.startsWith("http") ? "noopener noreferrer" : undefined}
                className="transition-colors hover:text-primary hover:underline"
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
