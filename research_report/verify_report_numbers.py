"""Check every quantitative claim in mini_research_report.md against the committed Phase 2 results.

    python research_report/verify_report_numbers.py

Each check recomputes a value from evaluation/results_phase2/ (summary.csv, paired_comparisons.csv, raw_results.csv,
run_info.json, tuned_parameters.json), formats it as the report does, and confirms the exact text appears in the report.
Every two-decimal number in the report body must also be covered by at least one check. Exit code 0 = all pass.
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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")            # the report uses "−"; non-UTF-8 consoles would crash

RES = ROOT / "evaluation" / "results_phase2"
REPORT = (HERE / "mini_research_report.md").read_text(encoding="utf-8")
METHODS = ("A_overlap_only", "B_time_bucket", "B_tuned", "C_v1")


def rows(name: str) -> list[dict]:
    with (RES / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


SUMMARY = {(r["config_id"], r["method"]): r for r in rows("summary.csv")}
PAIRED_ROWS = rows("paired_comparisons.csv")
PAIRED = {(r["config_id"], r["baseline"]): r for r in PAIRED_ROWS}
RAW = rows("raw_results.csv")
INFO = json.loads((RES / "run_info.json").read_text(encoding="utf-8"))
TUNED = json.loads((RES / "tuned_parameters.json").read_text(encoding="utf-8"))
failures: list[str] = []
covered: set[str] = set()


def f2(x) -> str:
    return f"{float(x):.2f}"


def signed(x) -> str:
    return f"{float(x):+.2f}".replace("-", "−")


def get(config: str, method: str, field: str) -> float:
    return float(SUMMARY[(config, method)][field])


def check(text: str, condition: bool = True, note: str = "") -> None:
    covered.update(re.findall(r"\d+\.\d{2}", text))
    if text not in REPORT:
        failures.append(f"text not found in report: {text!r} {note}")
    elif not condition:
        failures.append(f"value check failed: {text!r} {note}")


def wilson_cell(config: str, method: str) -> str:
    return f"{f2(get(config, method, 'null_fp_rate'))} [{f2(get(config, method, 'null_fp_lo'))}, {f2(get(config, method, 'null_fp_hi'))}]"


def f1(config: str, method: str) -> str:
    return f2(get(config, method, "f1_seed_mean"))


def boot(config: str, baseline: str = "B_tuned") -> str:
    q = PAIRED[(config, baseline)]
    return f"{signed(q['mean_difference'])} [{signed(q['boot_low'])}, {signed(q['boot_high'])}]"


H, P2, P3, P4 = "P1_headline|", "P2_cohort_spread|cohort_spread=", "P3_random_delays|cohort_spread=", "P4_participation|participation="
P5, P6, P8 = "P5_rotation|rotation=", "P6_notification_bursts|loyal_delay_mean=", "P8_jitter|jitter="

# ---- scale, splits, tuning
check(f"{INFO['datasets']:,} held-out datasets ({INFO['configurations']} configurations × {len(INFO['seeds'])} seeds)")
check(f"seeds {INFO['seeds'][0]}–{INFO['seeds'][-1]}")
check(f"Seeds {TUNED['tuning_seeds'][0]}–{TUNED['tuning_seeds'][1]} were used only to tune B")
tuning = json.loads((ROOT / "evaluation" / "configs" / "tuning.json").read_text(encoding="utf-8"))
grid = tuning["grid"]
check(f"over {TUNED['grid_cells']} cells (*w* = {min(grid['bucket_seconds'])}–{max(grid['bucket_seconds']):,} s, *n*_min = "
      f"{min(grid['min_group_accounts'])}–{max(grid['min_group_accounts'])}) and {TUNED['scenarios']} scenarios (7 coordinated, 4 negative)",
      sum(1 for s in tuning["scenarios"] if s["params"].get("group_size", 1) != 0) == 7)
check(f"**w = {TUNED['parameters']['bucket_seconds']:,} s, n_min = {TUNED['parameters']['min_group_accounts']}**")
check(f"tuning score was {TUNED['tuning_score']:.3f}, against {TUNED['original_tuning_score']:.3f} for the original setting")

# ---- interval method: normal intervals out of bounds; bootstrap verdict changes
outside = [r for r in PAIRED_ROWS if float(r["ci_low"]) < -1 or float(r["ci_high"]) > 1]
check(f"fell outside [−1, 1] in {len(outside)} of {len(PAIRED_ROWS)} comparisons (lowest {signed(min(float(r['ci_low']) for r in outside)).replace('+', '')[:6]}",
      all(-1 <= float(r["boot_low"]) and float(r["boot_high"]) <= 1 for r in PAIRED_ROWS))
check(f"lowest −{abs(min(float(r['ci_low']) for r in outside)):.3f}")
changed = [r for r in PAIRED_ROWS if r["verdict"] != r["verdict_bootstrap"]]
check("the verdicts are unchanged except in one negligible comparison",
      len(changed) == 1 and abs(float(changed[0]["mean_difference"])) < 0.02)
check("10,000 resamples")
check("originally specified paired intervals (mean ± 1.96 SE)")                    # a definition, not a result

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
check(f"On plain organic and heavy-user data ({flagged('C_v1', pure)[1]} datasets), every method was nearly clean, and A flagged {flagged('A_overlap_only', pure)[0]}",
      all(flagged(m, pure)[0] == 0 for m in ("B_time_bucket", "B_tuned", "C_v1")))
check(f"On follower-audience data ({flagged('C_v1', audience)[1]} datasets), A flagged {flagged('A_overlap_only', audience)[0]}, original B "
      f"{flagged('B_time_bucket', audience)[0]}, tuned B {flagged('B_tuned', audience)[0]}, and V1 none", flagged("C_v1", audience)[0] == 0)

# ---- audience bursts
fast = all(get(P6 + d, m, "null_fp_rate") == 1 for d in ("15", "45", "120") for m in ("B_time_bucket", "B_tuned"))
check("Both B variants flagged every audience with a mean delay of 120 s or less", fast and get(P6 + "300", "B_time_bucket", "null_fp_rate") < 1)
check("mean delay of 120 s or less", fast)
check(f"tuned B flagged {f2(get(P6 + '300', 'B_tuned', 'null_fp_rate'))} of datasets at 300 s and {f2(get(P6 + '900', 'B_tuned', 'null_fp_rate'))} at 900 s")

# ---- Table 2 (headline)
check("found the plain coordinated group in all 30 datasets", all(get(H + "coordinated", m, "detect_rate") == 1 for m in METHODS))
check(f"A absorbed an adjacent loyal audience (F1 {f1(H + 'coordinated + loyal followers', 'A_overlap_only')})")
check("| Coordinated group | " + " | ".join(f1(H + "coordinated", m) for m in METHODS) + " |")
check("| Coordinated + loyal audience | " + " | ".join(f1(H + "coordinated + loyal followers", m) for m in METHODS) + " |")
check(f"| Coordinated, V1 *strong* tier only | – | – | – | {f1(H + 'coordinated', 'C_v1_strong')} |")
for label, row in (("organic-only", "Organic only"), ("organic + loyal followers", "Loyal audience (mean delay 1,800 s)"),
                   ("organic + notification burst", "Notification burst (mean delay 45 s)")):
    check(f"| {row} | " + " | ".join(wilson_cell(H + label, m) for m in METHODS) + " |")
side = H + "coordinated, adjacent ids + repost signal"
check("*strong* tier fired in 30 of 30 diagnostic datasets", get(side, "C_v1_strong", "detect_rate") == 1)
check("never fired on default data (0 of 30 datasets)", get(H + "coordinated", "C_v1_strong", "detect_rate") == 0)

# ---- abstract
c_random = max(get(P3 + s, "C_v1", "f1_seed_mean") for s in ("120", "600", "2000"))
check(f"F1 ≤ {f2(c_random)} vs {f2(min(get(P3 + s, 'B_tuned', 'f1_seed_mean') for s in ('120', '600', '2000')))}")
check(f"at 40% participation ({f1(P4 + '0.4', 'C_v1')} vs {f1(P4 + '0.4', 'B_tuned')})")
check(f"40 s of timing jitter ({f1(P8 + '40', 'C_v1')} vs {f1(P8 + '40', 'B_tuned')})")

# ---- RQ2 text
check("V1 held at 1.00 up to a 2,000 s cohort spread", all(f1(P2 + s, "C_v1") == "1.00" for s in ("120", "300", "600", "1000", "2000")))
check(f"the original B fell to {f1(P2 + '2000', 'B_time_bucket')}, while tuned B ({f1(P2 + '2000', 'B_tuned')}) was indistinguishable",
      PAIRED[(P2 + "2000", "B_tuned")]["verdict_bootstrap"] == "no clear difference")
check(f"F1 ≤ {f2(c_random)}. This follows from its design")
check("at 0.4, the overlap step V1 shares with A no longer forms a group", get(P4 + "0.4", "A_overlap_only", "detect_rate") == 0)
check(f"F1 {f1(P8 + '20', 'C_v1')} at 20 s, then {f1(P8 + '40', 'C_v1')} at 40 s and {f1(P8 + '80', 'C_v1')} at 80 s")
check(f"A's F1 to {f1('P7_heavy_users|heavy_weight=50', 'A_overlap_only')} at weight 50")

# ---- Table 3
table3 = (("Cohort spread 2,000 s", P2 + "2000"), ("Random delays, range 120 s", P3 + "120"), ("Random delays, range 2,000 s", P3 + "2000"),
          ("Participation 0.6", P4 + "0.6"), ("Participation 0.4", P4 + "0.4"), ("Jitter sd 40 s", P8 + "40"), ("Jitter sd 80 s", P8 + "80"),
          ("Rotation 0.1", P5 + "0.1"), ("Rotation 0.4", P5 + "0.4"), ("Rotation 0.6", P5 + "0.6"))
for row, config in table3:
    check(f"| {row} | " + " | ".join(f1(config, m) for m in METHODS) + f" | {boot(config)} |")
max_se = max(get(config, m, "f1_seed_se") for _, config in table3 for m in METHODS)
check(f"The standard errors of all F1 means shown are at most {f2(max_se)}", round(max_se, 2) <= 0.07)

# ---- RQ3 text
check(f"V1 led only at rotation 0.1 ({f1(P5 + '0.1', 'C_v1')} vs {f1(P5 + '0.1', 'B_tuned')})",
      [c for (c, b), q in PAIRED.items() if b == "B_tuned" and c.startswith("P5") and q["verdict_bootstrap"] == "C better"] == [P5 + "0.1"])
check(f"fragments of the group ({f2(get(P5 + '0.4', 'C_v1', 'fragments_per_dataset'))} per dataset, against 0 for B)",
      get(P5 + "0.4", "B_tuned", "fragments_per_dataset") == 0 and get(P5 + "0.4", "B_time_bucket", "fragments_per_dataset") == 0)
pct = lambda r: f"{round(100 * get(P5 + r, 'C_v1', 'trace_post_recall'))}%"
check(f"recovered {pct('0.2')} of coordinated posts at rotation 0.2, {pct('0.4')} at 0.4 and {pct('0.8')} at 0.8")

# ---- exploratory summary (bootstrap verdicts, coordinated and organic-only counted separately)
def tally(baseline: str, kind: str) -> tuple[int, int, int, int]:
    v = [q["verdict_bootstrap"] for q in PAIRED_ROWS if q["baseline"] == baseline and q["kind"] == kind]
    return len(v), v.count("C better"), v.count("C worse"), v.count("no clear difference")
n_c, b_c, w_c, t_c = tally("B_tuned", "coordinated")
check(f"Against tuned B, V1 was better in {b_c}, worse in {w_c} and not distinguishable in {t_c} of the {n_c} coordinated configurations (compared on F1)")
n_o, b_o, w_o, t_o = tally("B_tuned", "organic-only")
check(f"On the {n_o} organic-only configurations (compared on false positives) it had fewer false positives in {b_o}, more in {w_o} and no clear difference in {t_o}")
_, ab, aw, at = tally("A_overlap_only", "coordinated")
_, ob, ow, ot = tally("A_overlap_only", "organic-only")
check(f"Against A, the counts were {ab} / {aw} / {at} and {ob} / {ow} / {ot}")
rt = lambda m: float(SUMMARY[(H + "coordinated", m)]["runtime_ms_median"])
check(f"median runtime per dataset was {rt('C_v1'):.1f} ms for V1, {rt('B_tuned'):.1f} ms for tuned B and {rt('A_overlap_only'):.1f} ms for A")

# ---- README results table and claims (same sources as the report)
README = (ROOT / "README.md").read_text(encoding="utf-8")


def check_readme(text: str) -> None:
    covered.update(re.findall(r"\d+\.\d{2}", text))
    if text not in README:
        failures.append(f"text not found in README: {text!r}")


a_flags, b_flags, c_flags = (flagged(m)[0] for m in ("A_overlap_only", "B_tuned", "C_v1"))
check_readme(f"| Organic-only datasets flagged (of {flagged('C_v1')[1]}) | {a_flags} | {b_flags} | {c_flags} |")
for label, config in (("Independent random delays (range 600 s): account F1", P3 + "600"), ("Participation 0.4: account F1", P4 + "0.4"),
                      ("Timing jitter sd 40 s: account F1", P8 + "40"), ("Account rotation 0.1: account F1", P5 + "0.1")):
    check_readme(f"| {label} | {f1(config, 'A_overlap_only')} | {f1(config, 'B_tuned')} | {f1(config, 'C_v1')} |")
check_readme(f"flagged none of the {flagged('C_v1')[1]} organic-only datasets")
check_readme(f"({rt('C_v1'):.1f} ms vs {rt('B_tuned'):.1f} ms per dataset at default settings")
check_readme(f"{INFO['datasets']:,} datasets")
check_readme(f"held-out seeds {INFO['seeds'][0]}-{INFO['seeds'][-1]} (30 per configuration, {INFO['configurations']} configurations")
check_readme(f"Tuning seeds {TUNED['tuning_seeds'][0]}-{TUNED['tuning_seeds'][1]}")
check_readme(f"tuned** setting ({TUNED['parameters']['bucket_seconds']:,} s, groups of {TUNED['parameters']['min_group_accounts']})")
check_readme(f"invalid in {len(outside)} of {len(PAIRED_ROWS)} comparisons")
check_readme("research_report/Yuxi_He_Research_Report.pdf")
if not (HERE / "Yuxi_He_Research_Report.pdf").exists():
    failures.append("the PDF referenced from the README is missing")

# ---- statements that must be present
for text in ("Evaluation code: https://github.com/heyuxi6666/social-coordination-detector/tree/research-evaluation", "**Yuxi He**\nPostgraduate Cyber Security student\nThe University of Queensland",
             "https://github.com/heyuxi6666/social-coordination-detector",
             "never combined", "exploratory"):
    check(text)
if "Figure 2" in REPORT or "figure2" in REPORT:
    failures.append("the report still refers to Figure 2, which was removed")

# ---- every two-decimal number in the report body must be backed by a check
body = REPORT.split("## References")[0]
unchecked = sorted(set(re.findall(r"\d+\.\d{2}", body)) - covered)
if unchecked:
    failures.append(f"numbers in the report not covered by any check: {unchecked}")

print(f"{len(covered)} distinct two-decimal values covered; {len(failures)} problem(s)")
for f in failures:
    print(" -", f)
raise SystemExit(1 if failures else 0)
