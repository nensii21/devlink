import { createFileRoute, Link } from "@tanstack/react-router";
import Lottie from "lottie-react";
import { AppShell } from "@/components/layout/AppShell";
import searchAnimation from "@/assets/404 Error - Doodle animation.json";

function AppNotFound() {
  return (
    <div className="fixed inset-0 z-50 flex min-h-screen w-full items-center justify-center bg-background px-4">
      <div className="w-full max-w-md text-center">
        <div className="mx-auto w-48 sm:w-56 md:w-64 aspect-square" aria-hidden="true">
          <Lottie animationData={searchAnimation} loop autoplay />
        </div>

        <h1 className="-mt-2 text-2xl font-bold text-foreground sm:text-3xl">
          Page not found
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
          The page you're looking for doesn't exist or has been moved to a new
          address.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            Go to Home
          </Link>
          <button
            type="button"
            onClick={() => window.history.back()}
            className="inline-flex items-center justify-center rounded-md border border-border bg-surface px-5 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            Back to previous page
          </button>
        </div>
      </div>
    </div>
  );
}

export const Route = createFileRoute("/_app")({
  component: AppShell,
  notFoundComponent: AppNotFound,
});
