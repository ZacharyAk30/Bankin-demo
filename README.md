# Bankin-demo — Plateforme Data & ML “fintech-grade”

Objectif: une plateforme **production-ready** inspirée d’une app type Bankin’:
ingestion → transformation (dbt) → features → ML (MLflow) → système hybride (règles/ML/LLM fallback) → API → monitoring → déploiement (Docker, simulation AWS).

## Structure

- `data/`: lake “S3-like” local + scripts ingestion
- `dbt/`: projet dbt (DuckDB en local) + tests + marts
- `ml/`: feature engineering, entraînement, registry, batch jobs
- `models/`: artefacts exportés (ex: dernier modèle servi)
- `llm/`: client LLM simulé (Bedrock/OpenAI), prompt, cache, coût/latence
- `api/`: service FastAPI (inférence + métriques + mini dashboard)
- `infra/`: abstraction S3 local, config, simulation Lambda/ECS
- `tests/`: tests unitaires (pytest)

## Prérequis

- Python 3.11+ (ok avec 3.13)
- Docker (optionnel mais recommandé)

## Installation (local)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Exécution end-to-end (local)

1) Générer des transactions brutes (lake S3 local).

```bash
python -m data.ingestion.generate_raw --n-users 200 --n-tx 20000
```

2) Charger dans DuckDB puis exécuter dbt (staging + marts + tests).

```bash
python -m infra.duckdb_loader --input data\lake\raw\transactions
dbt --project-dir dbt --profiles-dir dbt run
dbt --project-dir dbt --profiles-dir dbt test
```

3) Entraîner le modèle (MLflow tracking local) et exporter “latest” pour l’API.

```bash
python -m ml.train --db-path data\warehouse\bankin.duckdb --export-latest
```

4) Lancer l’API.

```bash
uvicorn api.main:app --reload
```

Tester:

```bash
curl -X POST http://127.0.0.1:8000/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"u_001\",\"amount\":-42.5,\"currency\":\"EUR\",\"label\":\"UBER TRIP PARIS\",\"booking_date\":\"2026-03-17\"}"
```

## Déploiement Docker (simulation)

```bash
docker compose up --build
```

Services:
- `api`: inférence + `/metrics` + `/dashboard`
- `mlflow`: tracking server MLflow

## Trade-offs (résumé)

- **Règles vs ML vs LLM**: règles = latence très faible & déterminisme; ML = bon compromis coût/qualité; LLM = uniquement fallback (coût/latence), protégé par cache + seuils.
- **Lambda vs ECS**: Lambda (simulé) pour inférence lightweight; ECS (simulé) pour jobs batch lourds (training, backfills, recalcul features).
- **DuckDB local vs Warehouse cloud**: DuckDB sert de “stand-in” pour Snowflake/Redshift; les couches dbt et l’architecture restent transférables.