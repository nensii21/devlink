import { Card } from "@/components/shared/primitives";
import {
  Folder,
  Mail,
  MessageCircle,
  Share2,
  Users2,
  TrendingUp,
  TrendingDown,
  Minus,
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
};

const primaryStats = stats.slice(0, 5);

// Mock trends for the dashboard
const trends = [
  { value: 12, positive: true },
  { value: 4, positive: true },
  { value: 0, positive: null },
  { value: 2, positive: false },
  { value: 8, positive: true },
];

export function StatsRow() {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      {primaryStats.map((s, i) => {
        const Icon = iconMap[s.icon] ?? Folder;
        const trend = trends[i];
        return (
          <motion.div
            key={s.key}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03, duration: 0.2 }}
            className="h-full"
          >
            <Card
              interactive
className="flex flex-col h-full gap-3 p-4 transition-all duration-200 hover:border-border hover:shadow-md"            >
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground p-1.5 rounded-lg bg-muted/30">
                  <Icon size={16} />
                </span>
                <span
                  className={cn(
                    "flex items-center gap-1 text-[11px] font-semibold tracking-wider",
                    trend.positive === true
                      ? "text-success"
                      : trend.positive === false
                        ? "text-destructive"
                        : "text-muted-foreground",
                  )}
                >
                  {trend.positive === true && <TrendingUp size={12} />}
                  {trend.positive === false && <TrendingDown size={12} />}
                  {trend.positive === null && <Minus size={12} />}
                  {trend.value}%
                </span>
              </div>
              <div className="mt-1">
                <p className="text-xl sm:text-2xl font-semibold tracking-tight text-foreground">
                  {s.value}
                </p>
                <p className="mt-0.5 text-xs font-medium text-muted-foreground">{s.label}</p>
              </div>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
