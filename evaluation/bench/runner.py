"""Run the methods on generated datasets and expand experiment configurations into scenarios."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable

from . import generator, methods, metrics

ROW_COLUMNS = (["experiment", "config_id", "label", "rq", "seed", "method"] + list(generator.PARAMETER_NAMES)
               + ["n_groups", "detected", "spurious_groups", "tp", "fp", "fn", "negatives", "any_group", "runtime_s",
                  "trace_built", "trace_post_recall", "trace_post_precision", "trace_cohort_recall", "trace_runtime_s"])


def run_dataset(scenario: generator.Scenario, seed: int, trace: bool = False) -> list[dict[str, Any]]:
    loaded, truth = generator.generate(scenario, seed)
    seen = set().union(*(p["likers"] for p in loaded["posts"].values()))
    outputs: dict[str, tuple[list, float]] = {}
    outputs["A_overlap_only"] = methods.timed(methods.overlap_only, loaded)
    outputs["B_time_bucket"] = methods.timed(methods.time_bucket, loaded)
    v1, seconds = methods.timed(methods.v1_detector, loaded)
    outputs["C_v1"], outputs["C_v1_strong"] = (v1["C"], seconds), (v1["C_strong"], seconds)
    rows = []
    for name in methods.METHODS:
        groups, seconds = outputs[name]
        row = metrics.score_groups(groups, set(truth.coord_posts), set(truth.coord_accounts), seen)
        row.update(method=name, runtime_s=seconds, seed=seed)
        if trace and name == "C_v1":
            net, trace_seconds = methods.timed(methods.trace, loaded, v1["result"])
            built = bool(net and net.get("ok"))
            row.update(trace_built=int(built), trace_runtime_s=trace_seconds, trace_post_recall="", trace_post_precision="",
                       trace_cohort_recall="")
            if truth.coord_posts:
                found = set(net["network"]) & truth.coord_posts if built else set()
                row["trace_post_recall"] = len(found) / len(truth.coord_posts)
                if built:
                    row["trace_post_precision"] = len(found) / len(net["network"])
                    row["trace_cohort_recall"] = len(set(net["cohort"]) & truth.coord_accounts) / max(1, len(truth.coord_accounts))
        rows.append(row)
    return rows


def expand(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Experiment config -> list of {experiment, config_id, label, rq, trace, params}."""
    base = {**config.get("defaults", {}), **config.get("base", {})}
    entries = []
    for item in config.get("configs", []):
        entries.append((item["label"], {**base, **item.get("params", {})}))
    for name, values in config.get("sweep", {}).items():
        for value in values:
            entries.append((f"{name}={value}", {**base, name: value}))
            if config.get("null_too"):
                entries.append((f"{name}={value} (organic-only)", {**base, name: value, "group_size": 0}))
    out = []
    for label, params in entries:
        generator.Scenario(**params)                                    # fails early on an unknown or invalid parameter
        out.append({"experiment": config["id"], "config_id": f"{config['id']}|{label}", "label": label,
                    "rq": config.get("rq", ""), "trace": bool(config.get("trace")), "params": params})
    return out


def run_config(entry: dict[str, Any], seeds: Iterable[int]) -> list[dict[str, Any]]:
    scenario = generator.Scenario(**entry["params"])
    rows = []
    for seed in seeds:
        for row in run_dataset(scenario, seed, entry["trace"]):
            row.update({k: entry[k] for k in ("experiment", "config_id", "label", "rq")}, **asdict(scenario))
            rows.append(row)
    return rows
