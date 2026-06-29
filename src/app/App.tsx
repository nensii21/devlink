import { Header } from "./components/layout/Header";
import { useState, useEffect } from "react";
import {
  LayoutDashboard, Users, FolderOpen, FileText, MessageSquare,
  User, Settings, LogOut, ChevronLeft, ChevronRight,
  Search, Plus, X, Check, MapPin, Github, Linkedin,
  Globe, ArrowRight, Send, Paperclip, Smile, MoreHorizontal,
  Eye, Code2, UserPlus, Building2, SlidersHorizontal,
  ExternalLink, CheckCircle2, XCircle, EyeOff
} from "lucide-react";
import {Skeleton} from "./components/ui/skeleton"
import { ME, BUILDERS } from "./data/builders";
import {
  CONVERSATIONS,
  MESSAGES,
} from "./data/messages";
import { PROJECTS } from "./data/projects";

type Screen = "auth" | "dashboard" | "discover" | "projects" | "applications" | "messages" | "profile" | "settings";



const APPLICATIONS = [
  { id: 1, applicant: BUILDERS[0], project: "AI Startup Platform", role: "ML Engineer", xp: "5 years", status: "pending", appliedAt: "2 days ago", bio: "5 years ML engineering. Shipped 3 production LLM products. Open to equity." },
  { id: 2, applicant: BUILDERS[1], project: "AI Startup Platform", role: "Frontend Developer", xp: "6 years", status: "pending", appliedAt: "3 days ago", bio: "React specialist. Prev built design systems at scale. Can start immediately." },
  { id: 3, applicant: BUILDERS[4], project: "Open Source Analytics", role: "Backend Engineer", xp: "8 years", status: "accepted", appliedAt: "1 week ago", bio: "Go expert. Contributed to Prometheus and open-source observability tooling." },
  { id: 4, applicant: BUILDERS[2], project: "SaaS Productivity App", role: "Mobile Lead", xp: "4 years", status: "rejected", appliedAt: "1 week ago", bio: "Focused on native iOS. Looking for mobile-first projects." },
];

// ── Shared Components ──────────────────────────────────────────

