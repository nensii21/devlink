import * as React from "react";
import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { TypoHeading, TypoCaption } from "@/components/shared/Typography";

export interface StatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  icon: React.ComponentType<{ size?: number; className?: string }> | React.ReactNode;
  value: string | number;
  label: string;
  trend?: string;
  trendType?: "positive" | "negative" | "neutral";
  description?: string;
  iconColor?: string;
  bgColor?: string;
  interactive?: boolean;
}

export function StatCard({
  icon: Icon,
  value,
  label,
  trend,
  trendType = "neutral",
  description,
  iconColor = "text-primary",
  bgColor = "bg-primary-soft",
  interactive = false,
  className,
  ...props
}: StatCardProps) {
  const isComponent = typeof Icon === "function" || (typeof Icon === "object" && Icon !== null && "render" in (Icon as object));
  const IconComp = isComponent ? (Icon as React.ComponentType<{ size?: number; className?: string }>) : null;

  return (
    <Card
      variant={interactive ? "interactive" : "default"}
      className={cn("flex flex-col h-full gap-3.5 p-5 bg-card shadow-xs", className)}
      {...props}
    >
      <div className="flex items-center gap-4">
        {/* Left: Icon container */}
        <div
          className={cn(
            "flex items-center justify-center h-12 w-12 rounded-xl shrink-0 transition-transform",
            bgColor,
            iconColor,
          )}
        >
          {IconComp ? <IconComp size={20} /> : (Icon as React.ReactNode)}
        </div>

        {/* Right: Value & Label */}
        <div className="min-w-0 flex-1">
          <TypoHeading as="p" className="text-2xl font-bold tracking-tight text-foreground leading-none">
            {value}
          </TypoHeading>
          <TypoCaption as="p" className="text-xs text-muted-foreground mt-1 truncate">
            {label}
          </TypoCaption>
        </div>
      </div>

      {/* Optional description */}
      {description && (
        <TypoCaption as="p" className="text-xs text-muted-foreground leading-relaxed">
          {description}
        </TypoCaption>
      )}

      {/* Bottom: Trend indicator */}
      {trend && (
        <div className="flex items-center gap-1.5 pt-2 border-t border-border/40 mt-auto">
          <TypoCaption
            as="span"
            className={cn(
              "inline-flex items-center text-[11px] font-semibold gap-0.5",
              trendType === "positive" && "text-success",
              trendType === "negative" && "text-destructive",
              trendType === "neutral" && "text-muted-foreground",
            )}
          >
            {trendType === "positive" && <ArrowUpRight size={13} className="shrink-0" />}
            {trendType === "negative" && <ArrowDownRight size={13} className="shrink-0" />}
            {trendType === "neutral" && <Minus size={13} className="shrink-0" />}
            {trend}
          </TypoCaption>
        </div>
      )}
    </Card>
  );
}
