# Fallbacks and empty states in the frontend

One rule:

> **Never render invented content as if it were the user's data.**

A failed request and an empty result are different things, and neither of them
is content. Three code paths broke this and shipped (#1249): invented
collaboration metrics, an invented team timeline, and a hardcoded maintenance
banner shown to every user who had no announcements.

## The three cases

| Situation | What to render |
|---|---|
| Request failed | an error state, with a retry if the component has one |
| Request succeeded, result is empty | an empty state |
| Backend not configured (`isBackendConfigured()` is false) | the seeded mock data — this is local mock mode and is deliberate |

The third is a development convenience and only applies when
`VITE_API_BASE_URL` is unset. It must never be reached because a *configured*
backend failed.

## Why an empty result is the easiest one to get wrong

```js
return res && res.length > 0 ? res : MOCK_ANNOUNCEMENTS;
```

That reads as defensive. It is not: `[]` is a correct, successful answer
meaning "there is nothing to announce", and treating it as a failure showed
every user a maintenance notice that did not exist. Dated `new Date()`, so it
was always tonight.

`if (res && res.project_id)` had the same shape — anything falsy fell through
to the mock, so "quiet project" and "backend is down" produced the same very
busy screen.

## Why this hid other bugs

`withFallback` in `services/index.ts` logged only under `import.meta.env.DEV`.
In production a swallowed failure produced no signal from either side: no error
on the page, nothing in the console, and a screenful of plausible content.

Eleven backend routers were 404ing on the legacy `/api` surface (#1246) and
nobody noticed, partly for this reason. The warning is unconditional now.

## Writing a fallback

Only ever fall back to something **empty**: `[]`, `null`, a zeroed summary. The
caller cannot tell a fallback from a real answer, so anything with content in
it becomes indistinguishable from data the user actually has.

If a component needs to distinguish "nothing" from "we do not know", it needs
the error, not a fallback — let the call throw.

## The components are usually ready for this

Worth checking before writing new UI. `ProjectCollaborationMetrics` already had
a loading skeleton, an error panel and a Retry button; `TeamActivityTimeline`
already had an error panel and a "No activity events found" state. Both were
complete and unreachable, because the API module caught everything before it
got there.

Shared pieces: `components/ui/empty-state.tsx`,
`components/shared/EmptyState.tsx`, `components/shared/EmptySearchState.tsx`,
`components/errors/SectionErrorBoundary.tsx`.
