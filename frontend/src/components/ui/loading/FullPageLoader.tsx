import React from "react";
import { Spinner } from "./Spinner";

export interface FullPageLoaderProps {
  message?: string;
}

export const FullPageLoader: React.FC<FullPageLoaderProps> = ({
  message = "Loading DevLink application...",
}) => {
  return (
    <div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-950/90 backdrop-blur-md text-slate-100 space-y-4"
      role="status"
      aria-busy="true"
      aria-label={message}
    >
      <Spinner size="xl" color="cyan" />
      <p className="text-sm font-semibold tracking-wide text-slate-300 animate-pulse">{message}</p>
    </div>
  );
};
