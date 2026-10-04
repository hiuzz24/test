# Database Performance & Indexing

## Summary

Task 3C was measured on an isolated PostgreSQL database with **1,000 users and 100,000 todos**,
using the repository's existing seed script. The README's million-todo command is not claimed
as the dataset used here. No main-stack data or pre-existing index was removed.

Selected index: `ix_todos_user_created_id ON todos (user_id, created_at DESC, id DESC)`.
It supports existing owner-scoped reads/counts and the separately measured ordered workload.
It does **not** add ordering or filtering to the current API.

## Environment and preserved baseline

- Date: 2026-10-04; Docker Desktop engine 29.7.2, Linux containers on a Windows host.
- Docker resources: 12 CPUs, 8,208,920,576 bytes memory; shared local machine, not dedicated hardware.
- PostgreSQL 16.15, x86_64 Alpine; database `tier3_benchmark`, no exposed host port.
- Baseline revision: `a0790c76a129`; index migration: `b3180d4e92af`.
- `shared_buffers=128MB`, `work_mem=4MB`, `effective_cache_size=4GB`,
  `random_page_cost=4`, `max_parallel_workers_per_gather=2`.
- Existing seed completed in 5.59 seconds. Actual counts were verified after every stage.
- Selected users have 70 / 100 / 132 todos (few / median / many); synthetic UUIDs are in raw JSON.

The initial migrations/model declare primary keys but no owner-filtering index. The actual
baseline schema confirmed the following, all valid:

| Index | Definition | Bytes |
|---|---|---:|
| `alembic_version_pkc` | Unique B-tree on `alembic_version(version_num)` | 16,384 |
| `todos_pkey` | Unique B-tree on `todos(id)` | 4,407,296 |
| `users_pkey` | Unique B-tree on `users(id)` | 57,344 |

Definitions and validity of all baseline indexes were checked across candidate, upgrade,
downgrade and re-upgrade snapshots. All remained unchanged. Only named indexes introduced
by this experiment were removed when switching candidates. No planner methods were disabled.

## Queries and method

`backend/scripts/benchmark_todos.py` connects directly to PostgreSQL and refuses databases
not named `tier3_benchmark`. Each stage runs `ANALYZE todos`, one warm-up per query/user,
then five `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` executions. Reported values are median
**Execution Time**, excluding planning and HTTP/network overhead. No Redis is involved.

```sql
-- Current service: default first page
SELECT * FROM todos WHERE user_id = $1 LIMIT 20 OFFSET 0;
-- Current frontend requests size=10000
SELECT * FROM todos WHERE user_id = $1 LIMIT 10000 OFFSET 0;
-- Ordering workload required for analysis; NOT the current API query
SELECT * FROM todos WHERE user_id = $1
ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET 0;
-- Current service's total count
SELECT count(*) FROM todos WHERE user_id = $1;
```

The same users, rows, SQL, limits and settings are used before/after. `id` is a deterministic
tie-breaker for the hypothetical ordered query. The existing unordered API does not promise
row order; a different access path can change its incidental row ordering.

## Candidate comparison

Each candidate was evaluated individually in addition to the preserved baseline.
Median-user times (100 matching todos), milliseconds:

| Query | Baseline | `(user_id)` | `(user_id, created_at DESC, id DESC)` |
|---|---:|---:|---:|
| list_20 | 1.162 | 0.067 | 0.060 |
| list_10000 | 7.413 | 0.104 | 0.095 |
| ordered_20 | 7.509 | 0.147 | 0.032 |
| count | 7.777 | 0.032 | 0.038 |
| Index size | — | 737,280 bytes | 5,914,624 bytes |

Baseline list/count scans read the table; median-user full-list query inspected 100,000 rows,
discarding 99,900, with 2,703 shared buffer hits. Ordering additionally used top-N heapsort.
Both candidates permit bitmap scans for unordered lists and index-only counts (zero heap fetches
in the observed count plans). The composite allows an ordered index scan, reads only 20 matches,
and removes the Sort node (23 shared buffer hits in the recorded median-user ordered plan).

