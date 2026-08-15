import * as React from "react";
import { BadgeCheck, Camera } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { getInitials, cn } from "@/lib/utils";
import { ImageCropUploadModal } from "@/components/shared/ImageCropUploadModal";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type UserAvatarSize = "xs" | "sm" | "md" | "lg" | "xl" | "2xl";

export type OnlineStatus = "online" | "offline" | "away" | "busy";

export interface UserAvatarProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** URL of the avatar image. Pass `null` or omit to show initials. */
  src?: string | null;
  /** Full display name used to derive initials and the accessible label. */
  name?: string;
  /** Override the img `alt` / aria-label value. */
  alt?: string;
  /** One of the preset sizes. Defaults to `"md"`. */
  size?: UserAvatarSize;
  /**
   * Presence indicator.
   * - `"online" | "away" | "busy" | "offline"` — show a coloured dot.
   * - `true` shorthand for `"online"`.
   * - `false` / omit — no indicator.
   */
  status?: OnlineStatus | boolean;
  /** Show a verification checkmark badge. */
  verified?: boolean;
  /** Show premium golden verified styling. */
  premium?: boolean;
  /** Override the initials derived from `name`. */
  initials?: string;
  /** Allow clicking avatar to open Crop & Upload Modal. */
  editable?: boolean;
  /** Callback when a new avatar image is cropped and uploaded. */
  onImageUpload?: (url: string) => void;
}

// ---------------------------------------------------------------------------
// Size & status maps
// ---------------------------------------------------------------------------

const sizeMap: Record<
  UserAvatarSize,
  {
    avatar: string;
    text: string;
    indicator: string;
    badge: string;
    badgeIcon: number;
  }
> = {
  xs: {
    avatar: "h-6 w-6",
    text: "text-[10px]",
    indicator: "h-1.5 w-1.5",
    badge: "h-3 w-3",
    badgeIcon: 10,
  },
  sm: {
    avatar: "h-8 w-8",
    text: "text-xs",
    indicator: "h-2 w-2",
    badge: "h-3.5 w-3.5",
    badgeIcon: 12,
  },
  md: {
    avatar: "h-10 w-10",
    text: "text-sm",
    indicator: "h-2.5 w-2.5",
    badge: "h-4 w-4",
    badgeIcon: 12,
  },
  lg: {
    avatar: "h-12 w-12",
    text: "text-base",
    indicator: "h-3 w-3",
    badge: "h-5 w-5",
    badgeIcon: 14,
  },
  xl: {
    avatar: "h-16 w-16",
    text: "text-lg",
    indicator: "h-3.5 w-3.5",
    badge: "h-6 w-6",
    badgeIcon: 16,
  },
  "2xl": {
    avatar: "h-24 w-24",
    text: "text-2xl",
    indicator: "h-4 w-4",
    badge: "h-7 w-7",
    badgeIcon: 20,
  },
};

const statusColorMap: Record<OnlineStatus, string> = {
  online: "bg-emerald-500",
  offline: "bg-muted-foreground/50",
  away: "bg-amber-500",
  busy: "bg-red-500",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const UserAvatar = React.forwardRef<HTMLSpanElement, UserAvatarProps>(
  (
    {
      src,
      name,
      alt,
      size = "md",
      status,
      verified = false,
      premium = false,
      initials: initialsOverride,
      editable = false,
      onImageUpload,
      className,
      ...props
    },
    ref,
  ) => {
    const s = sizeMap[size];
    const [isCropModalOpen, setIsCropModalOpen] = React.useState(false);
    const [currentSrc, setCurrentSrc] = React.useState<string | null | undefined>(src);

    React.useEffect(() => {
      setCurrentSrc(src);
    }, [src]);

    // Normalise the `status` prop
    const resolvedStatus: OnlineStatus | undefined =
      status === true ? "online" : status === false || status === undefined ? undefined : status;

    const displayInitials = initialsOverride ?? getInitials(name);
    const ariaLabel = alt ?? (name ? `${name}${verified ? ", verified" : ""}` : "User avatar");

    const handleUploadSuccess = (newUrl: string) => {
      setCurrentSrc(newUrl);
      if (onImageUpload) {
        onImageUpload(newUrl);
      }
    };

    return (
      <>
        <span
          ref={ref}
          className={cn(
            "relative inline-flex shrink-0",
            editable && "group cursor-pointer",
            className,
          )}
          onClick={editable ? () => setIsCropModalOpen(true) : undefined}
          {...props}
        >
          {/* Base avatar */}
          <Avatar className={cn(s.avatar, "relative overflow-hidden")}>
            {currentSrc ? (
              <img
                src={currentSrc}
                alt={ariaLabel}
                className="aspect-square h-full w-full object-cover"
              />
            ) : (
              <AvatarFallback
                className={cn(s.text, "select-none bg-muted font-medium text-muted-foreground")}
                aria-label={ariaLabel}
              >
                {displayInitials}
              </AvatarFallback>
            )}

            {/* Editable camera overlay */}
            {editable && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
                <Camera className="text-white" size={size === "xs" || size === "sm" ? 12 : 18} />
              </div>
            )}
          </Avatar>

          {/* Online status indicator dot */}
          {resolvedStatus ? (
            <span
              role="status"
              aria-label={`Status: ${resolvedStatus}`}
              className={cn(
                "absolute bottom-0 right-0 rounded-full ring-2 ring-background",
                s.indicator,
                statusColorMap[resolvedStatus],
              )}
            />
          ) : null}

          {/* Verification badge */}
          {verified ? (
            <span
              aria-label="Verified"
              className={cn(
                "absolute -right-0.5 -top-0.5 inline-flex items-center justify-center rounded-full bg-background",
                premium ? "text-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.35)]" : "text-primary",
                s.badge,
              )}
            >
              <BadgeCheck
                size={s.badgeIcon}
                className={cn(
                  premium
                    ? "fill-amber-500/10 text-amber-500 animate-pulse"
                    : "fill-primary text-primary-foreground",
                )}
              />
            </span>
          ) : null}
        </span>

        {editable && (
          <ImageCropUploadModal
            isOpen={isCropModalOpen}
            onClose={() => setIsCropModalOpen(false)}
            onUploadSuccess={handleUploadSuccess}
            mode="avatar"
            title="Upload Avatar Image"
          />
        )}
      </>
    );
  },
);

UserAvatar.displayName = "UserAvatar";

export { UserAvatar };
