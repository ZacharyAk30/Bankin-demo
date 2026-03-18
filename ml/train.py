from __future__ import annotations

import argparse
from pathlib import Path

import mlflow
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from bankin_platform.config import settings
from bankin_platform.logging import configure_logging
from ml.dataset import load_training_data
from ml.features import FeaturePipelineFactory
from ml.model_registry import save_latest


def train(db_path: Path, export_latest: bool) -> dict[str, float]:
    ds = load_training_data(db_path)
    X_train, X_test, y_train, y_test = train_test_split(
        ds.X,
        ds.y,
        test_size=0.2,
        random_state=42,
        stratify=ds.y,
    )

    fe = FeaturePipelineFactory().build()
    clf = LogisticRegression(
        max_iter=200,
        n_jobs=1,
        class_weight="balanced",  # gestion simple déséquilibre
        multi_class="auto",
    )
    pipe = Pipeline([("features", fe), ("clf", clf)])

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1_macro": float(f1_score(y_test, y_pred, average="macro")),
        "n_train": float(len(X_train)),
        "n_test": float(len(X_test)),
    }

    if export_latest:
        save_latest(pipe, Path(settings.model_latest_path))

    return metrics


def main() -> None:
    configure_logging()

    p = argparse.ArgumentParser(description="Train transaction categorization model and track with MLflow.")
    p.add_argument("--db-path", type=str, default=settings.duckdb_path)
    p.add_argument("--export-latest", action="store_true", default=False)
    p.add_argument("--tracking-uri", type=str, default=settings.mlflow_tracking_uri)
    p.add_argument("--experiment", type=str, default=settings.mlflow_experiment_name)
    args = p.parse_args()

    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(args.experiment)

    with mlflow.start_run(run_name="train_logreg_tfidf") as run:
        metrics = train(Path(args.db_path), export_latest=args.export_latest)
        mlflow.log_params(
            {
                "model": "LogisticRegression",
                "text_vectorizer": "TFIDF(label_norm, merchant)",
                "class_weight": "balanced",
            }
        )
        mlflow.log_metrics({k: float(v) for k, v in metrics.items()})

        # Log model as artifact for traceability
        if args.export_latest:
            mlflow.log_artifact(settings.model_latest_path, artifact_path="exported")

        print({"run_id": run.info.run_id, **metrics})


if __name__ == "__main__":
    main()

