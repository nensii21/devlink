import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  Board,
  BoardBrief,
  BoardCreate,
  BoardStatistics,
  BoardUpdate,
  PaginatedBoards,
  PaginatedTasks,
  Task,
  TaskBrief,
  TaskComment,
  TaskCommentCreate,
  TaskCreate,
  TaskMoveRequest,
  TaskUpdate,
} from "../types/contribution-board";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

// ── API Client ────────────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem("access_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Query Keys ────────────────────────────────────────────────────────────────

export const boardKeys = {
  all: ["contribution-boards"] as const,
  lists: () => [...boardKeys.all, "list"] as const,
  list: (projectId: string) => [...boardKeys.lists(), projectId] as const,
  details: () => [...boardKeys.all, "detail"] as const,
  detail: (boardId: string) => [...boardKeys.details(), boardId] as const,
  tasks: (boardId: string) => [...boardKeys.all, "tasks", boardId] as const,
  task: (taskId: string) => [...boardKeys.all, "task", taskId] as const,
  comments: (taskId: string) =>
    [...boardKeys.all, "comments", taskId] as const,
  activity: (taskId: string) =>
    [...boardKeys.all, "activity", taskId] as const,
  stats: (boardId: string) =>
    [...boardKeys.all, "stats", boardId] as const,
};

// ── Board Hooks ───────────────────────────────────────────────────────────────

export function useListBoards(
  projectId: string,
  page = 1,
  limit = 20,
  includeArchived = false,
) {
  return useQuery<PaginatedBoards>({
    queryKey: boardKeys.list(projectId),
    queryFn: () =>
      apiFetch(
        `/contribution-boards/${projectId}?page=${page}&limit=${limit}&include_archived=${includeArchived}`,
      ),
  });
}

export function useGetBoard(boardId: string) {
  return useQuery<Board>({
    queryKey: boardKeys.detail(boardId),
    queryFn: () => apiFetch(`/contribution-boards/board/${boardId}`),
  });
}

