import * as React from "react";
import { cn } from "../../lib/utils";
import { Ghost } from "lucide-react";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({
  className,
  icon,
  title,
  description,
  action,
  ...props
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[400px] flex-col items-center justify-center rounded-md border border-dashed p-8 text-center animate-in fade-in-50",
        className,
      )}
      {...props}
    >
      <div className="mx-auto flex max-w-[420px] flex-col items-center justify-center text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
          {icon || <Ghost className="h-10 w-10 text-muted-foreground" />}
        </div>
        <TypoHeading as="h2">{title}</TypoHeading>
        {description && <TypoCaption as="p">{description}</TypoCaption>}
        {action}
      </div>
    </div>
  );
}
