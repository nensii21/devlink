import React, { useState, useEffect } from "react";
import { Quote, Star, ChevronLeft, ChevronRight, MessageSquareQuote } from "lucide-react";
import { cn } from "@/lib/utils";
import { TypoHeading, TypoCaption, TypoCard } from "@/components/shared/Typography";
import { UserAvatar } from "@/components/user-avatar";

export interface Testimonial {
  id: string;
  name: string;
  role: string;
  company?: string;
  avatar?: string;
  quote: string;
  rating?: number;
  badge?: string;
}

export const DEFAULT_TESTIMONIALS: Testimonial[] = [
  {
    id: "1",
    name: "Sarah Chen",
    role: "Senior Full Stack Engineer",
    company: "OpenSource Lab",
    avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80",
    quote:
      "DevLink matched me with two incredible co-builders for a weekend Web3 hackathon. We shipped our MVP in 48 hours and took first place!",
    rating: 5,
    badge: "Hackathon Winner",
  },
  {
    id: "2",
    name: "Marcus Vance",
    role: "Core Contributor & Maintainer",
    company: "DevKit OSS",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
    quote:
      "Finding dependable collaborators used to take weeks of discord spam. DevLink's skill matching pinpointed engineers with exactly the stack we needed.",
    rating: 5,
    badge: "OSS Maintainer",
  },
  {
    id: "3",
    name: "Elena Rostova",
    role: "AI & ML Researcher",
    company: "DataMind AI",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
    quote:
      "The real-time project workspaces and skill-based scoring made joining remote teams seamless. I found my current startup co-founder here!",
    rating: 5,
    badge: "Startup Founder",
  },
  {
    id: "4",
    name: "David Kalu",
    role: "Backend Architect",
    company: "CloudScale",
    avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
    quote:
      "DevLink's automated portfolio generation and repository insights helped me highlight my contributions and land my dream freelance contract.",
    rating: 5,
    badge: "Top Builder",
  },
  {
    id: "5",
    name: "Aisha Patel",
    role: "Frontend Specialist",
    company: "UI Dynamics",
    avatar: "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80",
    quote:
      "The intuitive UI and accessible component architecture make team onboarding effortless. Best developer community platform I've used.",
    rating: 5,
    badge: "Active Contributor",
  },
];

export interface TestimonialsSectionProps {
  testimonials?: Testimonial[];
  title?: string;
  subtitle?: string;
  className?: string;
}

