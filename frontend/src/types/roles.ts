export const ROLE_PERMISSIONS: Record<string, string[]> = {
  OWNER: ["organization:manage", "members:manage", "roles:manage", "settings:manage"],
  ADMIN: ["members:manage", "roles:manage"],
  RECRUITER: ["members:manage"],
  MAINTAINER: ["repository:manage"],
  MEMBER: [],
};

export function hasPermission(role: string, permission: string): boolean {
  return ROLE_PERMISSIONS[role.toUpperCase()]?.includes(permission) || false;
}
