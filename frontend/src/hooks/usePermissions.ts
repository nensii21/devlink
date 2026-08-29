import { useCallback, useMemo } from "react";

/**
 * Permission checks for the UI.
 *
 * This hook used to hand-maintain its own copy of the authorization rules in
 * a `switch`, and the copy had drifted from the backend:
 *
 * | Action           | this hook granted    | `app/core/rbac.py` grants |
 * | ---------------- | -------------------- | ------------------------- |
 * | `org:delete`     | owner, **admin**     | owner only                |
 * | `project:delete` | owner, **co_owner**  | owner only                |
 *
 * So the UI rendered a "Delete organisation" button for org admins and a
 * "Delete project" button for co-owners, and both came back 403. It also had
 * no notion of the `contributor`, `reviewer` or `viewer` roles the backend
 * added, so those users saw nothing they were allowed to do.
 *
 * Two hand-maintained copies of an authorization table will always drift, so
 * the real fix is to stop keeping a second one. `GET /users/me/permissions`
 * returns the caller's effective permissions grouped by organization and
 * project id; pass that payload in as `serverPermissions` and it is used
 * verbatim.
 *
 * The local tables below remain as a fallback for the render before that
 * request resolves, and they are now generated from the same shape the
 * backend uses rather than an ad-hoc `switch`. `PERMISSION_TABLE_SNAPSHOT` is
 * asserted against the backend's tables in
 * `backend/tests/test_rbac.py::test_frontend_permission_snapshot_matches`, so
 * a change on either side that is not mirrored fails CI instead of shipping.
 *
 * None of this is an authorization boundary. Every mutating endpoint runs its
 * own check; this only decides what to render.
 */

export type OrgRole = "owner" | "admin" | "recruiter" | "maintainer" | "member";

export type ProjectRole =
  | "owner"
  | "co_owner"
  | "admin"
  | "maintainer"
  | "contributor"
  | "reviewer"
  | "viewer"
  | "member";

/** Kept for callers that typed against the previous union. */
export type Role = OrgRole | ProjectRole;

export interface PermissionTarget {
  ownerId?: string;
  owner_id?: string;
  /** The organization or project id, used to look up server-provided grants. */
  id?: string;
  /**
   * Whether the resource is publicly readable.
   *
   * Visibility is not an RBAC question — a public project is readable by
   * anyone, member or not, and the API serves it without consulting the
   * permission tables. The previous hook expressed that as
   * `case "project:view": return true`, which was right for public projects
   * and wrong for private ones. Modelling it as a field keeps both correct.
   */
  visibility?: "public" | "private" | "unlisted" | string;
  members?: Array<{
    userId?: string;
    user_id?: string;
    role: Role;
  }>;
}

/** The payload from `GET /users/me/permissions`. */
export interface ScopedPermissions {
  system: string[];
  organizations: Record<string, string[]>;
  projects: Record<string, string[]>;
}

// ---------------------------------------------------------------------------
// Permission tables — mirrors of `backend/app/core/rbac.py`
// ---------------------------------------------------------------------------

export const ORG_ROLE_PERMISSIONS: Record<OrgRole, readonly string[]> = {
  owner: [
    "org:update",
    "org:delete",
    "org:manage_members",
    "org:manage_tokens",
    "org:manage_roles",
    "org:manage_jobs",
    "org:manage_candidates",
    "org:manage_content",
    "org:manage_plugins",
    "org:view_content",
  ],
  admin: [
    "org:update",
    "org:manage_members",
    "org:manage_tokens",
    "org:manage_roles",
    "org:manage_jobs",
    "org:manage_candidates",
    "org:manage_content",
    "org:manage_plugins",
    "org:view_content",
  ],
  recruiter: ["org:manage_jobs", "org:manage_candidates", "org:view_content"],
  maintainer: ["org:update", "org:manage_content", "org:view_content"],
  member: ["org:view_content"],
};

