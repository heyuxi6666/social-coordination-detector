"""Scoring and aggregation.  Plain functions on sets and lists; no third-party code.

Per dataset:
* account level: union of the accounts of all predicted groups against the truth (true positives, false
  positives, false negatives); in organic-only datasets every flagged account is a false positive;
* group level: a coordinated dataset is "detected" when some predicted group's post set has Jaccard >= 0.5 with
  the true coordinated post set; every predicted group that does not match is "spurious";
* false-positive rate: share of organic-only datasets with at least one predicted group, and flagged
  non-coordinated accounts as a share of all non-coordinated accounts that appear in the data.

Across seeds: precision/recall/F1 are micro-averaged (counts summed over seeds) and the mean per-seed F1 is
reported with its standard error; rates carry Wilson 95% intervals.
"""

from __future__ import annotations

import math
import statistics
from typing import Any, Iterable

GROUP_MATCH_JACCARD = 0.5


def prf_counts(predicted: set, truth: set) -> tuple[int, int, int]:
    tp = len(predicted & truth)
    return tp, len(predicted) - tp, len(truth) - tp


def f1_from_counts(tp: int, fp: int, fn: int) -> float:
    return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0


def score_groups(groups: list[dict[str, set]], truth_posts: set, truth_accounts: set,
                 all_accounts: set) -> dict[str, Any]:
    predicted = set().union(*(g["accounts"] for g in groups)) if groups else set()
    tp, fp, fn = prf_counts(predicted, truth_accounts)
    matched = [g for g in groups if truth_posts and
               len(g["posts"] & truth_posts) / len(g["posts"] | truth_posts) >= GROUP_MATCH_JACCARD]
    negatives = len(all_accounts - truth_accounts)
    fragments = [g for g in groups if g not in matched and len(g["posts"] & truth_posts) >= 2]
    return {"n_groups": len(groups), "detected": (1 if matched else 0) if truth_posts else "",
            "spurious_groups": len(groups) - len(matched), "fragment_groups": len(fragments), "tp": tp, "fp": fp, "fn": fn,
            "negatives": negatives, "any_group": 1 if groups else 0}


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mean_se(values: Iterable[float]) -> tuple[float, float]:
    values = list(values)
    if not values:
        return (math.nan, math.nan)
    if len(values) == 1:
        return (values[0], 0.0)
    return (statistics.fmean(values), statistics.stdev(values) / math.sqrt(len(values)))


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate the per-seed rows of ONE (config, method)."""
    coordinated = [r for r in rows if r["detected"] != ""]
    organic = [r for r in rows if r["detected"] == ""]
    out: dict[str, Any] = {"n_seeds": len(rows), "runtime_ms_median": round(1000 * statistics.median(r["runtime_s"] for r in rows), 1)}
    if coordinated:
        tp, fp, fn = (sum(r[k] for r in coordinated) for k in ("tp", "fp", "fn"))
        detected = sum(r["detected"] for r in coordinated)
        lo, hi = wilson(detected, len(coordinated))
        f1_mean, f1_se = mean_se(f1_from_counts(r["tp"], r["fp"], r["fn"]) for r in coordinated)
        out.update(detect_rate=detected / len(coordinated), detect_lo=lo, detect_hi=hi,
                   precision=tp / (tp + fp) if tp + fp else "", recall=tp / (tp + fn) if tp + fn else "",
                   f1_micro=f1_from_counts(tp, fp, fn), f1_seed_mean=f1_mean, f1_seed_se=f1_se,
                   spurious_per_dataset=statistics.fmean(r["spurious_groups"] for r in coordinated),
                   fragments_per_dataset=statistics.fmean(r.get("fragment_groups", 0) for r in coordinated),
                   account_fpr=sum(r["fp"] for r in coordinated) / max(1, sum(r["negatives"] for r in coordinated)))
        traced = [r for r in coordinated if r.get("trace_built") not in ("", None)]
        if traced:
            out.update(trace_built_rate=statistics.fmean(r["trace_built"] for r in traced),
                       trace_post_recall=statistics.fmean(r["trace_post_recall"] for r in traced),
                       trace_post_precision=statistics.fmean(r["trace_post_precision"] for r in traced if r["trace_built"]) if any(r["trace_built"] for r in traced) else "")
    if organic:
        flagged = sum(r["any_group"] for r in organic)
        lo, hi = wilson(flagged, len(organic))
        out.update(null_fp_rate=flagged / len(organic), null_fp_lo=lo, null_fp_hi=hi,
                   null_groups_per_dataset=statistics.fmean(r["n_groups"] for r in organic),
                   null_account_fpr=sum(r["fp"] for r in organic) / max(1, sum(r["negatives"] for r in organic)))
    return out
