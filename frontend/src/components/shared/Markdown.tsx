import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import { cn } from "@/lib/utils";

const schema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    code: [...(defaultSchema.attributes?.code ?? []), "className"],
    input: [...(defaultSchema.attributes?.input ?? []), "type", "checked", "disabled"],
  },
};

export interface MarkdownProps {
  content: string;
  className?: string;
}

export const Markdown = memo(function Markdown({ content, className }: MarkdownProps) {
  if (!content?.trim()) return null;

  return (
    <div className={cn("max-w-none break-words text-[13px] leading-relaxed text-foreground", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeSanitize, schema]]}
        components={{
          a: ({ node, ...props }) => (
            <a
              {...props}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline underline-offset-2 hover:opacity-80"
            />
          ),
          img: ({ node, ...props }) => (
            // eslint-disable-next-line jsx-a11y/alt-text
            <img {...props} loading="lazy" className="my-2 max-w-full rounded-md border border-border" />
          ),
          h1: ({ node, ...props }) => (
            <h1 {...props} className="mt-4 mb-2 text-[19px] font-bold text-foreground first:mt-0" />
          ),
          h2: ({ node, ...props }) => (
            <h2 {...props} className="mt-4 mb-2 text-[17px] font-bold text-foreground first:mt-0" />
          ),
          h3: ({ node, ...props }) => (
            <h3 {...props} className="mt-3 mb-1.5 text-[15px] font-semibold text-foreground first:mt-0" />
          ),
          h4: ({ node, ...props }) => (
            <h4 {...props} className="mt-3 mb-1.5 text-[14px] font-semibold text-foreground first:mt-0" />
          ),
          p: ({ node, ...props }) => <p {...props} className="mb-2 last:mb-0" />,
          ul: ({ node, ...props }) => <ul {...props} className="mb-2 ml-5 list-disc space-y-1 last:mb-0" />,
          ol: ({ node, ...props }) => <ol {...props} className="mb-2 ml-5 list-decimal space-y-1 last:mb-0" />,
          li: ({ node, ...props }) => <li {...props} className="pl-0.5" />,
          blockquote: ({ node, ...props }) => (
            <blockquote {...props} className="my-2 border-l-2 border-border pl-3 text-muted-foreground" />
          ),
          hr: () => <hr className="my-4 border-border" />,
          table: ({ node, ...props }) => (
            <div className="my-2 w-full overflow-x-auto rounded-md border border-border">
              <table {...props} className="w-full border-collapse text-left text-[12px]" />
            </div>
          ),
          thead: ({ node, ...props }) => <thead {...props} className="bg-muted" />,
          th: ({ node, ...props }) => (
            <th {...props} className="border-b border-border px-3 py-1.5 font-semibold text-foreground" />
          ),
          td: ({ node, ...props }) => <td {...props} className="border-b border-border px-3 py-1.5 align-top" />,
          code: ({ node, className: codeClassName, children, ...props }) => {
            const isBlock = /language-/.test(codeClassName ?? "");
            if (!isBlock) {
              return (
                <code {...props} className="rounded bg-muted px-1 py-0.5 font-mono text-[12px] text-foreground">
                  {children}
                </code>
              );
            }
            return (
              <code {...props} className={cn(codeClassName, "font-mono text-[12px]")}>
                {children}
              </code>
            );
          },
          pre: ({ node, ...props }) => (
            <pre {...props} className="my-2 overflow-x-auto rounded-md border border border-border bg-muted p-3 text-[12px]" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});
