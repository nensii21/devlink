import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  inputSize?: "sm" | "md" | "lg";
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type,
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      inputSize = "md",
      id,
      disabled,
      required,
      ...props
    },
    ref,
  ) => {
    const generatedId = React.useId();
    const inputId = id || (label ? `input-${generatedId}` : undefined);
    const errorId = error ? `error-${generatedId}` : undefined;
    const helperId = helperText ? `helper-${generatedId}` : undefined;

    const sizeClasses = {
      sm: "h-8 px-2.5 text-xs",
      md: "h-9 px-3 py-1.5 text-sm",
      lg: "h-11 px-3.5 text-base",
    }[inputSize];

    const inputNode = (
      <div className="relative flex items-center w-full">
        {leftIcon && (
          <div className="absolute left-3 flex items-center pointer-events-none text-muted-foreground [&_svg]:size-4">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          type={type}
          disabled={disabled}
          required={required}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : helperText ? helperId : undefined}
          className={cn(
            "flex w-full rounded-md border border-input bg-surface text-foreground shadow-xs transition-colors",
            "file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground",
            "placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-primary",
            "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted/50",
            sizeClasses,
            leftIcon && "pl-9",
            rightIcon && "pr-9",
            error && "border-destructive focus-visible:ring-destructive/30 focus-visible:border-destructive text-destructive",
            className,
          )}
          ref={ref}
          {...props}
        />
        {rightIcon && (
          <div className="absolute right-3 flex items-center text-muted-foreground [&_svg]:size-4">
            {rightIcon}
          </div>
        )}
      </div>
    );

    if (!label && !error && !helperText) {
      return inputNode;
    }

    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-semibold text-foreground flex items-center gap-1 select-none"
          >
            {label}
            {required && <span className="text-destructive">*</span>}
          </label>
        )}
        {inputNode}
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

Input.displayName = "Input";

export { Input };
