"""Run directly: python -m cloudwise.cli --scenario ../scenarios/light.json."""

import argparse
import json
from pathlib import Path

from cloudwise.config.schemas import ScenarioConfig
from cloudwise.output.result_writer import save_comparison, save_run
from cloudwise.simulation.runner import run_comparison, run_simulation


def main() -> None:
    parser = argparse.ArgumentParser(description="CloudWise simulation runner")
    parser.add_argument("--scenario", type=Path, help="Scenario JSON file")
    parser.add_argument("--algorithm", choices=("FCFS", "RR", "AWLB"), help="Override the scenario policy")
    parser.add_argument("--compare", action="store_true", help="Use identical tasks for all three policies")
    parser.add_argument("--output", type=Path, default=Path("../results/raw"), help="Output directory")
    args = parser.parse_args()

    raw = json.loads(args.scenario.read_text(encoding="utf-8")) if args.scenario else {}
    if args.algorithm:
        raw["algorithm"] = args.algorithm
    config = ScenarioConfig.model_validate(raw)
    if args.compare:
        result = run_comparison(config)
        path = save_comparison(result, args.output)
        for policy, run in result["results"].items():
            print(f"{policy}: completed={run['summary']['completedTasks']}, "
                  f"avg_wait={run['summary']['averageWaitingTime']:.3f}s")
            save_run(run, args.output)
        print(f"Comparison exported: {path}")
    else:
        result = run_simulation(config)
        for path in save_run(result, args.output):
            print(f"Exported: {path}")
        print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
