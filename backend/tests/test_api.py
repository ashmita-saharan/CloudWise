"""Smoke tests for the two public simulation API endpoints."""

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok", "service": "cloudwise"}


def test_run_response_contract():
    response = client.post("/api/simulations/run", json={
        "hosts": 1, "vms": 1, "tasks": 2, "arrival_window": 0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["schemaVersion"] == "1.0"
    assert len(data["taskResults"]) == 2
    assert len(data["allocationLog"]) == 2
    assert set(("summary", "vmMetrics", "scenario")).issubset(data)


def test_compare_response_contract():
    response = client.post("/api/simulations/compare", json={
        "hosts": 1, "vms": 2, "tasks": 6, "arrival_window": 0,
    })
    assert response.status_code == 200
    assert set(response.json()["results"]) == {"FCFS", "RR", "AWLB"}


def test_invalid_capacity_returns_422():
    response = client.post("/api/simulations/run", json={"hosts": 1, "vms": 10})
    assert response.status_code == 422
