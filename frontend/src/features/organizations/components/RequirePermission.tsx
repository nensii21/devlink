import React from "react";
import { usePermissions } from "../hooks/usePermissions";
import { Permission } from "../types";

interface RequirePermissionProps {
  orgId: string;
  permission: Permission;
  children: React.ReactNode;
}

export function RequirePermission({ orgId, permission, children }: RequirePermissionProps) {
  const { can, isLoading } = usePermissions(orgId);

  if (isLoading) {
    return null; // Or a loading spinner
  }

  if (!can(permission)) {
    return null;
  }

  return <>{children}</>;
}
