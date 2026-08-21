import { api } from "../client";

export interface DashboardWidgetLayout {
  id: string;
  order: number;
  pinned: boolean;
  visible: boolean;
  column: number; // 1 for main, 2 for sidebar
}

export interface DashboardLayoutResponse {
  widgets: DashboardWidgetLayout[];
  is_customized: boolean;
}

export const dashboardLayoutApi = {
  getLayout: () => api.get<DashboardLayoutResponse>("/api/users/me/dashboard-layout"),

  updateLayout: (widgets: DashboardWidgetLayout[]) =>
    api.put<DashboardLayoutResponse>("/api/users/me/dashboard-layout", {
      widgets,
    }),

  resetLayout: () => api.delete<DashboardLayoutResponse>("/api/users/me/dashboard-layout"),
};
