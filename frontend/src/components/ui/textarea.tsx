import * as React from "react";
import { cn } from "@/lib/utils";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, id, disabled, required, ...props }, ref) => {
    const generatedId = React.useId();
    const textareaId = id || (label ? `textarea-${generatedId}` : undefined);
    const errorId = error ? `error-${generatedId}` : undefined;
    const helperId = helperText ? `helper-${generatedId}` : undefined;

    const textareaNode = (
      <textarea
        id={textareaId}
        disabled={disabled}
        required={required}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : helperText ? helperId : undefined}
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-input bg-surface px-3 py-2 text-sm shadow-xs transition-colors",
          "placeholder:text-muted-foreground",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-primary",
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted/50",
          error && "border-destructive focus-visible:ring-destructive/30 focus-visible:border-destructive text-destructive",
          className,
        )}
        ref={ref}
        {...props}
      />
    );

    if (!label && !error && !helperText) {
      return textareaNode;
    }

    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="text-xs font-semibold text-foreground flex items-center gap-1 select-none"
          >
            {label}
            {required && <span className="text-destructive">*</span>}
          </label>
        )}
        {textareaNode}
        {error && (
          <p id={errorId} className="text-xs text-destructive font-medium animate-in fade-in-50">
            {error}
          </p>
        )}
        {!error && helperText && (
          <p id={helperId} className="text-xs text-muted-foreground">
            {helperText}
          </p>
        )}
      </div>
    );
  },
);
Textarea.displayName = "Textarea";

export { Textarea };
