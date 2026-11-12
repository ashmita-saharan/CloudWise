"""A simulated workload unit, measured in MI, MB and simulated seconds."""

from dataclasses import dataclass


@dataclass
class CloudTask:
    task_id: str
    arrival_time: float
    length_mi: int
    required_ram_mb: int
    required_pes: int = 1
    status: str = "PENDING"
    assigned_vm_id: str | None = None
    start_time: float | None = None
    finish_time: float | None = None
    failure_reason: str | None = None
