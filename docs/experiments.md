# Experiment protocol

1. Do not vary hosts, VM capacities, workload-generation settings or random seed among policies within a comparison.
2. Run `python -m cloudwise.benchmark --scenarios ../scenarios/light.json --seeds 11 42 73` from `backend/`.
3. Inspect `results/reports/experiment-runs.csv` for individual seed outcomes; keep the raw rows as evidence.
4. Use `experiment-aggregate.csv` for per-policy mean and sample standard deviation across seeds. Single-seed standard deviation is reported as zero by convention, not as evidence of no variability.
5. Confirm that failed/unplaceable counts are recorded and do not silently disappear from results.
6. Interpret reported CPU/RAM utilization as estimates from the space-shared, single-task-per-VM model.
7. Do not claim that AWLB is universally optimal or improves outcomes unless the actual figures support the narrower comparison.

## Units and metric definitions

- Task processing length: MI. VM CPU capacity: MIPS. Execution duration: MI / MIPS, in simulated seconds.
- Waiting: `start - arrival`; turnaround: `finish - arrival`.
- Throughput: completed count divided by simulated interval from `t=0` until the final event.
- CPU/RAM utilization: time integrals normalized by provisioned capacity and total observation time.
- Sample standard deviation: across seeded runs for a given scenario and policy, not within-task dispersion and not a confidence interval.

## Extension boundary

This phase adds multi-seed experiment orchestration and exports. Dynamic VM scaling and statistical significance testing are **not yet implemented**.