**Decision:** keep only the composite to cover all three required workload families. It made
the ordered candidate workload about 4.6x faster than the simple index in this run, but uses
about 8x its storage. Count is slightly slower than the simple index; tiny sub-millisecond
differences should not be overinterpreted. For the current unordered API alone, the smaller
user-only index would be a reasonable choice. Ordering support is an explicit assessment-workload
tradeoff, not evidence that the current API performs ordered reads. No redundant user-only index
or unused completed-column index is retained.

## Before vs After (applied migration)

Values below compare `baseline.json` against `after_migration.json`; all times are milliseconds.
Ratios describe these SQL measurements, not end-to-end application speedups.

| User cohort | Query | Before | After | Before / After |
|---|---|---:|---:|---:|
| Few (70) | list_20 | 1.752 | 0.054 | 32.4x |
| Few (70) | list_10000 | 6.752 | 0.069 | 97.9x |
| Few (70) | ordered_20 | 7.300 | 0.032 | 228.1x |
| Few (70) | count | 8.475 | 0.034 | 249.3x |
| Median (100) | list_20 | 1.162 | 0.065 | 17.9x |
| Median (100) | list_10000 | 7.413 | 0.093 | 79.7x |
| Median (100) | ordered_20 | 7.509 | 0.027 | 278.1x |
| Median (100) | count | 7.777 | 0.035 | 222.2x |
| Many (132) | list_20 | 0.907 | 0.093 | 9.8x |
| Many (132) | list_10000 | 7.045 | 0.096 | 73.4x |
| Many (132) | ordered_20 | 6.769 | 0.029 | 233.4x |
| Many (132) | count | 6.792 | 0.045 | 150.9x |

Full five-run plans, buffers, cohorts and schema inventories:
[baseline](benchmarks/baseline.json), [simple candidate](benchmarks/candidate_user.json),
[composite candidate](benchmarks/candidate_composite.json), [after migration](benchmarks/after_migration.json),
[downgraded](benchmarks/downgraded.json), [re-upgraded](benchmarks/after_reupgrade.json).
This table is ready to include in the eventual PR; no PR was created in this stage.

## Reproduction

First follow [Docker setup](DOCKER_VALIDATION.md) and retain the same runtime environment variables.
Use an empty dedicated benchmark volume; do not run these commands against the main database.

```powershell
docker compose -f docker-compose.tier3.yml --profile benchmark up -d benchmark-db
docker compose -f docker-compose.tier3.yml run --rm benchmark alembic upgrade a0790c76a129
docker compose -f docker-compose.tier3.yml run --rm -e SEED_USERS=1000 -e SEED_TODOS=100000 benchmark python -m app.db.seed
docker compose -f docker-compose.tier3.yml run --rm benchmark python -m scripts.benchmark_todos --label baseline --output /results/baseline.json
```

The seed script skips todo creation when any todo exists. Check its output and resulting counts;
do not assume rerunning seed grows the dataset. UUIDs/text/distribution are randomized, so a new
seed need not reproduce exact timings. Keep one dataset for every stage within a comparison.
The commands overwrite generated report files: preserve prior evidence if performing another run.

To reproduce candidate evaluation on that fresh baseline:

```powershell
docker compose -f docker-compose.tier3.yml exec benchmark-db psql -U tier3 -d tier3_benchmark -v ON_ERROR_STOP=1 -c "CREATE INDEX CONCURRENTLY ix_bench_todos_user ON todos (user_id)"
docker compose -f docker-compose.tier3.yml run --rm benchmark python -m scripts.benchmark_todos --label candidate_user --output /results/candidate_user.json
docker compose -f docker-compose.tier3.yml exec benchmark-db psql -U tier3 -d tier3_benchmark -v ON_ERROR_STOP=1 -c "DROP INDEX CONCURRENTLY ix_bench_todos_user"
docker compose -f docker-compose.tier3.yml exec benchmark-db psql -U tier3 -d tier3_benchmark -v ON_ERROR_STOP=1 -c "CREATE INDEX CONCURRENTLY ix_bench_todos_user_created_id ON todos (user_id, created_at DESC, id DESC)"
docker compose -f docker-compose.tier3.yml run --rm benchmark python -m scripts.benchmark_todos --label candidate_composite --output /results/candidate_composite.json
docker compose -f docker-compose.tier3.yml exec benchmark-db psql -U tier3 -d tier3_benchmark -v ON_ERROR_STOP=1 -c "DROP INDEX CONCURRENTLY ix_bench_todos_user_created_id"
```

