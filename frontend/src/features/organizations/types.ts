export type OrganizationMemberRole = "owner" | "admin" | "recruiter" | "maintainer" | "member";

export type Permission =
  | "organization:manage"
  | "members:manage"
  | "roles:manage"
  | "settings:manage"
  | "jobs:create"
  | "jobs:manage"
  | "candidates:view"
  | "candidates:manage"
  | "content:manage"
  | "content:view"
  | "organization:view";

export interface OrganizationMember {
  id: string;
  organization_id: string;
  user_id: string;
  role: OrganizationMemberRole;
  is_active: boolean;
  joined_at: string;
  user?: {
    id: string;
    username: string;
    full_name?: string;
    avatar_url?: string;
  };
}
