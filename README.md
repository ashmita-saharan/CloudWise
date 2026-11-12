# CloudWise

**Intelligent Cloud Resource Allocation and Dynamic Load Balancing Simulator**

Starter repository based on the supplied *CloudWise — Python + SimPy Implementation Guide*. It models a data centre with Hosts, VMs and incoming tasks; uses **SimPy** to advance discrete-event time; compares **FCFS**, **Round Robin (RR)** and **Adaptive Weighted Load Balancing (AWLB)**; and displays metrics through an optional **FastAPI + React** dashboard.

> **Scope:** This is a simulation of resource allocation. It does not create real cloud VMs or provision AWS/Azure services. AWLB is a weighted heuristic, **not** trained machine learning.

## Repository tree

```text
cloudwise/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── requirements.txt          # pinned runtime dependencies
│   ├── requirements-dev.txt      # pinned test dependencies
│   ├── cloudwise/
│   │   ├── cli.py                # JSON/CSV command-line runner
│   │   ├── config/schemas.py     # Pydantic scenario validation
│   │   ├── models/               # Host, VM, CloudTask, DataCenter
│   │   ├── infrastructure/       # first-fit VM placement
│   │   ├── workload/             # seeded task generation
│   │   ├── scheduling/           # base, FCFS, RR, AWLB
│   │   ├── simulation/           # runner, broker, VM execution
│   │   ├── monitoring/           # metrics and allocation log
│   │   └── output/               # JSON and CSV exports
│   └── tests/                   # behaviour and API tests
├── frontend/
│   ├── package.json              # React, Vite, Tailwind, Recharts
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── charts/
│       └── services/api.js
├── scenarios/                   # light, medium, heavy, heterogeneous
├── results/raw/                 # generated files, ignored by Git
├── results/reports/
├── docs/                        # architecture + original guide + references
└── .github/workflows/           # Python CI tests
```

## 1. Quick start: Python simulation only

Use **Python 3.11 or 3.12** (3.13 may also work after package verification). From the repository root:

**Windows PowerShell**

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m cloudwise.cli --scenario ../scenarios/light.json
python -m cloudwise.cli --scenario ../scenarios/medium.json --compare
python -m pytest -q
```

**macOS / Linux**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m cloudwise.cli --scenario ../scenarios/light.json
python -m cloudwise.cli --scenario ../scenarios/medium.json --compare
python -m pytest -q
```

The CLI writes result JSON, task CSV and allocation CSV to `results/raw/` by default. Override with `--output <folder>`. To change policy, pass `--algorithm FCFS`, `RR` or `AWLB`. A comparison generates tasks **once** with a fixed seed and reuses them for every policy.

## 2. Start the FastAPI backend

In the backend folder with the virtual environment active:

```bash
python -m uvicorn main:app --reload --port 8000
```

- Health: <http://localhost:8000/api/health>
- Interactive API docs: <http://localhost:8000/docs>
- `POST /api/simulations/run`: one policy, returns a result object
- `POST /api/simulations/compare`: all three policies, same initial workload

Example request JSON:

```json
{
  "name": "demo",
  "hosts": 2,
  "vms": 4,
  "tasks": 100,
  "seed": 42,
  "algorithm": "AWLB",
  "arrival_window": 40
}
```

The response contains `schemaVersion`, `runId`, `algorithm`, `scenario`, `summary`, `vmMetrics`, `taskResults` and `allocationLog`. The `/compare` endpoint wraps three such results under `results.FCFS`, `results.RR` and `results.AWLB`.

## 3. Start the React dashboard

In a **second terminal** from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. The frontend expects the API at `http://localhost:8000`; to change it, copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_BASE_URL`.

## 4. Included scenarios

| File | Hosts | VMs | Tasks | Purpose |
| --- | ---: | ---: | ---: | --- |
| `light.json` | 2 | 4 | 100 | Baseline validation |
| `medium.json` | 3 | 6 | 500 | Moderate workload comparison |
| `heavy.json` | 4 | 8 | 1,000 | Queueing/contention |
| `heterogeneous.json` | 3 | 6 (mixed) | 500 | VM size and task requirement diversity |

These are experiment **inputs**, not measured results. Re-run a scenario with the same seed and infrastructure for reproducible comparisons.

## 5. Core assumptions

- Hosts reserve capacity for placed VMs by CPU cores, MIPS and RAM (first-fit placement).
- Task admission requires sufficient VM RAM and CPU cores; impossible tasks fail explicitly.
- VMs use **space-shared scheduling**: one active task per VM, sequential queue, aggregate VM MIPS determining its execution duration.
- RAM in-use counts the running task only; queue RAM is tracked separately.
- AWLB uses `0.50 * CPU_norm + 0.30 * RAM_norm + 0.20 * Queue_norm`; weights are configurable. Ties use queued MI and VM ID.
- CPU/RAM utilisation and throughput are **simulation-derived**, not physical telemetry. Throughput uses simulation time 0 to final event.
- Scale-out/in is **not yet implemented**; the source guide identifies it as an optional later extension.

See [architecture and metric definitions](docs/architecture.md) and [sources and attribution](docs/references.md).

## 6. Suggested next milestones

1. Verify small hand-calculated cases and compare FCFS / RR / AWLB on multiple seeds.
2. Add richer dashboard controls, allocation-decision drilldowns and separate metric charts.
3. Export experiment summary reports; add confidence intervals across repeated seeds.
4. Only then explore optional simulated scaling and historical storage.

## Troubleshooting

- **`ModuleNotFoundError: simpy`** — activate the backend virtual environment and install `backend/requirements.txt`.
- **`Cannot reach API`** in the browser — start Uvicorn on port 8000 and confirm the frontend API base URL.
- **`Cannot place vm-...`** — request fewer/smaller VMs or increase Host CPU/RAM limits. The builder intentionally rejects oversubscription.
- **422 errors** — fix invalid scenario numbers, mismatched `vm_specs` length or AWLB weights not summing to 1.
