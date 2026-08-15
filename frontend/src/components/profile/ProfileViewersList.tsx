import React, { useState } from "react";
import { Eye, EyeOff, Shield, User, Clock, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { TypoSection, TypoCaption } from "@/components/shared/Typography";

export interface ViewerItem {
  id: string;
  viewer_id?: string;
  viewer_name: string;
  viewer_username: string;
  viewer_avatar?: string;
  viewed_at: string;
  is_anonymous: boolean;
}

export interface ProfileViewersListProps {
  viewers?: ViewerItem[];
  totalViewers?: number;
  hideProfileViews?: boolean;
  onTogglePrivacy?: (enabled: boolean) => void;
  onPageChange?: (page: number) => void;
  currentPage?: number;
  totalPages?: number;
  className?: string;
}

const mockViewers: ViewerItem[] = [
  {
    id: "v-1",
    viewer_id: "u-101",
    viewer_name: "Sarah Chen",
    viewer_username: "sarahc",
    viewer_avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
    viewed_at: "2026-07-31T18:20:00Z",
    is_anonymous: false,
  },
  {
    id: "v-2",
    viewer_name: "Anonymous Developer",
    viewer_username: "anonymous",
    viewed_at: "2026-07-31T15:45:00Z",
    is_anonymous: true,
  },
  {
    id: "v-3",
    viewer_id: "u-102",
    viewer_name: "Alex Rivera",
    viewer_username: "arivera",
    viewer_avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
    viewed_at: "2026-07-30T22:10:00Z",
    is_anonymous: false,
  },
];

export function ProfileViewersList({
  viewers = mockViewers,
  totalViewers = 12,
  hideProfileViews = false,
  onTogglePrivacy,
  onPageChange,
  currentPage = 1,
  totalPages = 2,
  className,
}: ProfileViewersListProps) {
  const [privacyOptOut, setPrivacyOptOut] = useState(hideProfileViews);

  const handleToggle = () => {
    const next = !privacyOptOut;
    setPrivacyOptOut(next);
    onTogglePrivacy?.(next);
  };

  return (
    <div
      className={cn("rounded-xl border border-border bg-card p-6 shadow-sm space-y-6", className)}
    >
      {/* Header & Privacy Opt-Out Control */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <TypoSection>
            <Eye className="h-4 w-4 text-primary" />
            Recent Profile Visitors
          </TypoSection>
          <TypoCaption as="p">{totalViewers} developers viewed your profile recently.</TypoCaption>
        </div>

        {/* Privacy Toggle */}
        <div className="flex items-center gap-3 bg-muted/50 rounded-lg p-2.5 border border-border/60">
          <Shield className="h-4 w-4 text-muted-foreground shrink-0" />
          <div className="text-xs">
            <p className="font-medium text-foreground">Private Browsing</p>
            <TypoCaption as="p">Hide my visits to other profiles</TypoCaption>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={privacyOptOut}
            onClick={handleToggle}
            className={cn(
              "relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ml-auto",
              privacyOptOut ? "bg-primary" : "bg-muted",
            )}
          >
            <span
              className={cn(
                "pointer-events-none inline-block h-4 w-4 transform rounded-full bg-background shadow-lg ring-0 transition duration-200 ease-in-out",
                privacyOptOut ? "translate-x-4" : "translate-x-0",
              )}
            />
          </button>
        </div>
      </div>

      {/* Viewers List */}
      <ul className="divide-y divide-border/60" role="list">
        {viewers.map((viewer) => (
          <li key={viewer.id} className="py-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              {viewer.is_anonymous || !viewer.viewer_avatar ? (
                <TypoCaption>
                  {viewer.is_anonymous ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <User className="h-4 w-4" />
                  )}
                </TypoCaption>
              ) : (
                <img
                  src={viewer.viewer_avatar}
                  alt={viewer.viewer_name}
                  className="h-9 w-9 rounded-full object-cover ring-1 ring-border shrink-0"
                />
              )}

              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground truncate flex items-center gap-1.5">
                  {viewer.viewer_name}
                  {viewer.is_anonymous && <TypoCaption>Private</TypoCaption>}
                </p>
                <TypoCaption as="p">
                  {viewer.is_anonymous
                    ? "Visitor opted out of public identity"
                    : `@${viewer.viewer_username}`}
                </TypoCaption>
              </div>
            </div>

            <time className="text-[11px] text-muted-foreground flex items-center gap-1 shrink-0">
              <Clock className="h-3 w-3" />
              {new Date(viewer.viewed_at).toLocaleTimeString("en-US", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </time>
          </li>
        ))}
      </ul>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2 border-t border-border/60 text-xs">
          <TypoCaption>
            Page {currentPage} of {totalPages}
          </TypoCaption>

          <div className="flex items-center gap-1">
            <button
              type="button"
              disabled={currentPage <= 1}
              onClick={() => onPageChange?.(currentPage - 1)}
              className="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-foreground hover:bg-muted disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="h-3.5 w-3.5" /> Previous
            </button>
            <button
              type="button"
              disabled={currentPage >= totalPages}
              onClick={() => onPageChange?.(currentPage + 1)}
              className="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-foreground hover:bg-muted disabled:opacity-40 transition-colors"
            >
              Next <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
