"""Validated, reproducible scenario definitions (all memory quantities in MB)."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class VMSpec(BaseModel):
    """A requested VM size, used to create heterogeneous scenarios."""

    pes: int = Field(default=2, gt=0)
    mips_per_core: float = Field(default=1_000.0, gt=0)
    ram_mb: int = Field(default=4_096, gt=0)


class ScenarioConfig(BaseModel):
    name: str = Field(default="custom", min_length=1, max_length=80)
    hosts: int = Field(default=3, ge=1, le=200)
    vms: int = Field(default=6, ge=1, le=1_000)
    tasks: int = Field(default=100, ge=0, le=100_000)
    seed: int = 42
    algorithm: Literal["FCFS", "RR", "AWLB"] = "AWLB"

    host_cores: int = Field(default=8, gt=0)
    host_mips_per_core: float = Field(default=2_000.0, gt=0)
    host_ram_mb: int = Field(default=16_384, gt=0)
    vm_pes: int = Field(default=2, gt=0)
    vm_mips_per_core: float = Field(default=1_000.0, gt=0)
    vm_ram_mb: int = Field(default=4_096, gt=0)
    vm_specs: list[VMSpec] | None = None

    arrival_window: float = Field(default=30.0, ge=0)
    task_length_mi_min: int = Field(default=1_000, gt=0)
    task_length_mi_max: int = Field(default=12_000, gt=0)
    task_ram_mb_min: int = Field(default=256, gt=0)
    task_ram_mb_max: int = Field(default=2_048, gt=0)
    task_required_pes_max: int = Field(default=1, gt=0)

    queue_reference_mi: float = Field(default=12_000.0, gt=0)
    awlb_cpu_weight: float = Field(default=0.50, ge=0)
    awlb_ram_weight: float = Field(default=0.30, ge=0)
    awlb_queue_weight: float = Field(default=0.20, ge=0)

    @model_validator(mode="after")
    def check_ranges_and_weights(self) -> "ScenarioConfig":
        if self.task_length_mi_min > self.task_length_mi_max:
            raise ValueError("task_length_mi_min must be <= task_length_mi_max")
        if self.task_ram_mb_min > self.task_ram_mb_max:
            raise ValueError("task_ram_mb_min must be <= task_ram_mb_max")
        if self.vm_specs is not None and len(self.vm_specs) != self.vms:
            raise ValueError("vm_specs must have exactly vms entries")
        weights = self.awlb_cpu_weight + self.awlb_ram_weight + self.awlb_queue_weight
        if abs(weights - 1.0) > 1e-9:
            raise ValueError("AWLB weights must sum to 1")
        return self
