"""Draw the two report figures from evaluation/results_phase2/summary.csv (held-out seeds only).

    python research_report/make_figures.py

Reads only the committed summary; draws with the evaluation's own dependency-free SVG plotter.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evaluation"))

import summarize_phase2 as p2  # noqa: E402
from bench import svgplot  # noqa: E402

SUMMARY = ROOT / "evaluation" / "results_phase2" / "summary.csv"
OUT = Path(__file__).resolve().parent / "figures"
FLOATS = {"detect_rate", "detect_lo", "detect_hi", "f1_seed_mean", "f1_seed_se", "null_fp_rate", "null_fp_lo", "null_fp_hi"}


def load() -> list[dict]:
    with SUMMARY.open(encoding="utf-8", newline="") as handle:
        return [{k: (float(v) if k in FLOATS and v != "" else v) for k, v in row.items()} for row in csv.DictReader(handle)]


def main() -> int:
    summary = load()
    f1 = "account F1 (mean, 95% CI)"
    figures = {
        "figure1_false_positives_vs_participation.svg": svgplot.two_panel_chart(
            [p2.panel(summary, "P6_notification_bursts", "loyal_delay_mean", "fp", "(a) Organic data with an audience burst",
                      "mean reaction delay of the audience (s)", "datasets with any flag (95% CI)"),
             p2.panel(summary, "P4_participation", "participation", "f1", "(b) Coordinated group, partial participation",
                      "share of the group acting per post", f1)],
            p2.LEGEND, "30 held-out seeds per point; synthetic data; categorical x axis; points offset by method. In (a) every flag is a false positive."),
        "figure2_failure_modes.svg": svgplot.two_panel_chart(
            [p2.panel(summary, "P3_random_delays", "cohort_spread", "f1", "(a) Independently random delays",
                      "range of the random delay (s)", f1),
             p2.panel(summary, "P8_jitter", "jitter", "f1", "(b) Fixed delays with timing jitter",
                      "jitter, Gaussian sd per like (s)", f1)],
            p2.LEGEND, "30 held-out seeds per point; synthetic data; categorical x axis; points offset horizontally by method."),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in figures.items():
        (OUT / name).write_bytes(text.encode("utf-8"))
        print(f"wrote {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
