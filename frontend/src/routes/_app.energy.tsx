import { useState, useMemo, useEffect, useCallback } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Battery, BatteryCharging, BatteryFull, BatteryLow, BatteryMedium,
  Sun, Moon, Cloud, Zap, Clock, Timer, Coffee, Flame, Heart,
  Brain, Eye, EyeOff, TrendingUp, TrendingDown, BarChart3, Activity,
  Target, Award, Star, Bell, AlertTriangle, CheckCircle2, XCircle,
  Search, Filter, ChevronDown, ChevronUp, ArrowUpRight, ArrowDownRight,
  RefreshCw, Download, Settings, Play, Pause, Square, RotateCcw,
  PlayCircle, FastForward, Rewind, SkipForward, Volume2, VolumeX,
  Monitor, Smartphone, Laptop, Headphones, MonitorSpeaker,
  Sunrise, Sunset, Thermometer, Droplets, CloudRain,
  CircleDot, Layers, Grid, List, Info, Sparkles, Bookmark,
  Calendar, CalendarDays, Timer as TimerIcon, Hourglass,
  BrainCircuit, Lightbulb, Puzzle, Rocket, Shield, Compass,
  MapPin, Navigation, Gauge, Speedometer, Radix,
} from "lucide-react";
import { Card } from "@/components/shared/primitives";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/energy")({
  head: () => ({
    meta: [
      { title: "Energy & Focus Dashboard — DevLink" },
      { name: "description", content: "Track developer energy, focus sessions, screen time, and prevent burnout." },
    ],
  }),
  component: EnergyDashboard,
});

/* ─────────────── Types ─────────────── */

type EnergyLevel = "peak" | "high" | "moderate" | "low" | "depleted";
type FocusMode = "deep_work" | "shallow" | "creative" | "learning" | "break";
type BurnoutRisk = "thriving" | "healthy" | "caution" | "warning" | "critical";
type TimeOfDay = "morning" | "afternoon" | "evening" | "night";

interface FocusSession {
  id: string;
  date: string;
  startTime: string;
  endTime: string;
  duration: number;
  mode: FocusMode;
  interruptions: number;
  productivity: number;
  energyBefore: EnergyLevel;
  energyAfter: EnergyLevel;
  tasksCompleted: number;
  linesWritten: number;
  commitsMade: number;
  breakTaken: boolean;
  mood: number;
  notes: string;
}

interface EnergyEntry {
  id: string;
  timestamp: string;
  level: EnergyLevel;
  physicalEnergy: number;
  mentalEnergy: number;
  emotionalEnergy: number;
  triggers: string[];
  activities: string[];
  sleepHours: number;
  caffeine: number;
  exercise: boolean;
  meals: number;
  hydration: number;
}

interface ScreenTimeEntry {
  date: string;
  totalHours: number;
  productiveHours: number;
  socialHours: number;
  entertainmentHours: number;
  breakHours: number;
  ideHours: number;
  browserHours: number;
  terminalHours: number;
  longestStreak: number;
  breaksTaken: number;
  postureAlerts: number;
}

interface BurnoutMetric {
  category: string;
  score: number;
  maxScore: number;
  trend: "improving" | "stable" | "declining";
  description: string;
  recommendations: string[];
}

interface WeeklyPattern {
  day: string;
  avgFocus: number;
  avgEnergy: number;
  avgScreenTime: number;
  bestHour: string;
  sessionsCount: number;
}

interface EnergyInsight {
  id: string;
  type: "tip" | "warning" | "achievement" | "pattern" | "suggestion";
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  priority: number;
}

interface PomodoroState {
  isRunning: boolean;
  timeLeft: number;
  totalTime: number;
  sessionCount: number;
  mode: "work" | "short_break" | "long_break";
}

/* ─────────────── Constants ─────────────── */

const ENERGY_CONFIG: Record<EnergyLevel, { color: string; bg: string; icon: React.ReactNode; label: string; percentage: number }> = {
  peak: { color: "text-green-400", bg: "bg-green-500/20", icon: <BatteryFull size={16} />, label: "Peak", percentage: 100 },
  high: { color: "text-cyan-400", bg: "bg-cyan-500/20", icon: <BatteryCharging size={16} />, label: "High", percentage: 75 },
  moderate: { color: "text-yellow-400", bg: "bg-yellow-500/20", icon: <BatteryMedium size={16} />, label: "Moderate", percentage: 50 },
  low: { color: "text-orange-400", bg: "bg-orange-500/20", icon: <BatteryLow size={16} />, label: "Low", percentage: 25 },
  depleted: { color: "text-red-400", bg: "bg-red-500/20", icon: <Battery size={16} />, label: "Depleted", percentage: 5 },
};

const FOCUS_MODES: Record<FocusMode, { color: string; bg: string; icon: React.ReactNode; label: string; description: string; defaultDuration: number }> = {
  deep_work: { color: "text-purple-400", bg: "bg-purple-500/20", icon: <Brain size={16} />, label: "Deep Work", description: "Intense focus, no distractions", defaultDuration: 90 },
  shallow: { color: "text-blue-400", bg: "bg-blue-500/20", icon: <Puzzle size={16} />, label: "Shallow Work", description: "Emails, messages, reviews", defaultDuration: 30 },
  creative: { color: "text-pink-400", bg: "bg-pink-500/20", icon: <Lightbulb size={16} />, label: "Creative", description: "Design, brainstorming, prototyping", defaultDuration: 60 },
  learning: { color: "text-cyan-400", bg: "bg-cyan-500/20", icon: <BookOpen size={16} />, label: "Learning", description: "Reading, courses, tutorials", defaultDuration: 45 },
  break: { color: "text-green-400", bg: "bg-green-500/20", icon: <Coffee size={16} />, label: "Break", description: "Rest and recharge", defaultDuration: 15 },
};

