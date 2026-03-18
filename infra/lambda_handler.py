from __future__ import annotations

from typing import Any

from ml.hybrid import HybridCategorizer


_hybrid = HybridCategorizer()


def handler(event: dict[str, Any], context: Any | None = None) -> dict[str, Any]:
    """
    Simulation AWS Lambda: event JSON in, JSON out.
    """
    label = event["label"]
    merchant = event.get("merchant")
    amount = float(event["amount"])
    currency = event.get("currency", "EUR")

    p = _hybrid.predict(label=label, merchant=merchant, amount=amount, currency=currency)
    return {"category": p.category, "confidence": p.confidence, "source": p.source, "meta": p.meta}

