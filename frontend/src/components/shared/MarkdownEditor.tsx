import { useId, useState } from "react";
import { Eye, Pencil } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Markdown } from "@/components/shared/Markdown";
import { cn } from "@/lib/utils";

export interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  className?: string;
  textareaClassName?: string;
  autoFocus?: boolean;
}

/**
 * Write / Preview markdown editor.
 * "Write" is a plain textarea; "Preview" renders the same content through
 * the shared <Markdown> renderer so contributors see exactly what will be
 * published (GFM tables, code blocks, images, lists, headers, etc).
 */
export function MarkdownEditor({
  value,
  onChange,
  placeholder = "Write some markdown…",
  rows = 4,
  className,
  textareaClassName,
  autoFocus,
}: MarkdownEditorProps) {
  const [tab, setTab] = useState<"write" | "preview">("write");
  const previewId = useId();

  return (
    <div className={cn("w-full", className)}>
      <Tabs value={tab} onValueChange={(v) => setTab(v as "write" | "preview")}>
        <div className="flex items-center justify-between gap-2">
          <TabsList>
            <TabsTrigger value="write" className="gap-1.5">
              <Pencil size={12} /> Write
            </TabsTrigger>
            <TabsTrigger value="preview" className="gap-1.5">
              <Eye size={12} /> Preview
            </TabsTrigger>
          </TabsList>
          <p className="hidden text-[11px] text-muted-foreground sm:block">
            Markdown supported · **bold** _italic_ `code` [link](url)
          </p>
        </div>

        <TabsContent value="write" className="mt-2">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            rows={rows}
            autoFocus={autoFocus}
            className={cn(
              "w-full resize-y rounded-md border border-border bg-surface p-3 font-mono text-[13px] leading-relaxed text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20",
              textareaClassName,
            )}
          />
        </TabsContent>

        <TabsContent value="preview" className="mt-2">
          <div
            id={previewId}
            className="rounded-md border border-dashed border-border bg-surface p-3"
            style={{ minHeight: `${rows * 1.6}em` }}
          >
            {value.trim() ? (
              <Markdown content={value} />
            ) : (
              <p className="text-[13px] text-muted-foreground">Nothing to preview yet.</p>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
