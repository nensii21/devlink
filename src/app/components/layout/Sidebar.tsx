import React from "react";
import {
  LayoutDashboard,
  Briefcase,
  Flame,
  Users,
  MessageSquare,
  User,
  Settings,
  LogOut,
} from "lucide-react";
import { motion } from "motion/react";
import { DevLinkLogo } from "../DevLinkLogo";
import { cn } from "../ui/utils";
import { Button } from "../ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar";

interface SidebarItemProps {
  icon: React.ElementType;
  label: string;
  isActive?: boolean;
  onClick?: () => void;
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  icon: Icon,
  label,
  isActive,
  onClick,
}) => (
  <button
    onClick={onClick}
    className={cn(
      "group relative flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-[15px] font-medium transition-all duration-200",

      isActive
        ? "bg-cyan-50 text-cyan-600 shadow-sm"
        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
    )}
  >
    {isActive && (
      <motion.div
        layoutId="active-nav"
        className="absolute left-0 h-8 w-1 rounded-r-full bg-cyan-500"
        transition={{ duration: 0.2 }}
      />
    )}

    <Icon
      className={cn(
        "h-5 w-5 transition-colors",
        isActive
          ? "text-cyan-600"
          : "text-gray-400 group-hover:text-gray-700"
      )}
    />

    <span>{label}</span>
  </button>
);

export const Sidebar: React.FC<{ onLogout?: () => void }> = ({
  onLogout,
}) => {
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-72 flex-col border-r border-gray-200 bg-white shadow-sm">
      {/* Logo */}
      <div className="flex h-24 items-center border-b border-gray-100 px-8">
        <DevLinkLogo size={34} />
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-2 px-5 py-8">
        <SidebarItem
          icon={LayoutDashboard}
          label="Dashboard"
          isActive
        />

        <SidebarItem
          icon={Briefcase}
          label="Projects"
        />

        <SidebarItem
          icon={Flame}
          label="Builder's Flare"
        />

        <SidebarItem
          icon={Users}
          label="Builders"
        />

        <SidebarItem
          icon={MessageSquare}
          label="Messages"
        />

        <SidebarItem
          icon={User}
          label="Profile"
        />

        <SidebarItem
          icon={Settings}
          label="Settings"
        />
      </nav>

      {/* Profile */}
      <div className="border-t border-gray-200 p-6">
        <div className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-gray-50 p-3">
          <Avatar className="h-11 w-11 border border-gray-200">
            <AvatarImage src="https://i.pravatar.cc/150?u=radhesh" />
            <AvatarFallback className="bg-cyan-100 font-semibold text-cyan-700">
              RK
            </AvatarFallback>
          </Avatar>

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-gray-900">
              Radhesh Kumar
            </p>

            <p className="truncate text-xs text-gray-500">
              @radhesh
            </p>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={onLogout}
            className="h-9 w-9 rounded-xl text-gray-400 hover:bg-red-50 hover:text-red-500"
          >
            <LogOut className="h-4 w-4" />
            </Button>
        </div>
      </div>
    </aside>
  );
};