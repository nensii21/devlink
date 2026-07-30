import { createFileRoute, Link, Outlet } from "@tanstack/react-router";
import { useEffect, useRef } from "react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { SidebarProvider } from "@/context/SidebarContext";
import { ProfileCompletionChecklist } from "@/components/profile/ProfileCompletionChecklist";

const mockUserProfile = {
  avatar: "",
  bio: "Frontend Developer interested in React & Open Source.",
  skills: ["React", "TypeScript", "Tailwind CSS"],
  githubUrl: "https://github.com/mridul",
  portfolioUrl: "",
  experience: "2 yrs",
};

function AppLayoutWithProfileChecklist() {
  return (
    <div className="space-y-4">
      <ProfileCompletionChecklist userProfile={mockUserProfile} />
      <SidebarProvider>
        <DashboardLayout />
      </SidebarProvider>
    </div>
  );
}

function AppNotFound() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    let destroy: (() => void) | undefined;
    Promise.all([import("lottie-web"), import("@/assets/404 Error - Doodle animation.json")]).then(
      ([lottieMod, animMod]) => {
        if (!ref.current) return;
        const anim = lottieMod.default.loadAnimation({
          container: ref.current,
          animationData: animMod.default,
          loop: true,
          autoplay: true,
        });
        destroy = () => anim.destroy();
      },
    );
    return () => destroy?.();
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex min-h-screen w-full items-center justify-center bg-background px-4">
      <div className="w-full max-w-md text-center">
        <div
          ref={ref}
          className="mx-auto w-48 h-48 sm:w-56 sm:h-56 md:w-64 md:h-64 bg-background [&_svg]:bg-transparent"
        />

        <h1 className="mt-6 text-2xl font-bold text-foreground sm:text-3xl">Page not found</h1>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
          The page you're looking for doesn't exist or has been moved to a new address.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-transform hover:opacity-90 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            Go to Home
          </Link>
          <button
            type="button"
            onClick={() => window.history.back()}
            className="inline-flex items-center justify-center rounded-md border border-border bg-surface px-5 py-2.5 text-sm font-medium text-foreground transition-transform hover:bg-muted active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            Back to previous page
          </button>
        </div>
      </div>
    </div>
  );
}

export const Route = createFileRoute("/_app")({
  component: AppLayoutWithProfileChecklist,
  notFoundComponent: AppNotFound,
});
