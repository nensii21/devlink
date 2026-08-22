import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
  useRouterState,
} from "@tanstack/react-router";
import { AnimatePresence } from "framer-motion";
import { useEffect, useRef, type ReactNode } from "react";
import { Toaster, toast } from "sonner";
import { ThemeProvider } from "@/context/ThemeContext";
import { I18nProvider } from "@/context/I18nContext";
import { OfflineBanner } from "@/components/OfflineBanner";
import { AnnouncerProvider } from "@/components/a11y/Announcer";
import { SkipLink } from "@/components/a11y/SkipLink";
import { applyServiceWorkerUpdate, registerServiceWorker } from "@/lib/pwa";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";
import { ApiError } from "@/api/client";

import { UnauthorizedPage } from "@/components/errors/UnauthorizedPage";
import { ForbiddenPage } from "@/components/errors/ForbiddenPage";
import { ServerErrorPage } from "@/components/errors/ServerErrorPage";
import { OfflinePage } from "@/components/errors/OfflinePage";
import { NetworkErrorPage } from "@/components/errors/NetworkErrorPage";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

function NotFoundComponent() {
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
    <div className="flex min-h-screen w-full items-center justify-center bg-background px-4">
      <div className="w-full max-w-md text-center">
        <div
          ref={ref}
          className="mx-auto w-48 h-48 sm:w-56 sm:h-56 md:w-64 md:h-64 bg-background [&_svg]:bg-transparent"
        />

        <TypoHeading as="h1">Page not found</TypoHeading>
        <TypoCaption as="p">
          The page you're looking for doesn't exist or has been moved to a new address.
        </TypoCaption>
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

/**
 * The root route's errorComponent and notFoundComponent replace RootComponent
 * rather than rendering inside it, so anything they show sits outside the
 * providers. The error pages call useTranslation(), so they need their own
 * I18nProvider — without it an API 401 would surface as a provider error
 * instead of the sign-in page.
 */
function OutsideRootProviders({ children }: { children: ReactNode }) {
  return <I18nProvider>{children}</I18nProvider>;
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  if (error instanceof ApiError) {
    if (error.status === 401) {
      return (
        <OutsideRootProviders>
          <UnauthorizedPage />
        </OutsideRootProviders>
      );
    }

    if (error.status === 403) {
      return (
        <OutsideRootProviders>
          <ForbiddenPage />
        </OutsideRootProviders>
      );
    }

    if (error.status >= 500) {
      return (
        <OutsideRootProviders>
          <ServerErrorPage />
        </OutsideRootProviders>
      );
    }

    // status 0  -> fetch/network failure (coreFetch's catch block)
    // status 408 -> request aborted/timed out (coreFetch's AbortError branch)
    // Both are network-class failures from the user's perspective.
    if (error.status === 0 || error.status === 408) {
      // navigator is undefined during SSR; assume online in that case so we
      // don't render OfflinePage on the server for a purely client-side signal.
      const isOnline = typeof navigator === "undefined" ? true : navigator.onLine;
      return (
        <OutsideRootProviders>
          {isOnline ? <NetworkErrorPage /> : <OfflinePage />}
        </OutsideRootProviders>
      );
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <TypoHeading as="h1">This page didn't load</TypoHeading>
        <TypoCaption as="p">
          Something went wrong. You can try refreshing or head back home.
        </TypoCaption>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              // router.invalidate() returns a Promise; explicitly discard it
              // rather than leaving a floating unhandled promise.
              void router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
          >
            Try again
          </button>
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md border border-border bg-surface px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "DevLink — Where builders connect, collaborate and ship" },
      {
        name: "description",
        content:
          "DevLink is a developer collaboration platform: find teammates with AI matching, run projects, chat in real time, and enter hackathons together.",
      },
      { name: "author", content: "DevLink" },
      { property: "og:title", content: "DevLink — Where builders connect" },
      {
        property: "og:description",
        content: "Find teammates, run projects, and ship together.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      // Colours the browser/OS chrome when installed, and matches the
      // manifest's theme_color.
      { name: "theme-color", content: "#05b7d7" },
      { name: "apple-mobile-web-app-capable", content: "yes" },
      { name: "apple-mobile-web-app-title", content: "DevLink" },
      {
        name: "apple-mobile-web-app-status-bar-style",
        content: "black-translucent",
      },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "manifest", href: "/manifest.webmanifest" },
      { rel: "icon", type: "image/svg+xml", href: "/icons/icon.svg" },
      { rel: "apple-touch-icon", href: "/icons/icon.svg" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  const location = useRouterState({ select: (s) => s.location });

  useEffect(() => {
    // No-ops outside a production browser build; see src/lib/pwa.ts.
    void registerServiceWorker({
      onUpdateAvailable: (registration) => {
        toast("A new version of DevLink is available.", {
          duration: Infinity,
          action: {
            label: "Reload",
            onClick: () => applyServiceWorkerUpdate(registration),
          },
        });
      },
    });
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <AnnouncerProvider>
          <ThemeProvider defaultTheme="system">
            {/* First thing in the tab order, so a keyboard user is not made to
                walk the sidebar and header on every single navigation. */}
            <SkipLink />
            <OfflineBanner />
            <AnimatePresence mode="wait" initial={false}>
              <Outlet key={location.pathname} />
            </AnimatePresence>
            <Toaster position="top-right" richColors />
          </ThemeProvider>
        </AnnouncerProvider>
      </I18nProvider>
    </QueryClientProvider>
  );
}
