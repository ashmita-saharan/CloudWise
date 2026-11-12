"""Deterministic first-fit VM placement with hard capacity constraints."""

import simpy

from cloudwise.config.schemas import ScenarioConfig, VMSpec
from cloudwise.models.datacenter import DataCenter
from cloudwise.models.host import Host
from cloudwise.models.vm import VM


def build_datacenter(env: simpy.Environment, config: ScenarioConfig) -> DataCenter:
    hosts = [
        Host(
            host_id=f"host-{index:03d}",
            cores=config.host_cores,
            mips_per_core=config.host_mips_per_core,
            ram_mb=config.host_ram_mb,
        )
        for index in range(1, config.hosts + 1)
    ]
    default_spec = VMSpec(
        pes=config.vm_pes,
        mips_per_core=config.vm_mips_per_core,
        ram_mb=config.vm_ram_mb,
    )
    specs = config.vm_specs if config.vm_specs is not None else [default_spec] * config.vms
    for index, spec in enumerate(specs, start=1):
        selected = next(
            (host for host in hosts if host.can_fit(spec.pes, spec.pes * spec.mips_per_core, spec.ram_mb)),
            None,
        )
        if selected is None:
            raise ValueError(
                f"Cannot place vm-{index:03d}: insufficient available Host CPU cores, MIPS or RAM"
            )
        selected.vms.append(
            VM(
                vm_id=f"vm-{index:03d}",
                host_id=selected.host_id,
                pes=spec.pes,
                mips_per_core=spec.mips_per_core,
                ram_mb=spec.ram_mb,
                cpu_slot=simpy.Resource(env, capacity=1),
            )
        )
    return DataCenter(hosts=hosts)
