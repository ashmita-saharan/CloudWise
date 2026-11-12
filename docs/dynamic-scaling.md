# Expansion 2: Simulated dynamic VM scaling

This is a deterministic discrete-event controller built on SimPy. No real VMs
are created. It is an optional extension of the guide’s **fixed-VM model**.

## Control loop

- `scaling_enabled`: false unless explicitly set.
- `scaling_sample_interval`: monitoring period in simulated seconds (default 1).
- `scaling_up_threshold`: busy VM count / active VM count >= 0.80.
- `scaling_down_threshold`: busy VM fraction <= 0.30.
- `scaling_up_window` / `scaling_down_window`: qualifying consecutive samples.
- `scaling_cooldown`: minimum elapsed simulated seconds between adjustments.
- `scaling_min_vms` / `scaling_max_vms`: hard active-VM bounds.

Scale-out additionally requires `queued_work_mi > 0` across active VMs. A VM
is first-fit placed on a Host if the Host has sufficient cores, aggregate
MIPS and RAM. If no Host has headroom, no scaling event is recorded.

Scale-in removes only an idle VM with zero queued work, zero queued RAM, zero
resource holders and zero requests waiting; no task moves between VMs.
The controller finishes when the last task completes or fails.

## Measurements

Each scaling event captures simulated time, VM ID, Host ID, previous and new
VM count, CPU pressure and reason. CPU and RAM utilisation aggregate over
actual capacity * time, not the final VM count. Newly created/removed VMs
are retained in the historical `vmMetrics` list, with `createdAt` and
`removedAt`. This is modelled capacity, not measurement of physical machines.

## Limitations

No predictive scaling, VM boot delay, billing model, migration, host creation
or time-shared multi-task execution. The instantaneous busy fraction does not
measure actual hardware CPU use. FCFS first-eligible remains a deliberately
naive baseline. Evaluate scaling separately from fixed-capacity comparisons.
