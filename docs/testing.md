# Testing

## Checks

| Check | Result |
| --- | --- |
| `python -m compileall app` | PASSED (rerun 02 Oct 2026) |
| Mocked FastAPI workflow (homepage, generation, persistence, refinement) | PASSED (earlier run; no test files in the repository, not rerun) |
| Live Gemini workflow | PASSED (02 Oct 2026, model ID `gemini-3.5-flash-lite`) |
| Browser workflow | PASSED (02 Oct 2026, Microsoft Edge driven by Playwright) |
| Load / stress testing | NOT RUN |

The mocked workflow verified that the submitted user ID is persisted, the
original plan is retained, and refinement writes an updated plan.

## Live run on 02 Oct 2026 (local, single user)

- Profile submitted through the form; Gemini returned a 7-day plan (7 day
  cards, no fallback notice) in 6.2 s; feedback produced an updated plan in
  5.19 s and the "Plan Updated" badge was shown.
- `GET /result/{plan_id}`, `GET /view-all-users` and `/docs` returned HTTP 200.
- Invalid goal, age, intensity, blank name and empty feedback returned
  HTTP 422; unknown plan IDs returned HTTP 404.
- No horizontal overflow at 375 px width on the three pages.
- 50 sequential requests each: `GET /` 3.1 ms average, `GET /result/{plan_id}`
  5.2 ms, `GET /view-all-users` 8.9 ms, 0 errors.

These are small local samples, not capacity figures. Screenshots from the run
are in `../screenshots/`.