const BURNOUT_CONFIG: Record<BurnoutRisk, { color: string; bg: string; label: string; emoji: string }> = {
  thriving: { color: "text-green-400", bg: "bg-green-500/20", label: "Thriving", emoji: "🚀" },
  healthy: { color: "text-cyan-400", bg: "bg-cyan-500/20", label: "Healthy", emoji: "😊" },
  caution: { color: "text-yellow-400", bg: "bg-yellow-500/20", label: "Caution", emoji: "⚠️" },
  warning: { color: "text-orange-400", bg: "bg-orange-500/20", label: "Warning", emoji: "😰" },
  critical: { color: "text-red-400", bg: "bg-red-500/20", label: "Critical", emoji: "🛑" },
};

/* ─────────────── Sample Data ─────────────── */

const FOCUS_SESSIONS: FocusSession[] = [
  { id: "fs1", date: "2026-08-30", startTime: "09:15", endTime: "10:45", duration: 90, mode: "deep_work", interruptions: 1, productivity: 94, energyBefore: "peak", energyAfter: "moderate", tasksCompleted: 4, linesWritten: 342, commitsMade: 2, breakTaken: true, mood: 5, notes: "Solved the auth flow bug, refactored middleware" },
  { id: "fs2", date: "2026-08-30", startTime: "11:00", endTime: "11:30", duration: 30, mode: "shallow", interruptions: 5, productivity: 68, energyBefore: "moderate", energyAfter: "moderate", tasksCompleted: 6, linesWritten: 45, commitsMade: 0, breakTaken: false, mood: 3, notes: "PR reviews and Slack messages" },
  { id: "fs3", date: "2026-08-30", startTime: "14:00", endTime: "15:00", duration: 60, mode: "creative", interruptions: 2, productivity: 88, energyBefore: "high", energyAfter: "moderate", tasksCompleted: 2, linesWritten: 180, commitsMade: 1, breakTaken: true, mood: 4, notes: "Designed new dashboard layout" },
  { id: "fs4", date: "2026-08-29", startTime: "08:30", endTime: "10:00", duration: 90, mode: "deep_work", interruptions: 0, productivity: 97, energyBefore: "peak", energyAfter: "high", tasksCompleted: 5, linesWritten: 456, commitsMade: 3, breakTaken: true, mood: 5, notes: "Perfect flow state — implemented new API" },
  { id: "fs5", date: "2026-08-29", startTime: "13:00", endTime: "13:45", duration: 45, mode: "learning", interruptions: 1, productivity: 82, energyBefore: "moderate", energyAfter: "high", tasksCompleted: 1, linesWritten: 0, commitsMade: 0, breakTaken: false, mood: 4, notes: "Studied system design patterns" },
  { id: "fs6", date: "2026-08-28", startTime: "10:00", endTime: "11:30", duration: 90, mode: "deep_work", interruptions: 3, productivity: 76, energyBefore: "high", energyAfter: "low", tasksCompleted: 3, linesWritten: 210, commitsMade: 1, breakTaken: true, mood: 3, notes: "Complex debugging session" },
  { id: "fs7", date: "2026-08-28", startTime: "15:00", endTime: "15:15", duration: 15, mode: "break", interruptions: 0, productivity: 0, energyBefore: "low", energyAfter: "moderate", tasksCompleted: 0, linesWritten: 0, commitsMade: 0, breakTaken: true, mood: 4, notes: "Walk around the block" },
  { id: "fs8", date: "2026-08-27", startTime: "09:00", endTime: "10:30", duration: 90, mode: "deep_work", interruptions: 2, productivity: 85, energyBefore: "peak", energyAfter: "moderate", tasksCompleted: 3, linesWritten: 298, commitsMade: 2, breakTaken: true, mood: 4, notes: "Backend refactoring complete" },
];

const ENERGY_ENTRIES: EnergyEntry[] = [
  { id: "e1", timestamp: "2026-08-30T08:00", level: "peak", physicalEnergy: 85, mentalEnergy: 90, emotionalEnergy: 80, triggers: ["Good sleep", "Morning exercise", "Healthy breakfast"], activities: ["Meditation", "Walk"], sleepHours: 7.5, caffeine: 1, exercise: true, meals: 1, hydration: 80 },
  { id: "e2", timestamp: "2026-08-30T12:00", level: "moderate", physicalEnergy: 60, mentalEnergy: 55, emotionalEnergy: 65, triggers: ["Post-lunch dip", "Long meeting"], activities: ["Lunch", "Meeting"], sleepHours: 7.5, caffeine: 2, exercise: false, meals: 2, hydration: 60 },
  { id: "e3", timestamp: "2026-08-30T17:00", level: "low", physicalEnergy: 40, mentalEnergy: 35, emotionalEnergy: 50, triggers: ["Screen fatigue", "Deadline pressure"], activities: ["Coding", "Review"], sleepHours: 7.5, caffeine: 3, exercise: false, meals: 3, hydration: 50 },
  { id: "e4", timestamp: "2026-08-29T08:00", level: "peak", physicalEnergy: 90, mentalEnergy: 92, emotionalEnergy: 88, triggers: ["8h sleep", "Yoga", "No caffeine before 10am"], activities: ["Yoga", "Journaling"], sleepHours: 8, caffeine: 0, exercise: true, meals: 1, hydration: 90 },
  { id: "e5", timestamp: "2026-08-29T14:00", level: "high", physicalEnergy: 70, mentalEnergy: 75, emotionalEnergy: 72, triggers: ["Good lunch", "Short walk"], activities: ["Walk", "Reading"], sleepHours: 8, caffeine: 1, exercise: false, meals: 2, hydration: 75 },
];

