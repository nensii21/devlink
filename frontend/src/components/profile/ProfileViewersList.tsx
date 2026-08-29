import React, { useState } from "react";
import {
  Eye,
  EyeOff,
  Shield,
  User,
  Clock,
  Calendar,
  Sparkles,
  Lock,
  ChevronLeft,
  ChevronRight,
  Activity,
  Crown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { TypoSection, TypoCaption } from "@/components/shared/Typography";

export interface ViewerItem {
  id: string;
  viewer_id?: string;
  viewer_name: string;
  viewer_username: string;
  viewer_avatar?: string;
  viewed_at: string;
  visit_count?: number;
  is_anonymous: boolean;
}

export interface ProfileViewersListProps {
  viewers?: ViewerItem[];
  totalViewers?: number;
  hideProfileViews?: boolean;
  isPremium?: boolean;
  onTogglePrivacy?: (enabled: boolean) => void;
  onPageChange?: (page: number) => void;
  onUpgrade?: () => void;
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
    visit_count: 5,
    is_anonymous: false,
  },
  {
    id: "v-2",
    viewer_name: "Anonymous Developer",
    viewer_username: "anonymous",
    viewed_at: "2026-07-31T15:45:00Z",
    visit_count: 1,
    is_anonymous: true,
  },
  {
    id: "v-3",
    viewer_id: "u-102",
    viewer_name: "Alex Rivera",
    viewer_username: "arivera",
    viewer_avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
    viewed_at: "2026-07-30T22:10:00Z",
    visit_count: 3,
    is_anonymous: false,
  },
];

function formatVisitDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export function ProfileViewersList({
  viewers = mockViewers,
  totalViewers = 12,
  hideProfileViews = false,
  isPremium = true,
  onTogglePrivacy,
  onPageChange,
  onUpgrade,
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

  // Non-Premium Locked View
  if (!isPremium) {
    return (
      <div
        className={cn(
          "rounded-xl border border-primary/20 bg-gradient-to-br from-card via-card to-primary/5 p-6 shadow-sm space-y-6 relative overflow-hidden",
          className,
        )}
      >
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Crown className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
                Recent Profile Visitors
                <span className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">
                  <Sparkles className="h-3 w-3" /> PRO
                </span>
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Exclusive feature for premium members
              </p>
            </div>
          </div>
          <Lock className="h-5 w-5 text-muted-foreground" />
        </div>

        <div className="py-4 space-y-4 text-center max-w-md mx-auto">
          <div className="inline-flex items-center justify-center p-3 rounded-full bg-primary/10 text-primary mb-1">
            <Eye className="h-6 w-6" />
          </div>
          <h4 className="text-sm font-semibold text-foreground">
            See Who is Checking Out Your Profile
          </h4>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Upgrade to DevLink Pro to view recent visitor history, visit dates, visit frequencies,
            and enable private browsing mode.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-left">
            <div className="p-2.5 rounded-lg border border-border/80 bg-muted/40 text-xs">
              <p className="font-semibold text-foreground flex items-center gap-1">
                <User className="h-3.5 w-3.5 text-primary" /> Visitor Insights
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">
                Discover developers and recruiters exploring your portfolio.
              </p>
            </div>
            <div className="p-2.5 rounded-lg border border-border/80 bg-muted/40 text-xs">
              <p className="font-semibold text-foreground flex items-center gap-1">
                <Activity className="h-3.5 w-3.5 text-primary" /> Visit Frequency
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">
                Track how often profiles visit and view your work.
              </p>
            </div>
            <div className="p-2.5 rounded-lg border border-border/80 bg-muted/40 text-xs">
              <p className="font-semibold text-foreground flex items-center gap-1">
                <Shield className="h-3.5 w-3.5 text-primary" /> Privacy Control
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">
                Browse other profiles anonymously with stealth mode.
              </p>
            </div>
          </div>

          <div className="pt-3">
            <button
              type="button"
              onClick={onUpgrade}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-xs font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <Sparkles className="h-4 w-4" /> Upgrade to DevLink Pro
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Active Premium View
  return (
    <div
      className={cn("rounded-xl border border-border bg-card p-6 shadow-sm space-y-6", className)}
    >
      {/* Header & Privacy Opt-Out Control */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <TypoSection>
              <Eye className="h-4 w-4 text-primary" />
              Recent Profile Visitors
            </TypoSection>
            <span className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
              <Crown className="h-3 w-3" /> PRO
            </span>
          </div>
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
        {viewers.map((viewer) => {
          const visitCount = viewer.visit_count ?? 1;
          return (
            <li key={viewer.id} className="py-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 min-w-0">
                {viewer.is_anonymous || !viewer.viewer_avatar ? (
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-muted-foreground font-semibold text-xs border border-border shrink-0">
                    {viewer.is_anonymous ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <User className="h-4 w-4" />
                    )}
                  </span>
                ) : (
                  <img
                    src={viewer.viewer_avatar}
                    alt={viewer.viewer_name}
                    className="h-9 w-9 rounded-full object-cover ring-1 ring-border shrink-0"
                  />
                )}

                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-foreground truncate">
                      {viewer.viewer_name}
                    </p>
                    {viewer.is_anonymous ? (
                      <span className="inline-flex items-center rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                        Private
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                        <Activity className="h-2.5 w-2.5" />
                        {visitCount} {visitCount === 1 ? "visit" : "visits"}
                      </span>
                    )}
                  </div>
                  <TypoCaption as="p">
                    {viewer.is_anonymous
                      ? "Visitor opted out of public identity"
                      : `@${viewer.viewer_username}`}
                  </TypoCaption>
                </div>
              </div>

              <div className="flex flex-col items-end shrink-0 text-right">
                <time
                  dateTime={viewer.viewed_at}
                  className="text-[11px] text-muted-foreground flex items-center gap-1"
                >
                  <Calendar className="h-3 w-3" />
                  {formatVisitDate(viewer.viewed_at)}
                </time>
                {viewer.is_anonymous && (
                  <span className="text-[10px] text-muted-foreground mt-0.5 flex items-center gap-0.5">
                    <Clock className="h-2.5 w-2.5" /> {visitCount}{" "}
                    {visitCount === 1 ? "visit" : "visits"}
                  </span>
                )}
              </div>
            </li>
          );
        })}
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
