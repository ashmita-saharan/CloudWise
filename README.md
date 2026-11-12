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

## Expansion 1: Multi-seed benchmarking and research reports

Run an experiment matrix using **the same workload for FCFS, RR and AWLB at each seed**. The runner now creates a separate comparison for every scenario and seed, then calculates per-policy means and sample standard deviations. These are **descriptive statistics**, not significance tests.

From `cloudwise/backend` (with the dependencies installed):

```bash
python -m cloudwise.benchmark --seeds 11 42 73
```

To run a quick test first:

```bash
python -m cloudwise.benchmark --scenarios ../scenarios/light.json --seeds 42
```

The exports go to `results/reports/`:

- `experiment-report.json`: full raw rows, per-policy aggregates and model assumptions.
- `experiment-runs.csv`: one row per scenario/seed/policy.
- `experiment-aggregate.csv`: mean and sample standard deviation per scenario/policy.
- `experiment-report.md`: human-readable report ready for review.

The default benchmark runs four scenarios × three seeds × three algorithms = **36 policy runs**. Increase the number of seeds before drawing conclusions about performance. AWLB is a heuristic, not a learned model, and results are simulated estimates.

The React dashboard also offers **Export run JSON** and **Export comparison JSON** buttons once a result exists. Those download exactly the JSON returned by FastAPI, without fabricated metrics.


## Expansion 2 — Simulated dynamic VM scaling

Run the optional controller with the provided scenario:

```bash
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m cloudwise.cli --scenario ../scenarios/scaling-heavy.json
```

This writes a run JSON and task/allocation CSV files into `results/raw/`. When
scaling events occur, a `*-scaling-events.csv` file is also saved. The API
`POST /api/simulations/run` accepts the same scenario object; the response
contains `scalingEvents`, `summary.scaleOutEvents`, `summary.scaleInEvents`,
and `summary.finalActiveVms` when scaling is enabled.

**Controller assumptions:** scaling is disabled by default. It samples the
instantaneous busy-VM fraction each configured number of simulated seconds.
Scale-out requires both sustained CPU pressure and pending queued work.
Scale-in requires sustained low pressure and an entirely idle VM, which is
removed newest-first. A single shared cooldown applies after either action.
New VMs are first-fit placed on existing Hosts and consume real modelled
Host CPU-core/MIPS/RAM budgets; adding Hosts is not supported. VMs must be
uniform size when scaling is enabled. Existing tasks remain pinned to their
assigned VMs; there is no task migration. CPU/RAM summary utilisation uses
capacity-time over actual VM lifetimes, including retired VMs.

**Experiment integrity:** `--compare` is intentionally rejected for scaling
scenarios. Compare FCFS/RR/AWLB with fixed capacity separately; to compare
scaling settings, run independently configured scenarios using the same seed.
The controller does not provision actual infrastructure.

The FCFS baseline always picks the first eligible VM, so it may not make
effective use of VMs added later; use AWLB/RR to investigate dynamic balancing.
