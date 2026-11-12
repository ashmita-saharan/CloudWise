"""Common task-admission rule and policy interface."""

from abc import ABC, abstractmethod

from cloudwise.models.task import CloudTask
from cloudwise.models.vm import VM


class SchedulingPolicy(ABC):
    name: str

    @staticmethod
    def eligible(task: CloudTask, vm: VM) -> bool:
        return task.required_pes <= vm.pes and task.required_ram_mb <= vm.ram_mb

    @abstractmethod
    def select_vm(self, task: CloudTask, vms: list[VM]) -> tuple[VM | None, dict[str, float]]:
        """Choose an eligible VM and return optional per-candidate AWLB scores."""
