import { api } from "../client";
import type {
  Hackathon,
  HackathonTeam,
  HackathonSubmission,
  HackathonLeaderboardEntry,
} from "@/mocks/seed";

export type { HackathonSubmission, HackathonLeaderboardEntry };

export const hackathonsApi = {
  list: () => api.get<Hackathon[]>("/api/hackathons"),
  get: (id: string) => api.get<Hackathon>(`/api/hackathons/${id}`),
  create: (body: Partial<Hackathon>) => api.post<Hackathon>("/api/hackathons", body),
  update: (id: string, body: Partial<Hackathon>) =>
    api.put<Hackathon>(`/api/hackathons/${id}`, body),
  delete: (id: string) => api.delete<void>(`/api/hackathons/${id}`),
  register: (id: string, body?: { motivation?: string }) =>
    api.post<void>(`/api/hackathons/${id}/registrations`, body),
  cancelRegistration: (id: string) => api.delete<void>(`/api/hackathons/${id}/registrations`),
  getTeams: (id: string) => api.get<HackathonTeam[]>(`/api/hackathons/${id}/teams`),
  createTeam: (id: string, body: { name: string; description?: string }) =>
    api.post<HackathonTeam>(`/api/hackathons/${id}/teams`, body),
  joinTeam: (teamId: string) => api.post<void>(`/api/hackathons/teams/${teamId}/join`),
  leaveTeam: (teamId: string) => api.delete<void>(`/api/hackathons/teams/${teamId}/leave`),
  getSubmissions: (id: string) =>
    api.get<HackathonSubmission[]>(`/api/hackathons/${id}/submissions`),
  createSubmission: (
    id: string,
    body: {
      team_id: string;
      title: string;
      description: string;
      repo_url?: string;
      demo_url?: string;
    },
  ) => api.post<HackathonSubmission>(`/api/hackathons/${id}/submissions`, body),
  getLeaderboard: (id: string) =>
    api.get<HackathonLeaderboardEntry[]>(`/api/hackathons/${id}/leaderboard`),
};