export function useCreateBoard() {
  const qc = useQueryClient();
  return useMutation<Board, Error, { projectId: string; data: BoardCreate }>({
    mutationFn: ({ projectId, data }) =>
      apiFetch(`/contribution-boards/${projectId}`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: (_, { projectId }) => {
      qc.invalidateQueries({ queryKey: boardKeys.list(projectId) });
    },
  });
}

export function useUpdateBoard() {
  const qc = useQueryClient();
  return useMutation<Board, Error, { boardId: string; data: BoardUpdate }>({
    mutationFn: ({ boardId, data }) =>
      apiFetch(`/contribution-boards/board/${boardId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: (_, { boardId }) => {
      qc.invalidateQueries({ queryKey: boardKeys.detail(boardId) });
    },
  });
}

export function useDeleteBoard() {
  const qc = useQueryClient();
  return useMutation<void, Error, { boardId: string; projectId: string }>({
    mutationFn: ({ boardId }) =>
      apiFetch(`/contribution-boards/board/${boardId}`, { method: "DELETE" }),
    onSuccess: (_, { projectId }) => {
      qc.invalidateQueries({ queryKey: boardKeys.list(projectId) });
    },
  });
}

// ── Board Statistics ──────────────────────────────────────────────────────────

export function useBoardStatistics(boardId: string) {
  return useQuery<BoardStatistics>({
    queryKey: boardKeys.stats(boardId),
    queryFn: () => apiFetch(`/contribution-boards/board/${boardId}/statistics`),
  });
}

// ── Task Hooks ────────────────────────────────────────────────────────────────

export function useListTasks(
  boardId: string,
  params?: {
    column_id?: string;
    priority?: string;
    search?: string;
    page?: number;
    limit?: number;
  },
) {
  const searchParams = new URLSearchParams();
  if (params?.column_id) searchParams.set("column_id", params.column_id);
  if (params?.priority) searchParams.set("priority", params.priority);
  if (params?.search) searchParams.set("search", params.search);
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.limit) searchParams.set("limit", String(params.limit));

  return useQuery<PaginatedTasks>({
    queryKey: [...boardKeys.tasks(boardId), params],
    queryFn: () =>
      apiFetch(
        `/contribution-boards/board/${boardId}/tasks?${searchParams.toString()}`,
      ),
  });
}

export function useGetTask(taskId: string) {
  return useQuery<Task>({
    queryKey: boardKeys.task(taskId),
    queryFn: () => apiFetch(`/contribution-boards/tasks/${taskId}`),
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation<Task, Error, { boardId: string; data: TaskCreate }>({
    mutationFn: ({ boardId, data }) =>
      apiFetch(`/contribution-boards/board/${boardId}/tasks`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: (_, { boardId }) => {
      qc.invalidateQueries({ queryKey: boardKeys.tasks(boardId) });
      qc.invalidateQueries({ queryKey: boardKeys.detail(boardId) });
    },
  });
}

export function useUpdateTask() {
  const qc = useQueryClient();
  return useMutation<Task, Error, { taskId: string; data: TaskUpdate }>({
    mutationFn: ({ taskId, data }) =>
      apiFetch(`/contribution-boards/tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: (_, { taskId }) => {
      qc.invalidateQueries({ queryKey: boardKeys.task(taskId) });
      qc.invalidateQueries({ queryKey: boardKeys.tasks("*") });
    },
  });
}

export function useMoveTask() {
  const qc = useQueryClient();
  return useMutation<
    Task,
    Error,
    { taskId: string; data: TaskMoveRequest }
  >({
    mutationFn: ({ taskId, data }) =>
      apiFetch(`/contribution-boards/tasks/${taskId}/move`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: (task) => {
      qc.invalidateQueries({ queryKey: boardKeys.tasks(task.board_id) });
      qc.invalidateQueries({ queryKey: boardKeys.detail(task.board_id) });
    },
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation<void, Error, { taskId: string; boardId: string }>({
    mutationFn: ({ taskId }) =>
      apiFetch(`/contribution-boards/tasks/${taskId}`, { method: "DELETE" }),
    onSuccess: (_, { boardId }) => {
      qc.invalidateQueries({ queryKey: boardKeys.tasks(boardId) });
      qc.invalidateQueries({ queryKey: boardKeys.detail(boardId) });
    },
  });
}

// ── Comment Hooks ─────────────────────────────────────────────────────────────

export function useListComments(taskId: string) {
  return useQuery<TaskComment[]>({
    queryKey: boardKeys.comments(taskId),
    queryFn: () => apiFetch(`/contribution-boards/tasks/${taskId}/comments`),
  });
}

export function useAddComment() {
  const qc = useQueryClient();
  return useMutation<
    TaskComment,
    Error,
    { taskId: string; data: TaskCommentCreate }
  >({
    mutationFn: ({ taskId, data }) =>
      apiFetch(`/contribution-boards/tasks/${taskId}/comments`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: (_, { taskId }) => {
      qc.invalidateQueries({ queryKey: boardKeys.comments(taskId) });
    },
  });
}

// ── Activity Log ──────────────────────────────────────────────────────────────

export function useTaskActivity(taskId: string, limit = 50) {
  return useQuery({
    queryKey: boardKeys.activity(taskId),
    queryFn: () =>
      apiFetch(
        `/contribution-boards/tasks/${taskId}/activity?limit=${limit}`,
      ),
  });
}

// ── Assignment Hooks ──────────────────────────────────────────────────────────

export function useAssignUser() {
  const qc = useQueryClient();
  return useMutation<
    void,
    Error,
    { taskId: string; userId: string }
  >({
    mutationFn: ({ taskId, userId }) =>
      apiFetch(`/contribution-boards/tasks/${taskId}/assign/${userId}`, {
        method: "POST",
      }),
    onSuccess: (_, { taskId }) => {
      qc.invalidateQueries({ queryKey: boardKeys.task(taskId) });
    },
  });
}

export function useUnassignUser() {
  const qc = useQueryClient();
  return useMutation<
    void,
    Error,
    { taskId: string; userId: string; boardId: string }
  >({
    mutationFn: ({ taskId, userId }) =>
      apiFetch(`/contribution-boards/tasks/${taskId}/assign/${userId}`, {
        method: "DELETE",
      }),
    onSuccess: (_, { taskId, boardId }) => {
      qc.invalidateQueries({ queryKey: boardKeys.task(taskId) });
      qc.invalidateQueries({ queryKey: boardKeys.tasks(boardId) });
    },
  });
}
