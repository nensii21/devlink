import React from 'react';
import { Briefcase, Users, MailOpen, Sparkles, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { MOCK_STATS, StatItem } from '../../data/dashboard-mock';
import { motion } from 'motion/react';
import { cn } from '../ui/utils';

const ICON_MAP = {
  Briefcase: Briefcase,
  Users: Users,
  MailOpen: MailOpen,
  Sparkles: Sparkles,
};

const StatCard: React.FC<{ item: StatItem; index: number }> = ({ item, index }) => {
  const Icon = ICON_MAP[item.icon];
  const isPositive = item.trend > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5, ease: "easeOut" }}
      whileHover={{ y: -4 }}
      className="group"
    >
      <Card className="relative h-full overflow-hidden border-border bg-card rounded-xl shadow-xs transition-all duration-300 hover:border-primary/20 hover:shadow-md">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-secondary-bg text-icons transition-colors group-hover:bg-primary/5 group-hover:text-primary">
              <Icon className="h-5 w-5" />
            </div>
            <div className={cn(
              "flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-semibold tracking-tight",
              isPositive ? "text-success bg-success/5" : "text-destructive bg-destructive/5"
            )}>
              {isPositive ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
              {Math.abs(item.trend)}%
            </div>
          </div>
          
          <div className="mt-5">
            <p className="text-[11px] font-bold uppercase tracking-wider text-text-muted opacity-80">{item.title}</p>
            <div className="mt-1 flex items-baseline gap-2">
              <h3 className="text-2xl font-bold tracking-tight text-text-primary">{item.value}</h3>
              <span className="text-[11px] font-medium text-text-muted">{item.trendLabel}</span>
            </div>
          </div>
          
          {/* Subtle Sparkline-ish detail */}
          <div className="mt-6 flex h-1 w-full gap-1 overflow-hidden rounded-full bg-secondary-bg">
            {[...Array(8)].map((_, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, scaleY: 0.5 }}
                animate={{ opacity: 1, scaleY: 1 }}
                transition={{ delay: 0.4 + (index * 0.1) + (i * 0.05) }}
                className={cn(
                  "h-full flex-1 rounded-full transition-colors",
                  i < (isPositive ? 6 : 4) ? "bg-primary/20" : "bg-primary/5"
                )}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export const StatsSection: React.FC = () => {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
      {MOCK_STATS.map((stat, i) => (
        <StatCard key={stat.id} item={stat} index={i} />
      ))}
    </div>
  );
};
