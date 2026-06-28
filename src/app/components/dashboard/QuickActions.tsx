import React from 'react';
import { PlusCircle, Search, MessageSquarePlus, Flame, ArrowRight } from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '../ui/utils';

interface ActionButtonProps {
  icon: React.ElementType;
  label: string;
  description: string;
}

const ActionButton: React.FC<ActionButtonProps> = ({ icon: Icon, label, description }) => (
  <motion.button
    whileHover={{ x: 4 }}
    whileTap={{ scale: 0.98 }}
    className="group relative flex w-full items-center gap-4 rounded-xl border border-border bg-card p-4 transition-all duration-300 hover:border-primary/40 hover:shadow-md active:bg-secondary-bg/50"
  >
    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-secondary-bg text-icons transition-all duration-300 group-hover:bg-primary group-hover:text-white">
      <Icon className="h-5 w-5" />
    </div>
    <div className="flex flex-1 flex-col items-start text-left overflow-hidden">
      <span className="text-[14px] font-bold tracking-tight text-text-primary group-hover:text-primary transition-colors">{label}</span>
      <span className="truncate text-xs font-medium text-text-muted opacity-70 group-hover:opacity-100 transition-opacity">{description}</span>
    </div>
    <ArrowRight className="h-3.5 w-3.5 text-icons opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0 group-hover:text-primary" />
  </motion.button>
);

export const QuickActions: React.FC = () => {
  return (
    <section className="flex flex-col gap-4 antialiased">
      <div className="flex items-center gap-2 px-2">
        <h3 className="text-[11px] font-bold uppercase tracking-widest text-text-muted">Quick Actions</h3>
      </div>
      <div className="flex flex-col gap-3">
        <ActionButton 
          icon={PlusCircle} 
          label="Post Project" 
          description="Start a new collaboration" 
        />
        <ActionButton 
          icon={Search} 
          label="Discover Builders" 
          description="Find your perfect teammate" 
        />
        <ActionButton 
          icon={Flame} 
          label="Create Flare" 
          description="Announce your availability" 
        />
        <ActionButton 
          icon={MessageSquarePlus} 
          label="Send Message" 
          description="Reach out to builders" 
        />
      </div>
    </section>
  );
};
