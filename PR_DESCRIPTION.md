# Complete required assessment: security fixes, testing, specification and performance

## Summary

This PR completes the implementation and documentation for required Tiers 1–3.
Todo Sharing is a specification only; optional Tier 4 is not implemented.

- Fix eight core authentication, authorization, partial-update, caching and session-isolation issues.
- Add backend regression tests, Chromium E2E coverage and a structured manual test plan.
- Define Todo Sharing contracts, permissions, transaction locking and cache behavior.
- Improve Docker healthchecks, build contexts and runtime images.
- Measure SQL performance and apply an owner-scoped index through Alembic.

## Findings and fixes (Tier 1)

Reasons below describe the original defects; locations identify the affected files/functions.
See [BUG_REPORT.md](BUG_REPORT.md) for the full report.

| Finding | Location | Severity | Reason | Fix proposal implemented |
|---|---|---|---|---|
| BUG-01: expired JWT accepted | `backend/app/core/security.py::verify_token` | High | Disabling expiry checks allows expired credentials to remain usable. | Enable expiry verification and reject invalid signatures. |
| BUG-02: refresh token used as access | `backend/app/api/deps.py::get_current_user`; `backend/app/api/v1/auth.py::refresh_token` | High | Token purpose is not enforced on protected endpoints. | Require access type on protected requests and refresh type on refresh requests. |
| BUG-03: cross-user todo access | `backend/app/services/todo_service.py::get_todo_by_id`; todo GET/PUT/DELETE handlers | Critical | ID-only lookup permits reading, editing or deleting another user's todo. | Filter by both todo ID and authenticated owner; return 404 for non-owned resources. |
| BUG-04: shared Redis list key | `backend/app/api/v1/todos.py::list_todos`, `todo_list_cache_key` | Critical | One cache entry can mix users and pagination results. | Scope keys by user, page and size. |
| BUG-05: false completion ignored | `backend/app/api/v1/todos.py::update_existing_todo` | High | A truthiness check drops a valid `false` update. | Update explicitly supplied fields regardless of truthiness. |
| BUG-06: description erased | `backend/app/api/v1/todos.py::update_existing_todo` | High | Unset optional fields become null during partial updates. | Use `model_dump(exclude_unset=True)`; preserve omitted values. |
| BUG-07: stale list cache after mutations | `backend/app/api/v1/todos.py::invalidate_todo_cache` and mutation handlers; `backend/app/core/redis.py::delete_pattern` | High | Writes leave cached lists stale for the TTL. | Invalidate the owner's list variants on successful mutations with SCAN-based deletion. |
| BUG-08: cached state crosses sessions | `frontend/src/lib/authSession.ts`; `frontend/src/features/auth/api/auth.ts`; `frontend/src/lib/api.ts` | High | Tokens are cleared but cached identity/todos can survive user changes. | Clear query cache and session state on auth transitions. |

Additional manual findings were fixed and retested:

- Login enumeration (`backend/app/api/v1/auth.py::login`): wrong-password and unknown-email
  requests now return the same 401 and `Invalid email or password` (DEF-MANUAL-01, High).
- Missing login error toast (`frontend/src/lib/api.ts`): exclude login/register from the
  expired-session redirect so the form can display the error.
- Post-logout todo requests (`frontend/src/features/todos/api/todos.ts`): enable queries only
  with a token and pass AbortSignal to the request.

## Testing (Tier 2)

| Check | Recorded result | Scope |
|---|---|---|
| Backend pytest | 22 passed, 3 warnings; 7.81 s | JWT rejection, ownership, boolean toggle, partial update, cache behavior and auth flows; SQLite/Redis mock fixtures |
| Chromium E2E | 4 passed; 26.9 s | Full user journey, separate-context isolation and both invalid-login/toast scenarios; real Docker PostgreSQL/Redis |
| Frontend build | Passed | TypeScript and Vite build; existing >500 kB chunk warning remains |
| Manual plan | 12 Pass / 0 Fail / 0 Blocked / 0 Not Run, aggregated | Direct UI/Swagger observations and supplementary manual screenshots/confirmations, not inferred from automated results |

[TEST_PLAN.md](TEST_PLAN.md) preserves the Fail → Fix → Retest history and evidence limitations.
The entire 12-case manual suite was **not** rerun on the final Tier 3 images; the report retains
earlier results and explicitly identifies the login retest. Frontend cache checks cover token
removal and observable UI behavior, not a full inspection of React Query memory.

### Run the standard application and tests

From repository root, with Docker available:

```powershell
docker compose up -d --build
docker compose exec backend pytest tests/ -v
cd frontend
npm ci
npx playwright install chromium
npx playwright test
npx playwright test --headed
npm run build
```

For a configured local Python environment, the README command is also supported:

```powershell
cd backend
pytest tests/ -v
```

To reproduce the final isolated E2E run after following
[Tier 3 Docker setup](docs/DOCKER_VALIDATION.md):

```powershell
cd frontend
$env:E2E_BASE_URL = 'http://localhost:3300'
$env:E2E_API_URL = 'http://localhost:8300'
npx playwright test
```

The API-origin guard verifies that successful responses come from the intended backend.
Clear these environment variables before switching back to default ports. E2E accounts are
generated at runtime; test artifacts and storage state are not committed.

## Advanced engineering (Tier 3)

### 3A — Todo Sharing design

