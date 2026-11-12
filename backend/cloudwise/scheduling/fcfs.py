"""FCFS baseline: earliest arrival first, first eligible VM in fixed order."""

from .base import SchedulingPolicy
from cloudwise.models.task import CloudTask
from cloudwise.models.vm import VM


class FCFSPolicy(SchedulingPolicy):
    name = "FCFS"

    def select_vm(self, task: CloudTask, vms: list[VM]) -> tuple[VM | None, dict[str, float]]:
        return next((vm for vm in vms if self.eligible(task, vm)), None), {}
