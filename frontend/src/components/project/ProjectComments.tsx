import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  projectCommentsApi,
  type ProjectComment,
  type ProjectCommentThread,
} from "@/api/modules/projectComments";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { TypoCaption } from "@/components/shared/Typography";

const MAX_BODY_LENGTH = 5000;
const PAGE_SIZE = 20;

export interface ProjectCommentsProps {
  projectId: string;
  /** Signed-in user, or undefined when browsing anonymously. */
  currentUserId?: string;
  /** Project owners may delete any comment on their project. */
  isProjectOwner?: boolean;
}

function displayName(author: ProjectComment["author"]): string {
  if (!author) return "Unknown";
  const full = [author.first_name, author.last_name].filter(Boolean).join(" ");
  return full || author.username;
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString();
}

export function ProjectComments({
  projectId,
  currentUserId,
  isProjectOwner = false,
}: ProjectCommentsProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const queryKey = ["project-comments", projectId];

  const [body, setBody] = useState("");
  const [replyTo, setReplyTo] = useState<string | null>(null);
  const [replyBody, setReplyBody] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editBody, setEditBody] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey,
    queryFn: () => projectCommentsApi.list(projectId, { limit: PAGE_SIZE }),
  });

  // A delete is a soft delete: the row stays as a tombstone so replies keep
  // their context. Refetching is therefore the correct response to every
  // mutation -- removing the row locally would lose that.
  const refresh = () => queryClient.invalidateQueries({ queryKey });

  const failed = (action: string) => (error: unknown) => {
    toast({
      title: `Could not ${action} comment`,
      description: error instanceof Error ? error.message : "Please try again.",
      variant: "destructive",
    });
  };

  const createComment = useMutation({
    mutationFn: (payload: { body: string; parentId?: string | null }) =>
      projectCommentsApi.create(projectId, {
        body: payload.body,
        parent_id: payload.parentId ?? null,
      }),
    onSuccess: () => {
      setBody("");
      setReplyBody("");
      setReplyTo(null);
      refresh();
    },
    onError: failed("post"),
  });

  const updateComment = useMutation({
    mutationFn: (payload: { id: string; body: string }) =>
      projectCommentsApi.update(projectId, payload.id, { body: payload.body }),
    onSuccess: () => {
      setEditingId(null);
      setEditBody("");
      refresh();
    },
    onError: failed("update"),
  });

  const deleteComment = useMutation({
    mutationFn: (commentId: string) => projectCommentsApi.remove(projectId, commentId),
    onSuccess: refresh,
    onError: failed("delete"),
  });

  const canEdit = (comment: ProjectComment) =>
    !comment.is_deleted && !!currentUserId && comment.author?.id === currentUserId;

  const canDelete = (comment: ProjectComment) =>
    !comment.is_deleted &&
    !!currentUserId &&
    (comment.author?.id === currentUserId || isProjectOwner);

  const startEditing = (comment: ProjectComment) => {
    setEditingId(comment.id);
    setEditBody(comment.body);
  };

  const renderComment = (comment: ProjectComment, isReply: boolean) => {
    const isEditing = editingId === comment.id;

    return (
      <div
        key={comment.id}
        className={isReply ? "border-l border-border pl-4" : ""}
        data-testid={isReply ? "project-comment-reply" : "project-comment"}
      >
        <div className="flex items-baseline gap-2 text-sm">
          <span className="font-medium text-foreground">
            {comment.is_deleted ? "—" : displayName(comment.author)}
          </span>
          <time className="text-xs text-muted-foreground" dateTime={comment.created_at}>
            {formatTimestamp(comment.created_at)}
          </time>
          {comment.is_edited && !comment.is_deleted ? <TypoCaption>(edited)</TypoCaption> : null}
        </div>

        {isEditing ? (
          <div className="mt-2 space-y-2">
            <Textarea
              value={editBody}
              maxLength={MAX_BODY_LENGTH}
              onChange={(event) => setEditBody(event.target.value)}
              aria-label="Edit comment"
            />
            <div className="flex gap-2">
              <Button
                size="sm"
                disabled={!editBody.trim() || updateComment.isPending}
                onClick={() => updateComment.mutate({ id: comment.id, body: editBody.trim() })}
              >
                Save
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <p
            className={
              comment.is_deleted
                ? "mt-1 text-sm italic text-muted-foreground"
                : "mt-1 whitespace-pre-wrap text-sm text-foreground"
            }
          >
            {comment.is_deleted ? "This comment was deleted." : comment.body}
          </p>
        )}

        {!isEditing ? (
          <div className="mt-1 flex gap-3 text-xs">
            {/* Replies are one level deep, so a reply gets no reply button. */}
            {!isReply && !comment.is_deleted && currentUserId ? (
              <button
                type="button"
                className="text-muted-foreground hover:text-foreground"
                onClick={() => {
                  setReplyTo(replyTo === comment.id ? null : comment.id);
                  setReplyBody("");
                }}
              >
                Reply
              </button>
            ) : null}

            {canEdit(comment) ? (
              <button
                type="button"
                className="text-muted-foreground hover:text-foreground"
                onClick={() => startEditing(comment)}
              >
                Edit
              </button>
            ) : null}

            {canDelete(comment) ? (
              <button
                type="button"
                className="text-muted-foreground hover:text-destructive"
                disabled={deleteComment.isPending}
                onClick={() => deleteComment.mutate(comment.id)}
              >
                Delete
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
    );
  };

  const renderThread = (thread: ProjectCommentThread) => (
    <div key={thread.id} className="space-y-3 border-b border-border pb-4 last:border-0">
      {renderComment(thread, false)}

      {thread.replies.length > 0 ? (
        <div className="ml-4 space-y-3">
          {thread.replies.map((reply) => renderComment(reply, true))}
        </div>
      ) : null}

      {replyTo === thread.id ? (
        <div className="ml-4 space-y-2">
          <Textarea
            value={replyBody}
            maxLength={MAX_BODY_LENGTH}
            placeholder="Write a reply…"
            onChange={(event) => setReplyBody(event.target.value)}
            aria-label={`Reply to ${displayName(thread.author)}`}
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              disabled={!replyBody.trim() || createComment.isPending}
              onClick={() =>
                createComment.mutate({
                  body: replyBody.trim(),
                  parentId: thread.id,
                })
              }
            >
              Reply
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setReplyTo(null)}>
              Cancel
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );

  const threads = data?.items ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Discussion
          {data ? <TypoCaption>{data.total}</TypoCaption> : null}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {currentUserId ? (
          <div className="space-y-2">
            <Textarea
              value={body}
              maxLength={MAX_BODY_LENGTH}
              placeholder="Ask a question or share what you are working on…"
              onChange={(event) => setBody(event.target.value)}
              aria-label="Add a comment"
            />
            <div className="flex items-center justify-between">
              <TypoCaption>
                {body.length}/{MAX_BODY_LENGTH}
              </TypoCaption>
              <Button
                size="sm"
                disabled={!body.trim() || createComment.isPending}
                onClick={() => createComment.mutate({ body: body.trim() })}
              >
                {createComment.isPending ? "Posting…" : "Post comment"}
              </Button>
            </div>
          </div>
        ) : (
          <TypoCaption as="p">Sign in to join the discussion.</TypoCaption>
        )}

        {isLoading ? (
          <TypoCaption as="p">Loading discussion…</TypoCaption>
        ) : isError ? (
          <p className="text-sm text-destructive">Could not load the discussion. Please refresh.</p>
        ) : threads.length === 0 ? (
          <TypoCaption as="p">
            No comments yet. Ask the first question — the answer will be useful to the next person
            who looks at this project.
          </TypoCaption>
        ) : (
          <div className="space-y-4">{threads.map(renderThread)}</div>
        )}
      </CardContent>
    </Card>
  );
}

export default ProjectComments;
