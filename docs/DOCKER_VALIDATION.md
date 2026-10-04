# Docker Optimization & Validation

## Scope

Three README Task 3B categories are addressed: dependency healthchecks, build-context
exclusions, and image optimization. This is not a production deployment/security overhaul.

| Area | Existing behavior | Change |
|---|---|---|
| Startup | Backend depended on container start only | PostgreSQL/Redis healthchecks; backend waits for `service_healthy` |
| Context | Both `.dockerignore` files already existed | Added nested Python caches, alternate virtualenvs, build caches and environment variants |
| Backend image | Compiler remained in runtime | Wheels built in builder stage; runtime installs through a read-only BuildKit mount |
| Frontend image | Multi-stage already existed, Node/serve runtime | `npm ci`, Nginx Alpine runtime, SPA fallback, port 3000 preserved |
| Frontend API URL | Runtime environment could not change compiled Vite assets | Explicit build argument; default remains `http://localhost:8000` |

No application routing, API contract or CORS policy was changed. Existing wildcard CORS
allows the separate test origin; this is not a claim that the existing CORS policy is
production-hardened. Redis has no host port in the isolated configuration but still has
no authentication. The original development Compose retains its existing local defaults.

## Isolated environment

`docker-compose.tier3.yml` is standalone: do not merge it with the default Compose file.

| Resource | Tier 3 | Existing stack, left untouched |
|---|---|---|
| Project | `fabbi-tier3` | `test` |
| Frontend | `127.0.0.1:3300` → container 3000 | 3000 |
| Backend | `127.0.0.1:8300` → container 8000 | 8000 |
| PostgreSQL/Redis | Docker network only; no host ports | 5432 / 6379 |
| Application volume | `fabbi-tier3_tier3_postgres_data` | Existing PostgreSQL volume |
| Benchmark volume | `fabbi-tier3_tier3_benchmark_data` | Not used |

The five Tier 3 services (frontend, backend, postgres, redis, benchmark-db) and both named
volumes are retained for review. One-off benchmark containers use `--rm`. No existing
stack container or volume was removed. Generated test accounts stay in the Tier 3 database.

## Run on a new isolated environment

From the repository root, PowerShell (Docker must be on PATH):

```powershell
# Generate runtime-only test secrets. Keep this session for subsequent Compose commands.
$env:TIER3_DB_PASSWORD = [guid]::NewGuid().ToString('N')
$env:TIER3_JWT_SECRET = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
docker compose -f docker-compose.tier3.yml config --quiet
docker compose -f docker-compose.tier3.yml up -d --build
docker compose -f docker-compose.tier3.yml ps
Invoke-WebRequest http://localhost:8300/health
```

Do not generate a different database password when reusing an initialized volume: PostgreSQL
initialization variables do not change the existing database password. Recover the original
runtime environment securely or use a new explicitly named project/volume. Never commit secrets
or print a full expanded Compose config into a report. Ports can be changed with
`TIER3_WEB_PORT` and `TIER3_API_PORT`; rebuild frontend after changing its API port.

```powershell
docker compose -f docker-compose.tier3.yml exec backend pytest tests/ -v
cd frontend
npm ci
npx playwright install chromium
$env:E2E_BASE_URL = 'http://localhost:3300'
$env:E2E_API_URL = 'http://localhost:8300'
npx playwright test
```

`E2E_API_URL` is an optional API-origin guard in response waits. Both it and `E2E_BASE_URL`
must match the chosen Tier 3 ports. The existing default E2E behavior remains unchanged when
these variables are absent. E2E uses real PostgreSQL/Redis; pytest uses its existing SQLite
fixture and Redis mock, even when executed inside the backend container.

## Observed validation — 2026-10-04

| Check | Actual result |
|---|---|
| Compose validation | `config --quiet` exited 0 |
| Image build | Backend wheel/runtime stages and frontend TypeScript/Vite/Nginx build succeeded |
| Cold boot | New network and volumes created; PostgreSQL/Redis reached healthy before backend started |
| HTTP checks | `/health` on 8300 and `/login`, `/register` on 3300 returned 200 |
| CORS | Login preflight from `http://localhost:3300` returned 200 and echoed that allowed origin |
| Browser/API integration | All four Chromium E2E scenarios passed with origin guard set to 8300 after final migration/model rebuild (26.9 seconds) |
| Backend regression after migration/model changes | 22 passed, 3 warnings (7.81 seconds) |
| Applied application migration | `alembic current`: `b3180d4e92af (head)` in Tier 3 backend |
| Main stack | Original `test-*` containers remained running on their original ports |

Browser scenarios cover both login errors/toasts, full todo journey including reload, and
cross-user isolation. Direct navigation to login/register and the journey reload exercise SPA
fallback; response-origin guards verify requests are reaching the Tier 3 API, not the main stack.

Initial container pytest execution had 21 passes and one setup error (`could not get source
code`). Nested host Python bytecode caches were still entering the build context. After adding
recursive cache exclusions and rebuilding, all 22 assertions ran successfully. No test/application
logic was changed to hide the failure. A benchmark report serialization error was also corrected
before recording successful results; it did not alter database data.

### Image sizes

Same metric for both sides: `docker image inspect <image> --format '{{.Size}}'`.
These are Docker's reported image bytes on this installation, not total disk usage including
shared layers, build cache and volumes.

| Image | Before (`test-*`) | After (`fabbi-tier3-*`) | Reduction |
|---|---:|---:|---:|
| Backend | 167,610,397 bytes | 99,779,948 bytes | 40.5% |
| Frontend | 52,513,425 bytes | 26,262,196 bytes | 50.0% |

## Limitations

- Existing Python deprecations remain: Pydantic class Config, `crypt`, and custom pytest event loop.
- npm dependency/audit remediation is outside this infrastructure task.
- Standalone `npm run build` also passed; Vite retains its existing warning about a chunk over 500 kB.
- Cold boot was observed locally, not under injected dependency failures or production load.
- Dependencies/base tags are not fully immutable; pinning all transitive packages/digests is deferred.
- Runtime dependency list still includes test/development packages to preserve the current setup.
- No production secrets manager, Redis authentication, TLS or production Compose is claimed.
- Nothing was pushed and no PR was opened. Existing Tier 1/2 manual results were not rewritten.
