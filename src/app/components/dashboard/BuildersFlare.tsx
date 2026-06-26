import React from 'react';
import { Flame, Clock, RefreshCw, Star, UserCheck, ShieldCheck, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Button } from '../ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Badge } from '../ui/badge';
import { MOCK_FLARE_REQUESTS, FlareRequest } from '../../data/dashboard-mock';
import { cn } from '../ui/utils';
import { motion, AnimatePresence } from 'motion/react';

const FlareRequestCard: React.FC<{ request: FlareRequest; index: number }> = ({ request, index }) => (
  <motion.div
    initial={{ opacity: 0, x: 10 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: index * 0.05 }}
  >
    <Card className="group border-border bg-background shadow-xs transition-all duration-300 hover:border-primary/30 hover:shadow-sm">
      <CardContent className="p-4">
        <div className="flex items-start gap-3.5">
          <div className="relative">
            <Avatar className="h-11 w-11 border border-border">
              <AvatarImage src={request.builder.avatar} />
              <AvatarFallback className="bg-primary/5 text-xs font-bold text-primary">
                {request.builder.name[0]}
              </AvatarFallback>
            </Avatar>
            <div className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-success text-white ring-2 ring-background">
              <Star className="h-2.5 w-2.5 fill-white" />
            </div>
          </div>
          <div className="flex-1 overflow-hidden">
            <div className="flex items-center justify-between">
              <h5 className="truncate text-[15px] font-bold tracking-tight text-text-primary group-hover:text-primary transition-colors">{request.builder.name}</h5>
              <Badge variant="outline" className={cn(
                "h-5 rounded-md border-none px-1.5 text-[10px] font-bold uppercase tracking-tight ring-1 ring-inset",
                parseInt(request.expiresIn) < 10 ? "text-warning bg-warning/10 ring-warning/30" : "text-primary bg-primary/10 ring-primary/30"
              )}>
                <Clock className="mr-1 h-3 w-3" />
                {request.expiresIn}
              </Badge>
            </div>
            <p className="truncate text-xs font-medium text-text-secondary opacity-80">{request.builder.role}</p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-1.5">
          {request.builder.skills.slice(0, 3).map(skill => (
            <span key={skill} className="rounded-md bg-secondary-bg/50 px-2 py-0.5 text-[10px] font-medium text-text-muted ring-1 ring-border/30">
              {skill}
            </span>
          ))}
        </div>

        <div className="mt-5 flex gap-2">
          <Button className="h-9 flex-1 rounded-lg bg-primary text-[11px] font-bold text-white hover:bg-primary-hover active:scale-95 transition-all">
            Accept
          </Button>
          <Button variant="ghost" className="h-9 flex-1 rounded-lg border border-border text-[11px] font-bold text-text-primary hover:bg-secondary-bg active:scale-95 transition-all">
            Profile
          </Button>
        </div>
      </CardContent>
    </Card>
  </motion.div>
);

export const BuildersFlare: React.FC = () => {
  return (
    <Card className="flex h-full flex-col border-border bg-card rounded-xl shadow-xs transition-all hover:shadow-sm">
      <CardHeader className="space-y-1 px-6 pt-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/5 text-primary">
            <Flame className="h-5 w-5" />
          </div>
          <CardTitle className="text-lg font-bold tracking-tight text-text-primary">Builder's Flare</CardTitle>
        </div>
        <CardDescription className="text-xs font-medium leading-relaxed text-text-muted opacity-80">
          Collaboration requests that expire after 14 days. Re-flare to renew.
        </CardDescription>
      </CardHeader>
      
      <CardContent className="px-6 pb-6 pt-2">
        <Tabs defaultValue="joining" className="w-full">
          <TabsList className="grid h-10 w-full grid-cols-2 rounded-lg bg-secondary-bg/50 p-1">
            <TabsTrigger value="joining" className="rounded-md text-[11px] font-bold uppercase tracking-wider transition-all data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-xs">
              Joining
            </TabsTrigger>
            <TabsTrigger value="invite" className="rounded-md text-[11px] font-bold uppercase tracking-wider transition-all data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-xs">
              Invite
            </TabsTrigger>
          </TabsList>
          
          <div className="mt-6">
            <AnimatePresence mode="wait">
              <TabsContent value="joining" className="m-0 focus-visible:outline-none">
                <div className="space-y-4">
                  {MOCK_FLARE_REQUESTS.filter(r => r.type === 'joining').map((request, i) => (
                    <FlareRequestCard key={request.id} request={request} index={i} />
                  ))}
                  <Button variant="ghost" className="h-14 w-full flex-col gap-0.5 border-2 border-dashed border-border rounded-xl bg-transparent px-4 py-2 text-text-muted transition-all hover:border-primary/40 hover:bg-primary/5 hover:text-primary">
                    <div className="flex items-center gap-2">
                      <RefreshCw className="h-3.5 w-3.5" />
                      <span className="text-[11px] font-bold uppercase tracking-wider">Re-Flare Expired</span>
                    </div>
                    <span className="text-[10px] font-medium opacity-60 text-center">Renew your previous collaboration requests</span>
                  </Button>
                </div>
              </TabsContent>
              
              <TabsContent value="invite" className="m-0 focus-visible:outline-none">
                <div className="space-y-4">
                  {MOCK_FLARE_REQUESTS.filter(r => r.type === 'invite').map((request, i) => (
                    <FlareRequestCard key={request.id} request={request} index={i} />
                  ))}
                </div>
              </TabsContent>
            </AnimatePresence>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  );
};