Before each DDL operation inspect the inventory; stop if names already exist or belong to
another experiment. These DROP commands target only the two candidates created immediately above.

```powershell
docker compose -f docker-compose.tier3.yml run --rm benchmark alembic upgrade head
docker compose -f docker-compose.tier3.yml run --rm benchmark python -m scripts.benchmark_todos --label after_migration --output /results/after_migration.json
docker compose -f docker-compose.tier3.yml run --rm benchmark alembic downgrade a0790c76a129
docker compose -f docker-compose.tier3.yml run --rm benchmark python -m scripts.benchmark_todos --label downgraded --output /results/downgraded.json
docker compose -f docker-compose.tier3.yml run --rm benchmark alembic upgrade head
docker compose -f docker-compose.tier3.yml run --rm benchmark python -m scripts.benchmark_todos --label after_reupgrade --output /results/after_reupgrade.json
```

All three migration transitions succeeded on PostgreSQL. Snapshot inventory verifies the final
index is valid, is absent after downgrade, returns after re-upgrade, and baseline indexes persist.
All six stages report exactly 1,000 users and 100,000 todos. Application Tier 3 also reached head.

## Write/storage tradeoffs and safe rollout

- The composite costs 5,914,624 bytes (5.64 MiB) at this scale, in addition to existing indexes.
  Inserts/deletes maintain another B-tree and generate more WAL; changed indexed values also
  require index work. Non-indexed updates can still use HOT where PostgreSQL conditions allow.
  Write latency/WAL under concurrent load was not benchmarked; no numeric write-cost claim is made.
- Index-only count benefits depend on visibility-map coverage; busy tables can require heap fetches.
- `CREATE INDEX CONCURRENTLY` avoids blocking ordinary writes for the full build, but performs
  extra scans, consumes IO/CPU, and waits for conflicting transactions/snapshots. It is not zero-lock.
- Migration uses Alembic `autocommit_block()` because concurrent DDL cannot run inside the normal
  migration transaction. Earlier work may already be committed; rollback is not atomic across this
  boundary. Upgrade and downgrade set a five-second lock timeout and restore it afterward.
- Production rollout: inventory existing indexes first; check free disk/WAL capacity, long-running
  transactions and replica lag; use one migration runner, not multiple backend replicas migrating
  at once. Monitor `pg_stat_progress_create_index`, locks and latency. The existing startup migration
  command is retained for local development, not recommended as multi-replica deployment orchestration.
- An interrupted concurrent build can leave an INVALID index. Inspect `pg_index.indisvalid`,
  `pg_get_indexdef` and Alembic revision before retrying. If the failed index is confirmed to belong
  to this migration, remove that exact index concurrently outside a transaction and rerun. Do not
  drop unrelated/constraint-backed indexes or blindly use `IF NOT EXISTS` to conceal invalid state.
  If index creation succeeded but revision stamping failed, investigate before choosing a repair;
  do not automatically stamp head.

## Limitations

This is a warm-cache, first-page, local synthetic SQL benchmark, not a production load test.
All stages share the same host; background activity can influence timing (the downgraded run
shows noise). No cold-cache flush, deep-offset stress, million-row run, write-throughput test,
failure-injected concurrent migration or production lock-wait measurement is claimed. Main-stack
containers remained running. Random seed data has a narrow per-user distribution (70–132 here).
The API's separate user lookup per todo, serialization, Redis behavior and browser latency are
outside these SQL timings and were not optimized. Sharing remains a specification only.
