import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { CustomizeDashboardToolbar } from "../CustomizeDashboardToolbar";
import { DashboardWidgetWrapper } from "../DashboardWidgetWrapper";
import { WidgetConfigModal } from "../WidgetConfigModal";
import { WIDGET_REGISTRY, DEFAULT_WIDGET_LAYOUTS } from "../dashboardWidgets";

describe("Customizable Dashboard Features (#754)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("CustomizeDashboardToolbar", () => {
    it("renders customize button in normal view", () => {
      const toggle = vi.fn();
      render(
        <CustomizeDashboardToolbar
          isCustomizing={false}
          isSaving={false}
          hiddenCount={0}
          onToggleCustomizing={toggle}
          onOpenAddModal={vi.fn()}
          onResetLayout={vi.fn()}
          onSaveLayout={vi.fn()}
        />,
      );

      const btn = screen.getByRole("button", { name: /Customize Dashboard/i });
      expect(btn).toBeInTheDocument();
      fireEvent.click(btn);
      expect(toggle).toHaveBeenCalledTimes(1);
    });

    it("renders full toolbar with save, reset, and add modal buttons in edit mode", () => {
      const save = vi.fn();
      const reset = vi.fn();
      const openAdd = vi.fn();

      render(
        <CustomizeDashboardToolbar
          isCustomizing={true}
          isSaving={false}
          hiddenCount={2}
          onToggleCustomizing={vi.fn()}
          onOpenAddModal={openAdd}
          onResetLayout={reset}
          onSaveLayout={save}
        />,
      );

      expect(screen.getByText("Customizing Dashboard Layout")).toBeInTheDocument();
      expect(screen.getByText("2 hidden")).toBeInTheDocument();

      const saveBtn = screen.getByRole("button", { name: /Save Layout/i });
      fireEvent.click(saveBtn);
      expect(save).toHaveBeenCalledTimes(1);

      const resetBtn = screen.getByRole("button", { name: /Reset Layout/i });
      fireEvent.click(resetBtn);
      expect(reset).toHaveBeenCalledTimes(1);

      const manageBtn = screen.getByRole("button", { name: /Manage Widgets/i });
      fireEvent.click(manageBtn);
      expect(openAdd).toHaveBeenCalledTimes(1);
    });
  });

  describe("DashboardWidgetWrapper", () => {
    const mockWidget = {
      id: "test-widget",
      title: "Test Widget",
      description: "Test description",
      category: "main" as const,
      defaultColumn: 1,
      defaultOrder: 0,
      defaultPinned: false,
      defaultVisible: true,
      icon: () => null,
      component: () => <div>Test Widget Content</div>,
    };

    it("renders widget in normal mode without edit toolbar", () => {
      render(
        <DashboardWidgetWrapper
          widget={mockWidget}
          isCustomizing={false}
          isPinned={false}
          onPinToggle={vi.fn()}
          onHide={vi.fn()}
          onMoveUp={vi.fn()}
          onMoveDown={vi.fn()}
        />,
      );

      expect(screen.getByText("Test Widget Content")).toBeInTheDocument();
      expect(screen.queryByTitle("Drag to rearrange")).not.toBeInTheDocument();
    });

    it("renders edit toolbar with pin, hide, and move controls in customize mode", () => {
      const onPin = vi.fn();
      const onHide = vi.fn();
      const onMoveUp = vi.fn();
      const onMoveDown = vi.fn();

      render(
        <DashboardWidgetWrapper
          widget={mockWidget}
          isCustomizing={true}
          isPinned={false}
          canMoveUp={true}
          canMoveDown={true}
          onPinToggle={onPin}
          onHide={onHide}
          onMoveUp={onMoveUp}
          onMoveDown={onMoveDown}
        />,
      );

      expect(screen.getByTitle("Drag to rearrange")).toBeInTheDocument();

      const pinBtn = screen.getByTitle("Pin widget to top");
      fireEvent.click(pinBtn);
      expect(onPin).toHaveBeenCalledWith("test-widget");

      const hideBtn = screen.getByTitle("Hide widget");
      fireEvent.click(hideBtn);
      expect(onHide).toHaveBeenCalledWith("test-widget");

      const moveUpBtn = screen.getByTitle("Move Up");
      fireEvent.click(moveUpBtn);
      expect(onMoveUp).toHaveBeenCalledWith("test-widget");

      const moveDownBtn = screen.getByTitle("Move Down");
      fireEvent.click(moveDownBtn);
      expect(onMoveDown).toHaveBeenCalledWith("test-widget");
    });
  });

  describe("WidgetConfigModal", () => {
    it("renders list of widgets with visibility switches and pin toggles", () => {
      const toggleVis = vi.fn();
      const togglePin = vi.fn();
      const reset = vi.fn();

      render(
        <WidgetConfigModal
          open={true}
          onOpenChange={vi.fn()}
          layouts={DEFAULT_WIDGET_LAYOUTS}
          onToggleVisibility={toggleVis}
          onTogglePin={togglePin}
          onReset={reset}
        />,
      );

      expect(screen.getByText("Customize Widgets")).toBeInTheDocument();
      expect(screen.getByText("Current Projects")).toBeInTheDocument();
      expect(screen.getByText("AI Suggestions")).toBeInTheDocument();

      const switches = screen.getAllByRole("switch");
      expect(switches.length).toBeGreaterThan(0);
      fireEvent.click(switches[0]);
      expect(toggleVis).toHaveBeenCalled();

      const pinButtons = screen.getAllByTitle("Pin widget to top");
      expect(pinButtons.length).toBeGreaterThan(0);
      fireEvent.click(pinButtons[0]);
      expect(togglePin).toHaveBeenCalled();
    });
  });
});
