import { useQuery } from '@tanstack/react-query';
import api from './api';

export interface GitHubLanguage {
  name: string;
  percentage: number;
  count: number;
}

export interface GitHubStats {
  total_prs: number;
  total_issues: number;
  total_stars: number;
  followers: number;
  languages: GitHubLanguage[];
}

export interface GitHubRepository {
  id: number;
  name: string;
  description: string | null;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  updated_at: string;
  html_url: string;
}

export interface GitHubProfile {
  username: string;
  avatar_url: string;
  name: string | null;
  followers: number;
  following: number;
  public_repos: number;
}

export interface GitHubContribution {
  date: string;
  count: number;
  level: number;
}

const STALE_TIME = 5 * 60 * 1000; // 5 minutes

export const githubApi = {
  getProfile: async (username: string): Promise<GitHubProfile> => {
    const { data } = (await api.get(`/github/${username}/profile`)) as any;
    return data;
  },
  getRepositories: async (username: string): Promise<GitHubRepository[]> => {
    const { data } = (await api.get(`/github/${username}/repositories`)) as any;
    return data;
  },
  getStats: async (username: string): Promise<GitHubStats> => {
    const { data } = (await api.get(`/github/${username}/stats`)) as any;
    return data;
  },
  getContributions: async (username: string): Promise<GitHubContribution[]> => {
    const { data } = (await api.get(`/github/${username}/contributions`)) as any;
    return data;
  },
};

export const useGitHubProfile = (username?: string) => {
  return useQuery({
    queryKey: ['github', 'profile', username],
    queryFn: () => githubApi.getProfile(username!),
    enabled: !!username,
    staleTime: STALE_TIME,
  });
};

export const useGitHubRepositories = (username?: string) => {
  return useQuery({
    queryKey: ['github', 'repositories', username],
    queryFn: () => githubApi.getRepositories(username!),
    enabled: !!username,
    staleTime: STALE_TIME,
  });
};

export const useGitHubStats = (username?: string) => {
  return useQuery({
    queryKey: ['github', 'stats', username],
    queryFn: () => githubApi.getStats(username!),
    enabled: !!username,
    staleTime: STALE_TIME,
  });
};

export const useGitHubContributions = (username?: string) => {
  return useQuery({
    queryKey: ['github', 'contributions', username],
    queryFn: () => githubApi.getContributions(username!),
    enabled: !!username,
    staleTime: STALE_TIME,
  });
};
