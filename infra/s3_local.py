from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


@dataclass(frozen=True)
class S3Local:
    """
    Simulation minimale de S3 via filesystem.
    Convention: root/bucket/key
    """

    root: Path

    def _resolve(self, bucket: str, key: str) -> Path:
        safe_key = key.lstrip("/").replace("..", "__")
        return self.root / bucket / safe_key

    def put_bytes(self, bucket: str, key: str, data: bytes) -> Path:
        path = self._resolve(bucket, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def put_jsonl(self, bucket: str, key: str, rows: Iterable[dict]) -> Path:
        path = self._resolve(bucket, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return path

    def list(self, bucket: str, prefix: str) -> Iterator[Path]:
        base = self._resolve(bucket, prefix)
        if base.is_file():
            yield base
            return
        if not base.exists():
            return
        yield from (p for p in base.rglob("*") if p.is_file())