const SCREEN_TIME: ScreenTimeEntry[] = [
  { date: "2026-08-30", totalHours: 8.5, productiveHours: 5.2, socialHours: 0.8, entertainmentHours: 0.5, breakHours: 1.2, ideHours: 3.8, browserHours: 2.1, terminalHours: 2.6, longestStreak: 92, breaksTaken: 6, postureAlerts: 2 },
  { date: "2026-08-29", totalHours: 9.0, productiveHours: 6.1, socialHours: 0.6, entertainmentHours: 0.3, breakHours: 1.5, ideHours: 4.2, browserHours: 1.8, terminalHours: 3.0, longestStreak: 95, breaksTaken: 7, postureAlerts: 1 },
  { date: "2026-08-28", totalHours: 10.2, productiveHours: 5.8, socialHours: 1.2, entertainmentHours: 0.8, breakHours: 1.0, ideHours: 3.5, browserHours: 3.2, terminalHours: 2.5, longestStreak: 78, breaksTaken: 4, postureAlerts: 5 },
  { date: "2026-08-27", totalHours: 8.0, productiveHours: 5.5, socialHours: 0.5, entertainmentHours: 0.4, breakHours: 1.1, ideHours: 4.0, browserHours: 1.5, terminalHours: 2.5, longestStreak: 90, breaksTaken: 6, postureAlerts: 1 },
  { date: "2026-08-26", totalHours: 7.5, productiveHours: 5.0, socialHours: 0.4, entertainmentHours: 0.3, breakHours: 1.3, ideHours: 3.8, browserHours: 1.2, terminalHours: 2.5, longestStreak: 88, breaksTaken: 5, postureAlerts: 0 },
];

const BURNOUT_METRICS: BurnoutMetric[] = [
  { category: "Workload Balance", score: 7, maxScore: 10, trend: "improving", description: "Managing tasks well but occasional crunch", recommendations: ["Set stricter WIP limits", "Delegate shallow tasks"] },
  { category: "Recovery Quality", score: 6, maxScore: 10, trend: "stable", description: "Sleep is good, but weekend recovery could improve", recommendations: ["No screens 1hr before bed", "Weekend nature walks"] },
  { category: "Social Connection", score: 5, maxScore: 10, trend: "declining", description: "Remote work reducing team interactions", recommendations: ["Weekly virtual coffee chats", "Join a dev community"] },
  { category: "Autonomy & Control", score: 8, maxScore: 10, trend: "improving", description: "Great flexibility in choosing tasks", recommendations: ["Maintain current boundaries"] },
  { category: "Growth & Learning", score: 7, maxScore: 10, trend: "stable", description: "Regular learning but could be more structured", recommendations: ["Dedicated learning Fridays", "Set quarterly skill goals"] },
  { category: "Purpose & Meaning", score: 8, maxScore: 10, trend: "stable", description: "Strong connection to project goals", recommendations: ["Share impact metrics with team"] },
];

const WEEKLY_PATTERNS: WeeklyPattern[] = [
  { day: "Mon", avgFocus: 82, avgEnergy: 85, avgScreenTime: 8.5, bestHour: "9-11 AM", sessionsCount: 4 },
  { day: "Tue", avgFocus: 88, avgEnergy: 80, avgScreenTime: 9.0, bestHour: "9-12 PM", sessionsCount: 5 },
  { day: "Wed", avgFocus: 75, avgEnergy: 70, avgScreenTime: 8.0, bestHour: "10-12 PM", sessionsCount: 4 },
  { day: "Thu", avgFocus: 85, avgEnergy: 78, avgScreenTime: 8.8, bestHour: "9-11 AM", sessionsCount: 5 },
  { day: "Fri", avgFocus: 70, avgEnergy: 65, avgScreenTime: 7.5, bestHour: "9-10 AM", sessionsCount: 3 },
  { day: "Sat", avgFocus: 40, avgEnergy: 90, avgScreenTime: 3.0, bestHour: "—", sessionsCount: 1 },
  { day: "Sun", avgFocus: 20, avgEnergy: 95, avgScreenTime: 1.5, bestHour: "—", sessionsCount: 0 },
];

