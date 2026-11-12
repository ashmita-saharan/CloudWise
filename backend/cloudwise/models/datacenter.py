"""Container for hosts and their placed virtual machines."""

from dataclasses import dataclass

from .host import Host
from .vm import VM


@dataclass
class DataCenter:
    hosts: list[Host]

    @property
    def vms(self) -> list[VM]:
        return [vm for host in self.hosts for vm in host.vms]
