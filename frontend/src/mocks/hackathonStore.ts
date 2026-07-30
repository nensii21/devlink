/**
 * In-memory mock store for hackathon data.
 * Lets create/join/submit actions actually work in mock mode
 * so the UI reflects changes without a real backend.
 */

import type {
  Hackathon,
  HackathonTeam,
  HackathonSubmission,
  HackathonLeaderboardEntry,
} from "./seed";
import {
  hackathons as seedHackathons,
  hackathonTeams as seedTeams,
  hackathonSubmissions as seedSubmissions,
  hackathonLeaderboard as seedLeaderboard,
} from "./seed";

// Deep-clone seed data so mutations don't affect the original module
let hackathons: Hackathon[] = seedHackathons.map((h) => ({ ...h }));
let teams: HackathonTeam[] = seedTeams.map((t) => ({ ...t }));
let submissions: HackathonSubmission[] = seedSubmissions.map((s) => ({ ...s }));
const leaderboard: HackathonLeaderboardEntry[] = seedLeaderboard.map((e) => ({ ...e }));
const registrations = new Set<string>(); // "hackathonId:userId"

function uuid(): string {
  return "mock-" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
}

function now(): string {
  return new Date().toISOString();
}

const delay = (ms = 300) => new Promise<void>((r) => setTimeout(r, ms));

export const hackathonStore = {
  // ── Hackathons ────────────────────────────────────────────────────────────
  getAll() {
    return hackathons;
  },
  getById(id: string) {
    return hackathons.find((h) => h.id === id) ?? null;
  },
  async create(body: Partial<Hackathon>): Promise<Hackathon> {
    await delay();
    const h: Hackathon = {
      id: uuid(),
      name: body.name ?? "Untitled Hackathon",
      description: body.description ?? "",
      theme: body.theme ?? "",
      prize: body.prize ?? "",
      starts_at: body.starts_at ?? now(),
      ends_at: body.ends_at ?? now(),
      min_team_size: body.min_team_size ?? 1,
      max_team_size: body.max_team_size ?? 4,
      status: body.status ?? "registration_open",
      is_published: body.is_published ?? true,
      website_url: body.website_url,
      created_by: "me",
      created_at: now(),
      updated_at: now(),
    };
    hackathons = [...hackathons, h];
    return h;
  },

  // ── Teams ─────────────────────────────────────────────────────────────────
  getTeams(hackathonId: string): HackathonTeam[] {
    return teams.filter((t) => t.hackathon_id === hackathonId);
  },

  async createTeam(
    hackathonId: string,
    body: { name: string; description?: string },
  ): Promise<HackathonTeam> {
    await delay();
    const team: HackathonTeam = {
      id: uuid(),
      hackathon_id: hackathonId,
      name: body.name,
      description: body.description,
      created_by: "me",
      member_count: 1,
      created_at: now(),
      updated_at: now(),
    };
    teams = [...teams, team];
    return team;
  },

  async joinTeam(teamId: string): Promise<void> {
    await delay();
    teams = teams.map((t) => (t.id === teamId ? { ...t, member_count: t.member_count + 1 } : t));
  },

  async leaveTeam(teamId: string): Promise<void> {
    await delay();
    teams = teams.map((t) =>
      t.id === teamId ? { ...t, member_count: Math.max(0, t.member_count - 1) } : t,
    );
  },

  // ── Registrations ─────────────────────────────────────────────────────────
  isRegistered(hackathonId: string): boolean {
    return registrations.has(`${hackathonId}:me`);
  },

  async register(hackathonId: string): Promise<void> {
    await delay();
    registrations.add(`${hackathonId}:me`);
  },

  async cancelRegistration(hackathonId: string): Promise<void> {
    await delay();
    registrations.delete(`${hackathonId}:me`);
  },

  // ── Submissions ───────────────────────────────────────────────────────────
  getSubmissions(hackathonId: string): HackathonSubmission[] {
    return submissions.filter((s) => s.hackathon_id === hackathonId);
  },

  async createSubmission(
    hackathonId: string,
    body: {
      team_id: string;
      title: string;
      description: string;
      repo_url?: string;
      demo_url?: string;
    },
  ): Promise<HackathonSubmission> {
    await delay();
    const sub: HackathonSubmission = {
      id: uuid(),
      hackathon_id: hackathonId,
      team_id: body.team_id,
      submitted_by: "me",
      title: body.title,
      description: body.description,
      repo_url: body.repo_url,
      demo_url: body.demo_url,
      status: "submitted",
      created_at: now(),
      updated_at: now(),
    };
    submissions = [...submissions, sub];
    return sub;
  },

  // ── Leaderboard ───────────────────────────────────────────────────────────
  getLeaderboard(hackathonId: string): HackathonLeaderboardEntry[] {
    const hackathonTeamIds = teams.filter((t) => t.hackathon_id === hackathonId).map((t) => t.id);
    return leaderboard.filter((e) => hackathonTeamIds.includes(e.team_id));
  },
};
