"""HTTP prototype for LR2; no product data or database access yet."""

from fastapi import FastAPI

app = FastAPI(title="StudentLedger", docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/health")
def health() -> dict[str, str]:
    """Report process liveness, not database readiness."""
    return {"status": "ok"}
