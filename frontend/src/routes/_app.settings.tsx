import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/shared/primitives";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { currentUser } from "@/mocks/seed";

const tabs = ["Account", "Appearance", "Notifications", "Security", "Billing"] as const;
type Tab = (typeof tabs)[number];

export const Route = createFileRoute("/_app/settings")({
  head: () => ({
    meta: [
      { title: "Settings — DevLink" },
      {
        name: "description",
        content: "Manage your DevLink account, appearance, notifications and billing.",
      },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const [tab, setTab] = useState<Tab>("Account");
  const inp =
    "w-full rounded-md border border-border bg-surface px-3 py-[8px] text-[14px] text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20";
  const lbl = "mb-1 block text-[13px] font-semibold text-foreground";

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-[22px] font-bold tracking-tight text-foreground">Settings</h1>
        <p className="text-[13px] text-muted-foreground">Manage your workspace.</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-[220px_minmax(0,1fr)]">
        <Card className="p-2">
          <nav>
            {tabs.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={cn(
                  "flex w-full items-center rounded-md px-3 py-2 text-[13px] font-medium transition-colors",
                  tab === t ? "bg-primary-soft text-primary" : "text-foreground/80 hover:bg-muted",
                )}
              >
                {t}
              </button>
            ))}
          </nav>
        </Card>

        <Card className="p-6">
          <p className="text-[15px] font-semibold text-foreground">{tab}</p>
          <div className="mt-4 space-y-4">
            {tab === "Account" && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  toast.success("Saved");
                }}
                className="space-y-4"
              >
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className={lbl}>Full name</label>
                    <input className={inp} defaultValue={currentUser.name} />
                  </div>
                  <div>
                    <label className={lbl}>Username</label>
                    <input className={inp} defaultValue={currentUser.handle} />
                  </div>
                </div>
                <div>
                  <label className={lbl}>Email</label>
                  <input className={inp} defaultValue="nancy@devlink.io" />
                </div>
                <div>
                  <label className={lbl}>Bio</label>
                  <textarea
                    rows={3}
                    className={inp}
                    defaultValue="Product engineer. React / Postgres / Rust."
                  />
                </div>
                <button className="rounded-md bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90">
                  Save changes
                </button>
              </form>
            )}
            {tab === "Appearance" && (
              <div className="space-y-3 text-[13px] text-foreground">
                <p>
                  Theme: <span className="font-semibold">Light</span> (matches your auth screen).
                </p>
                <p className="text-muted-foreground">Dark mode coming soon.</p>
              </div>
            )}
            {tab === "Notifications" && (
              <div className="space-y-3 text-[13px] text-foreground">
                {[
                  "Direct messages",
                  "Builder requests",
                  "Project mentions",
                  "Hackathon deadlines",
                ].map((n) => (
                  <label
                    key={n}
                    className="flex items-center justify-between border-b border-border pb-3"
                  >
                    <span>{n}</span>
                    <input type="checkbox" defaultChecked className="h-4 w-4 accent-primary" />
                  </label>
                ))}
              </div>
            )}
            {tab === "Security" && (
              <div className="space-y-4">
                <div>
                  <label className={lbl}>Current password</label>
                  <input type="password" className={inp} />
                </div>
                <div>
                  <label className={lbl}>New password</label>
                  <input type="password" className={inp} />
                </div>
                <button className="rounded-md bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90">
                  Update password
                </button>
              </div>
            )}
            {tab === "Billing" && (
              <div className="rounded-md border border-primary/30 bg-primary-soft p-4 text-[13px] text-foreground">
                You're on the <span className="font-semibold">Pro</span> plan. Next invoice on Nov
                4, 2026.
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
