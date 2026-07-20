import { useState, useEffect, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function CollectionDialog({
  open,
  onOpenChange,
  initialName,
  title,
  description,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialName?: string;
  title: string;
  description: string;
  onSubmit: (name: string) => void;
}) {
  const [name, setName] = useState(initialName ?? "");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setName(initialName ?? "");
      setError("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open, initialName]);

  const trimmed = name.trim();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!trimmed) {
      setError("Collection name is required");
      return;
    }
    if (trimmed.length > 100) {
      setError("Name must be 100 characters or fewer");
      return;
    }
    if (initialName && trimmed === initialName) {
      onOpenChange(false);
      return;
    }
    onSubmit(trimmed);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3">
          <Input
            ref={inputRef}
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              setError("");
            }}
            placeholder="Collection name"
            maxLength={100}
            aria-label="Collection name"
            aria-invalid={!!error}
            aria-describedby={error ? "collection-name-error" : undefined}
            onKeyDown={(e) => {
              if (e.key === "Escape") onOpenChange(false);
            }}
          />
          {error && (
            <p id="collection-name-error" className="text-[12px] text-destructive" role="alert">
              {error}
            </p>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" size="sm" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={!trimmed}>
              {initialName ? "Rename" : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