const ENERGY_INSIGHTS: EnergyInsight[] = [
  { id: "i1", type: "pattern", title: "Peak Hours: 9-11 AM", description: "Your focus and energy peak between 9-11 AM. Schedule deep work here.", icon: <Sun size={16} />, color: "text-yellow-400", priority: 1 },
  { id: "i2", type: "warning", title: "Post-Lunch Dip Detected", description: "Energy drops 35% after lunch. Consider a 10-min walk or lighter tasks.", icon: <AlertTriangle size={16} />, color: "text-orange-400", priority: 2 },
  { id: "i3", type: "tip", title: "Caffeine Timing Matters", description: "Delaying first coffee to 10 AM improves afternoon energy by 20%.", icon: <Coffee size={16} />, color: "text-cyan-400", priority: 3 },
  { id: "i4", type: "achievement", title: "10-Day Focus Streak!", description: "You've completed at least one deep work session for 10 consecutive days.", icon: <Flame size={16} />, color: "text-orange-400", priority: 4 },
  { id: "i5", type: "suggestion", title: "Try Pomodoro for Shallow Work", description: "Shallow work sessions have high interruption rates. Pomodoro could help.", icon: <Timer size={16} />, color: "text-blue-400", priority: 5 },
  { id: "i6", type: "warning", title: "Screen Time Above 9h", description: "3 of last 5 days exceeded 9h screen time. Take more breaks.", icon: <Monitor size={16} />, color: "text-red-400", priority: 6 },
];

/* ─────────────── Sub-Components ─────────────── */

const KpiCard: React.FC<{ icon: React.ReactNode; label: string; value: string | number; sub?: string; color?: string; trend?: string; trendUp?: boolean }> = ({ icon, label, value, sub, color = "text-white", trend, trendUp }) => (
  <Card className="p-4 hover:border-white/20 transition-all">
    <div className="flex items-center gap-2 mb-2"><span className={color}>{icon}</span><span className="text-xs text-gray-400 uppercase tracking-wider">{label}</span></div>
    <div className={`text-2xl font-bold ${color}`}>{value}</div>
    {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    {trend && <div className={`text-xs mt-1 flex items-center gap-1 ${trendUp ? "text-green-400" : "text-red-400"}`}>{trendUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}{trend}</div>}
  </Card>
);

const EnergyGauge: React.FC<{ level: EnergyLevel; size?: number }> = ({ level, size = 120 }) => {
  const cfg = ENERGY_CONFIG[level];
  const radius = (size - 16) / 2;
  const circumference = Math.PI * radius;
  const offset = circumference - (cfg.percentage / 100) * circumference;
  return (
    <div className="relative flex flex-col items-center" style={{ width: size, height: size / 2 + 20 }}>
      <svg width={size} height={size / 2 + 10} className="overflow-visible">
        <path d={`M 8 ${size / 2 + 5} A ${radius} ${radius} 0 0 1 ${size - 8} ${size / 2 + 5}`} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="8" strokeLinecap="round" />
        <path d={`M 8 ${size / 2 + 5} A ${radius} ${radius} 0 0 1 ${size - 8} ${size / 2 + 5}`} fill="none" stroke={cfg.color === "text-green-400" ? "#4ade80" : cfg.color === "text-cyan-400" ? "#22d3ee" : cfg.color === "text-yellow-400" ? "#facc15" : cfg.color === "text-orange-400" ? "#fb923c" : "#f87171"} strokeWidth="8" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset} className="transition-all duration-1000" />
      </svg>
      <div className="absolute bottom-0 flex flex-col items-center">
        <span className={`text-lg font-bold ${cfg.color}`}>{cfg.percentage}%</span>
        <span className="text-[10px] text-gray-500">{cfg.label}</span>
      </div>
    </div>
  );
};

const PomodoroTimer: React.FC<{ state: PomodoroState; onStart: () => void; onPause: () => void; onReset: () => void; onSkip: () => void }> = ({ state, onStart, onPause, onReset, onSkip }) => {
  const minutes = Math.floor(state.timeLeft / 60);
  const seconds = state.timeLeft % 60;
  const progress = 1 - state.timeLeft / state.totalTime;
  const modeColor = state.mode === "work" ? "#a855f7" : state.mode === "short_break" ? "#22d3ee" : "#4ade80";
  const circumference = 2 * Math.PI * 54;
  return (
    <Card className="p-6 flex flex-col items-center">
      <TypoCaption className="text-gray-400 mb-4">Pomodoro Timer</TypoCaption>
      <div className="relative mb-4" style={{ width: 130, height: 130 }}>
        <svg width={130} height={130}>
          <circle cx={65} cy={65} r={54} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
          <circle cx={65} cy={65} r={54} fill="none" stroke={modeColor} strokeWidth="6" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference * (1 - progress)} transform="rotate(-90 65 65)" className="transition-all duration-1000" />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-white font-mono">{String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}</span>
          <span className="text-[10px] text-gray-500 capitalize">{state.mode.replace("_", " ")} #{state.sessionCount}</span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button onClick={onReset} className="p-2 rounded-lg bg-white/5 text-gray-400 hover:text-white transition"><RotateCcw size={16} /></button>
        <button onClick={state.isRunning ? onPause : onStart} className="p-3 rounded-xl text-white transition" style={{ backgroundColor: modeColor }}>
          {state.isRunning ? <Pause size={20} /> : <Play size={20} />}
        </button>
        <button onClick={onSkip} className="p-2 rounded-lg bg-white/5 text-gray-400 hover:text-white transition"><SkipForward size={16} /></button>
      </div>
    </Card>
  );
};

