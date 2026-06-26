import React from 'react';
import { 
  UserPlus, 
  RefreshCw, 
  Flame, 
  Clock, 
  CheckCircle2, 
  MessageSquare, 
  Link, 
  Sparkles 
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { MOCK_ACTIVITIES, ActivityItem } from '../../data/dashboard-mock';
import { cn } from '../ui/utils';
import { motion } from 'motion/react';

const ICON_MAP = {
  joining: UserPlus,
  update: RefreshCw,
  invite: CheckCircle2,
  connection: Link,
  flare_expire: Flame,
  message: MessageSquare,
};

const ActivityRow: React.FC<{ item: ActivityItem; isLast: boolean; index: number }> = ({ item, isLast, index }) => {
  const Icon = ICON_MAP[item.type] || Sparkles;
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 + index * 0.05 }}
      className="group relative flex gap-5 pb-7"
    >
      {!isLast && (
        <span className="absolute left-[19px] top-10 h-[calc(100%-24px)] w-[1.5px] bg-border/60 group-hover:bg-primary/20 transition-colors" />
      )}
      <div className={cn(
        "relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-border bg-background shadow-xs transition-all duration-300 group-hover:border-primary/30 group-hover:shadow-sm active:scale-95",
        item.status === 'success' && "text-success",
        item.status === 'warning' && "text-warning",
        item.status === 'error' && "text-destructive",
        item.status === 'info' && "text-primary"
      )}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex flex-1 flex-col gap-0.5 pt-1">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-bold text-text-primary group-hover:text-primary transition-colors tracking-tight">{item.title}</p>
          <span className="text-[11px] font-medium text-text-muted opacity-60 uppercase tracking-tight">{item.time}</span>
        </div>
        <p className="text-[13px] font-medium leading-relaxed text-text-secondary line-clamp-2">{item.description}</p>
      </div>
    </motion.div>
  );
};

export const RecentActivity: React.FC = () => {
  return (
    <Card className="flex h-[450px] flex-col overflow-hidden border-border bg-card rounded-xl shadow-xs transition-all hover:shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between border-b border-border/40 bg-secondary-bg/5 px-6 py-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/5 text-primary">
            <Clock className="h-4 w-4" />
          </div>
          <CardTitle className="text-base font-bold text-text-primary tracking-tight">Recent Activity</CardTitle>
        </div>
        <Button variant="ghost" size="sm" className="h-8 rounded-lg px-3 text-[11px] font-bold uppercase tracking-widest text-primary hover:bg-primary/5">
          View All
        </Button>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-6 scrollbar-hide">
        <div className="flex flex-col">
          {MOCK_ACTIVITIES.map((activity, index) => (
            <ActivityRow 
              key={activity.id} 
              item={activity} 
              index={index}
              isLast={index === MOCK_ACTIVITIES.length - 1} 
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
