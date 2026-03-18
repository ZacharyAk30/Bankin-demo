from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from bankin_platform.config import settings
from llm.client import LLMClient
from ml.model_registry import load_latest
from ml.rules import RuleBasedCategorizer


@dataclass(frozen=True)
class Prediction:
    category: str
    confidence: float
    source: str  # rule|ml|llm
    meta: dict[str, Any]


class HybridCategorizer:
    """
    3 couches:
    1) règles déterministes
    2) ML supervisé
    3) LLM fallback (cache + rate limit)
    """

    def __init__(self, model_path: str | Path | None = None) -> None:
        self.rules = RuleBasedCategorizer()
        self.model_path = Path(model_path or settings.model_latest_path)
        self.model: Any = load_latest(self.model_path) if self.model_path.exists() else None
        self.llm = LLMClient()

    def _ml_predict(self, row: dict[str, Any]) -> Prediction | None:
        if self.model is None:
            return None

        X = pd.DataFrame([row])
        # Le pipeline est sklearn: predict_proba disponible via LogisticRegression
        proba = getattr(self.model, "predict_proba", None)
        if proba is None:
            pred = self.model.predict(X)[0]
            return Prediction(category=str(pred), confidence=0.0, source="ml", meta={"proba": None})

        p = self.model.predict_proba(X)[0]
        classes = list(self.model.named_steps["clf"].classes_)
        idx = int(p.argmax())
        conf = float(p[idx])
        cat = str(classes[idx])
        return Prediction(category=cat, confidence=conf, source="ml", meta={"top_proba": conf})

    def predict(self, label: str, merchant: str | None, amount: float, currency: str) -> Prediction:
        label_norm = " ".join(str(label).upper().split())
        merchant_norm = " ".join(str(merchant).upper().split()) if merchant else None

        # 1) Rules
        r = self.rules.predict(label_norm=label_norm, merchant=merchant_norm)
        if r is not None:
            return Prediction(
                category=r.category,
                confidence=r.confidence,
                source="rule",
                meta={"rule_id": r.rule_id},
            )

        # 2) ML
        row = {
            "transaction_id": "na",
            "user_id": "na",
            "label_norm": label_norm,
            "merchant": merchant_norm or "unknown",
            "abs_amount": abs(float(amount)),
            "direction": "expense" if float(amount) < 0 else "income",
        }
        ml_pred = self._ml_predict(row)
        if ml_pred is not None and ml_pred.confidence >= float(settings.ml_confidence_threshold):
            return ml_pred

        # 3) LLM fallback
        llm_res = self.llm.classify(label=label_norm, merchant=merchant_norm, amount=amount, currency=currency)
        return Prediction(
            category=llm_res.category,
            confidence=llm_res.confidence,
            source="llm",
            meta={
                "cached": llm_res.cached,
                "estimated_cost_usd": llm_res.estimated_cost_usd,
                "latency_ms": llm_res.latency_ms,
                "ml_used": ml_pred is not None,
                "ml_confidence": None if ml_pred is None else ml_pred.confidence,
            },
        )

