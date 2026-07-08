import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useFollowStatus, useFollow, useUnfollow } from "@/hooks/useFollow";
import { Loader2, UserPlus, UserCheck, UserMinus } from "lucide-react";
import { cn } from "@/lib/utils";
import type { UUID } from "@/lib/api";

export function FollowButton({
  userId,
  className,
}: {
  userId: UUID;
  className?: string;
}) {
  const { data: status, isLoading: statusLoading } = useFollowStatus(userId);
  const followMutation = useFollow(userId);
  const unfollowMutation = useUnfollow(userId);

  const [hovered, setHovered] = useState(false);

  const isFollowing = status?.is_following ?? false;
  const isBusy = followMutation.isPending || unfollowMutation.isPending;

  function handleClick() {
    if (isBusy) return;
    if (isFollowing) {
      unfollowMutation.mutate();
    } else {
      followMutation.mutate();
    }
  }

  if (statusLoading) {
    return (
      <Button variant="outline" size="sm" disabled className={cn("min-w-[100px]", className)}>
        <Loader2 size={14} className="animate-spin" />
      </Button>
    );
  }

  if (isFollowing) {
    return (
      <Button
        variant={hovered ? "destructive" : "outline"}
        size="sm"
        onClick={handleClick}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        disabled={isBusy}
        className={cn("min-w-[100px] transition-all", className)}
      >
        {isBusy ? (
          <Loader2 size={14} className="animate-spin" />
        ) : hovered ? (
          <>
            <UserMinus size={14} />
            Unfollow
          </>
        ) : (
          <>
            <UserCheck size={14} />
            Following
          </>
        )}
      </Button>
    );
  }

  return (
    <Button
      size="sm"
      onClick={handleClick}
      disabled={isBusy}
      className={cn("min-w-[100px]", className)}
    >
      {isBusy ? (
        <Loader2 size={14} className="animate-spin" />
      ) : (
        <>
          <UserPlus size={14} />
          Follow
        </>
      )}
    </Button>
  );
}