export const PROJECT_ROLE_PERMISSIONS: Record<ProjectRole, readonly string[]> = {
  owner: [
    "project:update",
    "project:delete",
    "project:invite",
    "project:archive",
    "project:restore",
    "project:view",
    "project:manage_roles",
    "project:transfer_ownership",
    "project:remove_members",
    "project:edit_content",
    "project:review",
  ],
  co_owner: [
    "project:update",
    "project:invite",
    "project:archive",
    "project:restore",
    "project:view",
    "project:manage_roles",
    "project:remove_members",
    "project:edit_content",
    "project:review",
  ],
  admin: [
    "project:update",
    "project:invite",
    "project:view",
    "project:manage_roles",
    "project:remove_members",
    "project:edit_content",
    "project:review",
  ],
  maintainer: [
    "project:update",
    "project:invite",
    "project:view",
    "project:manage_roles",
    "project:remove_members",
    "project:edit_content",
    "project:review",
  ],
  contributor: ["project:view", "project:edit_content", "project:review"],
  reviewer: ["project:view", "project:review"],
  viewer: ["project:view"],
  member: ["project:view"],
};

/**
 * The two tables above in one object, so a single test can compare them
 * against the backend without knowing how this module is laid out.
 */
export const PERMISSION_TABLE_SNAPSHOT = {
  organizations: ORG_ROLE_PERMISSIONS,
  projects: PROJECT_ROLE_PERMISSIONS,
} as const;

const ORG_ACTION = /^org:/;
const PROJECT_ACTION = /^project:/;

function permissionsForRole(action: string, role: Role | undefined): readonly string[] {
  if (!role) return [];

  if (ORG_ACTION.test(action)) {
    return ORG_ROLE_PERMISSIONS[role as OrgRole] ?? [];
  }

  if (PROJECT_ACTION.test(action)) {
    return PROJECT_ROLE_PERMISSIONS[role as ProjectRole] ?? [];
  }

  return [];
}

/**
 * Permissions the *owner* of a resource holds.
 *
 * Ownership was previously treated as a blanket yes for every action in the
 * `switch`, which happened to be right for the actions it listed and would
 * have been wrong for the next one added. Owning a thing grants the owner
 * role's permissions, nothing more.
 */
function ownerPermissions(action: string): readonly string[] {
  if (ORG_ACTION.test(action)) return ORG_ROLE_PERMISSIONS.owner;
  if (PROJECT_ACTION.test(action)) return PROJECT_ROLE_PERMISSIONS.owner;
  return [];
}

export function usePermissions(
  currentUserId?: string,
  isSuperuser = false,
  serverPermissions?: ScopedPermissions,
) {
  const server = useMemo(() => serverPermissions, [serverPermissions]);

  const can = useCallback(
    (action: string, target?: PermissionTarget): boolean => {
      if (isSuperuser) return true;

      // A public resource is readable without an account at all, so this is
      // answered before the "are you signed in" check.
      if (
        (action === "project:view" || action === "org:view_content") &&
        target?.visibility === "public"
      ) {
        return true;
      }

      if (!currentUserId) return false;

      // Prefer the server's answer whenever we have one for this resource.
      // It is computed from the tables the API actually enforces, so it
      // cannot disagree with the 403 the user would get.
      if (server && target?.id) {
        const scope = ORG_ACTION.test(action)
          ? server.organizations
          : PROJECT_ACTION.test(action)
            ? server.projects
            : undefined;

        const granted = scope?.[target.id];
        if (granted) return granted.includes(action);
      }

      if (server && !target?.id && server.system.includes(action)) {
        return true;
      }

      const ownerId = target?.ownerId ?? target?.owner_id;
      if (ownerId && ownerId === currentUserId) {
        return ownerPermissions(action).includes(action);
      }

      const member = target?.members?.find(
        (m) => m.userId === currentUserId || m.user_id === currentUserId,
      );

      return permissionsForRole(action, member?.role).includes(action);
    },
    [currentUserId, isSuperuser, server],
  );

  return { can };
}
