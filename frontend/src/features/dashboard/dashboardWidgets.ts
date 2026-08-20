import React from "react";
import {
  CurrentProjects,
  AISuggestions,
  QuickActions,
  RecentActivity,
  Upcoming,
  NotificationsWidget,
  UpcomingEventsWidget,
  UpgradePlanCTA,
} from "./sections";
import {
  FolderGit2,
  Sparkles,
  Zap,
  Activity,
  Calendar,
  Bell,
  CalendarDays,
  Rocket,
} from "lucide-react";
import type { DashboardWidgetLayout } from "@/api/modules/dashboardLayout";

export interface WidgetDefinition {
  id: string;
  title: string;
  description: string;
  category: "main" | "sidebar";
  defaultColumn: number; // 1 for main, 2 for sidebar
  defaultOrder: number;
  defaultPinned: boolean;
  defaultVisible: boolean;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  component: React.ComponentType;
}

export const WIDGET_REGISTRY: Record<string, WidgetDefinition> = {
  "current-projects": {
    id: "current-projects",
    title: "Current Projects",
    description: "Active projects you are collaborating on or managing",
    category: "main",
    defaultColumn: 1,
    defaultOrder: 0,
    defaultPinned: false,
    defaultVisible: true,
    icon: FolderGit2,
    component: CurrentProjects,
  },
  "ai-suggestions": {
    id: "ai-suggestions",
    title: "AI Suggestions",
    description: "Personalized teammate recommendations, events, and profile tips",
    category: "main",
    defaultColumn: 1,
    defaultOrder: 1,
    defaultPinned: false,
    defaultVisible: true,
    icon: Sparkles,
    component: AISuggestions,
  },
  "quick-actions": {
    id: "quick-actions",
    title: "Quick Actions",
    description: "Fast shortcuts to create projects, publish flares, and find builders",
    category: "main",
    defaultColumn: 1,
    defaultOrder: 2,
    defaultPinned: false,
    defaultVisible: true,
    icon: Zap,
    component: QuickActions,
  },
  "recent-activity": {
    id: "recent-activity",
    title: "Recent Activity",
    description: "Timeline of comments, team invites, and flare publications",
    category: "main",
    defaultColumn: 1,
    defaultOrder: 3,
    defaultPinned: false,
    defaultVisible: true,
    icon: Activity,
    component: RecentActivity,
  },
  "upcoming": {
    id: "upcoming",
    title: "Upcoming Deadlines & Meetups",
    description: "Hackathons, meetups, and project deadlines calendar",
    category: "main",
    defaultColumn: 1,
    defaultOrder: 4,
    defaultPinned: false,
    defaultVisible: true,
    icon: Calendar,
    component: Upcoming,
  },
  "notifications": {
    id: "notifications",
    title: "Notifications",
    description: "Recent alerts, team updates, and discussion pings",
    category: "sidebar",
    defaultColumn: 2,
    defaultOrder: 5,
    defaultPinned: false,
    defaultVisible: true,
    icon: Bell,
    component: NotificationsWidget,
  },
  "upcoming-events": {
    id: "upcoming-events",
    title: "Upcoming Events",
    description: "Scheduled community events and hackathons",
    category: "sidebar",
    defaultColumn: 2,
    defaultOrder: 6,
    defaultPinned: false,
    defaultVisible: true,
    icon: CalendarDays,
    component: UpcomingEventsWidget,
  },
  "upgrade-plan": {
    id: "upgrade-plan",
    title: "Upgrade Plan",
    description: "Premium features and productivity boosts",
    category: "sidebar",
    defaultColumn: 2,
    defaultOrder: 7,
    defaultPinned: false,
    defaultVisible: true,
    icon: Rocket,
    component: UpgradePlanCTA,
  },
};

export const DEFAULT_WIDGET_LAYOUTS: DashboardWidgetLayout[] = Object.values(WIDGET_REGISTRY).map(
  (w) => ({
    id: w.id,
    order: w.defaultOrder,
    pinned: w.defaultPinned,
    visible: w.defaultVisible,
    column: w.defaultColumn,
  }),
);

const LOCAL_STORAGE_KEY = "devlink_dashboard_layout_v1";

export function loadStoredLayout(): DashboardWidgetLayout[] {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) return DEFAULT_WIDGET_LAYOUTS;
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || parsed.length === 0) return DEFAULT_WIDGET_LAYOUTS;

    // Merge with default registry to ensure any new widgets exist
    const map = new Map(parsed.map((item) => [item.id, item]));
    const merged: DashboardWidgetLayout[] = [];

    // Add existing in saved order
    parsed.forEach((item) => {
      if (WIDGET_REGISTRY[item.id]) {
        merged.push({
          id: item.id,
          order: item.order ?? 0,
          pinned: Boolean(item.pinned),
          visible: item.visible !== false,
          column: item.column || WIDGET_REGISTRY[item.id].defaultColumn,
        });
      }
    });

    // Append any newly registered widgets not in storage
    Object.values(WIDGET_REGISTRY).forEach((w) => {
      if (!map.has(w.id)) {
        merged.push({
          id: w.id,
          order: merged.length,
          pinned: w.defaultPinned,
          visible: w.defaultVisible,
          column: w.defaultColumn,
        });
      }
    });

    return merged;
  } catch {
    return DEFAULT_WIDGET_LAYOUTS;
  }
}

export function saveStoredLayout(layouts: DashboardWidgetLayout[]): void {
  try {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(layouts));
  } catch {
    // Ignore storage errors
  }
}

export function clearStoredLayout(): void {
  try {
    localStorage.removeItem(LOCAL_STORAGE_KEY);
  } catch {
    // Ignore storage errors
  }
}
