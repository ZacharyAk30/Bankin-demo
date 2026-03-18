from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler


def _amount_sign(df: pd.DataFrame) -> np.ndarray:
    # direction est déjà dérivée dans dbt, mais on encode une feature robuste.
    # expense=1, income=0
    return (df["direction"].astype(str).str.lower() == "expense").astype(int).to_numpy().reshape(-1, 1)


@dataclass(frozen=True)
class FeaturePipelineFactory:
    """
    Fabrique un pipeline sklearn:
    - Texte: TF-IDF sur libellé + merchant
    - Num: abs_amount + direction_sign
    """

    max_features: int = 4000
    ngram_range: tuple[int, int] = (1, 2)

    def build(self) -> ColumnTransformer:
        text_label = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            min_df=2,
        )
        text_merchant = TfidfVectorizer(
            max_features=800,
            ngram_range=(1, 2),
            min_df=2,
        )

        dir_sign = FunctionTransformer(_amount_sign, validate=False)

        pre = ColumnTransformer(
            transformers=[
                ("label_tfidf", text_label, "label_norm"),
                ("merchant_tfidf", text_merchant, "merchant"),
                ("amount", Pipeline([("scaler", StandardScaler())]), ["abs_amount"]),
                ("dir_sign", dir_sign, ["direction"]),
            ],
            remainder="drop",
            sparse_threshold=0.8,
        )
        return pre

