"use client";

import React, { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { blocksApi } from "@/api/modules/blocks";
import { type User } from "@/lib/api";
import { UserAvatar } from "@/components/user-avatar";
import { Button } from "@/components/ui/button";
import { Card, EmptyState, Skeleton } from "@/components/shared/primitives";
import { TypoHeading, TypoCaption } from "@/components/shared/Typography";
import { toast } from "sonner";
import { ShieldOff, Loader2, UserX } from "lucide-react";

export function BlockedUsersSettings() {
  const queryClient = useQueryClient();
  const [unblockingId, setUnblockingId] = useState<string | null>(null);

  const { data: blockedUsers = [], isLoading, error } = useQuery({
    queryKey: ["blocked-users-list"],
    queryFn: () => blocksApi.getBlockedUsers(),
  });

  const handleUnblock = async (userId: string) => {
    setUnblockingId(userId);
    try {
      await blocksApi.unblockUser(userId);
      toast.success("User unblocked successfully");
      await queryClient.invalidateQueries({ queryKey: ["blocked-users-list"] });
    } catch (err: any) {
      toast.error(err?.message || "Failed to unblock user");
    } finally {
      setUnblockingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} className="p-3.5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="space-y-1">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
            </div>
            <Skeleton className="h-8 w-20" />
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-4 border-destructive/30 bg-destructive/5">
        <p className="text-xs font-semibold text-destructive">Failed to load blocked users list</p>
      </Card>
    );
  }

  if (blockedUsers.length === 0) {
    return (
      <EmptyState
        icon={UserX}
        title="No blocked users"
        desc="Users you block won't be able to see your profile or posts, and their content will be hidden from your feed."
      />
    );
  }

  return (
    <div className="space-y-3">
      {blockedUsers.map((user: User) => {
        const name = `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.username;
        return (
          <Card key={user.id} className="p-3.5 border-border bg-card flex items-center justify-between">
            <div className="flex items-center gap-3">
              <UserAvatar user={user} className="h-10 w-10" />
              <div>
                <TypoHeading as="h4" className="text-xs font-bold text-foreground">
                  {name}
                </TypoHeading>
                <TypoCaption className="text-[11px] text-muted-foreground">
                  @{user.username}
                </TypoCaption>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleUnblock(user.id)}
              disabled={unblockingId === user.id}
              className="text-xs hover:bg-muted border-border gap-1 shrink-0"
            >
              {unblockingId === user.id ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <ShieldOff className="h-3 w-3" />
              )}
              Unblock
            </Button>
          </Card>
        );
      })}
    </div>
  );
}
