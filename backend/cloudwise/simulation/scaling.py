"""Optional, deterministic simulated VM auto-scaler (no real cloud provisioning).

CPU pressure is the instantaneous busy/active-VM ratio. It is evaluated at
fixed simulation-time intervals and uses consecutive qualifying samples.
Scale-out also requires pending work, to avoid creating idle capacity solely
because a single VM is busy. All actions respect Host first-fit constraints.
"""

import simpy

from cloudwise.config.schemas import ScenarioConfig
from cloudwise.models.datacenter import DataCenter
from cloudwise.models.vm import VM
from cloudwise.simulation.broker import Broker


class ScalingController:
    def __init__(self, env: simpy.Environment, datacenter: DataCenter,
                 broker: Broker, config: ScenarioConfig, stop_event: simpy.Event):
        self.env = env
        self.datacenter = datacenter
        self.broker = broker
        self.config = config
        self.stop_event = stop_event
        self.all_vms = list(datacenter.vms)
        self.next_vm_number = len(self.all_vms) + 1
        self.events: list[dict] = []
        self.high_samples = 0
        self.low_samples = 0
        self.last_action_time = float('-inf')

    def record(self, action: str, vm: VM, before: int, pressure: float, reason: str) -> None:
        self.events.append({
            "time": self.env.now, "action": action,
            "vmId": vm.vm_id, "hostId": vm.host_id,
            "previousCapacityVms": before, "newCapacityVms": len(self.datacenter.vms),
            "cpuBusyFraction": pressure, "reason": reason,
        })
        self.last_action_time = self.env.now
        self.high_samples = self.low_samples = 0

    def scale_out(self, pressure: float) -> bool:
        if len(self.datacenter.vms) >= self.config.scaling_max_vms:
            return False
        pes = self.config.vm_pes
        mips = pes * self.config.vm_mips_per_core
        host = next((h for h in self.datacenter.hosts
                     if h.can_fit(pes, mips, self.config.vm_ram_mb)), None)
        if host is None:
            return False
        before = len(self.datacenter.vms)
        vm = VM(vm_id=f"vm-{self.next_vm_number:03d}", host_id=host.host_id,
                pes=pes, mips_per_core=self.config.vm_mips_per_core,
                ram_mb=self.config.vm_ram_mb,
                cpu_slot=simpy.Resource(self.env, capacity=1), created_at=self.env.now)
        self.next_vm_number += 1
        host.vms.append(vm)
        self.broker.vms.append(vm)
        self.broker.vms.sort(key=lambda machine: machine.vm_id)
        self.all_vms.append(vm)
        self.record("SCALE_OUT", vm, before, pressure,
                    "Sustained CPU pressure with queued work; Host capacity available")
        return True

    def scale_in(self, pressure: float) -> bool:
        if len(self.datacenter.vms) <= self.config.scaling_min_vms:
            return False
        # Never remove a running, queued or reserved VM. Use newest idle first.
        candidates = [vm for vm in self.broker.vms
                      if vm.active_task_id is None and vm.queued_work_mi == 0
                      and vm.queued_ram_mb == 0 and vm.cpu_slot.count == 0
                      and len(vm.cpu_slot.queue) == 0]
        if not candidates:
            return False
        vm = max(candidates, key=lambda machine: machine.vm_id)
        before = len(self.datacenter.vms)
        vm.account_until(self.env.now)
        vm.removed_at = self.env.now
        self.broker.vms.remove(vm)
        host = next(host for host in self.datacenter.hosts if host.host_id == vm.host_id)
        host.vms.remove(vm)
        self.record("SCALE_IN", vm, before, pressure,
                    "Sustained low CPU pressure; idle VM removed")
        return True

    def run(self):
        while True:
            tick = self.env.timeout(self.config.scaling_sample_interval)
            yield self.env.any_of([tick, self.stop_event])
            if self.stop_event.triggered:
                return
            vms = self.broker.vms
            if not vms:
                return
            busy = sum(vm.active_task_id is not None for vm in vms)
            pressure = busy / len(vms)
            pending = sum(vm.queued_work_mi for vm in vms)
            if pressure >= self.config.scaling_up_threshold and pending > 0:
                self.high_samples += 1
            else:
                self.high_samples = 0
            if pressure <= self.config.scaling_down_threshold:
                self.low_samples += 1
            else:
                self.low_samples = 0
            if self.env.now - self.last_action_time < self.config.scaling_cooldown:
                continue
            if self.high_samples >= self.config.scaling_up_window:
                self.scale_out(pressure)
            elif self.low_samples >= self.config.scaling_down_window:
                self.scale_in(pressure)
