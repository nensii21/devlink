import { useCallback } from "react";

export type Role = "owner" | "co_owner" | "admin" | "maintainer" | "member" | "user";

export interface PermissionTarget {
  ownerId?: string;
  owner_id?: string;
  members?: Array<{
    userId: string;
    user_id?: string;
    role: Role;
  }>;
}

export function usePermissions(currentUserId?: string, isSuperuser = false) {
  const can = useCallback(
    (action: string, target?: PermissionTarget): boolean => {
      if (isSuperuser) return true;
      if (!currentUserId) return false;

      const ownerId = target?.ownerId ?? target?.owner_id;
      const isOwner = ownerId === currentUserId;

      // Extract current user membership record if target has members list
      const member = target?.members?.find(
        (m) => m.userId === currentUserId || m.user_id === currentUserId,
      );
      const userRole = member?.role;

      switch (action) {
        case "org:update":
        case "org:delete":
        case "org:manage_members":
          return isOwner || userRole === "owner" || userRole === "admin";

        case "project:update":
        case "project:invite":
        case "project:archive":
        case "project:restore":
          return (
            isOwner ||
            userRole === "owner" ||
            userRole === "co_owner" ||
            userRole === "admin" ||
            userRole === "maintainer"
          );

        case "project:delete":
          return isOwner || userRole === "owner" || userRole === "co_owner";

        case "project:view":
          return true; // Default public view permissions

        default:
          return false;
      }
    },
    [currentUserId, isSuperuser],
  );

  return { can };
}
