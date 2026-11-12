# Architecture and modelling contract

CloudWise is a **discrete-event simulator**, not an AWS/Azure provisioning tool. Python owns the cloud-specific models; [SimPy](https://simpy.readthedocs.io/en/stable/) owns the simulation clock and event processing.

```text
React/Vite/Tailwind dashboard
          | JSON over HTTP
          v
  FastAPI (backend/main.py)
          | synchronous Python call
          v
  Simulation runner (cloudwise/simulation/runner.py)
   |           |           |
   v           v           v
Builder     Workload    Broker + scheduling policy
Hosts/VMs   generator   FCFS / RR / AWLB
                  |           |
                  v           v
               SimPy Environment
                |  task arrival processes
                |  VM simpy.Resource(capacity=1) queues
                |  timeouts and completions
                v
        MetricsCollector + AllocationLogger
                |
                v
      JSON response / optional JSON, CSV export
```

## What is implemented

- A single `DataCenter`, with deterministic first-fit VM placement on Hosts.
- Host capacity constraints on allocated cores, aggregate VM MIPS, and provisioned RAM.
- `CloudTask` fields: ID, arrival time, work (MI), RAM (MB), required CPU cores, assigned VM, status, and event timestamps.
- Hard task eligibility checks: `required_pes <= vm.pes` and `required_ram_mb <= vm.ram_mb`. Unplaceable tasks are marked failed with a reason.
- One execution slot per VM (`simpy.Resource(capacity=1)`); the **entire VM aggregate MIPS** is allocated to its running task. Execution duration = task MI / VM MIPS.
- Waiting work and RAM demand are tracked on assignment; active RAM is reserved only while the task executes.
- FCFS: first eligible VM in fixed VM ID order; tasks processed in arrival order.
- RR: rotate through configured VM IDs; skip ineligible candidates, keep a persistent cursor.
- AWLB: choose the eligible VM with the smallest score `0.50 * CPU_norm + 0.30 * RAM_norm + 0.20 * Queue_norm`. Ties are broken by smaller queued MI, then VM ID. CPU is 0 or 1 in the single-slot model; RAM is active RAM / VM RAM; queue is pending MI / `queue_reference_mi`, with all ratios clamped to [0, 1]. Weights are configurable, must sum to 1, and are **not** learned by machine learning.
- Three policies use the same generated task set for a comparison, without reusing mutated task objects.
- JSON contract version 1.0 and CSV output from the CLI.

## Metric definitions

All time quantities are in **simulated seconds**. MI is million instructions; MIPS is million instructions/second. RAM values use MB as a consistent scenario unit (no GB conversions are performed).

| Metric | Definition |
| --- | --- |
| Waiting time | `start_time - arrival_time` |
| Execution time | `finish_time - start_time` |
| Turnaround time | `finish_time - arrival_time` |
| Response time | Identical to waiting time in this one-start task model |
| Throughput | Completed tasks / interval from simulated time **0** to the final event |
| VM CPU utilization | VM execution-slot busy time / total observation time |
| Aggregate CPU utilization | Sum over VMs of `(busy_time × VM aggregate MIPS)` / `(observation time × sum of VM aggregate MIPS)` |
| VM RAM utilization | Integral of active RAM MB over time / `(VM RAM MB × observation time)` |
| Aggregate RAM utilization | Sum of VM RAM × time integrals / `(observation time × sum of VM RAM capacities)` |
| Load imbalance indicator | Population standard deviation of VM CPU utilization ratios |

For no events or zero completed tasks, rates use `0.0`, never division by zero. For a failed-only workload, the observation interval lasts until the last arrival event. No simulated resource-use values are real machine telemetry.

## Intentional gaps / suggested follow-ups

This is a starter repository, not a full cloud emulator. It does **not** implement VM migration, physical networks, real cloud provisioning, energy costs, storage capacity, pre-emption, time-shared CPU execution, calibrated utilisation models, database persistence, or dynamic scale-out/in. Scaling should only be added after static-policy experiments are validated and should be evaluated independently.

The frontend is a lightweight working dashboard with config fields and metrics. The CLI accepts all advanced scenario parameters from JSON files. Future UI work can expose host/VM templates, AWLB weights, allocation-log drilldowns and scenario presets.
