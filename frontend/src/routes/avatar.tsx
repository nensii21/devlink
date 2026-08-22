import React from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { UserAvatar, type UserAvatarSize, type OnlineStatus } from "@/components/user-avatar";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

export const Route = createFileRoute("/avatar")({
  head: () => ({
    meta: [
      { title: "Avatar Component — DevLink" },
      {
        name: "description",
        content:
          "Reusable, accessible Avatar component with image and initials fallbacks, online status indicator, verification badge, and multiple sizes.",
      },
      { property: "og:title", content: "Avatar Component — DevLink" },
      {
        property: "og:description",
        content:
          "Reusable Avatar with fallback, presence indicator, verification badge, and size variants.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: AvatarDemo,
});

// ---------------------------------------------------------------------------
// Demo helpers
// ---------------------------------------------------------------------------

const SIZES: UserAvatarSize[] = ["xs", "sm", "md", "lg", "xl", "2xl"];

const STATUSES: OnlineStatus[] = ["online", "away", "busy", "offline"];

const STATUS_LABEL: Record<OnlineStatus, string> = {
  online: "Online",
  away: "Away",
  busy: "Busy",
  offline: "Offline",
};

const DEMO_IMG =
  "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=256&h=256&fit=crop&auto=format";

const SAMPLE_USERS = [
  { name: "Ada Lovelace", src: DEMO_IMG },
  { name: "Grace Hopper", src: undefined },
  { name: "Linus Torvalds", src: undefined },
  { name: "Margaret Hamilton", src: undefined },
  { name: "Dennis Ritchie", src: undefined },
];

// ---------------------------------------------------------------------------
// Section wrapper
// ---------------------------------------------------------------------------

function Section({
  id,
  title,
  description,
  children,
}: {
  id: string;
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section
      id={id}
      aria-labelledby={`${id}-heading`}
      className="rounded-xl border border-border bg-card p-6 shadow-card"
    >
      <h2 id={`${id}-heading`} className="text-lg font-semibold text-card-foreground">
        {title}
      </h2>
      {description ? <TypoCaption as="p">{description}</TypoCaption> : null}
      <div className="mt-6 flex flex-wrap items-end gap-6">{children}</div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

function AvatarDemo() {
  return (
    <main className="min-h-dvh bg-background px-4 py-10 sm:px-8">
      <div className="mx-auto flex max-w-4xl flex-col gap-8">
        {/* Back nav */}
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft size={14} />
          Back to home
        </Link>

        {/* Page header */}
        <header>
          <TypoHeading as="h1">Avatar</TypoHeading>
          <TypoCaption as="p">
            A reusable, accessible avatar component with image fallback, initials, online presence
            indicator, verification badge, and six size presets.
          </TypoCaption>
        </header>

        {/* ── Section: Sizes ───────────────────────────────────────────── */}
        <Section
          id="sizes"
          title="Sizes"
          description="Six preset sizes: xs · sm · md · lg · xl · 2xl"
        >
          {SIZES.map((size) => (
            <div key={size} className="flex flex-col items-center gap-2">
              <UserAvatar src={DEMO_IMG} name="Ada Lovelace" size={size} />
              <TypoCaption>{size}</TypoCaption>
            </div>
          ))}
        </Section>

        {/* ── Section: Initials fallback ───────────────────────────────── */}
        <Section
          id="initials"
          title="Initials fallback"
          description="Shown when no image is provided or the image fails to load."
        >
          {[
            { name: "Ada Lovelace" },
            { name: "Grace Hopper" },
            { name: "Linus" },
            { name: "Margaret Hamilton" },
            { name: undefined, initials: "?" },
          ].map((u, i) => (
            <div key={i} className="flex flex-col items-center gap-2">
              <UserAvatar
                name={u.name}
                initials={u.initials}
                size="lg"
                id={`initials-avatar-${i}`}
              />
              <TypoCaption>{u.name ?? "(no name)"}</TypoCaption>
            </div>
          ))}
        </Section>

        {/* ── Section: Status indicators ──────────────────────────────── */}
        <Section
          id="status"
          title="Online indicator"
          description="Presence dot with four status variants."
        >
          {STATUSES.map((s) => (
            <div key={s} className="flex flex-col items-center gap-2">
              <UserAvatar
                src={s === "online" || s === "offline" ? DEMO_IMG : undefined}
                name={
                  s === "online"
                    ? "Ada Lovelace"
                    : s === "away"
                      ? "Grace Hopper"
                      : s === "busy"
                        ? "Linus Torvalds"
                        : "Ada Lovelace"
                }
                size="lg"
                status={s}
                id={`status-avatar-${s}`}
              />
              <TypoCaption>{STATUS_LABEL[s]}</TypoCaption>
            </div>
          ))}
        </Section>

        {/* ── Section: Verification badge ─────────────────────────────── */}
        <Section
          id="verified"
          title="Verification badge"
          description="Composable with status and size — applies to any variant."
        >
          <UserAvatar src={DEMO_IMG} name="Ada Lovelace" size="lg" verified id="verified-img-lg" />
          <UserAvatar name="Grace Hopper" size="lg" verified id="verified-initials-lg" />
          <UserAvatar
            src={DEMO_IMG}
            name="Ada Lovelace"
            size="xl"
            verified
            status="online"
            id="verified-status-xl"
          />
          <UserAvatar
            name="Margaret Hamilton"
            size="2xl"
            verified
            status="online"
            id="verified-status-2xl"
          />
        </Section>

        {/* ── Section: Stacked group ───────────────────────────────────── */}
        <Section
          id="stacked"
          title="Stacked group"
          description="Common overlapping avatar list pattern — apply ring + negative margin."
        >
          <div className="flex -space-x-3">
            {SAMPLE_USERS.map((u, i) => (
              <UserAvatar
                key={i}
                src={u.src}
                name={u.name}
                size="md"
                className="rounded-full ring-2 ring-background"
                id={`stacked-avatar-${i}`}
              />
            ))}
          </div>

          <div className="flex -space-x-4">
            {SAMPLE_USERS.map((u, i) => (
              <UserAvatar
                key={i}
                src={u.src}
                name={u.name}
                size="lg"
                className="rounded-full ring-2 ring-background"
                id={`stacked-avatar-lg-${i}`}
              />
            ))}
          </div>
        </Section>

        {/* ── Section: Drag & Drop Crop Uploader ────────────────────── */}
        <Section
          id="editable-crop-uploader"
          title="Drag & Drop Crop Uploader (#575)"
          description="Click or hover the editable avatar to test drag-and-drop, real-time preview, interactive crop (zoom/pan/rotate), and upload progress indicator."
        >
          <div className="flex flex-wrap items-center gap-8">
            <div className="flex flex-col items-center gap-2">
              <UserAvatar
                src={DEMO_IMG}
                name="Ada Lovelace"
                size="2xl"
                editable
                status="online"
                verified
                id="editable-avatar-2xl"
              />
              <span className="text-xs font-semibold text-foreground">
                Click to Crop & Upload Avatar
              </span>
            </div>

            <div className="flex flex-col items-center gap-2">
              <UserAvatar
                name="Grace Hopper"
                size="xl"
                editable
                status="away"
                id="editable-avatar-xl"
              />
              <span className="text-xs font-semibold text-foreground">
                Editable Initials Avatar
              </span>
            </div>
          </div>
        </Section>
      </div>
    </main>
  );
}
