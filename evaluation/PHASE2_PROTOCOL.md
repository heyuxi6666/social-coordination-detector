# Phase 2 protocol: fair baseline comparison on held-out seeds

Written before the tuning run and before any held-out run. Phase 1 (`results/`, seeds 1000-1019) showed the time-bucket baseline matching or beating V1 on recall at fixed untuned settings, and that its bucket width was never tuned. Phase 2 asks whether that conclusion survives a fair, tuned baseline and harder scenarios.

## Data splits (disjoint seed ranges)

| Split | Seeds | Used for |
|---|---|---|
| Phase 1 development | 1000-1019 | Phase 1 only; not used again |
| **Tuning** | 2000-2019 | choosing the time-bucket baseline's two parameters; nothing else |
| **Held-out** | 5000-5029 (30 seeds per configuration) | all reported Phase 2 results |

Parameters are selected on tuning seeds only (`tune_baseline.py`, config `configs/tuning.json`) and written to `results_phase2/tuned_parameters.json`. The held-out run reads that file and never feeds back into it. If a held-out result looks surprising, the protocol is not rerun with different parameters.

## What is tuned, and what is not

- **Tuned:** method B's `bucket_seconds` in {60, 120, 300, 600, 1200, 2400, 3600} and `min_group_accounts` in {3, 5, 8, 10, 15, 20} (42 combinations). The other B settings (at least 3 shared items, item Jaccard >= 0.5) stay at their Phase 1 values.
- **Not tuned:** method A and method C. V1 is used exactly as released, with all its fixed thresholds. A is V1's group-forming step. V1's code is not modified.
- **Reported baselines:** A overlap-only; B original (300 s, 5 accounts); B tuned; C V1 (strong+moderate flagged, the Phase 1 decision rule); C strong-only as a sensitivity row.

## Tuning objective

A mix of 7 coordinated and 4 negative scenarios (`configs/tuning.json`), 20 tuning seeds each. The coordinated mix includes scenarios that do not suit V1 (independent random delays, wide spread) as well as ones that do. The objective, to maximise:

`score = mean over coordinated scenarios of the mean per-seed account F1  -  mean over negative scenarios of the share of datasets with at least one flagged group`

Ties are broken by smaller bucket width, then smaller minimum group size. Every grid cell is written to `results_phase2/tuning_grid.csv`.

## Held-out experiments (`configs/phase2.json`)

| ID | Question | Sweep |
|---|---|---|
| P1 | headline scenarios | coordinated, side signals, organic-only, loyal followers, notification burst, coordinated + loyal |
| P2 | cohort spread, fixed per-account delays | 120, 300, 600, 1000, 2000 s |
| P3 | independently randomised delays | spread 120, 600, 2000 s |
| P4 | partial participation | 1.0, 0.8, 0.6, 0.4, 0.2 |
| P5 | account rotation | 0, 0.1, 0.2, 0.4, 0.6, 0.8 |
| P6 | notification bursts | mean burst delay 15, 45, 120, 300, 900, 1800 s (organic-only plus a 35-account audience) |
| P7 | organic heavy-user activity | weight 1, 5, 20, 50, with organic-only twins |
| P8 | timing jitter | 5, 20, 40, 80 s |

No scenario was designed to favour V1; P3 and P6 are the ones where V1's fixed-delay test is expected to be at a disadvantage or an advantage respectively, and both are reported.

## Statistics

- Account-level precision, recall and F1 pooled over seeds; mean per-seed F1 ± 1.96 SE.
- Group detection rate with Wilson 95% intervals; group match = post-set Jaccard >= 0.5. "Fragment" groups (unmatched but containing at least two true coordinated posts) are counted separately from truly spurious groups.
- False-positive rate on organic-only datasets: share of datasets with any flagged group, Wilson 95%.
- Paired comparisons: every method sees the same dataset per seed, so per-seed F1 differences (C minus a baseline) are reported as mean ± 1.96 SE. A "win" or "loss" is only claimed when that interval excludes 0.
- No correction for multiple comparisons across configurations; the tables are descriptive, not hypothesis tests.
- Runtime: median wall-clock per dataset on one machine.

## Out of scope

No machine learning, no claim about real-platform accuracy, no change to V1.

## Amendment, 7 November 2026: interval method for paired comparisons

Added after the held-out results had been read, during the report revision. No experiment was rerun and no parameter changed.

- The pre-registered paired intervals (mean ± 1.96 SE) fall outside the valid range [−1, 1] in 4 of 129 comparisons (lowest −1.032), because some per-seed differences are nearly constant.
- `summarize_phase2.py` now also computes a seeded percentile-bootstrap interval (10,000 resamples) for every paired difference. These intervals always stay within the observed range.
- `paired_comparisons.csv` keeps the original columns (`ci_low`, `ci_high`, `verdict`) and adds `boot_low`, `boot_high` and `verdict_bootstrap`. `tables.md` and the report use the bootstrap columns.
- Only one verdict differs between the two methods: cohort spread 1,000 s against the original time-bucket baseline, where the mean difference is 0.005 F1. Every comparison against the tuned baseline has the same verdict under both methods.
- The scoreboard in `tables.md` now counts coordinated configurations (account F1) and organic-only configurations (false-positive indicator) separately. Configuration-level verdicts remain exploratory, because there is no multiple-comparison correction.
