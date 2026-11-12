"""Audit log for every scheduling decision, including failed admission."""

from dataclasses import dataclass, field

from cloudwise.models.task import CloudTask
from cloudwise.models.vm import VM


@dataclass
class AllocationLogger:
    records: list[dict] = field(default_factory=list)

    def record(self, time: float, policy: str, task: CloudTask, vm: VM | None,
               scores: dict[str, float]) -> None:
        self.records.append({
            "time": round(time, 6),
            "taskId": task.task_id,
            "policy": policy,
            "chosenVmId": vm.vm_id if vm is not None else None,
            "candidateScores": {key: round(value, 6) for key, value in scores.items()},
            "reason": task.failure_reason if vm is None else None,
        })
