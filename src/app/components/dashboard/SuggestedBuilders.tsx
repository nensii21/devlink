import React from 'react';
import { BadgeCheck, MapPin, Star, UserPlus, ArrowRight } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { MOCK_BUILDERS, Builder } from '../../data/dashboard-mock';
import { cn } from '../ui/utils';
import { motion } from 'motion/react';

const BuilderCard: React.FC<{ builder: Builder; index: number }> = ({ builder, index }) => (
  <motion.div
    initial={{ opacity: 0, x: 20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: 0.1 + index * 0.1, duration: 0.5 }}
    className="min-w-[340px] max-w-[340px]"
  >
    <Card className="group relative h-full overflow-hidden border-border bg-card rounded-xl shadow-xs transition-all duration-300 hover:border-primary/30 hover:shadow-md">
      <div className="absolute right-0 top-0 h-24 w-24 translate-x-12 -translate-y-12 rounded-full bg-primary/5 blur-3xl group-hover:bg-primary/10 transition-colors" />
      
      <CardContent className="relative p-6">
        <div className="flex items-start justify-between">
          <div className="relative">
            <Avatar className="h-16 w-16 border-2 border-background shadow-md">
              <AvatarImage src={builder.avatar} />
              <AvatarFallback className="bg-primary/5 text-sm font-bold text-primary">
                {builder.name.split(' ').map(n => n[0]).join('')}
              </AvatarFallback>
            </Avatar>
            {builder.isVerified && (
              <div className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-white shadow-sm ring-2 ring-background">
                <BadgeCheck className="h-4 w-4" />
              </div>
            )}
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center gap-1 rounded-full bg-success/5 px-2.5 py-1 text-[11px] font-bold text-success ring-1 ring-success/10">
              <Star className="h-3 w-3 fill-success" />
              {builder.match}%
            </div>
            <div className="rounded-md bg-secondary-bg/50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              {builder.experience} exp
            </div>
          </div>
        </div>

        <div className="mt-5">
          <h4 className="text-[17px] font-bold tracking-tight text-text-primary group-hover:text-primary transition-colors">{builder.name}</h4>
          <p className="text-sm font-medium text-text-secondary opacity-80">{builder.role}</p>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {builder.skills.slice(0, 3).map(skill => (
            <span key={skill} className="rounded-lg bg-secondary-bg/30 px-2.5 py-1 text-[11px] font-medium text-text-secondary ring-1 ring-border/50">
              {skill}
            </span>
          ))}
        </div>

        <div className="mt-5 flex items-center gap-1.5 text-text-muted">
          <MapPin className="h-4 w-4 opacity-60" />
          <span className="text-[13px] font-medium tracking-tight">{builder.location}</span>
        </div>

        <div className="mt-7 flex gap-2.5">
          <Button className="flex-1 rounded-lg bg-primary h-11 text-[13px] font-bold text-white shadow-sm hover:bg-primary-hover active:scale-95 transition-all">
            <UserPlus className="mr-2 h-4 w-4" />
            Connect
          </Button>
          <Button variant="ghost" className="flex-1 rounded-lg border border-border h-11 text-[13px] font-bold text-text-primary hover:bg-secondary-bg active:scale-95 transition-all">
            Profile
          </Button>
        </div>
      </CardContent>
    </Card>
  </motion.div>
);

export const SuggestedBuilders: React.FC = () => {
  return (
    <section className="flex flex-col gap-6 antialiased">
      <div className="flex items-center justify-between px-2">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/5 text-primary">
            <Star className="h-4 w-4" />
          </div>
          <h3 className="text-lg font-bold tracking-tight text-text-primary">Suggested Builders</h3>
        </div>
        <Button variant="ghost" className="h-8 gap-1.5 rounded-lg px-2 text-[11px] font-bold uppercase tracking-widest text-primary hover:bg-primary/5">
          See All
          <ArrowRight className="h-3 w-3" />
        </Button>
      </div>
      <div className="flex gap-6 overflow-x-auto pb-6 scrollbar-hide -mx-2 px-2">
        {MOCK_BUILDERS.map((builder, i) => (
          <BuilderCard key={builder.id} builder={builder} index={i} />
        ))}
      </div>
    </section>
  );
};
