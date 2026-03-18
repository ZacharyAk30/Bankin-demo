from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralise la configuration via variables d’environnement.
    En production, on brancherait ça à AWS SSM/Secrets Manager.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    s3_local_root: str = "data/lake"
    duckdb_path: str = "data/warehouse/bankin.duckdb"

    mlflow_tracking_uri: str = "http://127.0.0.1:5000"
    mlflow_experiment_name: str = "bankin_tx_categorization"

    model_latest_path: str = "models/artifacts/latest/model.joblib"

    ml_confidence_threshold: float = 0.65
    llm_enabled: bool = True
    llm_cache_dir: str = "data/cache/llm"
    llm_max_qps: int = 5
    llm_simulated_latency_ms: int = 450
    llm_cost_per_1k_tokens_usd: float = 0.003


settings = Settings()

