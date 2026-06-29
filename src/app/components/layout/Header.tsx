import React from "react";
import { Search, Bell, MessageSquare, User, Command } from "lucide-react";
import { getDailyQuote } from "../../utils/quotes";

import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Badge } from "../ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";

export const Header: React.FC = () => {
  const quote = getDailyQuote();

  return (
    <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-gray-200 bg-white/95 px-8 backdrop-blur-md">
      {/* Left */}
      <div className="flex flex-col">
        <h1 className="text-2xl font-bold text-gray-900">
          Good Morning, Nensi
        </h1>

        <p className="mt-1 max-w-md truncate text-sm text-gray-500">
          {quote}
        </p>
      </div>

      {/* Search */}
      <div className="mx-10 flex flex-1 justify-center">
        <div className="relative w-full max-w-xl">
          <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />

          <Input
            placeholder="Search projects, builders, tools..."
            className="h-12 rounded-xl border-gray-200 bg-white pl-11 pr-14 shadow-sm focus-visible:border-cyan-500 focus-visible:ring-4 focus-visible:ring-cyan-100"
          />

          <div className="absolute right-3 top-1/2 flex -translate-y-1/2 items-center gap-1 rounded-md border border-gray-200 bg-gray-50 px-2 py-1">
            <Command className="h-3.5 w-3.5 text-gray-500" />
            <span className="text-[11px] font-semibold text-gray-500">
              K
            </span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <TooltipProvider>
        <div className="flex items-center gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="relative h-11 w-11 rounded-xl hover:bg-gray-100"
              >
                <Bell className="h-5 w-5 text-gray-600" />

                <Badge className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-cyan-500 p-0 text-[10px] font-bold text-white">
                  3
                </Badge>
              </Button>
            </TooltipTrigger>

            <TooltipContent>
              Notifications
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-11 w-11 rounded-xl hover:bg-gray-100"
              >
                <MessageSquare className="h-5 w-5 text-gray-600" />
              </Button>
            </TooltipTrigger>

            <TooltipContent>
              Messages
            </TooltipContent>
          </Tooltip>

          <div className="mx-2 h-6 w-px bg-gray-200" />

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-11 w-11 rounded-xl hover:bg-gray-100"
              >
                <User className="h-5 w-5 text-gray-600" />
              </Button>
            </TooltipTrigger>

            <TooltipContent>
              Profile
            </TooltipContent>
          </Tooltip>
        </div>
      </TooltipProvider>
    </header>
  );
};