"""Run the benchmark and write results/raw_results.csv (one row per dataset x method).

    python evaluation/run_experiments.py                    # full grid, 20 seeds per configuration
    python evaluation/run_experiments.py --seeds 3 --only E1_jitter --out /tmp/quick

Everything is synthetic and deterministic: the same configuration and seeds give the same metric columns.
`runtime_s` and `trace_runtime_s` are wall-clock measurements and vary between runs.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bench import runner  # noqa: E402


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=runner.ROW_COLUMNS, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in row.items()})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the coordination-detection benchmark")
    parser.add_argument("--config", type=Path, default=HERE / "configs" / "experiments.json")
    parser.add_argument("--out", type=Path, default=HERE / "results")
    parser.add_argument("--seeds", type=int, help="override the number of seeds per configuration")
    parser.add_argument("--only", nargs="*", default=[], metavar="EXPERIMENT_ID")
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    n_seeds = args.seeds or config["seeds"]
    seeds = [config["base_seed"] + i for i in range(n_seeds)]
    entries = []
    for experiment in config["experiments"]:
        if not args.only or experiment["id"] in args.only:
            entries += runner.expand({**experiment, "defaults": config.get("defaults", {})})
    rows = []
    for number, entry in enumerate(entries, 1):
        rows += runner.run_config(entry, seeds)
        print(f"[{number}/{len(entries)}] {entry['config_id']}", flush=True)
    args.out.mkdir(parents=True, exist_ok=True)
    write_rows(args.out / "raw_results.csv", rows)
    meta = {"python": platform.python_version(), "platform": platform.platform(), "seeds": seeds,
            "configurations": len(entries), "datasets": len(entries) * len(seeds), "rows": len(rows),
            "config_file": args.config.name}
    (args.out / "run_info.json").write_bytes((json.dumps(meta, indent=2) + "\n").encode("utf-8"))
    print(f"wrote {len(rows)} rows for {meta['datasets']} datasets to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