export function TestimonialsSection({
  testimonials = DEFAULT_TESTIMONIALS,
  title = "Loved by developers & contributors",
  subtitle = "See how builders use DevLink to find teammates, launch side projects, and win hackathons.",
  className,
}: TestimonialsSectionProps) {
  const [activeIndex, setActiveIndex] = useState(0);

  const nextTestimonial = () => {
    setActiveIndex((prev) => (prev + 1) % testimonials.length);
  };

  const prevTestimonial = () => {
    setActiveIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
  };

  // Auto-advance carousel every 6 seconds (pauses on interaction)
  useEffect(() => {
    if (testimonials.length <= 1) return;
    const timer = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % testimonials.length);
    }, 6000);
    return () => clearInterval(timer);
  }, [testimonials.length]);

  return (
    <section
      id="testimonials"
      aria-label="Developer Testimonials"
      className={cn(
        "border-b border-border py-20 bg-gradient-to-b from-background via-surface/20 to-background relative overflow-hidden",
        className
      )}
    >
      {/* Background ambient glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-primary/5 rounded-full blur-[100px] pointer-events-none" />

      <div className="mx-auto max-w-6xl px-4 sm:px-6 relative z-10">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-14">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-primary-soft px-3.5 py-1 text-xs font-semibold text-primary mb-3">
            <MessageSquareQuote size={14} /> Developer Stories
          </div>
          <TypoHeading as="h2">{title}</TypoHeading>
          <TypoCaption as="p" className="mt-2 text-sm sm:text-base">
            {subtitle}
          </TypoCaption>
        </div>

        {/* Desktop / Responsive Grid View */}
        <div className="hidden md:grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-10">
          {testimonials.slice(0, 3).map((item) => (
            <div
              key={item.id}
              className="group relative flex flex-col justify-between rounded-2xl border border-border bg-card p-6 shadow-xs hover:border-primary/40 hover:shadow-md transition-all duration-300"
            >
              <div>
                {/* Rating & Badge */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-1 text-amber-400">
                    {Array.from({ length: item.rating || 5 }).map((_, i) => (
                      <Star key={i} size={14} className="fill-current" />
                    ))}
                  </div>
                  {item.badge && (
                    <span className="rounded-full bg-surface px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground border border-border/60">
                      {item.badge}
                    </span>
                  )}
                </div>

                {/* Quote */}
                <Quote size={24} className="text-primary/20 mb-2 group-hover:text-primary/40 transition-colors" />
                <p className="text-[13.5px] leading-relaxed text-foreground/90 font-normal italic">
                  "{item.quote}"
                </p>
              </div>

              {/* User Profile */}
              <div className="mt-6 pt-4 border-t border-border/50 flex items-center gap-3">
                <UserAvatar
                  src={item.avatar}
                  name={item.name}
                  size="md"
                  className="ring-2 ring-primary/20"
                />
                <div className="min-w-0 flex-1">
                  <TypoCard className="text-sm font-semibold truncate text-foreground">
                    {item.name}
                  </TypoCard>
                  <TypoCaption className="text-xs truncate block">
                    {item.role} {item.company ? `• ${item.company}` : ""}
                  </TypoCaption>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Mobile / Accessible Interactive Carousel Component */}
        <div className="relative max-w-2xl mx-auto md:hidden">
          <div
            role="region"
            aria-roledescription="carousel"
            aria-label="Developer testimonials carousel"
            className="overflow-hidden"
          >
            {testimonials.map((item, index) => {
              if (index !== activeIndex) return null;
              return (
                <div
                  key={item.id}
                  role="group"
                  aria-roledescription="slide"
                  aria-label={`${index + 1} of ${testimonials.length}`}
                  className="rounded-2xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between transition-all duration-300"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-1 text-amber-400">
                        {Array.from({ length: item.rating || 5 }).map((_, i) => (
                          <Star key={i} size={14} className="fill-current" />
                        ))}
                      </div>
                      {item.badge && (
                        <span className="rounded-full bg-surface px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground border border-border/60">
                          {item.badge}
                        </span>
                      )}
                    </div>

                    <Quote size={24} className="text-primary/30 mb-2" />
                    <p className="text-sm leading-relaxed text-foreground font-normal italic">
                      "{item.quote}"
                    </p>
                  </div>

                  <div className="mt-6 pt-4 border-t border-border/50 flex items-center gap-3">
                    <UserAvatar
                      src={item.avatar}
                      name={item.name}
                      size="md"
                      className="ring-2 ring-primary/20"
                    />
                    <div className="min-w-0 flex-1">
                      <TypoCard className="text-sm font-semibold truncate text-foreground">
                        {item.name}
                      </TypoCard>
                      <TypoCaption className="text-xs truncate block">
                        {item.role} {item.company ? `• ${item.company}` : ""}
                      </TypoCaption>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Accessible Carousel Navigation Controls */}
          <div className="flex items-center justify-between mt-6 px-2">
            <button
              type="button"
              onClick={prevTestimonial}
              aria-label="Previous testimonial"
              className="grid h-9 w-9 place-items-center rounded-full border border-border bg-surface text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <ChevronLeft size={18} />
            </button>

            {/* Dots indicators */}
            <div className="flex items-center gap-1.5" aria-label="Testimonial slides">
              {testimonials.map((_, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setActiveIndex(i)}
                  aria-label={`Go to testimonial ${i + 1}`}
                  aria-current={i === activeIndex ? "true" : undefined}
                  className={cn(
                    "h-2 rounded-full transition-all duration-300",
                    i === activeIndex ? "w-6 bg-primary" : "w-2 bg-muted-foreground/30 hover:bg-muted-foreground/50"
                  )}
                />
              ))}
            </div>

            <button
              type="button"
              onClick={nextTestimonial}
              aria-label="Next testimonial"
              className="grid h-9 w-9 place-items-center rounded-full border border-border bg-surface text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

export default TestimonialsSection;
