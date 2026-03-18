from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from bankin_platform.config import settings


def backfill_user_spending_summary(db_path: Path) -> int:
    """
    Simulation “ECS batch”: un job lourd planifié (ex: nightly) pour recalculer des agrégats.
    Ici, on déclenche une requête SQL sur le warehouse (DuckDB).
    """
    con = duckdb.connect(str(db_path), read_only=False)
    con.execute("create table if not exists batch_job_runs(run_at timestamp, job varchar);")
    con.execute("insert into batch_job_runs values (now(), 'backfill_user_spending_summary');")
    # Exemple insight business (matérialisable / exportable)
    con.execute(
        """
        create or replace table top_spenders_last_month as
        select
          user_id,
          spend_total
        from user_spending_summary
        where month = date_trunc('month', current_date - interval '1 month')
        order by spend_total desc
        limit 50
        """
    )
    con.close()
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Simulated ECS batch job runner.")
    p.add_argument("--db-path", type=str, default=settings.duckdb_path)
    args = p.parse_args()
    raise SystemExit(backfill_user_spending_summary(Path(args.db_path)))


if __name__ == "__main__":
    main()

