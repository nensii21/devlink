import React from 'react';
import { Search, Bell, MessageSquare, User, Command } from 'lucide-react';
import { getDailyQuote } from '../../utils/quotes';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from '../ui/tooltip';

export const Header: React.FC = () => {
  const quote = getDailyQuote();

  return (
    <header className="sticky top-0 z-30 flex h-20 w-full items-center justify-between border-b border-border bg-background/90 px-8 backdrop-blur-xl antialiased">
      {/* Left: Greeting & Quote */}
      <div className="flex flex-col gap-0.5">
        <h1 className="text-xl font-bold tracking-tight text-text-primary">Good Morning, Radhesh</h1>
        <p className="max-w-[400px] truncate text-xs font-medium text-text-muted">
          <span className="text-primary/60 font-bold mr-1">—</span> {quote}
        </p>
      </div>

      {/* Center: Search */}
      <div className="relative flex w-full max-w-lg items-center px-4">
        <div className="group relative w-full">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-icons transition-colors group-focus-within:text-primary" />
          <Input 
            placeholder="Search projects, builders, tools..." 
            className="h-11 w-full rounded-xl border-border bg-secondary-bg/30 pl-10 pr-12 transition-all focus-visible:bg-background focus-visible:ring-4 focus-visible:ring-primary/5"
          />
          <div className="absolute right-3 top-1/2 flex -translate-y-1/2 items-center gap-1 rounded-md border border-border bg-background px-1.5 py-1 shadow-xs md:flex">
            <Command className="h-3 w-3 text-text-muted" />
            <span className="text-[10px] font-bold text-text-muted tracking-widest leading-none">K</span>
          </div>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        <TooltipProvider>
          <div className="flex items-center gap-1">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="relative h-11 w-11 rounded-xl text-icons hover:bg-secondary-bg hover:text-text-primary transition-all active:scale-95">
                  <Bell className="h-[22px] w-[22px]" />
                  <Badge className="absolute right-2.5 top-2.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary p-0 text-[10px] font-black text-white ring-2 ring-background">
                    3
                  </Badge>
                </Button>
              </TooltipTrigger>
              <TooltipContent>Notifications</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-11 w-11 rounded-xl text-icons hover:bg-secondary-bg hover:text-text-primary transition-all active:scale-95">
                  <MessageSquare className="h-[22px] w-[22px]" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Messages</TooltipContent>
            </Tooltip>

            <div className="mx-2 h-6 w-px bg-border/60" />

            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-11 w-11 rounded-xl text-icons hover:bg-secondary-bg hover:text-text-primary transition-all active:scale-95">
                  <User className="h-[22px] w-[22px]" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Profile</TooltipContent>
            </Tooltip>
          </div>
        </TooltipProvider>
      </div>
    </header>
  );
};
