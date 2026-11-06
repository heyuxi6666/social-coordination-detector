"""Phase 2 tables, paired comparisons and figures from results_phase2/raw_results.csv.

    python evaluation/summarize_phase2.py [--results evaluation/results_phase2]

Writes summary.csv, paired_comparisons.csv, tables.md and figures/fig3..fig5 (SVG).  Reads only the CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import summarize as base  # noqa: E402
from bench import metrics, svgplot  # noqa: E402

COMPARED = ("A_overlap_only", "B_time_bucket", "B_tuned", "C_v1")
SHOWN = COMPARED + ("C_v1_strong",)
NAMES = {"A_overlap_only": "A overlap-only", "B_time_bucket": "B original", "B_tuned": "B tuned",
         "C_v1": "C V1 (strong+moderate)", "C_v1_strong": "C V1 (strong only)"}
LEGEND = {"A_overlap_only": "A overlap-only", "B_time_bucket": "B original", "B_tuned": "B tuned", "C_v1": "C V1 detector"}
BASELINES = ("A_overlap_only", "B_time_bucket", "B_tuned")
PAIRED_FIELDS = ["experiment", "config_id", "label", "kind", "baseline", "n_seeds", "metric", "mean_difference",
                 "ci_low", "ci_high", "verdict"]


def per_seed(rows: list[dict]) -> dict:
    out: dict = defaultdict(dict)
    for r in rows:
        key = (r["experiment"], r["config_id"], r["label"])
        coordinated = r["detected"] != ""
        value = metrics.f1_from_counts(r["tp"], r["fp"], r["fn"]) if coordinated else r["any_group"]
        out[key].setdefault(r["method"], {})[r["seed"]] = (coordinated, value)
    return out


def verdict(lo: float, hi: float, coordinated: bool) -> str:
    if lo > 0:
        return "C better" if coordinated else "C worse"       # F1: higher is better; false positives: lower is better
    if hi < 0:
        return "C worse" if coordinated else "C better"
    return "no clear difference"


def paired(rows: list[dict]) -> list[dict]:
    out = []
    for (experiment, config_id, label), methods_ in per_seed(rows).items():
        for baseline in BASELINES:
            if baseline not in methods_ or "C_v1" not in methods_:
                continue
            seeds = sorted(set(methods_["C_v1"]) & set(methods_[baseline]))
            coordinated = methods_["C_v1"][seeds[0]][0]
            diffs = [methods_["C_v1"][s][1] - methods_[baseline][s][1] for s in seeds]
            mean, se = metrics.mean_se(diffs)
            lo, hi = mean - 1.96 * se, mean + 1.96 * se
            out.append({"experiment": experiment, "config_id": config_id, "label": label,
                        "kind": "coordinated" if coordinated else "organic-only", "baseline": baseline, "n_seeds": len(seeds),
                        "metric": "account F1 (C minus baseline)" if coordinated else "any flagged group (C minus baseline)",
                        "mean_difference": mean, "ci_low": lo, "ci_high": hi, "verdict": verdict(lo, hi, coordinated)})
    return out


def write_paired(path: Path, entries: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PAIRED_FIELDS, lineterminator="\n")
        writer.writeheader()
        for e in entries:
            writer.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in e.items()})


def tables(summary: list[dict], pairs: list[dict], config: dict, info: dict, tuned: dict) -> str:
    meta = {e["id"]: e for e in config["experiments"]}
    p = tuned["parameters"]
    lines = ["# Phase 2 held-out results", "",
             f"{info['configurations']} configurations x {len(info['seeds'])} held-out seeds ({info['seeds'][0]}-{info['seeds'][-1]}), "
             f"{info['datasets']} synthetic datasets, Python {info['python']}. Synthetic data only; no claim about real platforms.", "",
             f"Tuned time-bucket baseline: bucket {p['bucket_seconds']} s, minimum group {p['min_group_accounts']} accounts, chosen on tuning seeds "
             f"{tuned['tuning_seeds'][0]}-{tuned['tuning_seeds'][1]} only (tuning score {tuned['tuning_score']} vs "
             f"{tuned['original_tuning_score']} for the original 300 s / 5). Original: 300 s / 5. V1 is unmodified.", "",
             "Columns as in `results/tables.md`; *Fragments* = unmatched groups that still contain at least two true coordinated posts; "
             "*Spurious* counts every unmatched group, fragments included.", ""]
    by_experiment: dict = defaultdict(list)
    for e in summary:
        by_experiment[e["experiment"]].append(e)
    pair_index = defaultdict(dict)
    for q in pairs:
        pair_index[q["config_id"]][q["baseline"]] = q
    for experiment, entries in by_experiment.items():
        lines += [f"## {experiment} ({meta[experiment]['rq']}): {meta[experiment]['title']}", "",
                  "| Config | Method | Detected [95% CI] | P | R | F1 (mean ± SE) | Fragments | Spurious | Organic FP [95% CI] | Acct FPR | ms |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        for e in entries:
            f1 = "–" if e.get("f1_seed_mean") in ("", None) else f"{e['f1_seed_mean']:.2f} ± {e['f1_seed_se']:.2f}"
            fpr = e.get("account_fpr") if e.get("account_fpr") not in ("", None) else e.get("null_account_fpr")
            spurious = e.get("spurious_per_dataset") if e.get("spurious_per_dataset") not in ("", None) else e.get("null_groups_per_dataset")
            lines.append(f"| {e['label']} | {NAMES[e['method']]} | {base.interval(e, 'detect_rate', 'detect_lo', 'detect_hi')} | "
                         f"{base.fmt(e.get('precision'))} | {base.fmt(e.get('recall'))} | {f1} | {base.fmt(e.get('fragments_per_dataset'))} | "
                         f"{base.fmt(spurious)} | {base.interval(e, 'null_fp_rate', 'null_fp_lo', 'null_fp_hi')} | {base.fmt(fpr, 3)} | "
                         f"{base.fmt(e['runtime_ms_median'], 1)} |")
        traced = [e for e in entries if e["method"] == "C_v1" and e.get("trace_built_rate") not in ("", None)]
        if traced:
            lines += ["", "V1 network tracer (from V1's first fixed-offset group):", "",
                      "| Config | Tracer built | Coordinated posts recovered | Traced posts that are coordinated |", "|---|---|---|---|"]
            lines += [f"| {e['label']} | {base.fmt(e['trace_built_rate'])} | {base.fmt(e['trace_post_recall'])} | {base.fmt(e['trace_post_precision'])} |"
                      for e in traced]
        configs = list(dict.fromkeys(e["config_id"] for e in entries))
        lines += ["", "Paired per-seed difference, V1 minus baseline (coordinated: account F1, positive favours V1; organic-only: share of datasets with a flagged group, negative favours V1). Mean [95% CI]:", "",
                  "| Config | vs A overlap-only | vs B original | vs B tuned |", "|---|---|---|---|"]
        for cid in configs:
            cells = []
            for b in BASELINES:
                q = pair_index[cid].get(b)
                cells.append("–" if not q else f"{q['mean_difference']:+.2f} [{q['ci_low']:+.2f}, {q['ci_high']:+.2f}] {q['verdict']}")
            lines.append(f"| {cid.split('|', 1)[1]} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## Scoreboard: number of configurations by paired verdict (V1 vs each baseline)", "",
              "| Experiment | Baseline | V1 better | V1 worse | No clear difference |", "|---|---|---|---|---|"]
    for experiment in by_experiment:
        for b in BASELINES:
            c = [q["verdict"] for q in pairs if q["experiment"] == experiment and q["baseline"] == b]
            lines.append(f"| {experiment} | {NAMES[b]} | {c.count('C better')} | {c.count('C worse')} | {c.count('no clear difference')} |")
    total = defaultdict(lambda: [0, 0, 0])
    for q in pairs:
        total[q["baseline"]][["C better", "C worse", "no clear difference"].index(q["verdict"])] += 1
    for b in BASELINES:
        lines.append(f"| **all** | {NAMES[b]} | {total[b][0]} | {total[b][1]} | {total[b][2]} |")
    lines.append("")
    return "\n".join(lines)


def series(summary: list[dict], experiment: str, parameter: str, kind: str):
    out, labels = {}, []
    for method in COMPARED:
        xs, pts = [], []
        for e in summary:
            if e["experiment"] != experiment or e["method"] != method or "(organic-only)" in e["label"] or not e["label"].startswith(parameter + "="):
                continue
            xs.append(e["label"].split("=", 1)[1])
            if kind == "f1":
                m, se = e["f1_seed_mean"], 1.96 * e["f1_seed_se"]
                pts.append((m, max(0.0, m - se), min(1.0, m + se)))
            elif kind == "detect":
                pts.append((e["detect_rate"], e["detect_lo"], e["detect_hi"]))
            else:
                pts.append((e["null_fp_rate"], e["null_fp_lo"], e["null_fp_hi"]))
        labels, out[method] = xs, pts
    return out, labels


def panel(summary, experiment, parameter, kind, title, xlabel, ylabel):
    data, labels = series(summary, experiment, parameter, kind)
    return {"title": title, "xlabel": xlabel, "ylabel": ylabel, "x_labels": labels, "series": data}


def figures(summary: list[dict], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    f1 = "account F1 (mean, 95% CI)"
    charts = {
        "fig3_cohort_spread_and_random_delays.svg": svgplot.two_panel_chart(
            [panel(summary, "P2_cohort_spread", "cohort_spread", "f1", "(a) Fixed per-account delays", "cohort spread (s)", f1),
             panel(summary, "P3_random_delays", "cohort_spread", "f1", "(b) Independent random delays", "delay range (s)", f1)],
            LEGEND, "Figure 3. 30 held-out seeds per point; synthetic data; categorical x axis; points offset horizontally by method."),
        "fig4_notification_bursts_and_participation.svg": svgplot.two_panel_chart(
            [panel(summary, "P6_notification_bursts", "loyal_delay_mean", "fp", "(a) Notification bursts, organic data", "mean delay of the audience (s)", "datasets with a flagged group (95% CI)"),
             panel(summary, "P4_participation", "participation", "f1", "(b) Partial participation", "share of group acting per post", f1)],
            LEGEND, "Figure 4. 30 held-out seeds; synthetic; categorical x axis; points offset by method. In (a) every flag is a false positive."),
        "fig5_rotation_and_jitter.svg": svgplot.two_panel_chart(
            [panel(summary, "P5_rotation", "rotation", "f1", "(a) Account rotation", "slot replacement probability", f1),
             panel(summary, "P8_jitter", "jitter", "f1", "(b) Timing jitter", "jitter sd per like (s)", f1)],
            LEGEND, "Figure 5. 30 held-out seeds per point; synthetic data; categorical x axis; points offset horizontally by method."),
    }
    paths = []
    for name, text in charts.items():
        (out_dir / name).write_bytes(text.encode("utf-8"))
        paths.append(out_dir / name)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarise Phase 2 held-out results")
    parser.add_argument("--results", type=Path, default=HERE / "results_phase2")
    parser.add_argument("--config", type=Path, default=HERE / "configs" / "phase2.json")
    args = parser.parse_args(argv)
    rows = base.read_rows(args.results / "raw_results.csv")
    summary = base.summarise_all(rows)
    base.write_summary(args.results / "summary.csv", summary)
    pairs = paired(rows)
    write_paired(args.results / "paired_comparisons.csv", pairs)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    info = json.loads((args.results / "run_info.json").read_text(encoding="utf-8"))
    tuned = json.loads((args.results / "tuned_parameters.json").read_text(encoding="utf-8"))
    (args.results / "tables.md").write_bytes((tables(summary, pairs, config, info, tuned) + "\n").encode("utf-8"))
    paths = figures(summary, args.results / "figures")
    print(f"summarised {len(rows)} rows -> summary.csv, paired_comparisons.csv, tables.md, {len(paths)} figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
