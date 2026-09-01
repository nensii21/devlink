import React, { useCallback, useMemo, useState } from "react";
import type {
  Board,
  BoardColumn as ColumnType,
  Task,
  TaskBrief,
  TaskPriority,
} from "../../types/contribution-board";
import {
  PRIORITY_COLORS,
  PRIORITY_LABELS,
} from "../../types/contribution-board";
import {
  useGetBoard,
  useListTasks,
  useMoveTask,
  useDeleteTask,
  useCreateTask,
  useUpdateTask,
} from "../../hooks/useContributionBoard";

// ── KanbanBoard ───────────────────────────────────────────────────────────────

interface KanbanBoardProps {
  boardId: string;
  onTaskClick?: (task: TaskBrief) => void;
}

export function KanbanBoard({ boardId, onTaskClick }: KanbanBoardProps) {
  const { data: board, isLoading: boardLoading } = useGetBoard(boardId);
  const { data: tasksData, isLoading: tasksLoading } = useListTasks(boardId, {
    limit: 500,
  });

  const columns = useMemo(() => board?.columns || [], [board]);
  const tasks = useMemo(() => tasksData?.items || [], [tasksData]);

  const tasksByColumn = useMemo(() => {
    const map: Record<string, TaskBrief[]> = {};
    for (const col of columns) {
      map[col.id] = [];
    }
    for (const task of tasks) {
      if (map[task.column_id]) {
        map[task.column_id].push(task);
      }
    }
    // Sort each column by position
    for (const colId of Object.keys(map)) {
      map[colId].sort((a, b) => a.position - b.position);
    }
    return map;
  }, [columns, tasks]);

  if (boardLoading || tasksLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <span style={{ color: "#8b949e", marginTop: 12 }}>Loading board…</span>
      </div>
    );
  }

  if (!board) {
    return (
      <div style={styles.emptyState}>
        <p>Board not found.</p>
      </div>
    );
  }

  return (
    <div style={styles.boardContainer}>
      <div style={styles.boardHeader}>
        <h2 style={styles.boardTitle}>{board.title}</h2>
        {board.description && (
          <p style={styles.boardDescription}>{board.description}</p>
        )}
        <span style={styles.taskBadge}>{tasks.length} tasks</span>
      </div>
      <div style={styles.columnsRow}>
        {columns.map((col) => (
          <KanbanColumn
            key={col.id}
            column={col}
            tasks={tasksByColumn[col.id] || []}
            boardId={boardId}
            onTaskClick={onTaskClick}
          />
        ))}
      </div>
    </div>
  );
}

// ── KanbanColumn ──────────────────────────────────────────────────────────────

interface KanbanColumnProps {
  column: ColumnType;
  tasks: TaskBrief[];
  boardId: string;
  onTaskClick?: (task: TaskBrief) => void;
}

function KanbanColumn({
  column,
  tasks,
  boardId,
  onTaskClick,
}: KanbanColumnProps) {
  const moveTask = useMoveTask();
  const [dragOver, setDragOver] = useState(false);

  const handleDragOver = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      setDragOver(true);
    },
    [],
  );

  const handleDragLeave = useCallback(() => setDragOver(false), []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragOver(false);
      const taskId = e.dataTransfer.getData("text/plain");
      if (!taskId) return;
      // Move to the bottom of this column
      const targetPosition = tasks.length;
      moveTask.mutate({
        taskId,
        data: { column_id: column.id, position: targetPosition },
      });
    },
    [column.id, tasks.length, moveTask],
  );

  const columnStyle: React.CSSProperties = {
    ...styles.column,
    borderColor: dragOver ? "#58a6ff" : "#30363d",
    backgroundColor: dragOver ? "rgba(56, 139, 253, 0.06)" : "#0d1117",
  };

  return (
    <div
      style={columnStyle}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div style={styles.columnHeader}>
        <div style={styles.columnTitleRow}>
          {column.color && (
            <div
              style={{
                ...styles.columnDot,
                backgroundColor: column.color,
              }}
            />
          )}
          <span style={styles.columnTitle}>{column.title}</span>
          <span style={styles.columnCount}>{tasks.length}</span>
        </div>
        {column.wip_limit && (
          <span style={styles.wipLimit}>
            WIP: {tasks.length}/{column.wip_limit}
          </span>
        )}
      </div>
      <div style={styles.tasksList}>
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onTaskClick={onTaskClick}
          />
        ))}
      </div>
    </div>
  );
}

