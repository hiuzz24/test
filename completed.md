# Assessment Progress

## Completed

- Bug report: documented eight meaningful issues in `BUG_REPORT.md` using the
  required Location, Severity, Reason, and Fix Proposal structure.
- Tier 1 fixes: implemented all eight reported fixes:
  - JWT expiration, signature, and access/refresh token-type enforcement.
  - Todo ownership checks for GET, PUT, and DELETE.
  - Partial updates that preserve omitted fields and persist `completed=false`.
  - User- and pagination-scoped Redis keys plus mutation invalidation using
    `SCAN`.
  - Frontend auth-session cleanup of tokens and React Query cache on login,
    registration, logout, and HTTP 401 responses.
- Tier 2A backend pytest scenarios:
  - JWT rejection.
  - Authorization boundary.
  - Boolean toggle.
  - Partial update.
  - Cache behavior and invalidation.
- Backend verification:
  - Command (from `backend`): `.venv\Scripts\python.exe -m pytest tests\ -v`
  - Result: **20 passed, 2 warnings in 6.74s**.
  - Warnings: one Pydantic class-based `Config` deprecation and one pytest-asyncio
    custom `event_loop` fixture deprecation.
- Frontend verification:
  - Command (from `frontend`): `npm run build`
  - Result: **passed** (`vite v8.0.16`, 2,075 modules transformed, built in
    616ms).
  - Vite reported a non-blocking warning that one generated chunk exceeds 500
    kB after minification.
- Commits:
  - `docs: add assessment bug findings`
  - `fix(auth): enforce token expiration and type`
  - `fix(todos): enforce todo ownership`
  - `fix(todos): preserve partial update fields`
  - `fix(cache): scope and invalidate todo list cache`
  - `fix(frontend): clear cached state on auth changes`
  - `test(backend): cover critical regression scenarios`
  - `docs: add assessment progress summary`

## Not completed

- Post-fix manual browser verification with two user accounts.
- Playwright E2E tests.
- Manual test plan.
- Todo Sharing specification.
- Docker improvements.
- Database benchmark and index.
- Pull Request description and AI disclosure.
- Optional Tier 4 work.
