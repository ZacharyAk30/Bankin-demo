from pathlib import Path

from llm.client import LLMClient


def test_llm_cache_hit(tmp_path: Path) -> None:
    c = LLMClient(cache_dir=str(tmp_path / "llm_cache"))
    r1 = c.classify(label="BRASSERIE DE LA GARE", merchant=None, amount=-12.3, currency="EUR")
    r2 = c.classify(label="BRASSERIE DE LA GARE", merchant=None, amount=-12.3, currency="EUR")
    assert r1.category == r2.category
    assert r2.cached is True
