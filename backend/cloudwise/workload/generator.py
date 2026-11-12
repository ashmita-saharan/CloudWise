"""Independent seeded RNG: exact same workload for fair policy comparisons."""

import random

from cloudwise.config.schemas import ScenarioConfig
from cloudwise.models.task import CloudTask


def generate_workload(config: ScenarioConfig) -> list[CloudTask]:
    rng = random.Random(config.seed)
    tasks = [
        CloudTask(
            task_id=f"task-{index:05d}",
            arrival_time=round(rng.uniform(0, config.arrival_window), 6),
            length_mi=rng.randint(config.task_length_mi_min, config.task_length_mi_max),
            required_ram_mb=rng.randint(config.task_ram_mb_min, config.task_ram_mb_max),
            required_pes=rng.randint(1, config.task_required_pes_max),
        )
        for index in range(1, config.tasks + 1)
    ]
    # The task ID provides stable ordering when several tasks share one timestamp.
    return sorted(tasks, key=lambda task: (task.arrival_time, task.task_id))
