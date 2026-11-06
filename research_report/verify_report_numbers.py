"""Check every quantitative claim in mini_research_report.md against the committed Phase 2 results.

    python research_report/verify_report_numbers.py

Each check recomputes a value from evaluation/results_phase2/ (summary.csv, paired_comparisons.csv, raw_results.csv,
run_info.json, tuned_parameters.json), formats it as the report does, and confirms that the exact text appears in the
report. Every two-decimal number in the report must also be covered by at least one check. Exit code 0 = all pass.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "evaluation"))
from bench import metrics  # noqa: E402

RES = ROOT / "evaluation" / "results_phase2"
REPORT = (HERE / "mini_research_report.md").read_text(encoding="utf-8")
METHODS = ("A_overlap_only", "B_time_bucket", "B_tuned", "C_v1")


def rows(name: str) -> list[dict]:
    with (RES / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


SUMMARY = {(r["config_id"], r["method"]): r for r in rows("summary.csv")}
PAIRED = {(r["config_id"], r["baseline"]): r for r in rows("paired_comparisons.csv")}
RAW = rows("raw_results.csv")
INFO = json.loads((RES / "run_info.json").read_text(encoding="utf-8"))
TUNED = json.loads((RES / "tuned_parameters.json").read_text(encoding="utf-8"))
failures: list[str] = []
covered: set[str] = set()


def f2(x) -> str:
    return f"{float(x):.2f}"


def get(config: str, method: str, field: str) -> float:
    return float(SUMMARY[(config, method)][field])


def check(text: str, condition: bool = True, note: str = "") -> None:
    covered.update(re.findall(r"\d+\.\d{2}", text))
    if text not in REPORT:
        failures.append(f"text not found in report: {text!r} {note}")
    elif not condition:
        failures.append(f"value check failed: {text!r} {note}")


def ci(config: str, method: str, prefix: str) -> str:
    return f"{f2(get(config, method, prefix + '_rate'))} [{f2(get(config, method, prefix + '_lo'))}, {f2(get(config, method, prefix + '_hi'))}]"


def f1se(config: str, method: str) -> str:
    return f"{f2(get(config, method, 'f1_seed_mean'))} ± {f2(get(config, method, 'f1_seed_se'))}"


def diff(config: str, baseline: str = "B_tuned") -> str:
    q = PAIRED[(config, baseline)]
    s = lambda v: f"{float(v):+.2f}".replace("-", "−")
    return f"{s(q['mean_difference'])} [{s(q['ci_low'])}, {s(q['ci_high'])}]"


# ---- scale and splits
check(f"{INFO['datasets']:,} held-out datasets ({INFO['configurations']} configurations × {len(INFO['seeds'])} seeds)")
check(f"seeds {INFO['seeds'][0]}–{INFO['seeds'][-1]}")
check(f"Tuning seeds {TUNED['tuning_seeds'][0]}–{TUNED['tuning_seeds'][1]}")
check(f"over {TUNED['grid_cells']} cells")
check(f"{TUNED['scenarios']} scenarios (7 coordinated, 4 negative)")
check(f"w = {TUNED['parameters']['bucket_seconds']:,} s, m = {TUNED['parameters']['min_group_accounts']}")
check(f"score {TUNED['tuning_score']:.3f}, against {TUNED['original_tuning_score']:.3f} for the original setting")
tuning = json.loads((ROOT / "evaluation" / "configs" / "tuning.json").read_text(encoding="utf-8"))
check(f"w = {min(tuning['grid']['bucket_seconds'])}–{max(tuning['grid']['bucket_seconds']):,} s, m = "
      f"{min(tuning['grid']['min_group_accounts'])}–{max(tuning['grid']['min_group_accounts'])}")
check("7 coordinated, 4 negative", sum(1 for s in tuning["scenarios"] if s["params"].get("group_size", 1) != 0) == 7)

# ---- organic-only aggregates
organic = [r for r in RAW if r["detected"] == ""]
def flagged(method, keep=lambda c: True):
    rs = [r for r in organic if r["method"] == method and keep(r["config_id"])]
    return sum(int(r["any_group"]) for r in rs), len(rs)
k, n = flagged("C_v1")
check(f"none of {n} organic-only held-out datasets", k == 0)
check(f"Wilson upper bound {metrics.wilson(k, n)[1]:.3f}")
audience = lambda c: "loyal" in c or "burst" in c or c.startswith("P6")
pure = lambda c: not audience(c)
check(f"plain organic and heavy-user data ({flagged('C_v1', pure)[1]} datasets) every method was nearly clean, and A flagged {flagged('A_overlap_only', pure)[0]}",
      all(flagged(m, pure)[0] == 0 for m in ("B_time_bucket", "B_tuned", "C_v1")))
check(f"follower-audience data ({flagged('C_v1', audience)[1]} datasets), A flagged {flagged('A_overlap_only', audience)[0]}, "
      f"original B {flagged('B_time_bucket', audience)[0]}, tuned B {flagged('B_tuned', audience)[0]}, and V1 none", flagged("C_v1", audience)[0] == 0)

# ---- audience bursts
P6 = "P6_notification_bursts|loyal_delay_mean="
fast = all(get(P6 + d, m, "null_fp_rate") == 1 for d in ("15", "45", "120") for m in ("B_time_bucket", "B_tuned"))
check("flag every audience reacting with a mean delay of 120 s or less", fast and get(P6 + "300", "B_time_bucket", "null_fp_rate") < 1)
check("delay of 120 s or less", fast)
check(f"tuned B flagged {f2(get(P6 + '300', 'B_tuned', 'null_fp_rate'))} of datasets at 300 s and {f2(get(P6 + '900', 'B_tuned', 'null_fp_rate'))} at 900 s")

# ---- headline (Table 1)
H = "P1_headline|"
check("detected the group in all 30 datasets", all(get(H + "coordinated", m, "detect_rate") == 1 for m in METHODS))
check(f"A absorbed it (F1 {f2(get(H + 'coordinated + loyal followers', 'A_overlap_only', 'f1_seed_mean'))})")
check("| Coordinated group | " + " | ".join(f2(get(H + "coordinated", m, "f1_seed_mean")) for m in METHODS) + " |")
check("| Coordinated + loyal audience | " + " | ".join(f2(get(H + "coordinated + loyal followers", m, "f1_seed_mean")) for m in METHODS) + " |")
check(f"| Coordinated, V1 *strong* tier only | – | – | – | {f2(get(H + 'coordinated', 'C_v1_strong', 'f1_seed_mean'))} |")
for label, row in (("organic-only", "Organic only"), ("organic + loyal followers", "Loyal audience (mean delay 1,800 s)"),
                   ("organic + notification burst", "Notification burst (mean delay 45 s)")):
    check(f"| {row} | " + " | ".join(ci(H + label, m, "null_fp") for m in METHODS) + " |")
side = H + "coordinated, adjacent ids + repost signal"
check("in 30 of 30 such datasets", get(side, "C_v1_strong", "detect_rate") == 1 and get(H + "coordinated", "C_v1_strong", "detect_rate") == 0)

# ---- abstract numbers
P3, P4, P8 = "P3_random_delays|cohort_spread=", "P4_participation|participation=", "P8_jitter|jitter="
c_random = max(get(P3 + s, "C_v1", "f1_seed_mean") for s in ("120", "600", "2000"))
check(f"F1 ≤ {f2(c_random)} vs {f2(min(get(P3 + s, 'B_tuned', 'f1_seed_mean') for s in ('120', '600', '2000')))}")
check(f"at 40% participation ({f2(get(P4 + '0.4', 'C_v1', 'f1_seed_mean'))} vs {f2(get(P4 + '0.4', 'B_tuned', 'f1_seed_mean'))})")
check(f"40 s of timing jitter ({f2(get(P8 + '40', 'C_v1', 'f1_seed_mean'))} vs {f2(get(P8 + '40', 'B_tuned', 'f1_seed_mean'))})")

# ---- robustness text
P2 = "P2_cohort_spread|cohort_spread="
check("V1 held at 1.00 up to a 2,000 s cohort spread", all(f2(get(P2 + s, "C_v1", "f1_seed_mean")) == "1.00" for s in ("120", "300", "600", "1000", "2000")))
check(f"original B fell to {f2(get(P2 + '2000', 'B_time_bucket', 'f1_seed_mean'))}, and tuned B ({f2(get(P2 + '2000', 'B_tuned', 'f1_seed_mean'))}) was indistinguishable",
      PAIRED[(P2 + "2000", "B_tuned")]["verdict"] == "no clear difference")
check(f"its F1 was at most {f2(c_random)}")
check(f"it scored {f2(get(P4 + '0.6', 'C_v1', 'f1_seed_mean'))} against {f2(get(P4 + '0.6', 'B_tuned', 'f1_seed_mean'))} at 0.6, and "
      f"{f2(get(P4 + '0.4', 'C_v1', 'f1_seed_mean'))} against {f2(get(P4 + '0.4', 'B_tuned', 'f1_seed_mean'))} at 0.4",
      get(P4 + "0.4", "A_overlap_only", "detect_rate") == 0)
check(f"it scored {f2(get(P8 + '20', 'C_v1', 'f1_seed_mean'))} at 20 s, {f2(get(P8 + '40', 'C_v1', 'f1_seed_mean'))} at 40 s and "
      f"{f2(get(P8 + '80', 'C_v1', 'f1_seed_mean'))} at 80 s, against 1.00 for B",
      all(f2(get(P8 + j, m, "f1_seed_mean")) == "1.00" for j in ("5", "20", "40", "80") for m in ("B_time_bucket", "B_tuned")))
check(f"A's F1 to {f2(get('P7_heavy_users|heavy_weight=50', 'A_overlap_only', 'f1_seed_mean'))} at weight 50")

# ---- Table 2
P5 = "P5_rotation|rotation="
for row, config in (("Cohort spread 2,000 s", P2 + "2000"), ("Random delays, range 600 s", P3 + "600"),
                    ("Participation 0.6", P4 + "0.6"), ("Participation 0.4", P4 + "0.4"), ("Jitter sd 40 s", P8 + "40"),
                    ("Rotation 0.1", P5 + "0.1"), ("Rotation 0.4", P5 + "0.4"), ("Rotation 0.6", P5 + "0.6")):
    check(f"| {row} | " + " | ".join(f1se(config, m) for m in METHODS) + f" | {diff(config)} |")

# ---- rotation text
check(f"V1 led at rotation 0.1 ({f2(get(P5 + '0.1', 'C_v1', 'f1_seed_mean'))} vs {f2(get(P5 + '0.1', 'B_tuned', 'f1_seed_mean'))})")
check(f"returned group fragments ({f2(get(P5 + '0.4', 'C_v1', 'fragments_per_dataset'))} per dataset, against 0 for B)",
      get(P5 + "0.4", "B_tuned", "fragments_per_dataset") == 0 and get(P5 + "0.4", "B_time_bucket", "fragments_per_dataset") == 0)
pct = lambda r: f"{round(100 * get(P5 + r, 'C_v1', 'trace_post_recall'))}%"
check(f"recovered {pct('0.2')} of coordinated posts at rotation 0.2, {pct('0.4')} at 0.4 and {pct('0.8')} at 0.8")

# ---- scoreboard and runtime
def tally(baseline):
    v = [q["verdict"] for (c, b), q in PAIRED.items() if b == baseline]
    return v.count("C better"), v.count("C worse"), v.count("no clear difference")
better = [c for (c, b), q in PAIRED.items() if b == "B_tuned" and q["verdict"] == "C better"]
check("V1 beat tuned B in {} (six audience settings and light rotation), lost in {} and tied in {}".format(*tally("B_tuned")),
      sorted(better) == sorted([H + "organic + notification burst", P5 + "0.1"] + [P6 + d for d in ("15", "45", "120", "300", "900")]))
check("Against A it won {}, lost {} and tied {}".format(*tally("A_overlap_only")))
rt = lambda m: float(SUMMARY[(H + "coordinated", m)]["runtime_ms_median"])
check(f"median runtime per dataset was {rt('C_v1'):.1f} ms for V1, {rt('B_tuned'):.1f} ms for tuned B and {rt('A_overlap_only'):.1f} ms for A")
c_rt = [float(r["runtime_ms_median"]) for (c, m), r in SUMMARY.items() if m == "C_v1"]
check(f"ranged from {round(min(c_rt))} to {round(max(c_rt))} ms")

# ---- every two-decimal number in the report must be backed by a check
body = REPORT.split("## References")[0]
unchecked = sorted(set(re.findall(r"\d+\.\d{2}", body)) - covered)
if unchecked:
    failures.append(f"numbers in the report not covered by any check: {unchecked}")

print(f"{len(covered)} distinct two-decimal values covered; {len(failures)} problem(s)")
for f in failures:
    print(" -", f)
raise SystemExit(1 if failures else 0)
