/**
 * TypeScript types for the Contribution Board feature.
 * Mirrors the backend Pydantic schemas exactly.
 */

// ── Enums ─────────────────────────────────────────────────────────────────────

export type TaskPriority = "low" | "medium" | "high" | "critical";

export type TaskStatus =
  | "open"
  | "in_progress"
  | "in_review"
  | "done"
  | "archived";

// ── Board Types ───────────────────────────────────────────────────────────────

export interface BoardColumn {
  id: string;
  board_id: string;
  title: string;
  position: number;
  color: string | null;
  wip_limit: number | null;
  task_count: number;
  created_at: string;
}

export interface BoardColumnCreate {
  title: string;
  position?: number;
  color?: string;
  wip_limit?: number;
}

export interface BoardColumnUpdate {
  title?: string;
  position?: number;
  color?: string;
  wip_limit?: number;
}

export interface Board {
  id: string;
  project_id: string;
  owner_id: string;
  title: string;
  description: string | null;
  is_archived: boolean;
  columns: BoardColumn[];
  task_count: number;
  created_at: string;
  updated_at: string;
}

export interface BoardBrief {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  is_archived: boolean;
  task_count: number;
  created_at: string;
}

export interface BoardCreate {
  title: string;
  description?: string;
  columns?: BoardColumnCreate[];
}

export interface BoardUpdate {
  title?: string;
  description?: string;
  is_archived?: boolean;
}

export interface PaginatedBoards {
  items: BoardBrief[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// ── Task Types ────────────────────────────────────────────────────────────────

export interface TaskAssignee {
  id: string;
  user_id: string;
  display_name: string | null;
  avatar_url: string | null;
  assigned_at: string;
}

export interface Task {
  id: string;
  board_id: string;
  column_id: string;
  creator_id: string;
  title: string;
  description: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  position: number;
  due_date: string | null;
  estimated_hours: number | null;
  labels: string | null;
  assignees: TaskAssignee[];
  comment_count: number;
  created_at: string;
  updated_at: string;
}

export interface TaskBrief {
  id: string;
  column_id: string;
  title: string;
  priority: TaskPriority;
  status: TaskStatus;
  position: number;
  labels: string | null;
  assignee_count: number;
  due_date: string | null;
  created_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  column_id: string;
  priority?: TaskPriority;
  due_date?: string;
  estimated_hours?: number;
  labels?: string;
  assignee_ids?: string[];
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  column_id?: string;
  priority?: TaskPriority;
  status?: TaskStatus;
  position?: number;
  due_date?: string;
  estimated_hours?: number;
  labels?: string;
}

export interface TaskMoveRequest {
  column_id: string;
  position: number;
}

export interface PaginatedTasks {
  items: TaskBrief[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// ── Comment Types ─────────────────────────────────────────────────────────────

export interface TaskComment {
  id: string;
  task_id: string;
  author_id: string;
  author_name: string | null;
  content: string;
  parent_comment_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCommentCreate {
  content: string;
  parent_comment_id?: string;
}

// ── Activity Types ────────────────────────────────────────────────────────────

export interface TaskActivity {
  id: string;
  task_id: string;
  actor_id: string | null;
  actor_name: string | null;
  action: string;
  from_value: string | null;
  to_value: string | null;
  created_at: string;
}

// ── Statistics Types ──────────────────────────────────────────────────────────

export interface BoardStatistics {
  board_id: string;
  total_tasks: number;
  open_tasks: number;
  in_progress_tasks: number;
  in_review_tasks: number;
  done_tasks: number;
  archived_tasks: number;
  overdue_tasks: number;
  tasks_by_priority: Record<TaskPriority, number>;
  tasks_by_column: Array<{
    column_id: string;
    title: string;
    count: number;
  }>;
  avg_estimated_hours: number | null;
  contributor_count: number;
}

// ── Priority Helpers ──────────────────────────────────────────────────────────

export const PRIORITY_COLORS: Record<TaskPriority, string> = {
  low: "#6b7280",
  medium: "#3b82f6",
  high: "#f59e0b",
  critical: "#ef4444",
};

export const PRIORITY_LABELS: Record<TaskPriority, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

export const STATUS_LABELS: Record<TaskStatus, string> = {
  open: "Open",
  in_progress: "In Progress",
  in_review: "In Review",
  done: "Done",
  archived: "Archived",
};
