import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/organizations")({
  component: OrganizationsLayout,
});

function OrganizationsLayout() {
  return <Outlet />;
}
