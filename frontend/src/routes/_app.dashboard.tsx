import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { GreetingHero } from "@/features/dashboard/GreetingHero";
import { StatsRow } from "@/features/dashboard/StatsRow";
import {
  WIDGET_REGISTRY,
  DEFAULT_WIDGET_LAYOUTS,
  loadStoredLayout,
  saveStoredLayout,
  clearStoredLayout,
  type WidgetDefinition,
} from "@/features/dashboard/dashboardWidgets";
import { DashboardWidgetWrapper } from "@/features/dashboard/DashboardWidgetWrapper";
import { CustomizeDashboardToolbar } from "@/features/dashboard/CustomizeDashboardToolbar";
import { WidgetConfigModal } from "@/features/dashboard/WidgetConfigModal";
import { dashboardLayoutApi, type DashboardWidgetLayout } from "@/api/modules/dashboardLayout";
import { Pin, EyeOff, LayoutGrid } from "lucide-react";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — DevLink" },
      {
        name: "description",
        content: "Your customizable DevLink command center: projects, matches, messages and streaks.",
      },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const queryClient = useQueryClient();

  // 1. Load layout from storage & backend
  const [layouts, setLayouts] = useState<DashboardWidgetLayout[]>(() => loadStoredLayout());
  const [isCustomizing, setIsCustomizing] = useState(false);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);

  // Drag state
  const [draggedWidgetId, setDraggedWidgetId] = useState<string | null>(null);
  const [dragOverWidgetId, setDragOverWidgetId] = useState<string | null>(null);

  // Query backend saved layout
  const { data: backendLayout } = useQuery({
    queryKey: ["dashboard-layout"],
    queryFn: async () => {
      try {
        const res = await dashboardLayoutApi.getLayout();
        return res;
      } catch {
        return null;
      }
    },
  });

  // Sync backend layout if customized
  useEffect(() => {
    if (backendLayout?.is_customized && backendLayout.widgets.length > 0) {
      setLayouts(backendLayout.widgets);
      saveStoredLayout(backendLayout.widgets);
    }
  }, [backendLayout]);

  // Mutation to save layout
  const saveMutation = useMutation({
    mutationFn: async (updated: DashboardWidgetLayout[]) => {
      saveStoredLayout(updated);
      await dashboardLayoutApi.updateLayout(updated);
      return updated;
    },
    onSuccess: (saved) => {
      toast.success("Dashboard layout saved!");
      queryClient.invalidateQueries({ queryKey: ["dashboard-layout"] });
      setIsCustomizing(false);
    },
    onError: () => {
      // Still saved to localStorage
      toast.success("Dashboard layout saved locally!");
      setIsCustomizing(false);
    },
  });

  // Mutation to reset layout
  const resetMutation = useMutation({
    mutationFn: async () => {
      clearStoredLayout();
      await dashboardLayoutApi.resetLayout();
      return DEFAULT_WIDGET_LAYOUTS;
    },
    onSuccess: () => {
      setLayouts(DEFAULT_WIDGET_LAYOUTS);
      toast.info("Dashboard layout reset to default.");
      queryClient.invalidateQueries({ queryKey: ["dashboard-layout"] });
    },
    onError: () => {
      setLayouts(DEFAULT_WIDGET_LAYOUTS);
      clearStoredLayout();
      toast.info("Dashboard layout reset to default.");
    },
  });

  // Derived sections
  const { pinnedWidgets, mainWidgets, sidebarWidgets, hiddenCount } = useMemo(() => {
    const layoutMap = new Map(layouts.map((l) => [l.id, l]));

    const pinned: Array<{ def: WidgetDefinition; layout: DashboardWidgetLayout }> = [];
    const main: Array<{ def: WidgetDefinition; layout: DashboardWidgetLayout }> = [];
    const sidebar: Array<{ def: WidgetDefinition; layout: DashboardWidgetLayout }> = [];
    let hidden = 0;

    // Sort by order
    const sortedLayouts = [...layouts].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

    sortedLayouts.forEach((l) => {
      const def = WIDGET_REGISTRY[l.id];
      if (!def) return;

      if (!l.visible) {
        hidden++;
        return;
      }

      if (l.pinned) {
        pinned.push({ def, layout: l });
      } else if (l.column === 2 || def.category === "sidebar") {
        sidebar.push({ def, layout: l });
      } else {
        main.push({ def, layout: l });
      }
    });

    return {
      pinnedWidgets: pinned,
      mainWidgets: main,
      sidebarWidgets: sidebar,
      hiddenCount: hidden,
    };
  }, [layouts]);

  // Actions
  const handlePinToggle = (id: string) => {
    setLayouts((prev) => {
      const next = prev.map((item) =>
        item.id === id ? { ...item, pinned: !item.pinned } : item,
      );
      saveStoredLayout(next);
      return next;
    });
    const widget = WIDGET_REGISTRY[id];
    const isNowPinned = !layouts.find((l) => l.id === id)?.pinned;
    toast.info(isNowPinned ? `Pinned ${widget?.title ?? "widget"}` : `Unpinned ${widget?.title ?? "widget"}`);
  };

  const handleHideWidget = (id: string) => {
    setLayouts((prev) => {
      const next = prev.map((item) =>
        item.id === id ? { ...item, visible: false } : item,
      );
      saveStoredLayout(next);
      return next;
    });
    const widget = WIDGET_REGISTRY[id];
    toast.info(`Hidden ${widget?.title ?? "widget"}. Restore from Customize menu.`);
  };

  const handleToggleVisibility = (id: string) => {
    setLayouts((prev) => {
      const next = prev.map((item) =>
        item.id === id ? { ...item, visible: !item.visible } : item,
      );
      saveStoredLayout(next);
      return next;
    });
  };

  const handleMoveWidget = (id: string, direction: "up" | "down") => {
    setLayouts((prev) => {
      const index = prev.findIndex((l) => l.id === id);
      if (index === -1) return prev;
      const targetIndex = direction === "up" ? index - 1 : index + 1;
      if (targetIndex < 0 || targetIndex >= prev.length) return prev;

      const next = [...prev];
      const temp = next[index];
      next[index] = next[targetIndex];
      next[targetIndex] = temp;

      // Reassign order
      const reordered = next.map((item, i) => ({ ...item, order: i }));
      saveStoredLayout(reordered);
      return reordered;
    });
  };

  // Drag & Drop handlers
  const handleDragStart = (e: React.DragEvent, id: string) => {
    setDraggedWidgetId(id);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", id);
  };

  const handleDragOver = (e: React.DragEvent, id: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (dragOverWidgetId !== id) {
      setDragOverWidgetId(id);
    }
  };

  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (!draggedWidgetId || draggedWidgetId === targetId) {
      setDraggedWidgetId(null);
      setDragOverWidgetId(null);
      return;
    }

    setLayouts((prev) => {
      const sourceIndex = prev.findIndex((l) => l.id === draggedWidgetId);
      const targetIndex = prev.findIndex((l) => l.id === targetId);
      if (sourceIndex === -1 || targetIndex === -1) return prev;

      const next = [...prev];
      const [movedItem] = next.splice(sourceIndex, 1);
      next.splice(targetIndex, 0, movedItem);

      const reordered = next.map((item, i) => ({ ...item, order: i }));
      saveStoredLayout(reordered);
      return reordered;
    });

    setDraggedWidgetId(null);
    setDragOverWidgetId(null);
  };

  const handleDragEnd = () => {
    setDraggedWidgetId(null);
    setDragOverWidgetId(null);
  };

  return (
    <div className="mx-auto flex max-w-[1536px] w-full flex-col gap-6 pb-12 pt-4 px-4 sm:px-6">
      {/* Top Banner / Customizer Bar */}
      <CustomizeDashboardToolbar
        isCustomizing={isCustomizing}
        isSaving={saveMutation.isPending}
        hiddenCount={hiddenCount}
        onToggleCustomizing={() => setIsCustomizing((prev) => !prev)}
        onOpenAddModal={() => setIsConfigModalOpen(true)}
        onResetLayout={() => resetMutation.mutate()}
        onSaveLayout={() => saveMutation.mutate(layouts)}
      />

      {/* Greeting Hero */}
      <GreetingHero />

      {/* Stats Row */}
      <StatsRow />

      {/* PINNED WIDGETS SECTION */}
      {pinnedWidgets.length > 0 && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary">
            <Pin size={13} className="fill-current" />
            Pinned Widgets
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {pinnedWidgets.map(({ def, layout }, index) => (
              <DashboardWidgetWrapper
                key={def.id}
                widget={def}
                isCustomizing={isCustomizing}
                isPinned={true}
                canMoveUp={index > 0}
                canMoveDown={index < pinnedWidgets.length - 1}
                onPinToggle={handlePinToggle}
                onHide={handleHideWidget}
                onMoveUp={(id) => handleMoveWidget(id, "up")}
                onMoveDown={(id) => handleMoveWidget(id, "down")}
                onDragStart={handleDragStart}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onDragEnd={handleDragEnd}
                isDragging={draggedWidgetId === def.id}
                isDragOver={dragOverWidgetId === def.id}
              />
            ))}
          </div>
        </div>
      )}

      {/* MAIN & SIDEBAR GRID */}
      <div className="grid gap-6 lg:grid-cols-12 items-start">
        {/* Main Column - 9 cols (or 12 if sidebar is empty) */}
        <div
          className={sidebarWidgets.length > 0 ? "lg:col-span-9 flex flex-col gap-6" : "lg:col-span-12 flex flex-col gap-6"}
        >
          {mainWidgets.length === 0 && !isCustomizing ? (
            <div className="p-8 text-center rounded-2xl border border-dashed border-border bg-card">
              <LayoutGrid className="mx-auto h-8 w-8 text-muted-foreground/50 mb-2" />
              <p className="text-sm font-semibold text-foreground">Main section widgets hidden</p>
              <p className="text-xs text-muted-foreground mt-1">
                Customize your dashboard to restore or reorder widgets.
              </p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2">
              {mainWidgets.map(({ def, layout }, index) => (
                <DashboardWidgetWrapper
                  key={def.id}
                  widget={def}
                  isCustomizing={isCustomizing}
                  isPinned={false}
                  canMoveUp={index > 0}
                  canMoveDown={index < mainWidgets.length - 1}
                  onPinToggle={handlePinToggle}
                  onHide={handleHideWidget}
                  onMoveUp={(id) => handleMoveWidget(id, "up")}
                  onMoveDown={(id) => handleMoveWidget(id, "down")}
                  onDragStart={handleDragStart}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                  onDragEnd={handleDragEnd}
                  isDragging={draggedWidgetId === def.id}
                  isDragOver={dragOverWidgetId === def.id}
                />
              ))}
            </div>
          )}
        </div>

        {/* Sidebar Column - 3 cols */}
        {sidebarWidgets.length > 0 && (
          <div className="lg:col-span-3 flex flex-col gap-6">
            {sidebarWidgets.map(({ def, layout }, index) => (
              <DashboardWidgetWrapper
                key={def.id}
                widget={def}
                isCustomizing={isCustomizing}
                isPinned={false}
                canMoveUp={index > 0}
                canMoveDown={index < sidebarWidgets.length - 1}
                onPinToggle={handlePinToggle}
                onHide={handleHideWidget}
                onMoveUp={(id) => handleMoveWidget(id, "up")}
                onMoveDown={(id) => handleMoveWidget(id, "down")}
                onDragStart={handleDragStart}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onDragEnd={handleDragEnd}
                isDragging={draggedWidgetId === def.id}
                isDragOver={dragOverWidgetId === def.id}
              />
            ))}
          </div>
        )}
      </div>

      {/* Widget Configuration Modal */}
      <WidgetConfigModal
        open={isConfigModalOpen}
        onOpenChange={setIsConfigModalOpen}
        layouts={layouts}
        onToggleVisibility={handleToggleVisibility}
        onTogglePin={handlePinToggle}
        onReset={() => resetMutation.mutate()}
      />
    </div>
  );
}
export default Dashboard;
