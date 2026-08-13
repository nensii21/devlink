import { api } from "../client";

export interface Organization {
  id: string;
  owner_id: string;
  name: string;
  slug: string;
  description: string | null;
  organization_type: string;
  website: string | null;
  email: string | null;
  phone: string | null;
  logo_url: string | null;
  banner_url: string | null;
  location: string | null;
  github_url: string | null;
  linkedin_url: string | null;
  twitter_url: string | null;
  hiring: boolean;
  active: boolean;
  verified: boolean;
  members_count: number;
  projects_count: number;
  followers_count: number;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  deleted_by_id?: string | null;
}

export interface OrganizationUpdateInput {
  name?: string;
  slug?: string;
  description?: string | null;
  organization_type?: string;
  website?: string | null;
  email?: string | null;
  phone?: string | null;
  logo_url?: string | null;
  banner_url?: string | null;
  location?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  twitter_url?: string | null;
  hiring?: boolean;
  active?: boolean;
}

export const organizationsApi = {
  get: (orgId: string) =>
    api.get<Organization>(`/api/v1/organizations/${encodeURIComponent(orgId)}`),

  list: () => api.get<Organization[]>("/api/v1/organizations"),

  listMine: () => api.get<Organization[]>("/api/v1/organizations/me"),

  update: (orgId: string, input: OrganizationUpdateInput) =>
    api.put<Organization>(`/api/v1/organizations/${encodeURIComponent(orgId)}`, input),
};
