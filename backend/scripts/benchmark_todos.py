"""Measure real SQL plans; never creates/drops indexes or prints credentials.

Run against the isolated benchmark database. Output JSON contains synthetic user IDs,
schema/index inventory, PostgreSQL settings, and all five measured execution plans.
"""

import argparse
import asyncio
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

import asyncpg

from app.core.config import settings


QUERIES = {
    "list_20": "SELECT * FROM todos WHERE user_id = $1 LIMIT 20 OFFSET 0",
    "list_10000": "SELECT * FROM todos WHERE user_id = $1 LIMIT 10000 OFFSET 0",
    "ordered_20": (
        "SELECT * FROM todos WHERE user_id = $1 "
        "ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET 0"
    ),
    "count": "SELECT count(*) FROM todos WHERE user_id = $1",
}


async def main(label, output):
    connection = await asyncpg.connect(
        settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    )
    try:
        database = await connection.fetchval("SELECT current_database()")
        if database != "tier3_benchmark":
            raise RuntimeError("Refusing to benchmark outside tier3_benchmark")
        await connection.execute("ANALYZE todos")
        counts = await connection.fetch(
            "SELECT user_id, count(*) AS n FROM todos GROUP BY user_id ORDER BY n, user_id"
        )
        if len(counts) < 3:
            raise RuntimeError("Seed the benchmark dataset first")
        inventory = await connection.fetch("""
            SELECT tab.relname AS table_name, idx.relname AS index_name,
                   pg_get_indexdef(i.indexrelid) AS definition,
                   i.indisvalid AS valid, i.indisprimary AS primary_key,
                   pg_relation_size(i.indexrelid) AS bytes,
                   c.contype::text AS constraint_type
            FROM pg_index i JOIN pg_class idx ON idx.oid = i.indexrelid
            JOIN pg_class tab ON tab.oid = i.indrelid
            JOIN pg_namespace ns ON ns.oid = tab.relnamespace
            LEFT JOIN pg_constraint c ON c.conindid = i.indexrelid
                AND c.contype IN ('p', 'u', 'x')
            WHERE ns.nspname = 'public' ORDER BY tab.relname, idx.relname
        """)
        result = {
            "label": label,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "database": database,
            "postgres": await connection.fetchval("SELECT version()"),
            "revision": await connection.fetchval("SELECT version_num FROM alembic_version"),
            "users": await connection.fetchval("SELECT count(*) FROM users"),
            "todos": await connection.fetchval("SELECT count(*) FROM todos"),
            "settings": {},
            "indexes": [dict(row) for row in inventory],
            "queries": QUERIES,
            "measurements": [],
        }
        for setting in (
            "shared_buffers", "work_mem", "effective_cache_size",
            "random_page_cost", "max_parallel_workers_per_gather",
        ):
            result["settings"][setting] = await connection.fetchval(f"SHOW {setting}")
        for cohort, row in zip(
            ("few", "median", "many"), (counts[0], counts[len(counts) // 2], counts[-1])
        ):
            for query_name, sql in QUERIES.items():
                statement = "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql
                await connection.fetchval(statement, row["user_id"])
                plans = [
                    json.loads(await connection.fetchval(statement, row["user_id"]))[0]
                    for _ in range(5)
                ]
                result["measurements"].append({
                    "cohort": cohort, "user_id": str(row["user_id"]),
                    "todo_count": row["n"], "query": query_name,
                    "median_ms": statistics.median(p["Execution Time"] for p in plans),
                    "runs": plans,
                })
        if output:
            Path(output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(f"Saved {label}: {result['users']} users, {result['todos']} todos")
            for measurement in result["measurements"]:
                print(measurement["cohort"], measurement["query"], measurement["median_ms"])
            print("Indexes:", [(i["index_name"], i["bytes"]) for i in result["indexes"]])
        else:
            print(json.dumps(result, indent=2))
    finally:
        await connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    asyncio.run(main(args.label, args.output))
