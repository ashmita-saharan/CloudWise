"""HTTP transport only: simulation logic is independent of FastAPI."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from cloudwise.config.schemas import ScenarioConfig
from cloudwise.simulation.runner import run_comparison, run_simulation

app = FastAPI(title="CloudWise API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "cloudwise"}


@app.post("/api/simulations/run")
def run(config: ScenarioConfig) -> dict:
    try:
        return run_simulation(config)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/simulations/compare")
def compare(config: ScenarioConfig) -> dict:
    try:
        return run_comparison(config)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
