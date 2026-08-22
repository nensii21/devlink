import { OrganizationMemberRole, Permission } from "./types";

export const ROLE_PERMISSIONS: Record<OrganizationMemberRole, readonly Permission[]> = {
  owner: [
    "organization:manage",
    "members:manage",
    "roles:manage",
    "settings:manage",
    "jobs:create",
    "jobs:manage",
    "candidates:view",
    "candidates:manage",
    "content:manage",
    "content:view",
    "organization:view",
  ],
  admin: [
    "members:manage",
    "roles:manage",
    "settings:manage",
    "jobs:create",
    "jobs:manage",
    "candidates:view",
    "candidates:manage",
    "content:manage",
    "content:view",
    "organization:view",
  ],
  recruiter: [
    "jobs:create",
    "jobs:manage",
    "candidates:view",
    "candidates:manage",
    "content:view",
    "organization:view",
  ],
  maintainer: ["content:manage", "settings:manage", "content:view", "organization:view"],
  member: ["organization:view", "content:view"],
} as const;

export function hasPermission(role: OrganizationMemberRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}
