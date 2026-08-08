# Project Discussions

Public, project-scoped comment threads (#930).

Before this, someone browsing a project and deciding whether to apply had no
way to ask a question in the open. Direct messages exist, but an answer written
in a DM is seen by one person — the same question then gets asked again by the
next twenty. Discussions put the question and its answer next to the project
they are about.

## Model

`project_comments`:

| Column | Notes |
| --- | --- |
| `id` | UUID primary key |
| `project_id` | FK to `projects`, `ON DELETE CASCADE` |
| `author_id` | FK to `users`, `ON DELETE CASCADE` |
| `parent_id` | Self-referential FK, null for a top-level comment |
| `body` | Text, 1–5000 characters after trimming |
| `is_edited`, `edited_at` | Set the first time the body actually changes |
| `deleted_at`, `deleted_by_id` | Soft delete |
| `created_at`, `updated_at` | Timezone-aware |

Indexes: `(project_id, created_at)` for the listing query, `(parent_id,
created_at)` for loading replies, plus single-column indexes on the foreign
keys and on `deleted_at`.

### Threading is one level deep

A comment is either top-level or a reply to one that is. Arbitrary nesting
reads badly on narrow screens and complicates both the query and the UI for
very little gain.

Replying to a *reply* is not an error — the new comment attaches to that
reply's parent instead. That is what the person meant, and it keeps the thread
flat without making them retry.

### Deletion is soft

A deleted comment is tombstoned, not removed:

- The row stays, so replies underneath keep their parent and the thread does
  not develop holes.
- The API returns `body: "[deleted]"`, `author: null`, `is_deleted: true`. The
  original text is never sent again.
- A deleted **top-level** comment stays in the listing, because its replies
  still need the context. A deleted **reply** has nothing hanging off it, so it
  is dropped from the response entirely.

## API

All routes are under `/api/v1/projects/{project_id}/comments`.

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `` | Optional | Page of top-level comments with replies |
| `GET` | `/count` | Optional | Live comments including replies |
| `POST` | `` | Required | Post a comment or reply |
| `PATCH` | `/{comment_id}` | Required | Edit a comment |
| `DELETE` | `/{comment_id}` | Required | Soft delete |

### Listing

```http
GET /api/v1/projects/{project_id}/comments?limit=20&offset=0
```

```json
{
  "items": [
    {
      "id": "…",
      "project_id": "…",
      "parent_id": null,
      "body": "Does this support Postgres 16?",
      "author": { "id": "…", "username": "aditi", "profile_image": null },
      "is_edited": false,
      "is_deleted": false,
      "created_at": "2026-08-06T12:00:00+00:00",
      "replies": [ … ],
      "reply_count": 1
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

Top-level comments come back newest first; replies within a thread are oldest
first, so a conversation reads in order. `total` counts **top-level comments
only**, so it agrees with the page size — use `/count` for the "12 comments"
number on a project card, which includes replies.

`limit` is clamped to 100.

### Posting a reply

```http
POST /api/v1/projects/{project_id}/comments
{ "body": "Yes, 16 and 17.", "parent_id": "…" }
```

## Permissions

**Reading** follows the project's own visibility. A public project's discussion
is public, including to signed-out visitors. A private project's discussion is
limited to its owner, its active members, and admins.

Denied access returns **404, not 403** — confirming that a private project
exists is itself a disclosure.

**Writing:**

| Action | Who |
| --- | --- |
| Post | Any signed-in user who can view the project |
| Edit | The author only |
| Delete | The author, the project owner, or an admin |

Edit is deliberately stricter than delete. Removing someone's words is
moderation; rewriting them under their name is a different thing, so not even
the project owner can do it.

## Validation

- Body is trimmed, then must be 1–5000 characters. `min_length=1` alone would
  let a single space through, which renders as an empty bubble.
- A `parent_id` naming a comment on a different project is a 404 — a comment id
  from one project must not reach into another.
- Replying to a deleted comment is a 404.

## Frontend

`frontend/src/api/modules/projectComments.ts` exposes `projectCommentsApi` with
`list`, `count`, `create`, `update`, and `remove`. `list` and `count` accept an
`AbortSignal` so a navigation can cancel in flight.

`frontend/src/components/project/ProjectComments.tsx` renders the thread with
compose, reply, edit, and delete.

```tsx
<ProjectComments
  projectId={project.id}
  currentUserId={currentUser?.id}
  isProjectOwner={project.owner_id === currentUser?.id}
/>
```

Because deletion is soft, every mutation invalidates the query and refetches
rather than removing the row locally — the tombstone has to come back from the
server.
