"""Choose the time-bucket baseline's parameters on TUNING seeds only.

    python evaluation/tune_baseline.py [--out evaluation/results_phase2]

Writes tuning_grid.csv (every grid cell, every scenario) and tuned_parameters.json.  Only methods.time_bucket is
evaluated; the V1 detector and the overlap baseline are not tuned.  Held-out seeds are never touched here
(a guard refuses overlapping seed ranges); see PHASE2_PROTOCOL.md.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bench import generator, methods, metrics  # noqa: E402

HELD_OUT_RANGE = range(5000, 5100)
PHASE1_RANGE = range(1000, 1100)


def scenario_scores(loaded_sets, bucket: int, minimum: int) -> dict:
    f1s, flags = [], []
    for loaded, truth in loaded_sets:
        groups = methods.time_bucket(loaded, bucket, minimum)
        if truth.coord_accounts:
            predicted = set().union(*(g["accounts"] for g in groups)) if groups else set()
            f1s.append(metrics.f1_from_counts(*metrics.prf_counts(predicted, set(truth.coord_accounts))))
        else:
            flags.append(1 if groups else 0)
    return {"f1": statistics.fmean(f1s) if f1s else None, "false_positive_rate": statistics.fmean(flags) if flags else None}


def tune(config: dict) -> tuple[list[dict], dict]:
    seeds = [config["base_seed"] + i for i in range(config["seeds"])]
    if set(seeds) & (set(HELD_OUT_RANGE) | set(PHASE1_RANGE)):
        raise SystemExit("tuning seeds overlap the held-out or Phase 1 seed range")
    data = []
    for scenario in config["scenarios"]:
        params = generator.Scenario(**scenario["params"])
        data.append((scenario["label"], [generator.generate(params, s) for s in seeds]))
    rows = []
    for bucket, minimum in itertools.product(config["grid"]["bucket_seconds"], config["grid"]["min_group_accounts"]):
        per_scenario = {label: scenario_scores(sets, bucket, minimum) for label, sets in data}
        coordinated = [v["f1"] for v in per_scenario.values() if v["f1"] is not None]
        negative = [v["false_positive_rate"] for v in per_scenario.values() if v["false_positive_rate"] is not None]
        mean_f1, mean_fp = statistics.fmean(coordinated), statistics.fmean(negative)
        rows.append({"bucket_seconds": bucket, "min_group_accounts": minimum, "mean_f1": mean_f1,
                     "mean_false_positive_rate": mean_fp, "score": mean_f1 - mean_fp,
                     **{f"scenario: {label}": (v["f1"] if v["f1"] is not None else v["false_positive_rate"])
                        for label, v in per_scenario.items()}})
    best = sorted(rows, key=lambda r: (-round(r["score"], 12), r["bucket_seconds"], r["min_group_accounts"]))[0]
    result = {"parameters": {"bucket_seconds": best["bucket_seconds"], "min_group_accounts": best["min_group_accounts"]},
              "tuning_score": round(best["score"], 4), "tuning_mean_f1": round(best["mean_f1"], 4),
              "tuning_mean_false_positive_rate": round(best["mean_false_positive_rate"], 4),
              "original_parameters": {"bucket_seconds": methods.BUCKET_SECONDS, "min_group_accounts": methods.MIN_GROUP_ACCOUNTS},
              "original_tuning_score": round(next(r["score"] for r in rows if r["bucket_seconds"] == methods.BUCKET_SECONDS
                                                  and r["min_group_accounts"] == methods.MIN_GROUP_ACCOUNTS), 4)
              if any(r["bucket_seconds"] == methods.BUCKET_SECONDS and r["min_group_accounts"] == methods.MIN_GROUP_ACCOUNTS for r in rows) else None,
              "tuning_seeds": [seeds[0], seeds[-1]], "scenarios": len(config["scenarios"]), "grid_cells": len(rows),
              "objective": "mean coordinated-scenario F1 minus mean organic-scenario false-positive rate"}
    return rows, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tune the time-bucket baseline on tuning seeds")
    parser.add_argument("--config", type=Path, default=HERE / "configs" / "tuning.json")
    parser.add_argument("--out", type=Path, default=HERE / "results_phase2")
    args = parser.parse_args(argv)
    rows, result = tune(json.loads(args.config.read_text(encoding="utf-8")))
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "tuning_grid.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in row.items()})
    (args.out / "tuned_parameters.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
