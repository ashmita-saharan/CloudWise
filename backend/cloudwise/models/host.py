"""Physical host model; VM placement reserves cores, throughput and RAM."""

from dataclasses import dataclass, field

from .vm import VM


@dataclass
class Host:
    host_id: str
    cores: int
    mips_per_core: float
    ram_mb: int
    vms: list[VM] = field(default_factory=list)

    @property
    def total_mips(self) -> float:
        return self.cores * self.mips_per_core

    def can_fit(self, pes: int, total_mips: float, ram_mb: int) -> bool:
        return (
            sum(vm.pes for vm in self.vms) + pes <= self.cores
            and sum(vm.total_mips for vm in self.vms) + total_mips <= self.total_mips
            and sum(vm.ram_mb for vm in self.vms) + ram_mb <= self.ram_mb
        )