[TODO_SHARING_SPEC.md](docs/TODO_SHARING_SPEC.md) follows the template and defines user stories,
acceptance criteria, tables/types/constraints/cascades, endpoint contracts, permission matrix,
duplicate/self-sharing behavior, version conflicts and cache invalidation.

All proposed writes share a stable list-row lock and recheck permissions after acquiring it.
Revocation and edits are ordered by transaction commit. Per-list write contention and reads
already authorized before revocation are explicit tradeoffs. No sharing code is implemented.

### 3B — Docker improvements

Three required categories are addressed:

1. PostgreSQL/Redis healthchecks and backend `service_healthy` dependencies.
2. Completed `.dockerignore` exclusions, including nested Python bytecode caches.
3. Backend builder/runtime separation and frontend Nginx runtime with `npm ci`.

Port 3000 and SPA fallback are preserved; `VITE_API_URL` is set at build time. Validation used
separate project/volumes and ports 3300/8300, with HTTP, CORS and E2E checks. Existing Tier 1/2
containers/data were not removed. Docker-reported image bytes decreased by 40.5% for backend
and 50.0% for frontend; see [DOCKER_VALIDATION.md](docs/DOCKER_VALIDATION.md).

This is not a production security overhaul: Redis authentication, TLS, production secret
management and fully immutable dependencies are outside the selected scope.

### 3C — Database benchmark and index

Dataset: **1,000 users / 100,000 todos**, generated using the existing seed script in a separate
database. Existing baseline indexes were inventoried and preserved. Each query/user had one
warm-up and five measured `EXPLAIN (ANALYZE, BUFFERS)` runs; values are median execution ms.

Selected index: `(user_id, created_at DESC, id DESC)`, migration `b3180d4e92af`.
The ordered query is an assessment workload, **not the current unordered API query**.

| User cohort | Query | Before (ms) | After (ms) |
|---|---|---:|---:|
| Few (70 todos) | List, limit 20 | 1.752 | 0.054 |
| Few | List, limit 10000 | 6.752 | 0.069 |
| Few | Ordered list, limit 20 | 7.300 | 0.032 |
| Few | Count | 8.475 | 0.034 |
| Median (100 todos) | List, limit 20 | 1.162 | 0.065 |
| Median | List, limit 10000 | 7.413 | 0.093 |
| Median | Ordered list, limit 20 | 7.509 | 0.027 |
| Median | Count | 7.777 | 0.035 |
| Many (132 todos) | List, limit 20 | 0.907 | 0.093 |
| Many | List, limit 10000 | 7.045 | 0.096 |
| Many | Ordered list, limit 20 | 6.769 | 0.029 |
| Many | Count | 6.792 | 0.045 |

The composite removes the ordered query's Sort node. It costs 5,914,624 bytes versus 737,280
bytes for the tested user-only candidate. The smaller index is reasonable for the current
unordered API alone; the composite was selected to cover all required benchmark workloads.
No duplicate candidate index is retained. Inserts/deletes incur extra index maintenance;
numeric write-latency impact was not measured.

Concurrent index creation uses an Alembic autocommit block with a bounded lock timeout.
Upgrade → downgrade → upgrade passed on PostgreSQL, with unchanged baseline indexes and row
counts. Concurrent builds still consume resources and can leave invalid indexes if interrupted.
[DATABASE_PERFORMANCE.md](docs/DATABASE_PERFORMANCE.md) contains reproduction commands,
raw execution-plan links, candidate comparisons and migration recovery guidance.

## Limitations and submission boundaries

- Warm-cache synthetic SQL results are not end-to-end API speedups or production guarantees.
- No million-row, concurrent write-load or failure-injected migration benchmark is claimed.
- Existing Python deprecations and Vite bundle warning remain.
- Tokens remain in localStorage; switching authentication to cookies was outside the agreed scope.
- Optional Tier 4 is not implemented.
- The personal progress file `completed.md` was removed; durable evidence remains in the reports.

## AI assistance disclosure

OpenAI Codex was used throughout the assessment to inspect code, explain Python concepts,
propose and implement fixes, write automated tests, assist browser/Swagger checks, author and
translate documentation, improve Docker configuration, and run/analyze database benchmarks.
The candidate also performed manual browser checks and supplied screenshots/confirmations.
This submission is AI-assisted, not independently hand-written without AI.

The following are representative prompt excerpts from the working conversation, not a complete
transcript. Private credentials, tokens and unrelated conversation content are omitted:

> Implement fixes for all eight reported bugs first, then implement the backend pytest scenarios.
> Preserve omitted partial-update fields and keep user-scoped cache/session data isolated.

> For E2E, check source code before choosing selectors or HTTP methods. Use independent browser
> contexts and actually log User B in. Wait for API/list completion before absence assertions.

> Record manual results only after real UI/Swagger interactions. Do not use pytest or Playwright
> results as manual evidence. Preserve Fail → Fix → Retest and unverified limitations.

> For Tier 3, define revoke/edit locking precisely, isolate Docker ports/volumes, preserve
> existing baseline indexes, and select the index from actual execution plans. Do not implement
> Tier 4 or alter Tier 1/2 data.

These English excerpts summarize the original Vietnamese instructions. Relevant reproducible
configuration is committed in Playwright config/helpers, pytest fixtures, Dockerfiles/Compose,
the benchmark script and Alembic migration. No full prompt log or hidden model configuration is
claimed. Automated results and manual evidence limitations are reported separately above.