const FocusSessionCard: React.FC<{ session: FocusSession }> = ({ session }) => {
  const modeCfg = FOCUS_MODES[session.mode];
  const energyBeforeCfg = ENERGY_CONFIG[session.energyBefore];
  const energyAfterCfg = ENERGY_CONFIG[session.energyAfter];
  return (
    <div className="bg-white/5 rounded-xl p-4 border border-white/10 hover:border-white/20 transition-all">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={modeCfg.color}>{modeCfg.icon}</span>
          <span className="text-sm font-semibold text-white">{modeCfg.label}</span>
        </div>
        <span className="text-xs text-gray-500">{session.date} · {session.startTime}-{session.endTime}</span>
      </div>
      <div className="grid grid-cols-4 gap-2 text-center text-xs mb-2">
        <div className="bg-white/5 rounded-lg p-2"><div className="text-gray-500">Duration</div><div className="text-white font-bold">{session.duration}m</div></div>
        <div className="bg-white/5 rounded-lg p-2"><div className="text-gray-500">Productivity</div><div className="text-green-400 font-bold">{session.productivity}%</div></div>
        <div className="bg-white/5 rounded-lg p-2"><div className="text-gray-500">Tasks</div><div className="text-white font-bold">{session.tasksCompleted}</div></div>
        <div className="bg-white/5 rounded-lg p-2"><div className="text-gray-500">Lines</div><div className="text-white font-bold">{session.linesWritten}</div></div>
      </div>
      <div className="flex items-center justify-between text-[10px]">
        <div className="flex items-center gap-2">
          <span className={`px-1.5 py-0.5 rounded-full ${energyBeforeCfg.bg} ${energyBeforeCfg.color}`}>{energyBeforeCfg.icon} {energyBeforeCfg.label}</span>
          <span className="text-gray-500">→</span>
          <span className={`px-1.5 py-0.5 rounded-full ${energyAfterCfg.bg} ${energyAfterCfg.color}`}>{energyAfterCfg.icon} {energyAfterCfg.label}</span>
        </div>
        <div className="flex items-center gap-2 text-gray-500">
          <span>{session.interruptions} interruptions</span>
          <span>{["😔", "😐", "🙂", "😊", "🤩"][session.mood - 1]}</span>
        </div>
      </div>
      {session.notes && <div className="mt-2 text-[10px] text-gray-500 italic">"{session.notes}"</div>}
    </div>
  );
};

const BurnoutGauge: React.FC<{ metrics: BurnoutMetric[] }> = ({ metrics }) => {
  const avgScore = metrics.reduce((s, m) => s + m.score, 0) / metrics.length;
  const maxAvg = metrics.reduce((s, m) => s + m.maxScore, 0) / metrics.length;
  const risk = avgScore >= 8 ? "thriving" : avgScore >= 6.5 ? "healthy" : avgScore >= 5 ? "caution" : avgScore >= 3.5 ? "warning" : "critical";
  const cfg = BURNOUT_CONFIG[risk];
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-4">
        <TypoHeading className="text-base">Burnout Prevention</TypoHeading>
        <span className={`text-sm font-bold ${cfg.color} flex items-center gap-1`}>{cfg.emoji} {cfg.label}</span>
      </div>
      <div className="space-y-3">
        {metrics.map((m) => (
          <div key={m.category}>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-gray-400">{m.category}</span>
              <span className="text-white font-bold">{m.score}/{m.maxScore}</span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div className={`h-2 rounded-full transition-all ${m.score >= 7 ? "bg-green-400" : m.score >= 5 ? "bg-yellow-400" : "bg-red-400"}`} style={{ width: `${(m.score / m.maxScore) * 100}%` }} />
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`text-[10px] ${m.trend === "improving" ? "text-green-400" : m.trend === "declining" ? "text-red-400" : "text-gray-500"}`}>
                {m.trend === "improving" ? "↑" : m.trend === "declining" ? "↓" : "→"} {m.trend}
              </span>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 p-3 bg-white/5 rounded-lg">
        <div className="text-xs text-gray-400 mb-1">Overall Score</div>
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-white/10 rounded-full h-3">
            <div className={`h-3 rounded-full ${cfg.color.replace("text-", "bg-")}`} style={{ width: `${(avgScore / maxAvg) * 100}%` }} />
          </div>
          <span className={`text-sm font-bold ${cfg.color}`}>{avgScore.toFixed(1)}/{maxAvg.toFixed(1)}</span>
        </div>
      </div>
    </Card>
  );
};

const InsightCard: React.FC<{ insight: EnergyInsight }> = ({ insight }) => {
  const typeColors: Record<string, string> = { tip: "border-cyan-400/30 bg-cyan-500/5", warning: "border-orange-400/30 bg-orange-500/5", achievement: "border-green-400/30 bg-green-500/5", pattern: "border-purple-400/30 bg-purple-500/5", suggestion: "border-blue-400/30 bg-blue-500/5" };
  return (
    <div className={`rounded-xl p-3 border ${typeColors[insight.type]} flex items-start gap-3`}>
      <span className={insight.color}>{insight.icon}</span>
      <div>
        <div className="text-sm font-semibold text-white">{insight.title}</div>
        <div className="text-xs text-gray-400">{insight.description}</div>
      </div>
    </div>
  );
};

const ScreenTimeBar: React.FC<{ entry: ScreenTimeEntry }> = ({ entry }) => {
  const total = entry.totalHours;
  const segments = [
    { label: "IDE", hours: entry.ideHours, color: "bg-purple-500" },
    { label: "Terminal", hours: entry.terminalHours, color: "bg-green-500" },
    { label: "Browser", hours: entry.browserHours, color: "bg-blue-500" },
    { label: "Social", hours: entry.socialHours, color: "bg-pink-500" },
    { label: "Entertainment", hours: entry.entertainmentHours, color: "bg-orange-500" },
    { label: "Break", hours: entry.breakHours, color: "bg-gray-500" },
  ];
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-gray-400">{entry.date}</span>
        <span className="text-white font-bold">{entry.totalHours}h total · {entry.productiveHours}h productive</span>
      </div>
      <div className="flex w-full h-6 rounded-lg overflow-hidden">
        {segments.filter((s) => s.hours > 0).map((s) => (
          <div key={s.label} className={`${s.color} h-full transition-all`} style={{ width: `${(s.hours / total) * 100}%` }} title={`${s.label}: ${s.hours}h`} />
        ))}
      </div>
      <div className="flex flex-wrap gap-3 mt-1">
        {segments.filter((s) => s.hours > 0).map((s) => (
          <span key={s.label} className="flex items-center gap-1 text-[10px] text-gray-500"><span className={`w-2 h-2 rounded-sm ${s.color}`} />{s.label} {s.hours}h</span>
        ))}
      </div>
    </div>
  );
};

