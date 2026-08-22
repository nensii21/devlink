import { TypoSection, TypoCaption } from "@/components/shared/Typography";
import { Sparkles, Calendar, Activity } from "lucide-react";

export function RightPanel() {
  return (
    <aside
      className="h-screen hidden xl:flex flex-col border-l border-border bg-surface w-[300px] overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
      aria-label="Activity panel"
    >
      <div className="p-5 flex flex-col gap-6">
        {/* AI Suggestions */}
        <section>
          <TypoSection>
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
          <TypoSection>
            <Calendar size={14} /> Upcoming Events
          </TypoSection>
          <div className="space-y-3">
            <div className="rounded-xl border border-border bg-card p-3 hover:border-primary/40 transition-colors cursor-pointer">
              <p className="text-[13px] font-medium text-foreground">Web3 Hackathon</p>
              <TypoCaption as="p">Tomorrow, 10:00 AM</TypoCaption>
            </div>
            <div className="rounded-xl border border-border bg-card p-3 hover:border-primary/40 transition-colors cursor-pointer">
              <p className="text-[13px] font-medium text-foreground">React Meetup</p>
              <TypoCaption as="p">Fri, 4:00 PM</TypoCaption>
            </div>
          </div>
        </section>

        {/* Recent Activity */}
        <section>
          <TypoSection>
            <Activity size={14} /> Recent Activity
          </TypoSection>
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="h-2 w-2 mt-1.5 rounded-full bg-primary shrink-0" />
              <div>
                <p className="text-[13px] text-foreground">
                  You starred <strong>devlink-ui</strong>
                </p>
                <TypoCaption as="p">2 hours ago</TypoCaption>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="h-2 w-2 mt-1.5 rounded-full bg-muted-foreground shrink-0" />
              <div>
                <p className="text-[13px] text-foreground">
                  <strong>Alex</strong> commented on your flare
                </p>
                <TypoCaption as="p">5 hours ago</TypoCaption>
              </div>
            </div>
          </div>
        </section>
      </div>
    </aside>
  );
}
