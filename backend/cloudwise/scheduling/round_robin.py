"""Round Robin: persistent cursor, skips ineligible VMs."""

from .base import SchedulingPolicy
from cloudwise.models.task import CloudTask
from cloudwise.models.vm import VM


class RoundRobinPolicy(SchedulingPolicy):
    name = "RR"

    def __init__(self) -> None:
        self._next_index = 0

    def select_vm(self, task: CloudTask, vms: list[VM]) -> tuple[VM | None, dict[str, float]]:
        if not vms:
            return None, {}
        for offset in range(len(vms)):
            index = (self._next_index + offset) % len(vms)
            if self.eligible(task, vms[index]):
                self._next_index = (index + 1) % len(vms)
                return vms[index], {}
        return None, {}
