# TODO

## Command palette search cleanup
- [ ] Edit `frontend/src/hooks/useCommandSearch.ts`
  - [x] Remove redundant `useEffect` that computes `pages` but discards it
  - [x] Ensure `projectsResults`, `developersResults`, `isLoading`, and `error` are deterministic when query length < 2

- [x] Run frontend lint
- [ ] Verify build/typecheck (if available)