function Avt({ src, name, size = "md", online }: { src: string; name: string; size?: "xs" | "sm" | "md" | "lg" | "xl"; online?: boolean }) {
  const s = { xs: "w-6 h-6", sm: "w-8 h-8", md: "w-10 h-10", lg: "w-14 h-14", xl: "w-20 h-20" };
  return (
    <div className="relative inline-flex shrink-0">
      <img src={src} alt={name} className={`${s[size]} rounded-full object-cover`} />
      {online && <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-[#22C55E] rounded-full ring-2 ring-[#111111]" />}
    </div>
  );
}

function SkillTag({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-white/[0.06] border border-white/[0.08] text-[11px] text-[#A1A1AA] font-medium tracking-wide">
      {children}
    </span>
  );
}

function BlueBtn({ children, onClick, size = "md", className = "" }: { children: React.ReactNode; onClick?: () => void; size?: "sm" | "md" | "lg"; className?: string }) {
  const sizes = { sm: "px-3 py-1.5 text-xs gap-1.5", md: "px-4 py-2 text-sm gap-2", lg: "px-5 py-2.5 text-sm gap-2" };
  return (
    <button onClick={onClick} className={`inline-flex items-center font-medium rounded-lg bg-[#4F8CFF] hover:bg-[#3d7ae8] text-white transition-colors ${sizes[size]} ${className}`}>
      {children}
    </button>
  );
}

function GhostBtn({ children, onClick, size = "md", className = "" }: { children: React.ReactNode; onClick?: () => void; size?: "sm" | "md" | "lg"; className?: string }) {
  const sizes = { sm: "px-3 py-1.5 text-xs gap-1.5", md: "px-4 py-2 text-sm gap-2", lg: "px-5 py-2.5 text-sm gap-2" };
  return (
    <button onClick={onClick} className={`inline-flex items-center font-medium rounded-lg bg-white/[0.06] hover:bg-white/[0.10] text-white border border-white/[0.08] transition-colors ${sizes[size]} ${className}`}>
      {children}
    </button>
  );
}

function DangerBtn({ children, onClick, size = "sm" }: { children: React.ReactNode; onClick?: () => void; size?: "sm" | "md" }) {
  const sizes = { sm: "px-3 py-1.5 text-xs gap-1.5", md: "px-4 py-2 text-sm gap-2" };
  return (
    <button onClick={onClick} className={`inline-flex items-center font-medium rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 transition-colors ${sizes[size]}`}>
      {children}
    </button>
  );
}

function GreenBtn({ children, onClick, size = "sm" }: { children: React.ReactNode; onClick?: () => void; size?: "sm" | "md" }) {
  const sizes = { sm: "px-3 py-1.5 text-xs gap-1.5", md: "px-4 py-2 text-sm gap-2" };
  return (
    <button onClick={onClick} className={`inline-flex items-center font-medium rounded-lg bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/20 transition-colors ${sizes[size]}`}>
      {children}
    </button>
  );
}

function DInput({ label, type = "text", placeholder }: { label?: string; type?: string; placeholder?: string }) {
  return (
    <div className="space-y-1.5">
      {label && <label className="text-xs font-medium text-[#A1A1AA]">{label}</label>}
      <input type={type} placeholder={placeholder}
        className="w-full bg-[#0D0D0D] border border-white/[0.08] rounded-lg px-3.5 py-2.5 text-sm text-white placeholder:text-[#444] focus:outline-none focus:border-[#4F8CFF]/50 focus:ring-1 focus:ring-[#4F8CFF]/20 transition-colors" />
    </div>
  );
}

function DTextarea({ label, placeholder, rows = 3 }: { label?: string; placeholder?: string; rows?: number }) {
  return (
    <div className="space-y-1.5">
      {label && <label className="text-xs font-medium text-[#A1A1AA]">{label}</label>}
      <textarea rows={rows} placeholder={placeholder}
        className="w-full bg-[#0D0D0D] border border-white/[0.08] rounded-lg px-3.5 py-2.5 text-sm text-white placeholder:text-[#444] focus:outline-none focus:border-[#4F8CFF]/50 focus:ring-1 focus:ring-[#4F8CFF]/20 transition-colors resize-none" />
    </div>
  );
}

function DSelect({ label, options }: { label?: string; options: string[] }) {
  return (
    <div className="space-y-1.5">
      {label && <label className="text-xs font-medium text-[#A1A1AA]">{label}</label>}
      <select className="w-full bg-[#0D0D0D] border border-white/[0.08] rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-[#4F8CFF]/50 transition-colors appearance-none cursor-pointer">
        {options.map(o => <option key={o} className="bg-[#171717]">{o}</option>)}
      </select>
    </div>
  );
}

function Toggle({ on }: { on: boolean }) {
  return (
    <div className={`relative w-10 h-6 rounded-full transition-colors cursor-pointer shrink-0 ${on ? "bg-[#4F8CFF]" : "bg-white/10"}`}>
      <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-all ${on ? "left-5" : "left-1"}`} />
    </div>
  );
}

function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between mb-8">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">{title}</h1>
        {subtitle && <p className="text-sm text-[#A1A1AA] mt-1">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

// ── Sidebar ────────────────────────────────────────────────────

function Sidebar({ screen, setScreen, collapsed, setCollapsed }: {
  screen: Screen; setScreen: (s: Screen) => void;
  collapsed: boolean; setCollapsed: (v: boolean) => void;
}) {
  const nav = [
    { id: "dashboard", icon: LayoutDashboard, label: "Dashboard" },
    { id: "discover", icon: Users, label: "Discover Builders" },
    { id: "projects", icon: FolderOpen, label: "Projects" },
    { id: "applications", icon: FileText, label: "Applications" },
    { id: "messages", icon: MessageSquare, label: "Messages", badge: 3 },
    { id: "profile", icon: User, label: "Profile" },
  ];

  return (
    <div className={`${collapsed ? "w-[72px]" : "w-[232px]"} transition-all duration-300 ease-out flex-shrink-0 p-3 flex flex-col`}>
      <div className="flex-1 bg-[#111111] border border-white/[0.07] rounded-2xl flex flex-col overflow-hidden shadow-2xl shadow-black/40">
        {/* Brand */}
        <div className={`flex items-center border-b border-white/[0.06] p-4 ${collapsed ? "justify-center" : "justify-between"}`}>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[#4F8CFF] flex items-center justify-center shrink-0">
              <Code2 size={14} className="text-white" />
            </div>
            {!collapsed && <span className="font-bold text-[14px] text-white tracking-tight">DevLink</span>}
          </div>
          {!collapsed && (
            <button onClick={() => setCollapsed(true)} className="p-1.5 rounded-lg hover:bg-white/[0.06] text-[#555] hover:text-[#A1A1AA] transition-colors">
              <ChevronLeft size={14} />
            </button>
          )}
        </div>

        {/* Nav items */}
        <nav className="flex-1 p-2 space-y-0.5 mt-1">
          {nav.map(({ id, icon: Icon, label, badge }) => {
            const active = screen === id;
            return (
              <button key={id} onClick={() => setScreen(id as Screen)} title={collapsed ? label : undefined}
                className={`w-full flex items-center rounded-xl text-sm transition-all duration-150 relative ${
                  collapsed ? "justify-center px-0 py-3" : "gap-3 px-3 py-2.5"
                } ${active ? "bg-white/[0.08] text-white" : "text-[#A1A1AA] hover:bg-white/[0.05] hover:text-white"}`}>
                <Icon size={16} className={active ? "text-[#4F8CFF]" : ""} />
                {!collapsed && (
                  <>
                    <span className="flex-1 text-left font-medium text-[13px]">{label}</span>
                    {badge && <span className="bg-[#4F8CFF] text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full">{badge}</span>}
                  </>
                )}
                {collapsed && badge && <span className="absolute top-2 right-2 w-2 h-2 bg-[#4F8CFF] rounded-full" />}
              </button>
            );
          })}
        </nav>

        {/* Bottom actions */}
        <div className="p-2 border-t border-white/[0.06] space-y-0.5">
          <button onClick={() => setScreen("settings")} title={collapsed ? "Settings" : undefined}
            className={`w-full flex items-center rounded-xl text-sm transition-all ${
              collapsed ? "justify-center px-0 py-2.5" : "gap-3 px-3 py-2.5"
            } ${screen === "settings" ? "bg-white/[0.08] text-white" : "text-[#A1A1AA] hover:bg-white/[0.05] hover:text-white"}`}>
            <Settings size={15} className={screen === "settings" ? "text-[#4F8CFF]" : ""} />
            {!collapsed && <span className="font-medium text-[13px]">Settings</span>}
          </button>
          <button onClick={() => setScreen("auth")} title={collapsed ? "Sign out" : undefined}
            className={`w-full flex items-center rounded-xl text-sm text-[#A1A1AA] hover:bg-white/[0.05] hover:text-white transition-all ${
              collapsed ? "justify-center px-0 py-2.5" : "gap-3 px-3 py-2.5"
            }`}>
            <LogOut size={15} />
            {!collapsed && <span className="font-medium text-[13px]">Sign out</span>}
          </button>
        </div>

        {/* User */}
        {!collapsed ? (
          <div className="p-3 border-t border-white/[0.06]">
            <button onClick={() => setScreen("profile")} className="w-full flex items-center gap-3 p-2.5 rounded-xl hover:bg-white/[0.05] transition-colors">
              <Avt src={ME.avatar} name={ME.name} size="sm" online />
              <div className="flex-1 min-w-0 text-left">
                <p className="text-[13px] font-semibold text-white truncate">{ME.name}</p>
                <p className="text-[11px] text-[#A1A1AA] truncate">{ME.role}</p>
              </div>
            </button>
          </div>
        ) : (
          <div className="p-3 border-t border-white/[0.06] flex flex-col items-center gap-2">
            <button onClick={() => setScreen("profile")}><Avt src={ME.avatar} name={ME.name} size="sm" online /></button>
            <button onClick={() => setCollapsed(false)} className="p-1.5 rounded-lg hover:bg-white/[0.06] text-[#555] hover:text-[#A1A1AA] transition-colors">
              <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}



// ── Auth ───────────────────────────────────────────────────────


function AuthScreen({ setScreen }: { setScreen: (s: Screen) => void }) {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [showPw, setShowPw] = useState(false);

  const [showConfirm, setShowConfirm] = useState(false);


  const inp = [
    "w-full border border-[#D0D7DE] rounded-md px-3 py-[8px] text-[14px]",
    "text-[#1F2328] bg-white outline-none",
    "focus:border-[#05B7D7] focus:ring-2 focus:ring-[#05B7D7]/20",
    "placeholder-[#6E7781] transition-all",
  ].join(" ");

  return (
    <div

      className="min-h-screen flex flex-col items-center  px-4 py-10 overflow-y-auto"
      style={{ background: "#F6F8FA", fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      {/* Logo + brand name */}
      <div className="flex items-center gap-3 mb-6">
        <img
          src="/lodo-dev.jpeg"
          alt="DevLink"
          className="h-10 w-10 rounded-full object-cover"
        />
        <span className="text-[32px] font-bold text-[#1F2328] tracking-tight">DevLink</span>
      </div>

      {/* Card */}
      <div className="w-full max-w-[420px] bg-white border border-[#D0D7DE] rounded-md px-8 py-6">

        {/* GitHub */}
        <button className="w-full flex items-center justify-center gap-2.5 border border-[#D0D7DE] rounded-md py-[8px] px-3 text-[14px] font-medium text-[#1F2328] bg-white hover:bg-[#F3F4F6] transition-colors mb-3">
          <Github size={16} />
          Continue with GitHub
        </button>

        {/* Google */}
        <button className="w-full flex items-center justify-center gap-2.5 border border-[#D0D7DE] rounded-md py-[8px] px-3 text-[14px] font-medium text-[#1F2328] bg-white hover:bg-[#F3F4F6] transition-colors mb-5">
          <svg width="16" height="16" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continue with Google
        </button>

        {/* Divider */}
        <div className="flex items-center gap-3 mb-5">
          <div className="flex-1 h-px bg-[#D0D7DE]" />
          <span className="text-[12px] text-[#6E7781]">Or</span>
          <div className="flex-1 h-px bg-[#D0D7DE]" />
        </div>


        {mode === "signup" && (
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="block text-[13px] font-semibold text-[#1F2328] mb-1">First name</label>
              <input type="text" className={inp} />

            </div>
            <div>
              <label className="block text-[13px] font-semibold text-[#1F2328] mb-1">Last name</label>
              <input type="text" className={inp} />
            </div>
          </div>
        )}

        {/* Email */}
        <div className="mb-4">
          <label className="block text-[13px] font-semibold text-[#1F2328] mb-1">Email</label>
          <input type="email" className={inp} />
        </div>

        {/* Password */}
        <div className="mb-1">
          <label className="block text-[13px] font-semibold text-[#1F2328] mb-1">Password</label>

          <div className="relative">
            <input type={showPw ? "text" : "password"} className={inp + " pr-9"} />
            <button type="button" onClick={() => setShowPw(s => !s)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#6E7781] hover:text-[#1F2328] transition-colors">
              {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
        </div>



        {/* Forgot password — signin only */}
        {mode === "signin" && (
          <div className="flex justify-end mt-1.5 mb-4">
            <a href="#" className="text-[13px] font-medium hover:underline" style={{ color: "#05B7D7" }}>
              Forgot password?
            </a>
          </div>
        )}


        {/* Confirm password — signup only */}
        {mode === "signup" && (
          <div className="mt-4 mb-4">
            <label className="block text-[13px] font-semibold text-[#1F2328] mb-1">Confirm password</label>
            <div className="relative">
              <input type={showConfirm ? "text" : "password"} className={inp + " pr-9"} />
              <button type="button" onClick={() => setShowConfirm(s => !s)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#6E7781] hover:text-[#1F2328] transition-colors">
                {showConfirm ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>
        )}

        {/* CTA */}
        <button
          onClick={() => setScreen("dashboard")}
          className="w-full py-[9px] mt-2 rounded-md text-[14px] font-semibold text-white transition-all active:scale-[0.98] hover:opacity-90"
          style={{ background: "#05B7D7" }}
        >
          {mode === "signin" ? "Sign In" : "Create account"}
        </button>

        {/* Switch mode */}
        <p className="text-center text-[13px] text-[#6E7781] mt-4">
          {mode === "signin" ? (
            <>Don't have an account?{" "}
              <button onClick={() => setMode("signup")} className="font-medium hover:underline" style={{ color: "#05B7D7" }}>
                Sign up
              </button>
            </>
          ) : (
            <>Already have an account?{" "}
              <button onClick={() => setMode("signin")} className="font-medium hover:underline" style={{ color: "#05B7D7" }}>
                Sign in
              </button>
            </>
          )}
        </p>
      </div>


      {/* Footer */}
      <div className="flex items-center gap-5 mt-6">
        {["Privacy", "Security", "Terms", "Status"].map(l => (
          <a
            key={l}
            href="#"
            className="text-[12px] text-[#6E7781] hover:underline transition-colors"
            onMouseOver={e => (e.currentTarget.style.color = "#05B7D7")}
            onMouseOut={e => (e.currentTarget.style.color = "#6E7781")}
          >
            {l}
          </a>
        ))}
      </div>
    </div>
  );
}
// ── Dashboard ──────────────────────────────────────────────────

function DashboardSkeleton() {
  return (
    <div className="p-6 lg:p-8 max-w-[1200px]">
      {/* Header */}
      <div className="mb-8">
        <Skeleton className="h-8 w-48 mb-2" />
        <Skeleton className="h-4 w-64" />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-[#111111] border border-white/[0.07] rounded-xl p-5">
            <Skeleton className="h-3 w-24 mb-3" />
            <Skeleton className="h-9 w-16 mb-1" />
            <Skeleton className="h-3 w-28" />
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 space-y-5">

          {/* Recent Activity */}
          <div className="bg-[#111111] border border-white/[0.07] rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-white/[0.06]">
              <Skeleton className="h-4 w-32" />
            </div>
            <div className="divide-y divide-white/[0.04]">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-start gap-3.5 px-5 py-3.5">
                  <Skeleton className="w-8 h-8 rounded-full shrink-0" />
                  <div className="flex-1">
                    <Skeleton className="h-3.5 w-3/4 mb-1.5" />
                    <Skeleton className="h-3 w-16" />
                  </div>
                  <Skeleton className="w-7 h-7 rounded-lg shrink-0" />
                </div>
              ))}
            </div>
          </div>

          {/* Suggested Builders */}
          <div className="bg-[#111111] border border-white/[0.07] rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
              <Skeleton className="h-4 w-36" />
              <Skeleton className="h-3 w-14" />
            </div>
            <div className="divide-y divide-white/[0.04]">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex items-center gap-3.5 px-5 py-3.5">
                  <Skeleton className="w-8 h-8 rounded-full shrink-0" />
                  <div className="flex-1">
                    <Skeleton className="h-3.5 w-28 mb-1.5" />
                    <Skeleton className="h-3 w-40" />
                  </div>
                  <Skeleton className="h-7 w-20 rounded-lg shrink-0" />
                </div>
              ))}
            </div>
          </div>

        </div>

        <div className="space-y-5">
          {/* Recent Applications */}
          <div className="bg-[#111111] border border-white/[0.07] rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
              <Skeleton className="h-4 w-36" />
              <Skeleton className="h-3 w-8" />
            </div>
            <div className="divide-y divide-white/[0.04]">
              {[...Array(2)].map((_, i) => (
                <div key={i} className="px-5 py-4">
                  <div className="flex items-center gap-3 mb-3">
                    <Skeleton className="w-8 h-8 rounded-full shrink-0" />
                    <div className="flex-1">
                      <Skeleton className="h-3.5 w-24 mb-1.5" />
                      <Skeleton className="h-3 w-20 mb-1" />
                      <Skeleton className="h-3 w-16" />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Skeleton className="h-7 w-20 rounded-lg" />
                    <Skeleton className="h-7 w-20 rounded-lg" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-4">
            <Skeleton className="h-3 w-24 mb-3" />
            <div className="space-y-1">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex items-center gap-3 px-3.5 py-2.5">
                  <Skeleton className="w-4 h-4 rounded shrink-0" />
                  <Skeleton className="h-3.5 flex-1" />
                  <Skeleton className="w-3 h-3 shrink-0" />
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
function DashboardScreen({ setScreen }: { setScreen: (s: Screen) => void }) {
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1500);
    return () => clearTimeout(timer);
  }, []);
  if (loading) return <div className="h-full overflow-auto"><DashboardSkeleton /></div>;
  const stats = [
    { label: "Active Projects", value: "4", note: "+1 this week" },
    { label: "Applications", value: "12", note: "3 pending review" },
    { label: "Messages", value: "8", note: "3 unread" },
    { label: "Profile Views", value: "94", note: "+18 this week" },
  ];

  const activity = [
    { type: "apply", user: BUILDERS[0], text: "applied to your AI Startup Platform", time: "2h ago" },
    { type: "message", user: BUILDERS[3], text: "sent you a message", time: "4h ago" },
    { type: "apply", user: BUILDERS[1], text: "applied to AI Startup Platform", time: "6h ago" },
    { type: "view", user: BUILDERS[4], text: "viewed your profile", time: "1d ago" },
    { type: "message", user: BUILDERS[2], text: "replied to your message", time: "1d ago" },
  ];

  return (
    <div className="h-full overflow-auto p-6 lg:p-8">
    <div className="mb-8">
      <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Welcome back, Nensi</h1>
      <p className="text-sm text-gray-500 mt-1">Continue building with your team.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
          {stats.map(s => (
            <div key={s.label} className="bg-[#111111] border border-white/[0.07] rounded-xl p-5 hover:border-white/[0.12] transition-colors">
              <p className="text-[10px] font-semibold text-[#444] uppercase tracking-wider mb-3">{s.label}</p>
              <p className="text-3xl font-bold text-white tracking-tight mb-1">{s.value}</p>
              <p className="text-[11px] text-[#555]">{s.note}</p>
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 space-y-5">
            {/* Activity */}
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
                <h2 className="text-[13px] font-semibold text-white">Recent Activity</h2>
              </div>
              <div className="divide-y divide-white/[0.04]">
                {activity.map((a, i) => (
                  <div key={i} className="flex items-start gap-3.5 px-5 py-3.5 hover:bg-white/[0.02] transition-colors">
                    <Avt src={a.user.avatar} name={a.user.name} size="sm" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] text-white leading-snug">
                        <span className="font-medium">{a.user.name}</span>{" "}
                        <span className="text-[#A1A1AA]">{a.text}</span>
                      </p>
                      <p className="text-[11px] text-[#555] mt-0.5">{a.time}</p>
                    </div>
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                      a.type === "apply" ? "bg-[#4F8CFF]/10" :
                      a.type === "message" ? "bg-green-500/10" : "bg-white/[0.05]"
                    }`}>
                      {a.type === "apply" && <FileText size={12} className="text-[#4F8CFF]" />}
                      {a.type === "message" && <MessageSquare size={12} className="text-green-400" />}
                      {a.type === "view" && <Eye size={12} className="text-[#A1A1AA]" />}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {/* Suggested */}
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
                <h2 className="text-[13px] font-semibold text-white">Suggested Builders</h2>
                <button onClick={() => setScreen("discover")} className="text-[12px] text-[#4F8CFF] hover:text-white transition-colors flex items-center gap-1">
                  View all <ArrowRight size={12} />
                </button>
              </div>
              <div className="divide-y divide-white/[0.04]">
                {BUILDERS.slice(0, 4).map(b => (
                  <div key={b.id} className="flex items-center gap-3.5 px-5 py-3.5 hover:bg-white/[0.02] transition-colors">
                    <Avt src={b.avatar} name={b.name} size="sm" online={b.online} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <p className="text-[13px] font-medium text-white">{b.name}</p>
                        {b.available && <span className="text-[10px] bg-green-500/10 text-green-400 px-1.5 py-0.5 rounded font-medium border border-green-500/20">Open</span>}
                      </div>
                      <p className="text-[11px] text-[#A1A1AA] truncate">{b.role} · {b.location}</p>
                    </div>
                    <button className="px-3 py-1.5 text-[11px] bg-[#4F8CFF]/10 hover:bg-[#4F8CFF]/20 text-[#4F8CFF] font-medium rounded-lg border border-[#4F8CFF]/20 transition-colors shrink-0">
                      Connect
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-5">
            {/* Applications */}
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
                <h2 className="text-[13px] font-semibold text-white">Recent Applications</h2>
                <button onClick={() => setScreen("applications")} className="text-[12px] text-[#4F8CFF] hover:text-white transition-colors flex items-center gap-1">
                  All <ArrowRight size={12} />
                </button>
              </div>
              <div className="divide-y divide-white/[0.04]">
                {APPLICATIONS.filter(a => a.status === "pending").map(a => (
                  <div key={a.id} className="px-5 py-4">
                    <div className="flex items-center gap-3 mb-3">
                      <Avt src={a.applicant.avatar} name={a.applicant.name} size="sm" />
                      <div className="flex-1 min-w-0">
                        <p className="text-[13px] font-medium text-white">{a.applicant.name}</p>
                        <p className="text-[11px] text-[#A1A1AA]">{a.role}</p>
                        <p className="text-[10px] text-[#555] mt-0.5">{a.appliedAt}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <GreenBtn><Check size={11} />Accept</GreenBtn>
                      <DangerBtn><X size={11} />Decline</DangerBtn>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick actions */}
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-4">
              <p className="text-[10px] font-semibold text-[#444] uppercase tracking-wider mb-3">Quick Actions</p>
              <div className="space-y-1">
                {[
                  { label: "Post a project", s: "projects", icon: Plus },
                  { label: "Discover builders", s: "discover", icon: Users },
                  { label: "Check messages", s: "messages", icon: MessageSquare },
                ].map(qa => (
                  <button key={qa.label} onClick={() => setScreen(qa.s as Screen)}
                    className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg hover:bg-white/[0.05] text-[#A1A1AA] hover:text-white transition-colors">
                    <qa.icon size={14} className="text-[#555]" />
                    <span className="text-[13px] flex-1 text-left">{qa.label}</span>
                    <ChevronRight size={12} className="text-[#444]" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
  );
}

// ── Discover Builders ──────────────────────────────────────────

function DiscoverScreen({ setScreen }: { setScreen: (s: Screen) => void }) {
  const [query, setQuery] = useState("");
  const [activeRole, setActiveRole] = useState("All");
  const roles = ["All", "Engineer", "Designer", "ML Engineer", "DevOps", "Founder"];

  const filtered = BUILDERS.filter(b =>
    (activeRole === "All" || b.role.toLowerCase().includes(activeRole.toLowerCase())) &&
    (query === "" || [b.name, b.role, ...b.skills].some(t => t.toLowerCase().includes(query.toLowerCase())))
  );

  return (
    <div className="h-full overflow-auto p-6 lg:p-8">
      <PageHeader title="Discover Builders" subtitle="Find developers, designers, and founders to build with." />

      <div className="flex gap-3 mb-5">
        <div className="relative flex-1 max-w-lg">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#444]" />
          <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search by name, role, or skill..."
            className="w-full bg-[#111111] border border-white/[0.08] rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder:text-[#444] focus:outline-none focus:border-[#4F8CFF]/50 transition-colors" />
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2.5 bg-white/[0.05] border border-white/[0.08] rounded-lg text-sm text-[#A1A1AA] hover:text-white hover:bg-white/[0.08] transition-colors">
          <SlidersHorizontal size={14} />Filters
        </button>
      </div>

      <div className="flex gap-2 mb-6 flex-wrap">
        {roles.map(r => (
          <button key={r} onClick={() => setActiveRole(r)}
            className={`px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-all ${
              activeRole === r
                ? "bg-[#4F8CFF] text-white shadow-lg shadow-[#4F8CFF]/20"
                : "bg-white/[0.05] border border-white/[0.08] text-[#A1A1AA] hover:text-white hover:bg-white/[0.08]"
            }`}>{r}
          </button>
        ))}
      </div>

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map(b => (
          <div key={b.id} className="bg-[#111111] border border-white/[0.07] rounded-xl p-5 hover:border-white/[0.14] transition-all duration-200">
            <div className="flex items-start gap-3.5 mb-3.5">
              <Avt src={b.avatar} name={b.name} size="md" online={b.online} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-0.5">
                  <p className="text-[14px] font-semibold text-white">{b.name}</p>
                  {b.available && <span className="text-[10px] bg-green-500/[0.12] text-green-400 px-1.5 py-0.5 rounded font-semibold border border-green-500/20 shrink-0">Available</span>}
                </div>
                <p className="text-[12px] text-[#A1A1AA]">{b.role}</p>
                <p className="text-[11px] text-[#555] flex items-center gap-1 mt-0.5"><MapPin size={10} />{b.location}</p>
              </div>
            </div>
            <p className="text-[12px] text-[#A1A1AA] leading-relaxed mb-3.5 line-clamp-2">{b.bio}</p>
            <div className="flex flex-wrap gap-1.5 mb-4">{b.skills.map(s => <SkillTag key={s}>{s}</SkillTag>)}</div>
            <div className="flex items-center gap-2 pt-3.5 border-t border-white/[0.06]">
              <BlueBtn size="sm" onClick={() => setScreen("messages")}><UserPlus size={12} />Connect</BlueBtn>
              <GhostBtn size="sm" onClick={() => setScreen("messages")}><MessageSquare size={12} />Message</GhostBtn>
              <a href="#" className="ml-auto p-2 rounded-lg hover:bg-white/[0.06] text-[#444] hover:text-[#A1A1AA] transition-colors"><Github size={14} /></a>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-16">
          <p className="text-[#A1A1AA] text-sm">No builders found matching your search.</p>
        </div>
      )}
    </div>
  );
}

// ── Create Project Modal ───────────────────────────────────────

function CreateProjectModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-[540px] bg-[#111111] border border-white/[0.09] rounded-2xl shadow-2xl shadow-black/60 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/[0.07]">
          <div>
            <h2 className="text-[15px] font-semibold text-white">Post a Project</h2>
            <p className="text-[12px] text-[#A1A1AA] mt-0.5">Find the right builders for your idea</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/[0.07] text-[#555] hover:text-white transition-colors"><X size={15} /></button>
        </div>
        <div className="p-6 space-y-4 max-h-[65vh] overflow-auto">
          <DInput label="Project name" placeholder="e.g., AI Startup Platform" />
          <DTextarea label="Description" placeholder="What are you building? What problem does it solve? What's the vision?" rows={4} />
          <DInput label="Required skills" placeholder="React, Python, Figma — comma separated" />
          <div className="grid grid-cols-2 gap-4">
            <DSelect label="Team size needed" options={["1–2 people", "2–3 people", "3–5 people", "5+ people"]} />
            <DSelect label="Project stage" options={["Idea", "Early", "MVP", "Beta", "Launched"]} />
          </div>
          <DSelect label="Work arrangement" options={["Remote only", "Hybrid", "On-site — SF", "On-site — NYC"]} />
        </div>
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/[0.07] bg-[#0D0D0D]">
          <GhostBtn onClick={onClose}>Cancel</GhostBtn>
          <BlueBtn onClick={onClose}>Post Project</BlueBtn>
        </div>
      </div>
    </div>
  );
}

// ── Projects ───────────────────────────────────────────────────

function ProjectCardBody({ p }: { p: typeof BUILD_POSTS[0] }) {
  return (
    <div className="p-4">
      <div className="flex items-center gap-2.5 mb-3">
        <Avt src={p.founder.avatar} name={p.founder.name} size="xs" />
        <div className="flex-1 min-w-0">
          <p className="text-[11px] text-[#A1A1AA] truncate">by <span className="text-white font-medium">{p.founder.name}</span></p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
            p.stage === "Beta" ? "bg-green-500/10 text-green-400 border-green-500/20" :
            p.stage === "MVP" ? "bg-[#4F8CFF]/10 text-[#4F8CFF] border-[#4F8CFF]/20" :
            "bg-white/[0.05] text-[#A1A1AA] border-white/[0.08]"
          }`}>{p.stage}</span>
          {p.remote && <span className="text-[10px] text-[#A1A1AA] bg-white/[0.05] border border-white/[0.08] px-1.5 py-0.5 rounded font-medium">Remote</span>}
        </div>
      </div>
      <p className="text-[12px] text-[#A1A1AA] leading-relaxed mb-3.5 line-clamp-2">{p.desc}</p>
      <div className="mb-3">
        <p className="text-[10px] font-semibold text-[#444] uppercase tracking-wider mb-1.5">Looking for</p>
        <div className="flex flex-wrap gap-1.5">
          {p.rolesNeeded.map(r => (
            <span key={r} className="text-[11px] px-2 py-1 rounded-md bg-[#4F8CFF]/[0.08] border border-[#4F8CFF]/20 text-[#4F8CFF] font-medium">{r}</span>
          ))}
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5 mb-3.5">{p.skills.map(s => <SkillTag key={s}>{s}</SkillTag>)}</div>
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5 text-[11px]">
          <span className="text-[#555]">Team {p.teamSize}/{p.maxTeam}</span>
          <span className="text-[#A1A1AA]">{Math.round((p.teamSize / p.maxTeam) * 100)}% filled · {p.apps} applicants</span>
        </div>
        <div className="h-1 bg-white/[0.07] rounded-full overflow-hidden">
          <div className="h-full bg-[#4F8CFF] rounded-full" style={{ width: `${(p.teamSize / p.maxTeam) * 100}%` }} />
        </div>
      </div>
      <BlueBtn size="sm" className="w-full justify-center">Apply to Join</BlueBtn>
    </div>
  );
}

function ProjectsSkeleton() {
  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <Skeleton className="h-6 w-36 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-9 w-32 rounded-lg" />
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-8 w-20 rounded-lg" />
        ))}
      </div>

      {/* Featured section */}
      <Skeleton className="h-3 w-16 mb-4" />
      <div className="grid md:grid-cols-2 gap-4 mb-8">
        {[...Array(2)].map((_, i) => (
          <div key={i} className="bg-[#111111] border border-white/[0.07] rounded-xl overflow-hidden">
            {/* Cover image */}
            <Skeleton className="w-full h-32" />
            {/* Card body */}
            <div className="p-4">
              <div className="flex items-center gap-2.5 mb-3">
                <Skeleton className="w-6 h-6 rounded-full shrink-0" />
                <Skeleton className="h-3 w-28 flex-1" />
                <Skeleton className="h-5 w-12 rounded" />
              </div>
              <Skeleton className="h-3.5 w-full mb-1.5" />
              <Skeleton className="h-3.5 w-4/5 mb-3.5" />
              <Skeleton className="h-3 w-20 mb-1.5" />
              <div className="flex gap-1.5 mb-3">
                <Skeleton className="h-6 w-24 rounded-md" />
                <Skeleton className="h-6 w-24 rounded-md" />
              </div>
              <div className="flex gap-1.5 mb-3.5">
                {[...Array(4)].map((_, j) => (
                  <Skeleton key={j} className="h-6 w-14 rounded-md" />
                ))}
              </div>
              <Skeleton className="h-1.5 w-full rounded-full mb-4" />
              <Skeleton className="h-8 w-full rounded-lg" />
            </div>
          </div>
        ))}
      </div>

      {/* All projects */}
      <Skeleton className="h-3 w-20 mb-4" />
      <div className="grid md:grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-[#111111] border border-white/[0.07] rounded-xl overflow-hidden">
            <div className="p-4">
              <div className="flex items-center gap-2.5 mb-3">
                <Skeleton className="w-6 h-6 rounded-full shrink-0" />
                <Skeleton className="h-3 w-28 flex-1" />
                <Skeleton className="h-5 w-12 rounded" />
              </div>
              <Skeleton className="h-3.5 w-full mb-1.5" />
              <Skeleton className="h-3.5 w-4/5 mb-3.5" />
              <div className="flex gap-1.5 mb-3">
                <Skeleton className="h-6 w-24 rounded-md" />
                <Skeleton className="h-6 w-24 rounded-md" />
              </div>
              <div className="flex gap-1.5 mb-3.5">
                {[...Array(4)].map((_, j) => (
                  <Skeleton key={j} className="h-6 w-14 rounded-md" />
                ))}
              </div>
              <Skeleton className="h-1.5 w-full rounded-full mb-4" />
              <Skeleton className="h-8 w-full rounded-lg" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
function ProjectsScreen() {
  const [loading, setLoading] = useState(true);

  const [showModal, setShowModal] = useState(false);
  const [activeFilter, setActiveFilter] = useState("All");
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1500);
    return () => clearTimeout(timer);
  }, []);
  if (loading) return <div className="h-full overflow-auto"><ProjectsSkeleton /></div>;

 
  const filters = ["All", "Featured", "Remote", "MVP", "Early Stage"];
  const techStack = ["React", "Python", "TypeScript", "Go", "Rust", "Next.js", "FastAPI", "PostgreSQL", "Docker", "AWS"];

  const filtered = BUILD_POSTS.filter(p =>
    activeFilter === "All" || (activeFilter === "Featured" && p.featured) ||
    (activeFilter === "Remote" && p.remote) || (activeFilter === "MVP" && p.stage === "MVP") ||
    (activeFilter === "Early Stage" && (p.stage === "Idea" || p.stage === "Early"))
  );

  return (
    <div className="h-full overflow-auto p-6 lg:p-8">
      <PageHeader
        title="Build With Me"
        subtitle="Browse projects looking for collaborators, or post your own."
        action={<BlueBtn onClick={() => setShowModal(true)}><Plus size={14} />Post a Project</BlueBtn>}
      />

      <div className="flex gap-2 mb-6 flex-wrap">
        {filters.map(f => (
          <button key={f} onClick={() => setActiveFilter(f)}
            className={`px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-all ${
              activeFilter === f
                ? "bg-[#4F8CFF] text-white shadow-lg shadow-[#4F8CFF]/20"
                : "bg-white/[0.05] border border-white/[0.08] text-[#A1A1AA] hover:text-white hover:bg-white/[0.08]"
            }`}>{f}
          </button>
        ))}
      </div>

      {activeFilter === "All" && (
        <div className="mb-8">
          <p className="text-[10px] font-semibold text-[#444] uppercase tracking-wider mb-4">Featured</p>
          <div className="grid md:grid-cols-2 gap-4">
            {BUILD_POSTS.filter(p => p.featured).map(p => (
              <div key={p.id} className="bg-[#111111] border border-[#4F8CFF]/[0.15] rounded-xl overflow-hidden hover:border-[#4F8CFF]/30 transition-all group">
                <div className="relative h-32 overflow-hidden">
                  <img src={p.cover} alt={p.title} className="w-full h-full object-cover opacity-50 group-hover:opacity-65 transition-opacity" />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#111111] via-[#111111]/30 to-transparent" />
                  <span className="absolute top-3 left-3 text-[10px] font-bold bg-[#4F8CFF] text-white px-2 py-1 rounded-md">Featured</span>
                  <h3 className="absolute bottom-3 left-4 text-white font-bold text-[15px]">{p.title}</h3>
                </div>
                <ProjectCardBody p={p} />
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="text-[10px] font-semibold text-[#444] uppercase tracking-wider mb-4">
        {activeFilter === "All" ? "All Projects" : activeFilter}
      </p>
      <div className="grid md:grid-cols-2 gap-4 mb-8">
        {filtered.map(p => (
          <div key={p.id} className="bg-[#111111] border border-white/[0.07] rounded-xl overflow-hidden hover:border-white/[0.13] transition-all">
            <ProjectCardBody p={p} />
          </div>
        ))}
      </div>

      <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-5">
        <h3 className="text-[13px] font-semibold text-white mb-3">Popular Technologies</h3>
        <div className="flex flex-wrap gap-2">
          {techStack.map(t => (
            <button key={t} className="px-3 py-1.5 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.07] rounded-lg text-[12px] text-[#A1A1AA] hover:text-white transition-colors">{t}</button>
          ))}
        </div>
      </div>

      {showModal && <CreateProjectModal onClose={() => setShowModal(false)} />}
    </div>
  );
}

// ── Applications ───────────────────────────────────────────────

function ApplicationsScreen() {
  const [tab, setTab] = useState<"pending" | "accepted" | "rejected">("pending");
  const filtered = APPLICATIONS.filter(a => a.status === tab);

  return (
    <div className="h-full overflow-auto p-6 lg:p-8">
      <PageHeader title="Applications" subtitle="Review and manage incoming project applications." />

      <div className="flex gap-1 p-1 bg-[#111111] border border-white/[0.07] rounded-xl w-fit mb-6">
        {(["pending", "accepted", "rejected"] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-[13px] font-medium capitalize transition-all flex items-center gap-2 ${
              tab === t ? "bg-white/[0.08] text-white" : "text-[#A1A1AA] hover:text-white"
            }`}>
            {t}
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
              tab === t ? "bg-[#4F8CFF] text-white" : "bg-white/[0.06] text-[#555]"
            }`}>{APPLICATIONS.filter(a => a.status === t).length}</span>
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-12 h-12 rounded-xl bg-white/[0.04] border border-white/[0.07] flex items-center justify-center mx-auto mb-3">
            <FileText size={18} className="text-[#444]" />
          </div>
          <p className="text-[#A1A1AA] text-sm">No {tab} applications</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(a => (
            <div key={a.id} className="bg-[#111111] border border-white/[0.07] rounded-xl p-5 hover:border-white/[0.12] transition-all">
              <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                <div className="flex items-start gap-4 flex-1 min-w-0">
                  <Avt src={a.applicant.avatar} name={a.applicant.name} size="md" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2.5 flex-wrap mb-1">
                      <p className="text-[14px] font-semibold text-white">{a.applicant.name}</p>
                      <span className="text-[11px] text-[#A1A1AA] bg-white/[0.05] border border-white/[0.08] px-2 py-0.5 rounded">{a.role}</span>
                      <span className="text-[11px] text-[#555]">{a.xp} exp</span>
                    </div>
                    <p className="text-[12px] text-[#A1A1AA] mb-2.5 leading-relaxed">{a.bio}</p>
                    <div className="flex flex-wrap gap-1.5">{a.applicant.skills.slice(0, 4).map(s => <SkillTag key={s}>{s}</SkillTag>)}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {a.status === "pending" && (
                    <><GreenBtn><Check size={12} />Accept</GreenBtn><DangerBtn><X size={12} />Reject</DangerBtn></>
                  )}
                  {a.status === "accepted" && (
                    <span className="inline-flex items-center gap-1.5 text-[12px] text-green-400 bg-green-500/10 border border-green-500/20 px-3 py-1.5 rounded-lg font-medium">
                      <CheckCircle2 size={12} />Accepted
                    </span>
                  )}
                  {a.status === "rejected" && (
                    <span className="inline-flex items-center gap-1.5 text-[12px] text-red-400 bg-red-500/10 border border-red-500/20 px-3 py-1.5 rounded-lg font-medium">
                      <XCircle size={12} />Rejected
                    </span>
                  )}
                  <button className="p-2 rounded-lg hover:bg-white/[0.06] text-[#444] hover:text-[#A1A1AA] transition-colors"><MessageSquare size={14} /></button>
                  <button className="p-2 rounded-lg hover:bg-white/[0.06] text-[#444] hover:text-[#A1A1AA] transition-colors"><ExternalLink size={14} /></button>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-white/[0.05] flex items-center justify-between text-[11px] text-[#555]">
                <span>Applied to <span className="text-[#A1A1AA]">{a.project}</span></span>
                <span>{a.appliedAt}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Messages ───────────────────────────────────────────────────


function MessagesSkeleton() {
  return (
    <div className="h-full flex overflow-hidden">
      <div className="w-[264px] flex-shrink-0 border-r border-white/[0.07] flex flex-col">
        <div className="p-4 border-b border-white/[0.07]">
          <Skeleton className="h-4 w-20 mb-3" />
          <Skeleton className="h-8 w-full rounded-lg" />
        </div>
        <div className="flex-1">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3.5 border-b border-white/[0.04]">
              <Skeleton className="w-8 h-8 rounded-full shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <Skeleton className="h-3.5 w-24" />
                  <Skeleton className="h-3 w-6" />
                </div>
                <Skeleton className="h-3 w-40" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="h-[58px] border-b border-white/[0.07] flex items-center gap-3.5 px-5 shrink-0">
          <Skeleton className="w-8 h-8 rounded-full shrink-0" />
          <div>
            <Skeleton className="h-3.5 w-24 mb-1.5" />
            <Skeleton className="h-3 w-32" />
          </div>
          <div className="ml-auto">
            <Skeleton className="w-8 h-8 rounded-lg" />
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-auto p-5 space-y-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className={`flex items-end gap-2.5 ${i % 2 === 0 ? "" : "flex-row-reverse"}`}>
              {i % 2 === 0 && <Skeleton className="w-6 h-6 rounded-full shrink-0" />}
              <div className={`flex flex-col gap-1 ${i % 2 === 0 ? "items-start" : "items-end"}`}>
                <Skeleton className={`h-10 rounded-2xl ${i % 2 === 0 ? "w-64" : "w-48"}`} />
                <Skeleton className="h-3 w-12" />
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-white/[0.07] shrink-0">
          <Skeleton className="h-12 w-full rounded-xl" />
        </div>
      </div>
    </div>
  );
}

function MessagesScreen() {
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState(CONVERSATIONS[0]);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1500);
    return () => clearTimeout(timer);
  }, []);

  if (loading) return <MessagesSkeleton />;

  return (
    <div className="h-full flex overflow-hidden">
      <div className="w-[264px] flex-shrink-0 border-r border-white/[0.07] flex flex-col">
        <div className="p-4 border-b border-white/[0.07]">
          <p className="text-[13px] font-semibold text-white mb-3">Messages</p>
          <div className="relative">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#444]" />
            <input placeholder="Search..." className="w-full bg-[#111111] border border-white/[0.08] rounded-lg pl-8 pr-3 py-2 text-[12px] text-white placeholder:text-[#444] focus:outline-none focus:border-[#4F8CFF]/40 transition-colors" />
          </div>
        </div>
        <div className="flex-1 overflow-auto">
          {CONVERSATIONS.map(c => (
            <button key={c.id} onClick={() => setActive(c)}
              className={`w-full flex items-center gap-3 px-4 py-3.5 border-b border-white/[0.04] text-left transition-colors ${active.id === c.id ? "bg-white/[0.04]" : "hover:bg-white/[0.02]"}`}>
              <Avt src={c.with.avatar} name={c.with.name} size="sm" online={c.with.online} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-0.5">
                  <p className="text-[13px] font-medium text-white truncate">{c.with.name}</p>
                  <span className="text-[10px] text-[#444] shrink-0">{c.time}</span>
                </div>
                <p className="text-[11px] text-[#A1A1AA] truncate">{c.lastMsg}</p>
              </div>
              {c.unread > 0 && <span className="w-4 h-4 rounded-full bg-[#4F8CFF] text-white text-[9px] font-bold flex items-center justify-center shrink-0">{c.unread}</span>}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="h-[58px] border-b border-white/[0.07] flex items-center gap-3.5 px-5 shrink-0">
          <Avt src={active.with.avatar} name={active.with.name} size="sm" online={active.with.online} />
          <div>
            <p className="text-[13px] font-semibold text-white">{active.with.name}</p>
            <p className="text-[11px] text-[#555]">{active.with.online ? "Online" : "Offline"} · {active.with.role}</p>
          </div>
          <div className="ml-auto">
            <button className="p-2 hover:bg-white/[0.06] rounded-lg transition-colors text-[#444] hover:text-[#A1A1AA]"><MoreHorizontal size={15} /></button>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-5 space-y-4">
          <div className="text-center">
            <span className="text-[10px] text-[#444] bg-white/[0.04] px-3 py-1 rounded-full">Today</span>
          </div>
          {CHAT_HISTORY.map(m => (
            <div key={m.id} className={`flex items-end gap-2.5 ${m.own ? "flex-row-reverse" : ""}`}>
              {!m.own && <Avt src={active.with.avatar} name={active.with.name} size="xs" />}
              <div className={`max-w-[72%] flex flex-col gap-1 ${m.own ? "items-end" : "items-start"}`}>
                <div className={`px-4 py-2.5 rounded-2xl text-[13px] leading-relaxed ${
                  m.own ? "bg-[#4F8CFF] text-white rounded-br-sm" : "bg-[#1A1A1A] border border-white/[0.07] text-white rounded-bl-sm"
                }`}>{m.text}</div>
                <span className="text-[10px] text-[#444] mx-1">{m.time}</span>
              </div>
            </div>
          ))}
          <div className="flex items-end gap-2.5">
            <Avt src={active.with.avatar} name={active.with.name} size="xs" />
            <div className="bg-[#1A1A1A] border border-white/[0.07] rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1">
                {[0,1,2].map(i => <span key={i} className="w-1.5 h-1.5 rounded-full bg-[#555] animate-bounce" style={{ animationDelay: `${i*0.15}s` }} />)}
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-white/[0.07] shrink-0">
          <div className="flex items-center gap-3 bg-[#111111] border border-white/[0.08] rounded-xl px-4 py-3">
            <button className="text-[#444] hover:text-[#A1A1AA] transition-colors"><Paperclip size={15} /></button>
            <input value={msg} onChange={e => setMsg(e.target.value)} onKeyDown={e => e.key === "Enter" && setMsg("")}
              placeholder={`Message ${active.with.name}...`}
              className="flex-1 bg-transparent text-[13px] text-white placeholder:text-[#444] focus:outline-none" />
            <button className="text-[#444] hover:text-[#A1A1AA] transition-colors"><Smile size={15} /></button>
            <button onClick={() => setMsg("")}
              className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${msg ? "bg-[#4F8CFF] text-white hover:bg-[#3d7ae8]" : "bg-white/[0.05] text-[#444]"}`}>
              <Send size={13} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Profile ────────────────────────────────────────────────────
function ProfileSkeleton() {
  return (
    <div className="p-6 lg:p-8">
      <div className="max-w-4xl mx-auto grid lg:grid-cols-3 gap-6">
        
        <div className="space-y-4">
          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-5">
            <div className="flex flex-col items-center">
              <Skeleton className="w-20 h-20 rounded-2xl mb-4" />
              <Skeleton className="h-5 w-32 mb-2" />
              <Skeleton className="h-3.5 w-24 mb-2" />
              <Skeleton className="h-3 w-28 mb-4" />
              <Skeleton className="h-7 w-36 rounded-full mb-5" />
              <div className="flex gap-2">
                <Skeleton className="w-8 h-8 rounded-lg" />
                <Skeleton className="w-8 h-8 rounded-lg" />
                <Skeleton className="w-8 h-8 rounded-lg" />
              </div>
            </div>
          </div>

          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-5">
            <Skeleton className="h-3 w-16 mb-3" />
            <div className="flex flex-wrap gap-1.5">
              {[...Array(9)].map((_, i) => (
                <Skeleton key={i} className="h-6 w-16 rounded-md" />
              ))}
            </div>
          </div>

          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-5">
            <Skeleton className="h-3 w-20 mb-3" />
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex items-start gap-3">
                  <Skeleton className="w-8 h-8 rounded-lg shrink-0" />
                  <div className="flex-1">
                    <Skeleton className="h-3.5 w-28 mb-1.5" />
                    <Skeleton className="h-3 w-36" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-5">
          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-5">
            <Skeleton className="h-4 w-16 mb-3" />
            <Skeleton className="h-3.5 w-full mb-2" />
            <Skeleton className="h-3.5 w-full mb-2" />
            <Skeleton className="h-3.5 w-3/4 mb-4" />
            <Skeleton className="h-3.5 w-full mb-2" />
            <Skeleton className="h-3.5 w-2/3" />
          </div>

          <div className="flex gap-1 p-1 bg-[#111111] border border-white/[0.07] rounded-xl w-fit">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-7 w-24 rounded-lg" />
            ))}
          </div>

          {/* Project cards */}
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-[#111111] border border-white/[0.07] rounded-xl p-4">
                <div className="flex items-start justify-between mb-1.5">
                  <Skeleton className="h-4 w-40" />
                  <Skeleton className="h-5 w-12 rounded" />
                </div>
                <Skeleton className="h-3.5 w-full mb-2" />
                <div className="flex gap-1.5">
                  <Skeleton className="h-6 w-16 rounded-md" />
                  <Skeleton className="h-6 w-16 rounded-md" />
                  <Skeleton className="h-6 w-16 rounded-md" />
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}


function ProfileScreen({ setScreen }: { setScreen: (s: Screen) => void }) {
  const [loading,setLoading]=useState(true)
  const [tab, setTab] = useState("projects");

  useEffect(()=>{
    const timer=setTimeout(()=>setLoading(false),1500);
    return()=>clearTimeout(timer)
  
  },[])
  if (loading) return <div className="h-full overflow-auto"><ProfileSkeleton /></div>;
  
  const expItems = [
    { title: "Senior Engineer", company: "Stripe", period: "2022–2024", desc: "Core infrastructure for the Stripe Dashboard. Led team of 4. Shipped billing products used by 100k+ customers." },
    { title: "Software Engineer", company: "Vercel", period: "2020–2022", desc: "Frontend infra for the Vercel platform. Contributed to Edge Runtime and Next.js core." },
    { title: "Co-Founder & CTO", company: "Launchpad (YC W19)", period: "2019–2020", desc: "Built and shipped a SaaS product for remote teams. Raised $1.2M seed. Team of 8." },
  ];
  const techCats = [
    { cat: "Frontend", items: ["React", "Next.js", "TypeScript", "Tailwind CSS"] },
    { cat: "Backend", items: ["Go", "Node.js", "GraphQL", "gRPC"] },
    { cat: "Infrastructure", items: ["AWS", "Docker", "Kubernetes", "Terraform"] },
    { cat: "Database", items: ["PostgreSQL", "Redis", "Supabase"] },
  ];

  return (
    <div className="h-full overflow-auto p-6 lg:p-8">
      <div className="max-w-4xl mx-auto grid lg:grid-cols-3 gap-6">
        {/* Left */}
        <div className="space-y-4">
          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-5">
            <div className="flex flex-col items-center text-center">
              <div className="relative mb-4">
                <img src={ME.avatar} alt={ME.name} className="w-20 h-20 rounded-2xl object-cover" />
                <span className="absolute bottom-1 right-1 w-3.5 h-3.5 bg-[#22C55E] rounded-full ring-2 ring-[#111111]" />
              </div>
              <h2 className="text-[16px] font-bold text-white mb-0.5">{ME.name}</h2>
              <p className="text-[13px] text-[#A1A1AA] mb-1">{ME.role}</p>
              <p className="text-[11px] text-[#555] flex items-center gap-1 mb-4"><MapPin size={10} />{ME.location}</p>
              <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-[#22C55E] bg-green-500/10 border border-green-500/20 px-3 py-1.5 rounded-full mb-5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]" />Open to collaborate
              </span>
              <div className="flex gap-2">
                {[Github, Linkedin, Globe].map((Icon, i) => (
                  <a key={i} href="#" className="p-2 rounded-lg border border-white/[0.08] text-[#444] hover:text-white hover:border-white/20 transition-colors"><Icon size={14} /></a>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-5">
            <p className="text-[10px] font-semibold text-[#444] uppercase tracking-wider mb-3">Skills</p>
            <div className="flex flex-wrap gap-1.5">
              {["React", "TypeScript", "Go", "Node.js", "PostgreSQL", "Docker", "AWS", "GraphQL", "Rust"].map(s => <SkillTag key={s}>{s}</SkillTag>)}
            </div>
          </div>

          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-5">
            <p className="text-[10px] font-semibold text-[#444] uppercase tracking-wider mb-3">Experience</p>
            <div className="space-y-3">
              {expItems.map(e => (
                <div key={e.company} className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-white/[0.05] border border-white/[0.08] flex items-center justify-center shrink-0 mt-0.5">
                    <Building2 size={12} className="text-[#555]" />
                  </div>
                  <div>
                    <p className="text-[12px] font-semibold text-white">{e.title}</p>
                    <p className="text-[11px] text-[#A1A1AA]">{e.company} · {e.period}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right */}
        <div className="lg:col-span-2 space-y-5">
          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-5">
            <h3 className="text-[13px] font-semibold text-white mb-3">About</h3>
            <p className="text-[13px] text-[#A1A1AA] leading-relaxed mb-3">
              Full-Stack Engineer with 6 years building production systems. Previously at Stripe and Vercel. Passionate about developer tooling, open-source infrastructure, and finding the right team to ship ambitious products.
            </p>
            <p className="text-[13px] text-[#A1A1AA] leading-relaxed">
              Currently looking to co-found or join an early-stage startup. Strongest in TypeScript, React, Go, and distributed systems. Open to equity-only for the right project.
            </p>
          </div>

          <div className="flex gap-1 p-1 bg-[#111111] border border-white/[0.07] rounded-xl w-fit">
            {["projects", "experience", "tech stack"].map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-1.5 rounded-lg text-[13px] font-medium capitalize transition-all ${tab === t ? "bg-white/[0.08] text-white" : "text-[#A1A1AA] hover:text-white"}`}>{t}</button>
            ))}
          </div>

          {tab === "projects" && (
            <div className="space-y-3">
              {BUILD_POSTS.slice(0, 3).map(p => (
                <div key={p.id} className="bg-[#111111] border border-white/[0.07] rounded-xl p-4 hover:border-white/[0.14] transition-colors">
                  <div className="flex items-start justify-between mb-1.5">
                    <h4 className="text-[13px] font-semibold text-white">{p.title}</h4>
                    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${
                      p.stage === "Beta" ? "bg-green-500/10 text-green-400 border-green-500/20" : "bg-[#4F8CFF]/10 text-[#4F8CFF] border-[#4F8CFF]/20"
                    }`}>{p.stage}</span>
                  </div>
                  <p className="text-[12px] text-[#A1A1AA] line-clamp-1 mb-2">{p.desc}</p>
                  <div className="flex gap-1.5 flex-wrap">{p.skills.slice(0, 3).map(s => <SkillTag key={s}>{s}</SkillTag>)}</div>
                </div>
              ))}
            </div>
          )}

          {tab === "experience" && (
            <div className="space-y-3">
              {expItems.map((e, i) => (
                <div key={i} className="bg-[#111111] border border-white/[0.07] rounded-xl p-4">
                  <div className="flex items-start gap-3.5">
                    <div className="w-10 h-10 rounded-xl bg-white/[0.05] border border-white/[0.08] flex items-center justify-center shrink-0">
                      <Building2 size={15} className="text-[#555]" />
                    </div>
                    <div>
                      <h4 className="text-[13px] font-semibold text-white mb-0.5">{e.title}</h4>
                      <p className="text-[12px] text-[#4F8CFF] mb-1.5">{e.company} · {e.period}</p>
                      <p className="text-[12px] text-[#A1A1AA] leading-relaxed">{e.desc}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === "tech stack" && (
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-5">
              <div className="grid grid-cols-2 gap-5">
                {techCats.map(cat => (
                  <div key={cat.cat}>
                    <p className="text-[10px] font-semibold text-[#444] uppercase tracking-wider mb-2.5">{cat.cat}</p>
                    <div className="flex flex-wrap gap-1.5">{cat.items.map(s => <SkillTag key={s}>{s}</SkillTag>)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Settings ───────────────────────────────────────────────────

function SettingsScreen() {
  const [section, setSection] = useState("profile");
  const sections = [
    { id: "profile", label: "Profile" },
    { id: "account", label: "Account" },
    { id: "privacy", label: "Privacy" },
    { id: "notifications", label: "Notifications" },
    { id: "connected", label: "Connected Accounts" },
  ];

  return (
    <div className="h-full overflow-auto p-6 lg:p-8">
      <PageHeader title="Settings" subtitle="Manage your account and preferences." />

      <div className="grid lg:grid-cols-4 gap-6 max-w-4xl">
        <div className="lg:col-span-1">
          <nav className="bg-[#111111] border border-white/[0.07] rounded-xl p-2 space-y-0.5">
            {sections.map(s => (
              <button key={s.id} onClick={() => setSection(s.id)}
                className={`w-full text-left px-3.5 py-2.5 rounded-lg text-[13px] font-medium transition-colors ${
                  section === s.id ? "bg-white/[0.08] text-white" : "text-[#A1A1AA] hover:text-white hover:bg-white/[0.05]"
                }`}>{s.label}</button>
            ))}
          </nav>
        </div>

        <div className="lg:col-span-3 space-y-4">
          {section === "profile" && (
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl divide-y divide-white/[0.06]">
              <div className="px-6 py-5">
                <h3 className="text-[14px] font-semibold text-white">Profile Settings</h3>
                <p className="text-[12px] text-[#A1A1AA] mt-0.5">How you appear to other builders on DevLink.</p>
              </div>
              <div className="px-6 py-5 space-y-4">
                <div className="flex items-center gap-4 mb-2">
                  <img src={ME.avatar} alt={ME.name} className="w-14 h-14 rounded-xl object-cover" />
                  <div>
                    <BlueBtn size="sm">Change photo</BlueBtn>
                    <p className="text-[11px] text-[#555] mt-1.5">JPG or PNG · Max 2MB</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <DInput label="First name" placeholder="Nancy" />
                  <DInput label="Last name" placeholder="Wells" />
                </div>
                <DInput label="Role / Title" placeholder="Full-Stack Engineer" />
                <DTextarea label="Bio" placeholder="Tell builders what you're working on and what you're looking for." rows={3} />
                <DInput label="Location" placeholder="San Francisco, CA" />
                <DInput label="Website" placeholder="https://yourwebsite.com" />
                <div className="flex justify-end pt-1"><BlueBtn>Save changes</BlueBtn></div>
              </div>
            </div>
          )}

          {section === "account" && (
            <div className="space-y-4">
              <div className="bg-[#111111] border border-white/[0.07] rounded-xl divide-y divide-white/[0.06]">
                <div className="px-6 py-5"><h3 className="text-[14px] font-semibold text-white">Email address</h3></div>
                <div className="px-6 py-5 space-y-3">
                  <DInput label="Current email" type="email" placeholder="nancy@example.com" />
                  <div className="flex justify-end"><BlueBtn size="sm">Update email</BlueBtn></div>
                </div>
              </div>
              <div className="bg-[#111111] border border-white/[0.07] rounded-xl divide-y divide-white/[0.06]">
                <div className="px-6 py-5"><h3 className="text-[14px] font-semibold text-white">Change password</h3></div>
                <div className="px-6 py-5 space-y-3">
                  <DInput label="Current password" type="password" placeholder="••••••••" />
                  <DInput label="New password" type="password" placeholder="••••••••" />
                  <DInput label="Confirm new password" type="password" placeholder="••••••••" />
                  <div className="flex justify-end"><BlueBtn size="sm">Update password</BlueBtn></div>
                </div>
              </div>
              <div className="bg-[#111111] border border-red-500/[0.12] rounded-xl divide-y divide-white/[0.06]">
                <div className="px-6 py-5">
                  <h3 className="text-[14px] font-semibold text-red-400">Danger zone</h3>
                  <p className="text-[12px] text-[#A1A1AA] mt-0.5">Permanently delete your account and all data.</p>
                </div>
                <div className="px-6 py-5"><DangerBtn size="md">Delete my account</DangerBtn></div>
              </div>
            </div>
          )}

          {(section === "privacy" || section === "notifications") && (
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl divide-y divide-white/[0.06]">
              <div className="px-6 py-5">
                <h3 className="text-[14px] font-semibold text-white capitalize">{section}</h3>
              </div>
              <div className="px-6 py-5 space-y-6">
                {(section === "privacy" ? [
                  { label: "Profile visibility", desc: "Make your profile discoverable to other builders", on: true },
                  { label: "Show online status", desc: "Let others see when you're active", on: true },
                  { label: "Appear in Discover Builders", desc: "Show up in the public builder directory", on: false },
                  { label: "Allow direct messages", desc: "Receive DMs from builders you haven't connected with", on: true },
                ] : [
                  { label: "New applications", desc: "When someone applies to your project", on: true },
                  { label: "Direct messages", desc: "When you receive a new message", on: true },
                  { label: "Connection requests", desc: "When someone wants to connect", on: false },
                  { label: "Application updates", desc: "Status changes on your applications", on: true },
                  { label: "Weekly digest", desc: "Summary of activity and recommended builders", on: false },
                ]).map(item => (
                  <div key={item.label} className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-[13px] font-medium text-white">{item.label}</p>
                      <p className="text-[12px] text-[#A1A1AA] mt-0.5">{item.desc}</p>
                    </div>
                    <Toggle on={item.on} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {section === "connected" && (
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl divide-y divide-white/[0.06]">
              <div className="px-6 py-5">
                <h3 className="text-[14px] font-semibold text-white">Connected Accounts</h3>
                <p className="text-[12px] text-[#A1A1AA] mt-0.5">Link external accounts to enhance your profile.</p>
              </div>
              <div className="px-6 py-5 space-y-5">
                {[
                  { icon: Github, name: "GitHub", handle: "@nancywells", connected: true },
                  { icon: Linkedin, name: "LinkedIn", handle: "linkedin.com/in/nancywells", connected: true },
                  { icon: Globe, name: "Portfolio", handle: "nancywells.dev", connected: false },
                ].map(acc => (
                  <div key={acc.name} className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-white/[0.05] border border-white/[0.08] flex items-center justify-center shrink-0">
                      <acc.icon size={16} className="text-[#A1A1AA]" />
                    </div>
                    <div className="flex-1">
                      <p className="text-[13px] font-medium text-white">{acc.name}</p>
                      <p className="text-[11px] text-[#555]">{acc.connected ? acc.handle : "Not connected"}</p>
                    </div>
                    {acc.connected ? <DangerBtn size="sm">Disconnect</DangerBtn> : <BlueBtn size="sm">Connect</BlueBtn>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── App ────────────────────────────────────────────────────────

export default function App() {
  const [screen, setScreen] = useState<Screen>("auth");
  const [collapsed, setCollapsed] = useState(false);

  if (screen === "auth") return <AuthScreen setScreen={setScreen} />;

  return (
    <div className="flex h-screen bg-[#0A0A0A] overflow-hidden" style={{ fontFamily: "'Inter', system-ui, -apple-system, sans-serif" }}>
      <Sidebar screen={screen} setScreen={setScreen} collapsed={collapsed} setCollapsed={setCollapsed} />
      <main className="flex-1 flex flex-col overflow-hidden relative z-10"><Header />
      <div className="flex-1 overflow-hidden">
        {screen === "dashboard" && <DashboardScreen setScreen={setScreen} />}
        {screen === "discover" && <DiscoverScreen setScreen={setScreen} />}
        {screen === "projects" && <ProjectsScreen />}
        {screen === "applications" && <ApplicationsScreen />}
        {screen === "messages" && <MessagesScreen />}
        {screen === "profile" && <ProfileScreen setScreen={setScreen} />}
        {screen === "settings" && <SettingsScreen />}
          </div>
      </main>
    </div>
  );
}
