from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from bankin_platform.config import settings


def _iter_jsonl_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input dir not found: {input_dir}")
    return sorted([p for p in input_dir.rglob("*.jsonl") if p.is_file()])


def load_transactions_jsonl(input_dir: Path, db_path: Path) -> None:
    files = _iter_jsonl_files(input_dir)
    if not files:
        raise FileNotFoundError(f"No jsonl files under {input_dir}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute(
        """
        create table if not exists raw_transactions(
            transaction_id varchar,
            user_id varchar,
            amount double,
            currency varchar,
            label varchar,
            booking_date date,
            created_at timestamp,
            category varchar,
            source_file varchar
        );
        """
    )

    for f in files:
        con.execute(
            """
            insert into raw_transactions
            select
                j.transaction_id,
                j.user_id,
                j.amount,
                j.currency,
                j.label,
                cast(j.booking_date as date),
                cast(j.created_at as timestamp),
                j.category,
                ?
            from read_json_auto(?) as j;
            """,
            [str(f), str(f)],
        )

    con.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Load raw transactions into DuckDB.")
    p.add_argument(
        "--input",
        type=str,
        default="data/lake/raw/transactions",
        help="Directory containing JSONL files.",
    )
    p.add_argument(
        "--db-path",
        type=str,
        default=settings.duckdb_path,
        help="DuckDB file path.",
    )
    args = p.parse_args()

    load_transactions_jsonl(Path(args.input), Path(args.db_path))


if __name__ == "__main__":
    main()