/* ─────────────── Main Component ─────────────── */

function EnergyDashboard() {
  const [activeTab, setActiveTab] = useState<"overview" | "focus" | "energy" | "screen_time" | "burnout" | "insights">("overview");
  const [pomodoro, setPomodoro] = useState<PomodoroState>({ isRunning: false, timeLeft: 25 * 60, totalTime: 25 * 60, sessionCount: 1, mode: "work" });
  const [selectedDate, setSelectedDate] = useState("2026-08-30");
  const [showTimer, setShowTimer] = useState(false);

  useEffect(() => {
    if (!pomodoro.isRunning) return;
    const interval = setInterval(() => {
      setPomodoro((prev) => {
        if (prev.timeLeft <= 1) {
          const nextMode = prev.mode === "work" ? (prev.sessionCount % 4 === 0 ? "long_break" : "short_break") : "work";
          const nextDuration = nextMode === "work" ? 25 * 60 : nextMode === "short_break" ? 5 * 60 : 15 * 60;
          return { isRunning: false, timeLeft: nextDuration, totalTime: nextDuration, sessionCount: nextMode === "work" ? prev.sessionCount + 1 : prev.sessionCount, mode: nextMode as any };
        }
        return { ...prev, timeLeft: prev.timeLeft - 1 };
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [pomodoro.isRunning]);

  const todaySession = FOCUS_SESSIONS.filter((s) => s.date === selectedDate);
  const todayEnergy = ENERGY_ENTRIES.filter((e) => e.timestamp.startsWith(selectedDate));
  const todayScreen = SCREEN_TIME.find((s) => s.date === selectedDate);

  const stats = useMemo(() => {
    const totalFocus = FOCUS_SESSIONS.reduce((s, fs) => s + fs.duration, 0);
    const avgProductivity = Math.round(FOCUS_SESSIONS.reduce((s, fs) => s + fs.productivity, 0) / FOCUS_SESSIONS.length);
    const totalLines = FOCUS_SESSIONS.reduce((s, fs) => s + fs.linesWritten, 0);
    const totalCommits = FOCUS_SESSIONS.reduce((s, fs) => s + fs.commitsMade, 0);
    const deepWorkHours = FOCUS_SESSIONS.filter((s) => s.mode === "deep_work").reduce((s, fs) => s + fs.duration, 0) / 60;
    return { totalFocus, avgProductivity, totalLines, totalCommits, deepWorkHours };
  }, []);

  const startPomodoro = useCallback(() => setPomodoro((p) => ({ ...p, isRunning: true })), []);
  const pausePomodoro = useCallback(() => setPomodoro((p) => ({ ...p, isRunning: false })), []);
  const resetPomodoro = useCallback(() => setPomodoro({ isRunning: false, timeLeft: 25 * 60, totalTime: 25 * 60, sessionCount: 1, mode: "work" }), []);
  const skipPomodoro = useCallback(() => {
    setPomodoro((prev) => {
      const nextMode = prev.mode === "work" ? "short_break" : "work";
      const nextDuration = nextMode === "work" ? 25 * 60 : 5 * 60;
      return { isRunning: false, timeLeft: nextDuration, totalTime: nextDuration, sessionCount: nextMode === "work" ? prev.sessionCount + 1 : prev.sessionCount, mode: nextMode as any };
    });
  }, []);

  const tabs = [
    { id: "overview" as const, label: "Overview", icon: <BarChart3 size={14} /> },
    { id: "focus" as const, label: "Focus Sessions", icon: <Brain size={14} /> },
    { id: "energy" as const, label: "Energy", icon: <Battery size={14} /> },
    { id: "screen_time" as const, label: "Screen Time", icon: <Monitor size={14} /> },
    { id: "burnout" as const, label: "Burnout", icon: <Heart size={14} /> },
    { id: "insights" as const, label: "Insights", icon: <Sparkles size={14} /> },
  ];

  return (
    <div className="mx-auto flex max-w-[1536px] w-full flex-col gap-4 pb-6 pt-2 px-1 sm:px-2">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center">
            <Battery size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Energy & Focus</h1>
            <p className="text-sm text-gray-400">Track energy · Focus deeply · Prevent burnout</p>
          </div>
        </div>
        <Button onClick={() => setShowTimer(!showTimer)} variant="outline" className="gap-2">
          <Timer size={14} />{showTimer ? "Hide Timer" : "Pomodoro Timer"}
        </Button>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <KpiCard icon={<Brain size={18} />} label="Focus Time" value={`${Math.round(stats.totalFocus / 60)}h`} sub="total deep work" color="text-purple-400" trend="+12% this week" trendUp />
        <KpiCard icon={<Target size={18} />} label="Productivity" value={`${stats.avgProductivity}%`} sub="avg across sessions" color="text-green-400" />
        <KpiCard icon={<Code2 size={18} />} label="Lines Written" value={stats.totalLines.toLocaleString()} sub={`${stats.totalCommits} commits`} color="text-cyan-400" />
        <KpiCard icon={<Flame size={18} />} label="Focus Streak" value="10 days" sub="consecutive sessions" color="text-orange-400" />
        <KpiCard icon={<Battery size={18} />} label="Energy" value="Moderate" sub="current level" color="text-yellow-400" trend="↓ from peak" trendUp={false} />
      </div>

      {/* Pomodoro Timer */}
      {showTimer && (
        <div className="flex justify-center">
          <PomodoroTimer state={pomodoro} onStart={startPomodoro} onPause={pausePomodoro} onReset={resetPomodoro} onSkip={skipPomodoro} />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-white/5 rounded-xl p-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${activeTab === tab.id ? "bg-green-500/20 text-green-400 border border-green-400/30" : "text-gray-400 hover:text-white hover:bg-white/5"}`}>
            {tab.icon}{tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            {/* Weekly Patterns */}
            <Card className="p-5">
              <TypoHeading className="text-base mb-4">Weekly Energy Pattern</TypoHeading>
              <div className="space-y-2">
                {WEEKLY_PATTERNS.map((wp) => (
                  <div key={wp.day} className="flex items-center gap-3 text-xs">
                    <span className="text-gray-400 w-8 font-medium">{wp.day}</span>
                    <div className="flex-1 flex items-center gap-2">
                      <span className="text-gray-500 w-12">{wp.avgFocus}%</span>
                      <div className="flex-1 bg-white/10 rounded-full h-2.5 relative">
                        <div className="bg-purple-400 h-2.5 rounded-full" style={{ width: `${wp.avgFocus}%` }} />
                        <div className="absolute top-0 h-2.5 bg-cyan-400/40 rounded-full" style={{ width: `${wp.avgEnergy}%` }} />
                      </div>
                      <span className="text-gray-500 w-8">{wp.sessionsCount}x</span>
                    </div>
                    <span className="text-gray-500 w-20 text-right">{wp.bestHour}</span>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-4 mt-2 text-[10px] text-gray-500">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-purple-400" />Focus %</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-cyan-400/40" />Energy %</span>
              </div>
            </Card>

            {/* Recent Sessions */}
            <Card className="p-5">
              <TypoHeading className="text-base mb-4">Recent Focus Sessions</TypoHeading>
              <div className="space-y-3">
                {FOCUS_SESSIONS.slice(0, 4).map((s) => <FocusSessionCard key={s.id} session={s} />)}
              </div>
            </Card>
          </div>
          <div className="space-y-4">
            {/* Energy Gauge */}
            <Card className="p-5 flex flex-col items-center">
              <TypoCaption className="text-gray-400 mb-2">Current Energy</TypoCaption>
              <EnergyGauge level="moderate" size={140} />
            </Card>

            {/* Today's Breakdown */}
            <Card className="p-5">
              <TypoCaption className="text-gray-400 mb-3">Today's Energy Levels</TypoCaption>
              <div className="space-y-2">
                {todayEnergy.map((e) => {
                  const cfg = ENERGY_CONFIG[e.level];
                  return (
                    <div key={e.id} className="flex items-center gap-3 p-2 bg-white/5 rounded-lg">
                      <span className={cfg.color}>{cfg.icon}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2"><span className="text-xs text-white font-medium">{cfg.label}</span><span className="text-[10px] text-gray-500">{e.timestamp.split("T")[1]}</span></div>
                        <div className="flex gap-2 mt-1">
                          <div className="flex-1 bg-white/10 rounded-full h-1"><div className="bg-cyan-400 h-1 rounded-full" style={{ width: `${e.physicalEnergy}%` }} /></div>
                          <div className="flex-1 bg-white/10 rounded-full h-1"><div className="bg-purple-400 h-1 rounded-full" style={{ width: `${e.mentalEnergy}%` }} /></div>
                          <div className="flex-1 bg-white/10 rounded-full h-1"><div className="bg-pink-400 h-1 rounded-full" style={{ width: `${e.emotionalEnergy}%` }} /></div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="flex items-center gap-3 mt-2 text-[10px] text-gray-500">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-cyan-400" />Physical</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-purple-400" />Mental</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-pink-400" />Emotional</span>
              </div>
            </Card>

            {/* Lifestyle Factors */}
            <Card className="p-5">
              <TypoCaption className="text-gray-400 mb-3">Lifestyle Factors</TypoCaption>
              {todayEnergy.length > 0 && (() => {
                const latest = todayEnergy[0];
                return (
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between"><span className="text-gray-400">Sleep</span><span className="text-white">{latest.sleepHours}h</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Caffeine</span><span className="text-white">{latest.caffeine} cups</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Exercise</span><span className={latest.exercise ? "text-green-400" : "text-red-400"}>{latest.exercise ? "✓ Yes" : "✗ No"}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Meals</span><span className="text-white">{latest.meals}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Hydration</span><span className="text-white">{latest.hydration}%</span></div>
                  </div>
                );
              })()}
            </Card>
          </div>
        </div>
      )}

      {/* Focus Sessions Tab */}
      {activeTab === "focus" && (
        <div className="space-y-3">
          <TypoHeading className="text-base">All Focus Sessions</TypoHeading>
          {FOCUS_SESSIONS.map((s) => <FocusSessionCard key={s.id} session={s} />)}
        </div>
      )}

      {/* Energy Tab */}
      {activeTab === "energy" && (
        <div className="space-y-4">
          <TypoHeading className="text-base">Energy Tracking</TypoHeading>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {ENERGY_ENTRIES.map((e) => {
              const cfg = ENERGY_CONFIG[e.level];
              return (
                <Card key={e.id} className="p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className={cfg.color}>{cfg.icon}</span>
                    <span className="font-semibold text-white">{cfg.label}</span>
                    <span className="text-[10px] text-gray-500 ml-auto">{e.timestamp.split("T")[1]}</span>
                  </div>
                  <div className="space-y-2">
                    <div><div className="flex justify-between text-[10px] mb-0.5"><span className="text-gray-500">Physical</span><span className="text-gray-400">{e.physicalEnergy}%</span></div><div className="w-full bg-white/10 rounded-full h-1.5"><div className="bg-cyan-400 h-1.5 rounded-full" style={{ width: `${e.physicalEnergy}%` }} /></div></div>
                    <div><div className="flex justify-between text-[10px] mb-0.5"><span className="text-gray-500">Mental</span><span className="text-gray-400">{e.mentalEnergy}%</span></div><div className="w-full bg-white/10 rounded-full h-1.5"><div className="bg-purple-400 h-1.5 rounded-full" style={{ width: `${e.mentalEnergy}%` }} /></div></div>
                    <div><div className="flex justify-between text-[10px] mb-0.5"><span className="text-gray-500">Emotional</span><span className="text-gray-400">{e.emotionalEnergy}%</span></div><div className="w-full bg-white/10 rounded-full h-1.5"><div className="bg-pink-400 h-1.5 rounded-full" style={{ width: `${e.emotionalEnergy}%` }} /></div></div>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {e.triggers.map((t) => <span key={t} className="text-[9px] bg-white/10 px-1.5 py-0.5 rounded-full text-gray-400">{t}</span>)}
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Screen Time Tab */}
      {activeTab === "screen_time" && (
        <div className="space-y-4">
          <TypoHeading className="text-base">Screen Time Analytics</TypoHeading>
          <div className="space-y-4">
            {SCREEN_TIME.map((st) => (
              <Card key={st.date} className="p-5">
                <ScreenTimeBar entry={st} />
                <div className="grid grid-cols-4 gap-2 mt-3 text-center text-[10px]">
                  <div className="bg-white/5 rounded-lg p-2"><div className="text-gray-500">Longest Streak</div><div className="text-white font-bold">{st.longestStreak}min</div></div>
                  <div className="bg-white/5 rounded-lg p-2"><div className="text-gray-500">Breaks</div><div className="text-green-400 font-bold">{st.breaksTaken}</div></div>
                  <div className="bg-white/5 rounded-lg p-2"><div className="text-gray-500">Posture Alerts</div><div className={st.postureAlerts > 2 ? "text-red-400 font-bold" : "text-white font-bold"}>{st.postureAlerts}</div></div>
                  <div className="bg-white/5 rounded-lg p-2"><div className="text-gray-500">Productive %</div><div className="text-cyan-400 font-bold">{Math.round((st.productiveHours / st.totalHours) * 100)}%</div></div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Burnout Tab */}
      {activeTab === "burnout" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BurnoutGauge metrics={BURNOUT_METRICS} />
          <Card className="p-5">
            <TypoHeading className="text-base mb-4">Recommendations</TypoHeading>
            <div className="space-y-3">
              {BURNOUT_METRICS.filter((m) => m.score < 7).map((m) => (
                <div key={m.category} className="bg-white/5 rounded-lg p-3">
                  <div className="text-sm font-semibold text-white mb-1">{m.category} <span className="text-yellow-400">({m.score}/{m.maxScore})</span></div>
                  <div className="space-y-1">
                    {m.recommendations.map((r, i) => (
                      <div key={i} className="flex items-start gap-2 text-xs text-gray-400"><Lightbulb size={12} className="text-yellow-400 mt-0.5 shrink-0" />{r}</div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Insights Tab */}
      {activeTab === "insights" && (
        <div className="space-y-3 max-w-3xl">
          <TypoHeading className="text-base">Energy Insights</TypoHeading>
          {ENERGY_INSIGHTS.sort((a, b) => a.priority - b.priority).map((insight) => <InsightCard key={insight.id} insight={insight} />)}
        </div>
      )}
    </div>
  );
}

function Code2({ size }: { size: number }) { return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" /></svg>; }
function BookOpen({ size }: { size: number }) { return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" /></svg>; }
function Wind({ size }: { size: number }) { return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2" /><path d="M9.6 4.6A2 2 0 1 1 11 8H2" /><path d="M12.6 19.4A2 2 0 1 0 14 16H2" /></svg>; }
