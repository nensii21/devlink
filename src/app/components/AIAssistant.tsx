import React from 'react';
import { Sparkles } from 'lucide-react';
import { motion } from 'motion/react';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from './ui/tooltip';

export const AIAssistant: React.FC = () => {
  return (
    <div className="fixed bottom-8 right-8 z-50">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <motion.button
              whileHover={{ scale: 1.1, rotate: 5 }}
              whileTap={{ scale: 0.9 }}
              className="group relative flex h-14 w-14 items-center justify-center rounded-full border border-border bg-background shadow-xl text-primary transition-all hover:border-primary/40 hover:shadow-primary/10"
            >
              <Sparkles className="h-6 w-6" />
              <div className="absolute -right-0.5 -top-0.5 h-3.5 w-3.5 rounded-full bg-primary border-2 border-background shadow-sm" />
              <div className="absolute -right-0.5 -top-0.5 h-3.5 w-3.5 rounded-full bg-primary animate-ping opacity-20" />
            </motion.button>
          </TooltipTrigger>
          <TooltipContent side="left" sideOffset={12} className="rounded-xl border-border bg-card px-4 py-2 shadow-lg">
            <p className="text-[13px] font-black tracking-tight text-text-primary">DevLink AI Assistant</p>
            <p className="text-[11px] font-bold text-text-muted opacity-80">Ready to help you build.</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
};
