"""CLI: python -m cloudwise.benchmark --seeds 11 42 73."""
import argparse
import json
from pathlib import Path

from cloudwise.config.schemas import ScenarioConfig
from cloudwise.experiments import run_experiments, save_experiment_report


def main() -> None:
    parser = argparse.ArgumentParser(description="CloudWise repeatable multi-seed benchmark")
    parser.add_argument("--scenarios", nargs="+", type=Path,
                        default=[Path("../scenarios/light.json"), Path("../scenarios/medium.json"),
                                 Path("../scenarios/heavy.json"), Path("../scenarios/heterogeneous.json")])
    parser.add_argument("--seeds", nargs="+", type=int, default=[11, 42, 73])
    parser.add_argument("--output", type=Path, default=Path("../results/reports"))
    args = parser.parse_args()
    scenarios = [ScenarioConfig.model_validate(json.loads(path.read_text(encoding="utf-8")))
                 for path in args.scenarios]
    report = run_experiments(scenarios, args.seeds)
    for path in save_experiment_report(report, args.output):
        print(f"Exported: {path}")
    print(f"Finished {len(report['runs'])} policy runs across {len(scenarios)} scenarios and {len(args.seeds)} seeds")


if __name__ == "__main__":
    main()
