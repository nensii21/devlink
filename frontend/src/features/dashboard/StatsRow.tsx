import { Card } from "@/components/shared/primitives";
import { Folder, Mail, MessageCircle, Share2, Users2, type LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import { stats } from "@/mocks/seed";
import { cn } from "@/lib/utils";

const iconMap: Record<string, LucideIcon> = {
  folder: Folder,
  users: Users2,
  message: MessageCircle,
  mail: Mail,
  share: Share2,
};

const tintClass: Record<string, string> = {
  info: "bg-blue-500/10 text-blue-500",
  primary: "bg-cyan-500/10 text-cyan-500",
  warning: "bg-amber-500/10 text-amber-500",
  success: "bg-emerald-500/10 text-emerald-500",
};

// Render the 5 primary metrics matching the dashboard screenshot
const primaryStats = stats.slice(0, 5);

export function StatsRow() {
  return (
    <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 lg:grid-cols-5">
      {primaryStats.map((s, i) => {
        const Icon = iconMap[s.icon] ?? Folder;
        return (
          <motion.div
            key={s.key}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03, duration: 0.25, ease: "easeOut" }}
            whileHover={{ y: -2 }}
          >
            <Card
              interactive
              className="flex items-center gap-3.5 rounded-2xl p-4 transition-all duration-200 hover:border-primary/40 hover:shadow-card"
            >
              <span
                className={cn(
                  "grid h-11 w-11 shrink-0 place-items-center rounded-xl font-bold transition-transform duration-200",
                  tintClass[s.tint] ?? tintClass.primary,
                )}
              >
                <Icon size={20} />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-xl font-extrabold tracking-tight text-foreground leading-none">
                  {s.value}
                </p>
                <p className="mt-1 truncate text-[11px] font-bold tracking-wider text-muted-foreground uppercase leading-none">
                  {s.label}
                </p>
              </div>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
