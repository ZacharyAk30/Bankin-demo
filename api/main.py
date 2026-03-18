from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import HTMLResponse, Response

from bankin_platform.logging import configure_logging
from api.monitoring import InMemoryMonitor
from api.schemas import PredictRequest, PredictResponse
from ml.hybrid import HybridCategorizer


configure_logging()

app = FastAPI(title="Bankin-demo Transaction Categorization API", version="1.0.0")

hybrid = HybridCategorizer()
monitor = InMemoryMonitor()

REQS = Counter("predict_requests_total", "Total /predict requests")
LAT = Histogram("predict_latency_seconds", "Latency of /predict")
SRC = Counter("predict_source_total", "Prediction source", labelnames=("source",))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    REQS.inc()
    with LAT.time():
        p = hybrid.predict(
            label=req.label,
            merchant=req.merchant,
            amount=req.amount,
            currency=req.currency,
        )
        SRC.labels(source=p.source).inc()
        monitor.observe(p.category)
        return PredictResponse(category=p.category, confidence=p.confidence, source=p.source, meta=p.meta)


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    drift = monitor.drift()
    drift_html = "<p>Drift: baseline en cours de construction…</p>"
    if drift is not None:
        drift_html = f"""
        <h3>Drift (KL divergence)</h3>
        <p>KL: <b>{drift.kl_divergence:.4f}</b></p>
        <pre>baseline={drift.baseline}</pre>
        <pre>current={drift.current}</pre>
        """

    html = f"""
    <html>
      <head>
        <title>Bankin-demo Dashboard</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; }}
          code, pre {{ background: #f6f8fa; padding: 8px; border-radius: 6px; }}
        </style>
      </head>
      <body>
        <h2>Bankin-demo — Dashboard minimal</h2>
        <p>Endpoints: <code>/predict</code>, <code>/metrics</code>, <code>/health</code></p>
        {drift_html}
      </body>
    </html>
    """
    return HTMLResponse(html)

