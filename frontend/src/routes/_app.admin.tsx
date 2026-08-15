import { TypoCaption, TypoHeading } from "@/components/shared/Typography";
import { Outlet, createFileRoute, Link } from "@tanstack/react-router";

const tabActiveProps = {
  className:
    "border-b-2 border-primary font-semibold text-foreground px-4 py-2 text-sm whitespace-nowrap",
};

const tabInactiveProps = {
  className:
    "text-muted-foreground px-4 py-2 hover:text-foreground transition-colors text-sm whitespace-nowrap",
};

/**
 * Every admin sub-route, in the order they appear in the tab strip.
 *
 * Kept as data rather than as repeated JSX because the strip had already
 * drifted: pages were added under /admin without a matching tab, so the only
 * way to reach them was to type the URL.
 */
const ADMIN_TABS = [
  { to: "/admin/audit-logs", label: "Audit Logs" },
  { to: "/admin/notifications", label: "Notification Delivery" },
  { to: "/admin/jobs", label: "Background Jobs" },
  { to: "/admin/maintenance", label: "Maintenance Mode" },
  { to: "/admin/search-analytics", label: "Search Analytics" },
  { to: "/admin/community-stats", label: "Community Stats" },
  { to: "/admin/api-request-analytics", label: "API Request Analytics" },
] as const;

export const Route = createFileRoute("/_app/admin")({
  beforeLoad: () => {
    // Access to this section is still enforced server-side only. Once the
    // frontend carries the signed-in user's roles in route context, the
    // super-admin check belongs here so we stop rendering an empty console to
    // people who will only get 403s from every panel inside it.
  },
  component: AdminLayout,
});

function AdminLayout() {
  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto p-4 md:p-8">
      <div className="flex flex-col gap-2">
        <TypoHeading as="h1">Admin Console</TypoHeading>
        <TypoCaption as="p">Manage your platform and view audit logs.</TypoCaption>

        <div className="flex gap-4 border-b pb-2 mt-4">
          <a href="/admin/audit-logs" className="text-blue-600 hover:underline">
            Audit Logs
          </a>
          <a href="/admin/notifications" className="text-blue-600 hover:underline">
            Notifications
          </a>
          <a href="/admin/maintenance" className="text-blue-600 hover:underline">
            Maintenance Mode
          </a>
          <a href="/admin/search-analytics" className="text-blue-600 hover:underline">
            Search Analytics
          </a>
          <a href="/admin/community-stats" className="text-blue-600 hover:underline">
            Community Stats
          </a>
          <a href="/admin/email-templates" className="text-blue-600 hover:underline">
            Email Templates
          </a>
          <a href="/admin/api-request-analytics" className="text-blue-600 hover:underline">
            API Request Analytics
          </a>
        </div>
        <TypoCaption as="p">
          Manage your platform, view audit logs, and monitor background tasks.
        </TypoCaption>
      </div>

      <div className="flex border-b border-border gap-2 md:gap-4 overflow-x-auto scrollbar-none">
        <Link
          to="/admin/audit-logs"
          activeProps={{
            className:
              "border-b-2 border-primary font-semibold text-foreground px-4 py-2 text-sm whitespace-nowrap",
          }}
          inactiveProps={{
            className:
              "text-muted-foreground px-4 py-2 hover:text-foreground transition-colors text-sm whitespace-nowrap",
          }}
        >
          Audit Logs
        </Link>
        <Link
          to="/admin/notifications"
          activeProps={{
            className:
              "border-b-2 border-primary font-semibold text-foreground px-4 py-2 text-sm whitespace-nowrap",
          }}
          inactiveProps={{
            className:
              "text-muted-foreground px-4 py-2 hover:text-foreground transition-colors text-sm whitespace-nowrap",
          }}
        >
          Notification Delivery
        </Link>
        <Link
          to="/admin/jobs"
          activeProps={{
            className:
              "border-b-2 border-primary font-semibold text-foreground px-4 py-2 text-sm whitespace-nowrap",
          }}
          inactiveProps={{
            className:
              "text-muted-foreground px-4 py-2 hover:text-foreground transition-colors text-sm whitespace-nowrap",
          }}
        >
          Background Jobs
        </Link>
        {ADMIN_TABS.map((tab) => (
          <Link
            key={tab.to}
            to={tab.to}
            activeProps={tabActiveProps}
            inactiveProps={tabInactiveProps}
          >
            {tab.label}
          </Link>
        ))}
      </div>

      <Outlet />
    </div>
  );
}