// ── TaskCard ──────────────────────────────────────────────────────────────────

interface TaskCardProps {
  task: TaskBrief;
  onTaskClick?: (task: TaskBrief) => void;
}

function TaskCard({ task, onTaskClick }: TaskCardProps) {
  const handleDragStart = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.dataTransfer.setData("text/plain", task.id);
      e.dataTransfer.effectAllowed = "move";
    },
    [task.id],
  );

  const isOverdue =
    task.due_date && new Date(task.due_date) < new Date() && task.status !== "done";

  const priorityColor = PRIORITY_COLORS[task.priority] || "#6b7280";
  const priorityLabel = PRIORITY_LABELS[task.priority] || task.priority;

  const labels = task.labels
    ? task.labels.split(",").map((l) => l.trim()).filter(Boolean)
    : [];

  return (
    <div
      style={styles.taskCard}
      draggable
      onDragStart={handleDragStart}
      onClick={() => onTaskClick?.(task)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onTaskClick?.(task);
      }}
    >
      {/* Priority indicator bar */}
      <div
        style={{
          ...styles.priorityBar,
          backgroundColor: priorityColor,
        }}
      />

      <div style={styles.taskCardContent}>
        <div style={styles.taskCardHeader}>
          <span style={styles.taskTitle}>{task.title}</span>
          <span
            style={{
              ...styles.priorityBadge,
              backgroundColor: `${priorityColor}22`,
              color: priorityColor,
            }}
          >
            {priorityLabel}
          </span>
        </div>

        {labels.length > 0 && (
          <div style={styles.labelsRow}>
            {labels.map((label) => (
              <span key={label} style={styles.label}>
                {label}
              </span>
            ))}
          </div>
        )}

        <div style={styles.taskCardFooter}>
          {task.assignee_count > 0 && (
            <span style={styles.assigneeCount}>
              👤 {task.assignee_count}
            </span>
          )}
          {task.due_date && (
            <span
              style={{
                ...styles.dueDate,
                color: isOverdue ? "#f85149" : "#8b949e",
              }}
            >
              📅 {new Date(task.due_date).toLocaleDateString()}
            </span>
          )}
          <span style={styles.taskPosition}>#{task.position + 1}</span>
        </div>
      </div>
    </div>
  );
}

// ── Add Task Form ─────────────────────────────────────────────────────────────

interface AddTaskFormProps {
  boardId: string;
  columnId: string;
  onCreated?: () => void;
  onCancel?: () => void;
}

export function AddTaskForm({
  boardId,
  columnId,
  onCreated,
  onCancel,
}: AddTaskFormProps) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<TaskPriority>("medium");
  const createTask = useCreateTask();

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!title.trim()) return;
      createTask.mutate(
        {
          boardId,
          data: { title: title.trim(), column_id: columnId, priority },
        },
        {
          onSuccess: () => {
            setTitle("");
            onCreated?.();
          },
        },
      );
    },
    [boardId, columnId, title, priority, createTask, onCreated],
  );

  return (
    <form onSubmit={handleSubmit} style={styles.addTaskForm}>
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Task title…"
        style={styles.addTaskInput}
        autoFocus
      />
      <div style={styles.addTaskActions}>
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value as TaskPriority)}
          style={styles.prioritySelect}
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <button type="submit" style={styles.addTaskBtn} disabled={createTask.isPending}>
          {createTask.isPending ? "…" : "Add"}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} style={styles.cancelBtn}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

// ── Board Statistics Panel ────────────────────────────────────────────────────

interface BoardStatsProps {
  boardId: string;
}

