"""Single-server (space-shared) virtual machine and event-based accounting."""

from dataclasses import dataclass, field

import simpy


@dataclass
class VM:
    vm_id: str
    host_id: str
    pes: int
    mips_per_core: float
    ram_mb: int
    cpu_slot: simpy.Resource = field(repr=False)
    created_at: float = 0.0
    removed_at: float | None = None
    queued_work_mi: int = 0
    queued_ram_mb: int = 0
    ram_in_use_mb: int = 0
    active_task_id: str | None = None
    assigned_tasks: int = 0
    completed_tasks: int = 0
    busy_time: float = 0.0
    ram_mb_seconds: float = 0.0
    _accounted_until: float = field(default=0.0, repr=False)

    @property
    def total_mips(self) -> float:
        return self.pes * self.mips_per_core

    def account_until(self, now: float) -> None:
        """Integrate resource use over time before a state change."""
        delta = now - self._accounted_until
        if delta < -1e-9:
            raise ValueError("Simulation clock moved backwards")
        if self.active_task_id is not None:
            self.busy_time += max(0.0, delta)
        self.ram_mb_seconds += self.ram_in_use_mb * max(0.0, delta)
        self._accounted_until = now
