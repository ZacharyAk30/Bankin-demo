from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib


@dataclass(frozen=True)
class ModelArtifact:
    model: object
    path: Path


def save_latest(model: object, path: Path) -> ModelArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return ModelArtifact(model=model, path=path)


def load_latest(path: Path) -> object:
    return joblib.load(path)