export function BoardStats({ boardId }: BoardStatsProps) {
  const { data: stats } = useGetBoardStats(boardId);

  if (!stats) return null;

  const completionRate =
    stats.total_tasks > 0
      ? Math.round((stats.done_tasks / stats.total_tasks) * 100)
      : 0;

  return (
    <div style={styles.statsPanel}>
      <h3 style={styles.statsTitle}>📊 Board Statistics</h3>
      <div style={styles.statsGrid}>
        <StatCard label="Total Tasks" value={stats.total_tasks} color="#58a6ff" />
        <StatCard label="Open" value={stats.open_tasks} color="#6b7280" />
        <StatCard
          label="In Progress"
          value={stats.in_progress_tasks}
          color="#f59e0b"
        />
        <StatCard label="In Review" value={stats.in_review_tasks} color="#8b5cf6" />
        <StatCard label="Done" value={stats.done_tasks} color="#10b981" />
        <StatCard label="Overdue" value={stats.overdue_tasks} color="#f85149" />
      </div>
      <div style={styles.progressBar}>
        <div
          style={{
            ...styles.progressFill,
            width: `${completionRate}%`,
          }}
        />
      </div>
      <span style={styles.progressLabel}>{completionRate}% Complete</span>
      <div style={styles.statsMeta}>
        <span>👥 {stats.contributor_count} contributors</span>
        {stats.avg_estimated_hours && (
          <span>⏱ ~{stats.avg_estimated_hours}h avg</span>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div style={styles.statCard}>
      <span style={{ ...styles.statValue, color }}>{value}</span>
      <span style={styles.statLabel}>{label}</span>
    </div>
  );
}

// Internal hook for stats (avoids circular import issues)
function useGetBoardStats(boardId: string) {
  const { useQuery } = require("@tanstack/react-query");
  return useQuery({
    queryKey: ["contribution-boards", "stats", boardId],
    queryFn: () =>
      fetch(
        `${import.meta.env.VITE_API_URL || "/api"}/contribution-boards/board/${boardId}/statistics`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
          },
        },
      ).then((r) => r.json()),
  });
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  // Board
  boardContainer: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    minWidth: 0,
  },
  boardHeader: {
    padding: "16px 20px",
    borderBottom: "1px solid #30363d",
    display: "flex",
    alignItems: "center",
    gap: 12,
    flexWrap: "wrap",
  },
  boardTitle: {
    margin: 0,
    fontSize: 18,
    fontWeight: 600,
    color: "#f0f6fc",
  },
  boardDescription: {
    margin: 0,
    fontSize: 13,
    color: "#8b949e",
  },
  taskBadge: {
    fontSize: 12,
    color: "#8b949e",
    backgroundColor: "#21262d",
    padding: "2px 8px",
    borderRadius: 12,
  },
  columnsRow: {
    display: "flex",
    gap: 16,
    padding: "16px 20px",
    overflowX: "auto",
    flex: 1,
    alignItems: "flex-start",
  },

  // Column
  column: {
    minWidth: 280,
    maxWidth: 320,
    flex: "0 0 auto",
    backgroundColor: "#0d1117",
    border: "1px solid #30363d",
    borderRadius: 8,
    display: "flex",
    flexDirection: "column",
    transition: "border-color 0.15s, background-color 0.15s",
  },
  columnHeader: {
    padding: "12px 14px",
    borderBottom: "1px solid #21262d",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  columnTitleRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  columnDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    flexShrink: 0,
  },
  columnTitle: {
    fontSize: 13,
    fontWeight: 600,
    color: "#f0f6fc",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  columnCount: {
    fontSize: 11,
    color: "#8b949e",
    backgroundColor: "#21262d",
    padding: "1px 6px",
    borderRadius: 10,
  },
  wipLimit: {
    fontSize: 11,
    color: "#d29922",
  },
  tasksList: {
    padding: 8,
    display: "flex",
    flexDirection: "column",
    gap: 8,
    minHeight: 60,
    flex: 1,
  },

  // Task Card
  taskCard: {
    backgroundColor: "#161b22",
    border: "1px solid #30363d",
    borderRadius: 6,
    cursor: "grab",
    display: "flex",
    overflow: "hidden",
    transition: "border-color 0.15s, box-shadow 0.15s",
    position: "relative" as const,
  },
  taskCardContent: {
    padding: "10px 12px",
    flex: 1,
    minWidth: 0,
  },
  taskCardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 8,
  },
  taskTitle: {
    fontSize: 13,
    fontWeight: 500,
    color: "#f0f6fc",
    lineHeight: 1.4,
    wordBreak: "break-word",
  },
  priorityBar: {
    width: 3,
    flexShrink: 0,
  },
  priorityBadge: {
    fontSize: 10,
    fontWeight: 600,
    padding: "2px 6px",
    borderRadius: 4,
    whiteSpace: "nowrap",
    flexShrink: 0,
  },
  labelsRow: {
    display: "flex",
    gap: 4,
    marginTop: 6,
    flexWrap: "wrap",
  },
  label: {
    fontSize: 10,
    color: "#79c0ff",
    backgroundColor: "rgba(56, 139, 253, 0.15)",
    padding: "1px 6px",
    borderRadius: 4,
  },
  taskCardFooter: {
    display: "flex",
    gap: 10,
    marginTop: 8,
    fontSize: 11,
    color: "#8b949e",
    alignItems: "center",
  },
  assigneeCount: {},
  dueDate: {},
  taskPosition: {
    marginLeft: "auto",
    fontSize: 10,
    color: "#484f58",
  },

  // Add Task Form
  addTaskForm: {
    padding: 8,
    display: "flex",
    flexDirection: "column",
    gap: 6,
  },
  addTaskInput: {
    backgroundColor: "#161b22",
    border: "1px solid #30363d",
    borderRadius: 4,
    padding: "8px 10px",
    fontSize: 13,
    color: "#f0f6fc",
    outline: "none",
  },
  addTaskActions: {
    display: "flex",
    gap: 6,
    alignItems: "center",
  },
  prioritySelect: {
    backgroundColor: "#161b22",
    border: "1px solid #30363d",
    borderRadius: 4,
    padding: "4px 6px",
    fontSize: 12,
    color: "#f0f6fc",
    outline: "none",
  },
  addTaskBtn: {
    backgroundColor: "#238636",
    color: "#fff",
    border: "none",
    borderRadius: 4,
    padding: "4px 12px",
    fontSize: 12,
    fontWeight: 600,
    cursor: "pointer",
  },
  cancelBtn: {
    backgroundColor: "transparent",
    color: "#8b949e",
    border: "1px solid #30363d",
    borderRadius: 4,
    padding: "4px 8px",
    fontSize: 12,
    cursor: "pointer",
  },

  // Stats Panel
  statsPanel: {
    backgroundColor: "#161b22",
    border: "1px solid #30363d",
    borderRadius: 8,
    padding: 20,
    marginBottom: 16,
  },
  statsTitle: {
    margin: "0 0 16px 0",
    fontSize: 15,
    fontWeight: 600,
    color: "#f0f6fc",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(80px, 1fr))",
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 4,
    padding: "8px 0",
  },
  statValue: {
    fontSize: 24,
    fontWeight: 700,
  },
  statLabel: {
    fontSize: 11,
    color: "#8b949e",
  },
  progressBar: {
    width: "100%",
    height: 6,
    backgroundColor: "#21262d",
    borderRadius: 3,
    overflow: "hidden",
    marginBottom: 4,
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#10b981",
    borderRadius: 3,
    transition: "width 0.3s ease",
  },
  progressLabel: {
    fontSize: 12,
    color: "#8b949e",
    display: "block",
    marginBottom: 8,
  },
  statsMeta: {
    display: "flex",
    gap: 16,
    fontSize: 12,
    color: "#8b949e",
  },

  // Loading / Empty
  loadingContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: 48,
  },
  spinner: {
    width: 32,
    height: 32,
    border: "3px solid #30363d",
    borderTopColor: "#58a6ff",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  emptyState: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 48,
    color: "#8b949e",
    fontSize: 14,
  },
};
