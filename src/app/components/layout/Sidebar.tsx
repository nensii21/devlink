import React from 'react';
import { 
  LayoutDashboard, 
  Briefcase, 
  Flame, 
  Users, 
  MessageSquare, 
  User, 
  Settings, 
  LogOut 
} from 'lucide-react';
import { motion } from 'motion/react';
import { DevLinkLogo } from '../DevLinkLogo';
import { cn } from '../ui/utils';
import { Button } from '../ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';

interface SidebarItemProps {
  icon: React.ElementType;
  label: string;
  isActive?: boolean;
  onClick?: () => void;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ icon: Icon, label, isActive, onClick }) => (
  <button
    onClick={onClick}
    className={cn(
      "group relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
      isActive 
        ? "bg-blue-50/50 text-primary" 
        : "text-text-secondary hover:bg-secondary-bg hover:text-text-primary"
    )}
  >
    {isActive && (
      <motion.div
        layoutId="active-nav"
        className="absolute left-0 h-5 w-1 rounded-r-full bg-primary"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
      />
    )}
    <Icon className={cn("h-[18px] w-[18px] shrink-0 transition-colors", isActive ? "text-primary" : "text-icons group-hover:text-text-primary")} />
    <span>{label}</span>
  </button>
);

export const Sidebar: React.FC<{ onLogout?: () => void }> = ({ onLogout }) => {
  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-[280px] border-r border-border bg-background flex flex-col antialiased">
      {/* Header / Logo */}
      <div className="flex h-20 items-center px-6">
        <DevLinkLogo size={32} />
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-4 py-6">
        <SidebarItem icon={LayoutDashboard} label="Dashboard" isActive />
        <SidebarItem icon={Briefcase} label="Projects" />
        <SidebarItem icon={Flame} label="Builder's Flare" />
        <SidebarItem icon={Users} label="Builders" />
        <SidebarItem icon={MessageSquare} label="Messages" />
        <SidebarItem icon={User} label="Profile" />
        <SidebarItem icon={Settings} label="Settings" />
      </nav>

      {/* User Profile / Logout */}
      <div className="mt-auto border-t border-border p-5">
        <div className="flex items-center gap-3.5 rounded-xl bg-secondary-bg p-2.5">
          <Avatar className="h-10 w-10 border border-border shadow-xs">
            <AvatarImage src="https://i.pravatar.cc/150?u=radhesh" />
            <AvatarFallback className="bg-primary/5 text-xs font-bold text-primary">RK</AvatarFallback>
          </Avatar>
          <div className="flex-1 overflow-hidden">
            <p className="truncate text-sm font-bold text-text-primary">Radhesh Kumar</p>
            <p className="truncate text-[10px] font-bold text-text-muted uppercase tracking-wider opacity-70">@radhesh</p>
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onLogout}
            className="h-8 w-8 text-icons hover:bg-destructive/5 hover:text-destructive transition-colors"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
};
