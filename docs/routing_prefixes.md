# Router prefixes

One rule, because getting it wrong is silent:

> **A router owns its prefix. A mount owns the surface it is mounted on.**

```python
# app/routers/bookmarks.py
router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])

# app/main.py            -> /api/bookmarks/...
app.include_router(bookmarks.router, prefix="/api", tags=["Bookmarks"])

# app/api/v1/router.py   -> /api/v1/bookmarks/...
api_v1_router.include_router(bookmarks.router)
```

The router says *what* the resource is called. The mount says *where* that
resource is exposed — `/api` for the legacy surface, `/api/v1` for the
versioned one. Neither repeats the other's half.

## What goes wrong

Both prefixes are applied, so a repeated segment produces a real, reachable,
wrong URL rather than an error:

```python
router = APIRouter(prefix="/bookmarks")                       # says "bookmarks"
app.include_router(bookmarks.router, prefix="/api/bookmarks") # says it again
#                                     -> /api/bookmarks/bookmarks/...
```

FastAPI is right to allow this — nesting prefixes is how `/projects/{id}/milestones`
is built — so nothing warns. Eleven routers were mounted this way and the
documented paths returned 404 for as long as it took someone to check
(#1246).

Two shapes to watch for:

**A mount that repeats the router's own segment.** The example above. Drop the
segment from the mount, not from the router — the router's prefix is what makes
the same file mountable on both surfaces.

**A router prefix that names the mount.** `saved_searches` declared
`prefix="/api/saved-searches"`, which gave `/api/saved-searches/api/saved-searches`
on the legacy surface and `/api/v1/api/saved-searches` under v1. A router prefix
is relative to wherever it is mounted and must never contain `/api`.

## Mounting the same router twice

Legitimate when the two mounts are genuinely different paths:

```python
app.include_router(profile_suggestions.router, prefix="/api")
app.include_router(profile_suggestions.router, prefix="/api/users/me")
```

Not legitimate when they are the same. `conversations`, `project_milestones`
and `background_jobs` were each included twice with identical arguments. The
second registration is dead — it serves nothing new, and editing it changes
nothing, which is the actual cost.

## The check

`backend/tests/test_route_paths.py` walks every route the app serves and fails
on any path with an immediately repeated segment, any `/api/v1/` path with a
nested `/api/`, and any router mounted twice at the same prefix.

It is mechanical on purpose. A list of known-good paths would have to be
updated by whoever just made the mistake, which is the one person guaranteed
not to.

Deliberate exceptions go in `DELIBERATE_ALIASES` with a comment saying why —
there is currently one, a hidden compatibility alias in `project_tags`.
