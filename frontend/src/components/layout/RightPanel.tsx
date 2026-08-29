import { Sparkles, Calendar, Activity } from "lucide-react";
import { TypoSection, TypoCaption } from "@/components/shared/Typography";

export function RightPanel() {
  return (
    <aside
      className="h-screen hidden xl:flex flex-col border-l border-border bg-surface w-[300px] overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
      aria-label="Activity panel"
    >
      <div className="p-5 flex flex-col gap-6">
        {/* AI Suggestions */}
        <section>
          <TypoSection as="h3" className="text-[13px] font-semibold tracking-tight text-muted-foreground uppercase mb-3 flex items-center gap-1.5">
            <Sparkles size={14} className="text-primary" /> AI Suggestions
          </TypoSection>
          <div className="rounded-xl border border-primary/20 bg-primary-soft p-4">
            <p className="text-[13px] text-foreground mb-3 font-medium">
              You have 3 profile matches for your latest project!
            </p>
            <button className="w-full rounded-md bg-primary py-1.5 text-[12px] font-semibold text-primary-foreground transition-opacity hover:opacity-90">
              View Matches
            </button>
          </div>
        </section>

        {/* Upcoming Events */}
        <section>
          <TypoSection as="h3" className="text-[13px] font-semibold tracking-tight text-muted-foreground uppercase mb-3 flex items-center gap-1.5">
            <Calendar size={14} /> Upcoming Events
          </TypoSection>
          <div className="space-y-3">
            <div className="rounded-xl border border-border bg-card p-3 hover:border-primary/40 transition-colors cursor-pointer">
              <p className="text-[13px] font-medium text-foreground">Web3 Hackathon</p>
              <TypoCaption as="p" className="text-[11px] text-muted-foreground mt-1">Tomorrow, 10:00 AM</TypoCaption>
            </div>
            <div className="rounded-xl border border-border bg-card p-3 hover:border-primary/40 transition-colors cursor-pointer">
              <p className="text-[13px] font-medium text-foreground">React Meetup</p>
              <TypoCaption as="p" className="text-[11px] text-muted-foreground mt-1">Fri, 4:00 PM</TypoCaption>
            </div>
          </div>
        </section>

        {/* Recent Activity */}
        <section>
          <TypoSection as="h3" className="text-[13px] font-semibold tracking-tight text-muted-foreground uppercase mb-3 flex items-center gap-1.5">
            <Activity size={14} /> Recent Activity
          </TypoSection>
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="h-2 w-2 mt-1.5 rounded-full bg-primary shrink-0" />
              <div>
                <p className="text-[13px] text-foreground">
                  You starred <strong>devlink-ui</strong>
                </p>
                <TypoCaption as="p" className="text-[11px] text-muted-foreground">2 hours ago</TypoCaption>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="h-2 w-2 mt-1.5 rounded-full bg-muted-foreground shrink-0" />
              <div>
                <p className="text-[13px] text-foreground">
                  <strong>Alex</strong> commented on your flare
                </p>
                <TypoCaption as="p" className="text-[11px] text-muted-foreground">5 hours ago</TypoCaption>
              </div>
            </div>
          </div>
        </section>
      </div>
    </aside>
  );
}
