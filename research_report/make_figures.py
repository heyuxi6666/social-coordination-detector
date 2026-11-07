"""Draw the report figure from the committed held-out results (seeds 5000-5029 only).

    python research_report/make_figures.py

Figure 1 (a): share of organic-only datasets flagged, with Wilson 95% intervals (from summary.csv).
Figure 1 (b): mean per-seed account F1 with 95% percentile-bootstrap intervals computed from raw_results.csv, so every
interval stays inside [0, 1] (mean ± 1.96 SE would cross 1 for near-perfect methods).
"""

from __future__ import annotations

import csv
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evaluation"))

import summarize_phase2 as p2  # noqa: E402
from bench import metrics, svgplot  # noqa: E402

RESULTS = ROOT / "evaluation" / "results_phase2"
OUT = Path(__file__).resolve().parent / "figures"
FLOATS = {"null_fp_rate", "null_fp_lo", "null_fp_hi"}
BOOT_REPS = 10_000


def read(name: str) -> list[dict]:
    with (RESULTS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def f1_points(raw: list[dict], experiment: str, parameter: str) -> tuple[list[str], dict]:
    per: dict = {}
    for r in raw:
        if r["experiment"] == experiment and r["method"] in p2.COMPARED and r["label"].startswith(parameter + "="):
            f1 = metrics.f1_from_counts(int(r["tp"]), int(r["fp"]), int(r["fn"]))
            per.setdefault(r["label"], {}).setdefault(r["method"], []).append(f1)
    labels = list(per)                                        # raw rows are written in configuration order
    series = {m: [] for m in p2.COMPARED}
    for label in labels:
        for m in p2.COMPARED:
            values = per[label][m]
            lo, hi = metrics.bootstrap_mean_ci(values, BOOT_REPS, zlib.crc32(f"{label}|{m}".encode("utf-8")))
            series[m].append((sum(values) / len(values), lo, hi))
    return [label.split("=", 1)[1] for label in labels], series


def main() -> int:
    summary = [{k: (float(v) if k in FLOATS and v != "" else v) for k, v in row.items()} for row in read("summary.csv")]
    labels, series = f1_points(read("raw_results.csv"), "P4_participation", "participation")
    figure = svgplot.two_panel_chart(
        [p2.panel(summary, "P6_notification_bursts", "loyal_delay_mean", "fp", "(a) Organic data with an audience burst",
                  "mean reaction delay of the audience (s)", "datasets with any flag (Wilson 95% CI)"),
         {"title": "(b) Coordinated group, partial participation", "xlabel": "share of the group acting per post",
          "ylabel": "account F1 (mean, bootstrap 95% CI)", "x_labels": labels, "series": series}],
        p2.LEGEND, "30 held-out seeds per point; synthetic data; categorical x axis; points offset by method. In (a) every flag is a false positive.")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "figure1_false_positives_vs_participation.svg").write_bytes(figure.encode("utf-8"))
    print("wrote figure1_false_positives_vs_participation.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
