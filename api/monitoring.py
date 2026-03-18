from __future__ import annotations

import math
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Deque


@dataclass
class DriftSnapshot:
    timestamp: float
    baseline: dict[str, float]
    current: dict[str, float]
    kl_divergence: float


def _normalize(counter: Counter[str]) -> dict[str, float]:
    total = sum(counter.values()) or 1
    return {k: v / total for k, v in counter.items()}


def _kl(p: dict[str, float], q: dict[str, float], eps: float = 1e-9) -> float:
    keys = set(p) | set(q)
    s = 0.0
    for k in keys:
        pk = p.get(k, 0.0) + eps
        qk = q.get(k, 0.0) + eps
        s += pk * math.log(pk / qk)
    return float(s)


class InMemoryMonitor:
    """
    Monitoring “simple mais prod-minded”:
    - conserve une baseline (distribution catégories) au démarrage
    - compare une fenêtre glissante récente via KL divergence
    En prod: export vers Prometheus, stockage time-series, alerting.
    """

    def __init__(self, window_size: int = 2000) -> None:
        self.window_size = window_size
        self._recent: Deque[str] = deque(maxlen=window_size)
        self._baseline: Counter[str] = Counter()
        self._baseline_frozen = False

    def observe(self, category: str) -> None:
        self._recent.append(category)
        if not self._baseline_frozen:
            self._baseline[category] += 1
            if sum(self._baseline.values()) >= min(500, self.window_size):
                self._baseline_frozen = True

    def drift(self) -> DriftSnapshot | None:
        if not self._baseline_frozen or len(self._recent) < 200:
            return None
        base = _normalize(self._baseline)
        cur = _normalize(Counter(self._recent))
        return DriftSnapshot(
            timestamp=time.time(),
            baseline=base,
            current=cur,
            kl_divergence=_kl(cur, base),
        )

