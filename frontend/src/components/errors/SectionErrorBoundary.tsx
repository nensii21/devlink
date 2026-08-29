import React, { Component, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { reportLovableError } from "@/lib/lovable-error-reporting";
import { TypoSection, TypoCaption } from "@/components/shared/Typography";

export interface SectionErrorBoundaryProps {
  children: ReactNode;
  sectionName?: string;
  fallback?: ReactNode;
  onRetry?: () => void;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface SectionErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  showDetails: boolean;
}

export class SectionErrorBoundary extends Component<
  SectionErrorBoundaryProps,
  SectionErrorBoundaryState
> {
  public state: SectionErrorBoundaryState = {
    hasError: false,
    error: null,
    errorInfo: null,
    showDetails: false,
  };

  public static getDerivedStateFromError(error: Error): Partial<SectionErrorBoundaryState> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    this.setState({ errorInfo });

    // Execute custom onError callback if passed
    this.props.onError?.(error, errorInfo);

    // Log to reporting service
    const sectionName = this.props.sectionName || "section";
    console.error(`[SectionErrorBoundary:${sectionName}]`, error, errorInfo);
    reportLovableError(error, {
      boundary: `SectionErrorBoundary_${sectionName}`,
      componentStack: errorInfo.componentStack,
    });
  }

  public handleReset = (): void => {
    this.props.onRetry?.();
    this.setState({ hasError: false, error: null, errorInfo: null, showDetails: false });
  };

  public toggleDetails = (): void => {
    this.setState((prev) => ({ showDetails: !prev.showDetails }));
  };

  public render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const sectionName = this.props.sectionName || "Section";
      const { error, errorInfo, showDetails } = this.state;

      return (
        <div className="my-4 rounded-xl border border-destructive/30 bg-destructive/5 p-6 shadow-2xs transition-all">
          <div className="flex items-start gap-4">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-destructive/10 text-destructive">
              <AlertTriangle size={20} />
            </div>

            <div className="min-w-0 flex-1">
 feature/account-deactivation-1306
              <h3 className="text-[15px] font-semibold tracking-tight text-foreground">
                Something went wrong in {sectionName}
              </h3>
              <p className="mt-1 text-[13px] text-muted-foreground leading-relaxed">

              <TypoSection as="h3" className="text-[15px] font-semibold tracking-tight text-foreground">
                Something went wrong in {sectionName}
              </TypoSection>
              <TypoCaption as="p" className="mt-1 text-[13px] text-muted-foreground leading-relaxed">
 main
                An unexpected error occurred while loading this part of the application. You can try
                reloading this section or refreshing the page.
              </TypoCaption>

              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={this.handleReset}
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-1.5 text-[12.5px] font-semibold text-primary-foreground transition-opacity hover:opacity-90 active:scale-95 cursor-pointer shadow-2xs"
                >
                  <RefreshCw size={14} /> Try again
                </button>

                {error && (
                  <button
                    type="button"
                    onClick={this.toggleDetails}
                    className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-3 py-1.5 text-[12px] font-medium text-foreground transition-colors hover:bg-muted cursor-pointer"
                  >
                    {showDetails ? "Hide error details" : "Show error details"}
                  </button>
                )}
              </div>

              {showDetails && error && (
                <div className="mt-4 rounded-lg border border-border/80 bg-surface p-3 font-mono text-[11px] text-destructive overflow-x-auto">
                  <p className="font-semibold">
                    {error.name}: {error.message}
                  </p>
                  {errorInfo?.componentStack && (
                    <pre className="mt-2 text-muted-foreground whitespace-pre-wrap">
                      {errorInfo.componentStack}
                    </pre>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
