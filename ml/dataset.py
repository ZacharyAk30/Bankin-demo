from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd


@dataclass(frozen=True)
class TrainingDataset:
    X: pd.DataFrame
    y: pd.Series


def load_training_data(db_path: Path, limit: int | None = None) -> TrainingDataset:
    con = duckdb.connect(str(db_path), read_only=True)
    q = """
    select
      transaction_id,
      user_id,
      label_norm,
      merchant,
      abs_amount,
      direction,
      category_true as category
    from transactions_cleaned
    """
    if limit:
        q += f" limit {int(limit)}"
    df = con.execute(q).df()
    con.close()

    y = df["category"]
    X = df.drop(columns=["category"])
    return TrainingDataset(X=X, y=y)

