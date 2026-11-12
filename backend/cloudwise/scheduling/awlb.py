"""Adaptive Weighted Load Balancing (heuristic, not machine learning)."""

from cloudwise.config.schemas import ScenarioConfig
from cloudwise.models.task import CloudTask
from cloudwise.models.vm import VM

from .base import SchedulingPolicy


def clamp_01(value: float) -> float:
    return max(0.0, min(1.0, value))


class AWLBPolicy(SchedulingPolicy):
    name = "AWLB"

    def __init__(self, config: ScenarioConfig) -> None:
        self.config = config

    def select_vm(self, task: CloudTask, vms: list[VM]) -> tuple[VM | None, dict[str, float]]:
        eligible = [vm for vm in vms if self.eligible(task, vm)]
        if not eligible:
            return None, {}
        scores = {}
        for vm in eligible:
            # Space-shared model: the one execution slot is either idle or fully busy.
            cpu_norm = 1.0 if vm.active_task_id is not None else 0.0
            ram_norm = clamp_01(vm.ram_in_use_mb / vm.ram_mb)
            queue_norm = clamp_01(vm.queued_work_mi / self.config.queue_reference_mi)
            scores[vm.vm_id] = (
                self.config.awlb_cpu_weight * cpu_norm
                + self.config.awlb_ram_weight * ram_norm
                + self.config.awlb_queue_weight * queue_norm
            )
        selected = min(eligible, key=lambda vm: (scores[vm.vm_id], vm.queued_work_mi, vm.vm_id))
        return selected, scores
