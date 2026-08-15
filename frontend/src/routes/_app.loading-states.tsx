import { createFileRoute } from "@tanstack/react-router";
import { LoadingLibraryShowcase } from "@/components/ui/loading/LoadingLibraryShowcase";

export const Route = createFileRoute("/_app/loading-states")({
  component: LoadingStatesPage,
});

function LoadingStatesPage() {
  return (
    <div className="w-full">
      <LoadingLibraryShowcase />
    </div>
  );
}
