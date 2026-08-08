import * as React from "react";
import { toast as sonnerToast, ExternalToast } from "sonner";

export type ToastType = "success" | "error" | "warning" | "info" | "default" | "destructive";

export interface ToastProps {
  id?: string;
  title?: React.ReactNode;
  description?: React.ReactNode | (() => React.ReactNode);
  variant?: "default" | "destructive" | "success" | "warning" | "info";
  type?: ToastType;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  onDismiss?: () => void;
  onAutoClose?: () => void;
}

/**
 * Sonner options we are happy to forward untouched.
 *
 * The keys removed here are the ones this module already models with its own,
 * narrower shape. Intersecting the whole of `ExternalToast` (as this used to)
 * produced an `action` of type `{ label; onClick } & ReactNode`, which nothing
 * can satisfy — so every `toast.success(...)` call failed to type-check.
 */
type SonnerPassthrough = Omit<
  ExternalToast,
  "id" | "description" | "duration" | "action" | "onDismiss" | "onAutoClose"
>;

/** Everything `toast()` accepts: our own props plus the sonner passthrough. */
export type ToastInput = ToastProps & SonnerPassthrough;

/** What the `toast.success` / `.error` / … helpers take after the title. */
export type ToastOptions = Omit<ToastInput, "title">;

interface ToastState {
  toasts: ToastProps[];
}

const TOAST_LIMIT = 5;
const TOAST_REMOVE_DELAY = 1000000;

type ActionType =
  | { type: "ADD_TOAST"; toast: ToastProps }
  | { type: "UPDATE_TOAST"; toast: Partial<ToastProps> }
  | { type: "DISMISS_TOAST"; toastId?: string }
  | { type: "REMOVE_TOAST"; toastId?: string };

let count = 0;

function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER;
  return count.toString();
}

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>();

const memoryState: ToastState = { toasts: [] };
const listeners: Array<(state: ToastState) => void> = [];

function dispatch(action: ActionType) {
  switch (action.type) {
    case "ADD_TOAST":
      memoryState.toasts = [action.toast, ...memoryState.toasts].slice(0, TOAST_LIMIT);
      break;
    case "UPDATE_TOAST":
      memoryState.toasts = memoryState.toasts.map((t) =>
        t.id === action.toast.id ? { ...t, ...action.toast } : t,
      );
      break;
    case "DISMISS_TOAST": {
      const { toastId } = action;

      if (toastId) {
        addToRemoveQueue(toastId);
      } else {
        memoryState.toasts.forEach((t) => {
          if (t.id) addToRemoveQueue(t.id);
        });
      }

      memoryState.toasts = memoryState.toasts.map((t) =>
        t.id === toastId || toastId === undefined
          ? {
              ...t,
            }
          : t,
      );
      break;
    }
    case "REMOVE_TOAST":
      if (action.toastId === undefined) {
        memoryState.toasts = [];
      } else {
        memoryState.toasts = memoryState.toasts.filter((t) => t.id !== action.toastId);
      }
      break;
  }

  listeners.forEach((listener) => {
    listener(memoryState);
  });
}

function addToRemoveQueue(toastId: string) {
  if (toastTimeouts.has(toastId)) {
    return;
  }

  const timeout = setTimeout(() => {
    toastTimeouts.delete(toastId);
    dispatch({
      type: "REMOVE_TOAST",
      toastId,
    });
  }, TOAST_REMOVE_DELAY);

  toastTimeouts.set(toastId, timeout);
}

export function toast({
  title,
  description,
  variant = "default",
  type,
  duration = 4000,
  action,
  ...props
}: ToastInput) {
  const id = props.id || genId();

  const effectiveType: ToastType = type || (variant === "destructive" ? "error" : variant);

  const sonnerOptions: ExternalToast = {
    duration,
    description,
    action: action
      ? {
          label: action.label,
          onClick: action.onClick,
        }
      : undefined,
    ...props,
  };

  // Map to sonner calls for unified UI rendering & accessibility
  switch (effectiveType) {
    case "success":
      sonnerToast.success(title, sonnerOptions);
      break;
    case "error":
    case "destructive":
      sonnerToast.error(title, sonnerOptions);
      break;
    case "warning":
      sonnerToast.warning(title, sonnerOptions);
      break;
    case "info":
      sonnerToast.info(title, sonnerOptions);
      break;
    default:
      sonnerToast(title, sonnerOptions);
      break;
  }

  dispatch({
    type: "ADD_TOAST",
    toast: {
      id,
      title,
      description,
      variant,
      type: effectiveType,
      duration,
      action,
    },
  });

  return {
    id,
    dismiss: () => sonnerToast.dismiss(id),
    update: (props: ToastProps) =>
      dispatch({
        type: "UPDATE_TOAST",
        toast: { ...props, id },
      }),
  };
}

toast.success = (title: React.ReactNode, options?: ToastOptions) =>
  toast({ title, type: "success", variant: "success", ...options } as ToastProps);

toast.error = (title: React.ReactNode, options?: ToastOptions) =>
  toast({ title, type: "error", variant: "destructive", ...options } as ToastProps);

toast.warning = (title: React.ReactNode, options?: ToastOptions) =>
  toast({ title, type: "warning", variant: "warning", ...options } as ToastProps);

toast.info = (title: React.ReactNode, options?: ToastOptions) =>
  toast({ title, type: "info", variant: "info", ...options } as ToastProps);

toast.dismiss = (toastId?: string) => {
  sonnerToast.dismiss(toastId);
  dispatch({ type: "DISMISS_TOAST", toastId });
};

export function useToast() {
  const [state, setState] = React.useState<ToastState>(memoryState);

  React.useEffect(() => {
    listeners.push(setState);
    return () => {
      const index = listeners.indexOf(setState);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  }, [state]);

  return {
    ...state,
    toast,
    dismiss: (toastId?: string) => toast.dismiss(toastId),
  };
}
