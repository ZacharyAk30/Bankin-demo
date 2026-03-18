from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any

from diskcache import Cache
from tenacity import retry, stop_after_attempt, wait_exponential

from bankin_platform.config import settings
from llm.prompt import classification_prompt


@dataclass(frozen=True)
class LLMResult:
    category: str
    confidence: float
    cached: bool
    estimated_cost_usd: float
    latency_ms: int


class LLMClient:
    """
    Client LLM simulé (Bedrock/OpenAI).
    Contrainte: utilisé uniquement en fallback + cache + rate limiting.
    """

    def __init__(self, cache_dir: str | None = None) -> None:
        self.cache = Cache(cache_dir or settings.llm_cache_dir)
        self._min_interval_s = 1.0 / max(1, int(settings.llm_max_qps))
        self._last_call = 0.0

    def _cache_key(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _rate_limit(self) -> None:
        now = time.time()
        dt = now - self._last_call
        if dt < self._min_interval_s:
            time.sleep(self._min_interval_s - dt)
        self._last_call = time.time()

    def _estimate_cost(self, prompt: str) -> float:
        # Heuristique tokens ~ chars/4
        tokens = max(1, int(len(prompt) / 4))
        return (tokens / 1000.0) * float(settings.llm_cost_per_1k_tokens_usd)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2.0))
    def classify(self, label: str, merchant: str | None, amount: float, currency: str) -> LLMResult:
        if not settings.llm_enabled:
            return LLMResult(
                category="unknown",
                confidence=0.0,
                cached=False,
                estimated_cost_usd=0.0,
                latency_ms=0,
            )

        payload = {"label": label, "merchant": merchant, "amount": amount, "currency": currency}
        key = self._cache_key(payload)

        cached = self.cache.get(key)
        if cached is not None:
            cached["cached"] = True
            return LLMResult(**cached)

        self._rate_limit()

        prompt = classification_prompt(label=label, merchant=merchant, amount=amount, currency=currency)
        cost = self._estimate_cost(prompt)

        t0 = time.time()
        # Simulation latence “réseau + modèle”
        time.sleep(max(0, int(settings.llm_simulated_latency_ms)) / 1000.0)

        # Simulateur: mapping heuristique proche règles, mais plus “souple”
        text = f"{label} {merchant or ''}".upper()
        if "RESTAUR" in text or "CAFE" in text or "BRASSERIE" in text:
            cat, conf = "restaurants", 0.74
        elif "CARREFOUR" in text or "LECLERC" in text or "AUCHAN" in text:
            cat, conf = "groceries", 0.78
        elif "ASSURANCE" in text or "AXA" in text:
            cat, conf = "insurance", 0.70
        elif amount > 0:
            cat, conf = "salary", 0.60
        else:
            cat, conf = "unknown", 0.35

        latency_ms = int((time.time() - t0) * 1000)
        res = LLMResult(
            category=cat,
            confidence=float(conf),
            cached=False,
            estimated_cost_usd=float(cost),
            latency_ms=latency_ms,
        )
        self.cache.set(key, res.__dict__, expire=60 * 60 * 24 * 30)  # 30 jours
        return res

