import { Card } from "@/components/shared/primitives";
import {
  Activity as ActivityIcon,
  Eye,
  Folder,
  Github,
  Mail,
  MessageCircle,
  Share2,
  Sparkles,
  Trophy,
  Users2,
  type LucideIcon,
} from "lucide-react";
import { motion } from "framer-motion";
import { stats } from "@/mocks/seed";
import { cn } from "@/lib/utils";

const iconMap: Record<string, LucideIcon> = {
  folder: Folder,
  users: Users2,
  message: MessageCircle,
  mail: Mail,
  share: Share2,
  eye: Eye,
  activity: ActivityIcon,
  github: Github,
  trophy: Trophy,
  sparkles: Sparkles,
};

const tintClass: Record<string, string> = {
  primary: "bg-primary-soft text-primary",
  info: "bg-info/10 text-info",
  warning: "bg-warning/10 text-warning",
  success: "bg-success/10 text-success",
  foreground: "bg-muted text-foreground",
};

export function StatsRow() {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5 xl:grid-cols-10">
      {stats.map((s, i) => {
        const Icon = iconMap[s.icon] ?? Folder;
        return (
          <motion.div
            key={s.key}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03, duration: 0.25, ease: "easeOut" }}
          >
            <Card interactive className="flex flex-col items-center gap-2 p-3 text-center">
              <span
                className={cn(
                  "grid h-9 w-9 place-items-center rounded-md",
                  tintClass[s.tint] ?? tintClass.primary,
                )}
              >
                <Icon size={16} />
              </span>
              <p className="text-[18px] font-bold leading-tight text-foreground">{s.value}</p>
              <p className="text-[11px] font-medium leading-tight text-muted-foreground">
                {s.label}
              </p>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
