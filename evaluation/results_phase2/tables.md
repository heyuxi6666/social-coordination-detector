# Phase 2 held-out results

43 configurations x 30 held-out seeds (5000-5029), 1290 synthetic datasets, Python 3.11.9. Synthetic data only; no claim about real platforms.

Tuned time-bucket baseline: bucket 2400 s, minimum group 15 accounts, chosen on tuning seeds 2000-2019 only (tuning score 0.6914 vs 0.6771 for the original 300 s / 5). Original: 300 s / 5. V1 is unmodified.

Columns as in `results/tables.md`; *Fragments* = unmatched groups that still contain at least two true coordinated posts; *Spurious* counts every unmatched group, fragments included.

## P1_headline (RQ1): Headline scenarios at default settings

| Config | Method | Detected [95% CI] | P | R | F1 (mean ± SE) | Fragments | Spurious | Organic FP [95% CI] | Acct FPR | ms |
|---|---|---|---|---|---|---|---|---|---|---|
| coordinated | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| coordinated | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| coordinated | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 176.5 |
| coordinated | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 176.5 |
| coordinated | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.0 |
| coordinated, adjacent ids + repost signal | A overlap-only | 1.00 [0.89, 1.00] | 0.98 | 1.00 | 0.99 ± 0.00 | 0.00 | 0.00 | – | 0.001 | 0.7 |
| coordinated, adjacent ids + repost signal | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| coordinated, adjacent ids + repost signal | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 176.9 |
| coordinated, adjacent ids + repost signal | C V1 (strong only) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 176.9 |
| coordinated, adjacent ids + repost signal | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 2.9 |
| organic-only | A overlap-only | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.4 |
| organic-only | B original | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.7 |
| organic-only | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 24.3 |
| organic-only | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 24.3 |
| organic-only | B tuned | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 1.7 |
| organic + loyal followers | A overlap-only | – | – | – | – | – | 1.00 | 1.00 [0.89, 1.00] | 0.045 | 0.4 |
| organic + loyal followers | B original | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.8 |
| organic + loyal followers | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 66.7 |
| organic + loyal followers | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 66.7 |
| organic + loyal followers | B tuned | – | – | – | – | – | 0.03 | 0.03 [0.01, 0.17] | 0.001 | 1.8 |
| organic + notification burst | A overlap-only | – | – | – | – | – | 1.00 | 1.00 [0.89, 1.00] | 0.045 | 0.4 |
| organic + notification burst | B original | – | – | – | – | – | 1.77 | 1.00 [0.89, 1.00] | 0.040 | 1.0 |
| organic + notification burst | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 70.1 |
| organic + notification burst | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 70.1 |
| organic + notification burst | B tuned | – | – | – | – | – | 1.03 | 1.00 [0.89, 1.00] | 0.043 | 2.0 |
| coordinated + loyal followers | A overlap-only | 1.00 [0.89, 1.00] | 0.52 | 1.00 | 0.68 ± 0.00 | 0.00 | 1.00 | – | 0.046 | 0.8 |
| coordinated + loyal followers | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| coordinated + loyal followers | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 219.8 |
| coordinated + loyal followers | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 219.8 |
| coordinated + loyal followers | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.1 |

Paired per-seed difference, V1 minus baseline (coordinated: account F1, positive favours V1; organic-only: share of datasets with a flagged group, negative favours V1). Mean [95% percentile-bootstrap CI]; exploratory, no multiple-comparison correction:

| Config | vs A overlap-only | vs B original | vs B tuned |
|---|---|---|---|
| coordinated | +0.02 [+0.01, +0.02] C better | -0.00 [-0.00, +0.00] no clear difference | -0.00 [-0.00, +0.00] no clear difference |
| coordinated, adjacent ids + repost signal | +0.01 [+0.01, +0.01] C better | -0.00 [-0.00, +0.00] no clear difference | -0.00 [-0.00, +0.00] no clear difference |
| organic-only | +0.00 [+0.00, +0.00] no clear difference | +0.00 [+0.00, +0.00] no clear difference | +0.00 [+0.00, +0.00] no clear difference |
| organic + loyal followers | -1.00 [-1.00, -1.00] C better | +0.00 [+0.00, +0.00] no clear difference | -0.03 [-0.10, +0.00] no clear difference |
| organic + notification burst | -1.00 [-1.00, -1.00] C better | -1.00 [-1.00, -1.00] C better | -1.00 [-1.00, -1.00] C better |
| coordinated + loyal followers | +0.31 [+0.31, +0.32] C better | -0.00 [-0.00, +0.00] no clear difference | -0.00 [-0.00, +0.00] no clear difference |

## P2_cohort_spread (RQ2): Cohort spread (seconds over which the group's personal delays are spread), fixed per-account delays

| Config | Method | Detected [95% CI] | P | R | F1 (mean ± SE) | Fragments | Spurious | Organic FP [95% CI] | Acct FPR | ms |
|---|---|---|---|---|---|---|---|---|---|---|
| cohort_spread=120 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| cohort_spread=120 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| cohort_spread=120 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 177.1 |
| cohort_spread=120 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 177.1 |
| cohort_spread=120 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.1 |
| cohort_spread=300 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| cohort_spread=300 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.4 |
| cohort_spread=300 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 167.3 |
| cohort_spread=300 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 167.3 |
| cohort_spread=300 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 2.9 |
| cohort_spread=600 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| cohort_spread=600 | B original | 1.00 [0.89, 1.00] | 1.00 | 0.99 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.3 |
| cohort_spread=600 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 163.7 |
| cohort_spread=600 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 163.7 |
| cohort_spread=600 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.1 |
| cohort_spread=1000 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| cohort_spread=1000 | B original | 1.00 [0.89, 1.00] | 1.00 | 0.99 | 0.99 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.1 |
| cohort_spread=1000 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 161.1 |
| cohort_spread=1000 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 161.1 |
| cohort_spread=1000 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.0 |
| cohort_spread=2000 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| cohort_spread=2000 | B original | 1.00 [0.89, 1.00] | 1.00 | 0.85 | 0.91 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 1.0 |
| cohort_spread=2000 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 159.2 |
| cohort_spread=2000 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 159.2 |
| cohort_spread=2000 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 0.98 | 0.99 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 2.9 |

Paired per-seed difference, V1 minus baseline (coordinated: account F1, positive favours V1; organic-only: share of datasets with a flagged group, negative favours V1). Mean [95% percentile-bootstrap CI]; exploratory, no multiple-comparison correction:

| Config | vs A overlap-only | vs B original | vs B tuned |
|---|---|---|---|
| cohort_spread=120 | +0.02 [+0.01, +0.02] C better | -0.00 [-0.00, +0.00] no clear difference | -0.00 [-0.00, +0.00] no clear difference |
| cohort_spread=300 | +0.02 [+0.01, +0.02] C better | -0.00 [-0.00, +0.00] no clear difference | -0.00 [-0.00, +0.00] no clear difference |
| cohort_spread=600 | +0.02 [+0.01, +0.02] C better | +0.00 [-0.00, +0.01] no clear difference | -0.00 [-0.00, +0.00] no clear difference |
| cohort_spread=1000 | +0.02 [+0.01, +0.02] C better | +0.01 [+0.00, +0.01] C better | +0.00 [-0.00, +0.00] no clear difference |
| cohort_spread=2000 | +0.02 [+0.01, +0.02] C better | +0.08 [+0.06, +0.11] C better | +0.01 [-0.00, +0.02] no clear difference |

## P3_random_delays (RQ2): Independently randomised reaction delays (no repeated per-account offset)

| Config | Method | Detected [95% CI] | P | R | F1 (mean ± SE) | Fragments | Spurious | Organic FP [95% CI] | Acct FPR | ms |
|---|---|---|---|---|---|---|---|---|---|---|
| cohort_spread=120 | A overlap-only | 1.00 [0.89, 1.00] | 0.96 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| cohort_spread=120 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| cohort_spread=120 | C V1 (strong+moderate) | 0.07 [0.02, 0.21] | 1.00 | 0.03 | 0.04 ± 0.03 | 0.00 | 0.00 | – | 0.000 | 175.7 |
| cohort_spread=120 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 175.7 |
| cohort_spread=120 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 2.8 |
| cohort_spread=600 | A overlap-only | 1.00 [0.89, 1.00] | 0.96 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| cohort_spread=600 | B original | 1.00 [0.89, 1.00] | 1.00 | 0.99 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.2 |
| cohort_spread=600 | C V1 (strong+moderate) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 162.9 |
| cohort_spread=600 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 162.9 |
| cohort_spread=600 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 2.9 |
| cohort_spread=2000 | A overlap-only | 1.00 [0.89, 1.00] | 0.96 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| cohort_spread=2000 | B original | 0.03 [0.01, 0.17] | 1.00 | 0.00 | 0.01 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 1.0 |
| cohort_spread=2000 | C V1 (strong+moderate) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 158.2 |
| cohort_spread=2000 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 158.2 |
| cohort_spread=2000 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 2.9 |

Paired per-seed difference, V1 minus baseline (coordinated: account F1, positive favours V1; organic-only: share of datasets with a flagged group, negative favours V1). Mean [95% percentile-bootstrap CI]; exploratory, no multiple-comparison correction:

| Config | vs A overlap-only | vs B original | vs B tuned |
|---|---|---|---|
| cohort_spread=120 | -0.94 [-0.98, -0.88] C worse | -0.96 [-1.00, -0.90] C worse | -0.96 [-1.00, -0.90] C worse |
| cohort_spread=600 | -0.98 [-0.98, -0.97] C worse | -1.00 [-1.00, -0.99] C worse | -1.00 [-1.00, -1.00] C worse |
| cohort_spread=2000 | -0.98 [-0.98, -0.97] C worse | -0.01 [-0.02, +0.00] no clear difference | -1.00 [-1.00, -1.00] C worse |

## P4_participation (RQ2): Participation rate of group accounts per coordinated post

| Config | Method | Detected [95% CI] | P | R | F1 (mean ± SE) | Fragments | Spurious | Organic FP [95% CI] | Acct FPR | ms |
|---|---|---|---|---|---|---|---|---|---|---|
| participation=1.0 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| participation=1.0 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| participation=1.0 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 176.3 |
| participation=1.0 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 176.3 |
| participation=1.0 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.0 |
| participation=0.8 | A overlap-only | 1.00 [0.89, 1.00] | 0.96 | 0.99 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.8 |
| participation=0.8 | B original | 1.00 [0.89, 1.00] | 1.00 | 0.99 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.3 |
| participation=0.8 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 117.5 |
| participation=0.8 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 117.5 |
| participation=0.8 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 0.99 | 0.99 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 2.7 |
| participation=0.6 | A overlap-only | 0.80 [0.63, 0.90] | 0.90 | 0.66 | 0.72 ± 0.05 | 0.17 | 0.17 | – | 0.004 | 0.5 |
| participation=0.6 | B original | 1.00 [0.89, 1.00] | 1.00 | 0.79 | 0.88 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 1.1 |
| participation=0.6 | C V1 (strong+moderate) | 0.80 [0.63, 0.90] | 1.00 | 0.71 | 0.78 ± 0.05 | 0.17 | 0.17 | – | 0.000 | 88.0 |
| participation=0.6 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 88.0 |
| participation=0.6 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 0.80 | 0.89 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 2.3 |
| participation=0.4 | A overlap-only | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 0.4 |
| participation=0.4 | B original | 0.97 [0.83, 0.99] | 1.00 | 0.36 | 0.51 ± 0.03 | 0.00 | 0.00 | – | 0.000 | 0.9 |
| participation=0.4 | C V1 (strong+moderate) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 41.6 |
| participation=0.4 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 41.6 |
| participation=0.4 | B tuned | 0.67 [0.49, 0.81] | 0.99 | 0.33 | 0.43 ± 0.06 | 0.00 | 0.00 | – | 0.000 | 2.1 |
| participation=0.2 | A overlap-only | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 0.4 |
| participation=0.2 | B original | 0.03 [0.01, 0.17] | 1.00 | 0.01 | 0.01 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 0.8 |
| participation=0.2 | C V1 (strong+moderate) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 24.9 |
| participation=0.2 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 24.9 |
| participation=0.2 | B tuned | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.7 |

Paired per-seed difference, V1 minus baseline (coordinated: account F1, positive favours V1; organic-only: share of datasets with a flagged group, negative favours V1). Mean [95% percentile-bootstrap CI]; exploratory, no multiple-comparison correction:

| Config | vs A overlap-only | vs B original | vs B tuned |
|---|---|---|---|
| participation=1.0 | +0.02 [+0.01, +0.02] C better | -0.00 [-0.00, +0.00] no clear difference | -0.00 [-0.00, +0.00] no clear difference |
| participation=0.8 | +0.02 [+0.01, +0.02] C better | +0.00 [-0.00, +0.00] no clear difference | +0.00 [-0.00, +0.00] no clear difference |
| participation=0.6 | +0.06 [+0.04, +0.08] C better | -0.10 [-0.20, -0.02] C worse | -0.11 [-0.21, -0.02] C worse |
| participation=0.4 | +0.00 [+0.00, +0.00] no clear difference | -0.51 [-0.56, -0.45] C worse | -0.43 [-0.54, -0.32] C worse |
| participation=0.2 | +0.00 [+0.00, +0.00] no clear difference | -0.01 [-0.04, +0.00] no clear difference | +0.00 [+0.00, +0.00] no clear difference |

## P5_rotation (RQ3): Account rotation (per-slot replacement probability before each coordinated post)

| Config | Method | Detected [95% CI] | P | R | F1 (mean ± SE) | Fragments | Spurious | Organic FP [95% CI] | Acct FPR | ms |
|---|---|---|---|---|---|---|---|---|---|---|
| rotation=0 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| rotation=0 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| rotation=0 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 177.1 |
| rotation=0 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 177.1 |
| rotation=0 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 2.9 |
| rotation=0.1 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 0.71 | 0.82 ± 0.01 | 0.00 | 0.00 | – | 0.002 | 0.8 |
| rotation=0.1 | B original | 1.00 [0.89, 1.00] | 1.00 | 0.71 | 0.83 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 1.6 |
| rotation=0.1 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 0.99 | 0.84 | 0.91 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 143.6 |
| rotation=0.1 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 143.6 |
| rotation=0.1 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 0.71 | 0.83 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 3.0 |
| rotation=0.2 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 0.53 | 0.68 ± 0.01 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| rotation=0.2 | B original | 1.00 [0.89, 1.00] | 1.00 | 0.53 | 0.69 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 1.6 |
| rotation=0.2 | C V1 (strong+moderate) | 0.83 [0.66, 0.93] | 0.99 | 0.60 | 0.71 ± 0.06 | 0.00 | 0.00 | – | 0.000 | 117.4 |
| rotation=0.2 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 117.4 |
| rotation=0.2 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 0.53 | 0.69 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 3.0 |
| rotation=0.4 | A overlap-only | 0.93 [0.79, 0.98] | 0.92 | 0.37 | 0.52 ± 0.02 | 0.57 | 0.57 | – | 0.005 | 0.6 |
| rotation=0.4 | B original | 1.00 [0.89, 1.00] | 1.00 | 0.26 | 0.41 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 1.6 |
| rotation=0.4 | C V1 (strong+moderate) | 0.37 [0.22, 0.54] | 1.00 | 0.22 | 0.30 ± 0.05 | 0.57 | 0.57 | – | 0.000 | 96.9 |
| rotation=0.4 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 96.9 |
| rotation=0.4 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 0.26 | 0.42 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 2.9 |
| rotation=0.6 | A overlap-only | 0.03 [0.01, 0.17] | 0.90 | 0.04 | 0.06 ± 0.02 | 0.23 | 0.23 | – | 0.001 | 0.4 |
| rotation=0.6 | B original | 0.97 [0.83, 0.99] | 1.00 | 0.10 | 0.18 ± 0.01 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| rotation=0.6 | C V1 (strong+moderate) | 0.03 [0.01, 0.17] | 1.00 | 0.04 | 0.06 ± 0.02 | 0.23 | 0.23 | – | 0.000 | 52.3 |
| rotation=0.6 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 52.3 |
| rotation=0.6 | B tuned | 0.73 [0.56, 0.86] | 1.00 | 0.09 | 0.16 ± 0.02 | 0.00 | 0.00 | – | 0.000 | 2.9 |
| rotation=0.8 | A overlap-only | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 0.4 |
| rotation=0.8 | B original | 0.17 [0.07, 0.34] | 1.00 | 0.00 | 0.01 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| rotation=0.8 | C V1 (strong+moderate) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 36.4 |
| rotation=0.8 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 36.4 |
| rotation=0.8 | B tuned | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 2.8 |

V1 network tracer (from V1's first fixed-offset group):

| Config | Tracer built | Coordinated posts recovered | Traced posts that are coordinated |
|---|---|---|---|
| rotation=0 | 1.00 | 1.00 | 1.00 |
| rotation=0.1 | 1.00 | 1.00 | 1.00 |
| rotation=0.2 | 0.87 | 0.87 | 1.00 |
| rotation=0.4 | 0.57 | 0.33 | 1.00 |
| rotation=0.6 | 0.27 | 0.10 | 1.00 |
| rotation=0.8 | 0.00 | 0.00 | – |

Paired per-seed difference, V1 minus baseline (coordinated: account F1, positive favours V1; organic-only: share of datasets with a flagged group, negative favours V1). Mean [95% percentile-bootstrap CI]; exploratory, no multiple-comparison correction:

| Config | vs A overlap-only | vs B original | vs B tuned |
|---|---|---|---|
| rotation=0 | +0.02 [+0.01, +0.02] C better | -0.00 [-0.00, +0.00] no clear difference | -0.00 [-0.00, +0.00] no clear difference |
| rotation=0.1 | +0.09 [+0.08, +0.10] C better | +0.08 [+0.07, +0.09] C better | +0.08 [+0.07, +0.09] C better |
| rotation=0.2 | +0.02 [-0.09, +0.12] no clear difference | +0.02 [-0.10, +0.12] no clear difference | +0.02 [-0.10, +0.12] no clear difference |
| rotation=0.4 | -0.22 [-0.29, -0.14] C worse | -0.11 [-0.22, +0.00] no clear difference | -0.11 [-0.22, -0.01] C worse |
| rotation=0.6 | +0.00 [+0.00, +0.00] C better | -0.12 [-0.15, -0.07] C worse | -0.10 [-0.15, -0.04] C worse |
| rotation=0.8 | +0.00 [+0.00, +0.00] no clear difference | -0.01 [-0.02, -0.00] C worse | +0.00 [+0.00, +0.00] no clear difference |

## P6_notification_bursts (RQ1): Notification bursts: organic-only data plus 35 followers who like each of 3 posts after an exponential delay of the given mean (seconds)

| Config | Method | Detected [95% CI] | P | R | F1 (mean ± SE) | Fragments | Spurious | Organic FP [95% CI] | Acct FPR | ms |
|---|---|---|---|---|---|---|---|---|---|---|
| loyal_delay_mean=15 | A overlap-only | – | – | – | – | – | 1.00 | 1.00 [0.89, 1.00] | 0.045 | 0.4 |
| loyal_delay_mean=15 | B original | – | – | – | – | – | 1.40 | 1.00 [0.89, 1.00] | 0.043 | 1.0 |
| loyal_delay_mean=15 | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 75.5 |
| loyal_delay_mean=15 | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 75.5 |
| loyal_delay_mean=15 | B tuned | – | – | – | – | – | 1.00 | 1.00 [0.89, 1.00] | 0.043 | 2.0 |
| loyal_delay_mean=45 | A overlap-only | – | – | – | – | – | 1.00 | 1.00 [0.89, 1.00] | 0.045 | 0.4 |
| loyal_delay_mean=45 | B original | – | – | – | – | – | 1.77 | 1.00 [0.89, 1.00] | 0.040 | 1.0 |
| loyal_delay_mean=45 | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 70.2 |
| loyal_delay_mean=45 | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 70.2 |
| loyal_delay_mean=45 | B tuned | – | – | – | – | – | 1.03 | 1.00 [0.89, 1.00] | 0.043 | 2.0 |
| loyal_delay_mean=120 | A overlap-only | – | – | – | – | – | 1.00 | 1.00 [0.89, 1.00] | 0.045 | 0.4 |
| loyal_delay_mean=120 | B original | – | – | – | – | – | 2.30 | 1.00 [0.89, 1.00] | 0.030 | 0.9 |
| loyal_delay_mean=120 | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 68.0 |
| loyal_delay_mean=120 | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 68.0 |
| loyal_delay_mean=120 | B tuned | – | – | – | – | – | 1.03 | 1.00 [0.89, 1.00] | 0.040 | 1.9 |
| loyal_delay_mean=300 | A overlap-only | – | – | – | – | – | 1.00 | 1.00 [0.89, 1.00] | 0.045 | 0.4 |
| loyal_delay_mean=300 | B original | – | – | – | – | – | 0.93 | 0.73 [0.56, 0.86] | 0.007 | 0.8 |
| loyal_delay_mean=300 | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 67.0 |
| loyal_delay_mean=300 | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 67.0 |
| loyal_delay_mean=300 | B tuned | – | – | – | – | – | 1.03 | 0.97 [0.83, 0.99] | 0.037 | 1.9 |
| loyal_delay_mean=900 | A overlap-only | – | – | – | – | – | 1.00 | 1.00 [0.89, 1.00] | 0.045 | 0.4 |
| loyal_delay_mean=900 | B original | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.8 |
| loyal_delay_mean=900 | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 67.0 |
| loyal_delay_mean=900 | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 67.0 |
| loyal_delay_mean=900 | B tuned | – | – | – | – | – | 0.53 | 0.53 [0.36, 0.70] | 0.013 | 1.9 |
| loyal_delay_mean=1800 | A overlap-only | – | – | – | – | – | 1.00 | 1.00 [0.89, 1.00] | 0.045 | 0.4 |
| loyal_delay_mean=1800 | B original | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.8 |
| loyal_delay_mean=1800 | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 67.2 |
| loyal_delay_mean=1800 | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 67.2 |
| loyal_delay_mean=1800 | B tuned | – | – | – | – | – | 0.03 | 0.03 [0.01, 0.17] | 0.001 | 1.8 |

Paired per-seed difference, V1 minus baseline (coordinated: account F1, positive favours V1; organic-only: share of datasets with a flagged group, negative favours V1). Mean [95% percentile-bootstrap CI]; exploratory, no multiple-comparison correction:

| Config | vs A overlap-only | vs B original | vs B tuned |
|---|---|---|---|
| loyal_delay_mean=15 | -1.00 [-1.00, -1.00] C better | -1.00 [-1.00, -1.00] C better | -1.00 [-1.00, -1.00] C better |
| loyal_delay_mean=45 | -1.00 [-1.00, -1.00] C better | -1.00 [-1.00, -1.00] C better | -1.00 [-1.00, -1.00] C better |
| loyal_delay_mean=120 | -1.00 [-1.00, -1.00] C better | -1.00 [-1.00, -1.00] C better | -1.00 [-1.00, -1.00] C better |
| loyal_delay_mean=300 | -1.00 [-1.00, -1.00] C better | -0.73 [-0.87, -0.57] C better | -0.97 [-1.00, -0.90] C better |
| loyal_delay_mean=900 | -1.00 [-1.00, -1.00] C better | +0.00 [+0.00, +0.00] no clear difference | -0.53 [-0.70, -0.37] C better |
| loyal_delay_mean=1800 | -1.00 [-1.00, -1.00] C better | +0.00 [+0.00, +0.00] no clear difference | -0.03 [-0.10, +0.00] no clear difference |

## P7_heavy_users (RQ2): Organic heavy-user activity (weight of the 10% heavy accounts)

| Config | Method | Detected [95% CI] | P | R | F1 (mean ± SE) | Fragments | Spurious | Organic FP [95% CI] | Acct FPR | ms |
|---|---|---|---|---|---|---|---|---|---|---|
| heavy_weight=1 | A overlap-only | 1.00 [0.89, 1.00] | 0.99 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 0.7 |
| heavy_weight=1 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| heavy_weight=1 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 174.4 |
| heavy_weight=1 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 174.4 |
| heavy_weight=1 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.0 |
| heavy_weight=1 (organic-only) | A overlap-only | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.4 |
| heavy_weight=1 (organic-only) | B original | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.7 |
| heavy_weight=1 (organic-only) | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 22.4 |
| heavy_weight=1 (organic-only) | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 22.4 |
| heavy_weight=1 (organic-only) | B tuned | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 1.7 |
| heavy_weight=5 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| heavy_weight=5 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| heavy_weight=5 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 178.3 |
| heavy_weight=5 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 178.3 |
| heavy_weight=5 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.0 |
| heavy_weight=5 (organic-only) | A overlap-only | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.4 |
| heavy_weight=5 (organic-only) | B original | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.7 |
| heavy_weight=5 (organic-only) | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 24.5 |
| heavy_weight=5 (organic-only) | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 24.5 |
| heavy_weight=5 (organic-only) | B tuned | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 1.6 |
| heavy_weight=20 | A overlap-only | 1.00 [0.89, 1.00] | 0.82 | 1.00 | 0.90 ± 0.01 | 0.00 | 0.07 | – | 0.016 | 0.7 |
| heavy_weight=20 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| heavy_weight=20 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 0.99 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 221.0 |
| heavy_weight=20 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 221.0 |
| heavy_weight=20 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.0 |
| heavy_weight=20 (organic-only) | A overlap-only | – | – | – | – | – | 0.07 | 0.07 [0.02, 0.21] | 0.002 | 0.4 |
| heavy_weight=20 (organic-only) | B original | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.7 |
| heavy_weight=20 (organic-only) | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 59.6 |
| heavy_weight=20 (organic-only) | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 59.6 |
| heavy_weight=20 (organic-only) | B tuned | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 1.7 |
| heavy_weight=50 | A overlap-only | 1.00 [0.89, 1.00] | 0.74 | 1.00 | 0.85 ± 0.01 | 0.00 | 0.07 | – | 0.036 | 0.7 |
| heavy_weight=50 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| heavy_weight=50 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 0.99 | 1.00 | 0.99 ± 0.00 | 0.00 | 0.00 | – | 0.001 | 353.5 |
| heavy_weight=50 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 353.5 |
| heavy_weight=50 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.0 |
| heavy_weight=50 (organic-only) | A overlap-only | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.5 |
| heavy_weight=50 (organic-only) | B original | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 0.7 |
| heavy_weight=50 (organic-only) | C V1 (strong+moderate) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 197.4 |
| heavy_weight=50 (organic-only) | C V1 (strong only) | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 197.4 |
| heavy_weight=50 (organic-only) | B tuned | – | – | – | – | – | 0.00 | 0.00 [0.00, 0.11] | 0.000 | 1.6 |

Paired per-seed difference, V1 minus baseline (coordinated: account F1, positive favours V1; organic-only: share of datasets with a flagged group, negative favours V1). Mean [95% percentile-bootstrap CI]; exploratory, no multiple-comparison correction:

| Config | vs A overlap-only | vs B original | vs B tuned |
|---|---|---|---|
| heavy_weight=1 | +0.00 [+0.00, +0.01] C better | -0.00 [-0.00, +0.00] no clear difference | -0.00 [-0.00, +0.00] no clear difference |
| heavy_weight=1 (organic-only) | +0.00 [+0.00, +0.00] no clear difference | +0.00 [+0.00, +0.00] no clear difference | +0.00 [+0.00, +0.00] no clear difference |
| heavy_weight=5 | +0.02 [+0.01, +0.02] C better | -0.00 [-0.00, +0.00] no clear difference | -0.00 [-0.00, +0.00] no clear difference |
| heavy_weight=5 (organic-only) | +0.00 [+0.00, +0.00] no clear difference | +0.00 [+0.00, +0.00] no clear difference | +0.00 [+0.00, +0.00] no clear difference |
| heavy_weight=20 | +0.09 [+0.08, +0.11] C better | -0.00 [-0.01, -0.00] C worse | -0.00 [-0.01, -0.00] C worse |
| heavy_weight=20 (organic-only) | -0.07 [-0.17, +0.00] no clear difference | +0.00 [+0.00, +0.00] no clear difference | +0.00 [+0.00, +0.00] no clear difference |
| heavy_weight=50 | +0.14 [+0.13, +0.16] C better | -0.01 [-0.01, -0.00] C worse | -0.01 [-0.01, -0.00] C worse |
| heavy_weight=50 (organic-only) | +0.00 [+0.00, +0.00] no clear difference | +0.00 [+0.00, +0.00] no clear difference | +0.00 [+0.00, +0.00] no clear difference |

## P8_jitter (RQ2): Timing jitter (seconds, Gaussian sd per like)

| Config | Method | Detected [95% CI] | P | R | F1 (mean ± SE) | Fragments | Spurious | Organic FP [95% CI] | Acct FPR | ms |
|---|---|---|---|---|---|---|---|---|---|---|
| jitter=5 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| jitter=5 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| jitter=5 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 177.6 |
| jitter=5 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 177.6 |
| jitter=5 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.1 |
| jitter=20 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| jitter=20 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| jitter=20 | C V1 (strong+moderate) | 1.00 [0.89, 1.00] | 1.00 | 0.98 | 0.99 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 176.3 |
| jitter=20 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 176.3 |
| jitter=20 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.1 |
| jitter=40 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| jitter=40 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.5 |
| jitter=40 | C V1 (strong+moderate) | 0.63 [0.46, 0.78] | 1.00 | 0.33 | 0.42 ± 0.07 | 0.00 | 0.00 | – | 0.000 | 173.1 |
| jitter=40 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 173.1 |
| jitter=40 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.1 |
| jitter=80 | A overlap-only | 1.00 [0.89, 1.00] | 0.97 | 1.00 | 0.98 ± 0.00 | 0.00 | 0.00 | – | 0.002 | 0.7 |
| jitter=80 | B original | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 1.4 |
| jitter=80 | C V1 (strong+moderate) | 0.23 [0.12, 0.41] | 1.00 | 0.09 | 0.13 ± 0.04 | 0.00 | 0.00 | – | 0.000 | 170.0 |
| jitter=80 | C V1 (strong only) | 0.00 [0.00, 0.11] | – | 0.00 | 0.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 170.0 |
| jitter=80 | B tuned | 1.00 [0.89, 1.00] | 1.00 | 1.00 | 1.00 ± 0.00 | 0.00 | 0.00 | – | 0.000 | 3.0 |

Paired per-seed difference, V1 minus baseline (coordinated: account F1, positive favours V1; organic-only: share of datasets with a flagged group, negative favours V1). Mean [95% percentile-bootstrap CI]; exploratory, no multiple-comparison correction:

| Config | vs A overlap-only | vs B original | vs B tuned |
|---|---|---|---|
| jitter=5 | +0.02 [+0.01, +0.02] C better | -0.00 [-0.00, +0.00] no clear difference | -0.00 [-0.00, +0.00] no clear difference |
| jitter=20 | +0.01 [+0.00, +0.02] C better | -0.01 [-0.01, -0.00] C worse | -0.01 [-0.01, -0.00] C worse |
| jitter=40 | -0.57 [-0.69, -0.44] C worse | -0.58 [-0.71, -0.46] C worse | -0.58 [-0.71, -0.46] C worse |
| jitter=80 | -0.86 [-0.93, -0.77] C worse | -0.87 [-0.95, -0.78] C worse | -0.87 [-0.95, -0.78] C worse |

## Exploratory scoreboard: configurations by paired bootstrap verdict (V1 vs each baseline)

Coordinated configurations are judged on account F1 (higher is better); organic-only configurations on the share of datasets with any flagged group (lower is better). The two kinds are counted separately and never combined. No multiple-comparison correction: treat the counts as descriptive.

| Experiment | Kind | Baseline | V1 better | V1 worse | No clear difference |
|---|---|---|---|---|---|
| P1_headline | coordinated | A overlap-only | 3 | 0 | 0 |
| P1_headline | coordinated | B original | 0 | 0 | 3 |
| P1_headline | coordinated | B tuned | 0 | 0 | 3 |
| P1_headline | organic-only | A overlap-only | 2 | 0 | 1 |
| P1_headline | organic-only | B original | 1 | 0 | 2 |
| P1_headline | organic-only | B tuned | 1 | 0 | 2 |
| P2_cohort_spread | coordinated | A overlap-only | 5 | 0 | 0 |
| P2_cohort_spread | coordinated | B original | 2 | 0 | 3 |
| P2_cohort_spread | coordinated | B tuned | 0 | 0 | 5 |
| P3_random_delays | coordinated | A overlap-only | 0 | 3 | 0 |
| P3_random_delays | coordinated | B original | 0 | 2 | 1 |
| P3_random_delays | coordinated | B tuned | 0 | 3 | 0 |
| P4_participation | coordinated | A overlap-only | 3 | 0 | 2 |
| P4_participation | coordinated | B original | 0 | 2 | 3 |
| P4_participation | coordinated | B tuned | 0 | 2 | 3 |
| P5_rotation | coordinated | A overlap-only | 3 | 1 | 2 |
| P5_rotation | coordinated | B original | 1 | 2 | 3 |
| P5_rotation | coordinated | B tuned | 1 | 2 | 3 |
| P6_notification_bursts | organic-only | A overlap-only | 6 | 0 | 0 |
| P6_notification_bursts | organic-only | B original | 4 | 0 | 2 |
| P6_notification_bursts | organic-only | B tuned | 5 | 0 | 1 |
| P7_heavy_users | coordinated | A overlap-only | 4 | 0 | 0 |
| P7_heavy_users | coordinated | B original | 0 | 2 | 2 |
| P7_heavy_users | coordinated | B tuned | 0 | 2 | 2 |
| P7_heavy_users | organic-only | A overlap-only | 0 | 0 | 4 |
| P7_heavy_users | organic-only | B original | 0 | 0 | 4 |
| P7_heavy_users | organic-only | B tuned | 0 | 0 | 4 |
| P8_jitter | coordinated | A overlap-only | 2 | 2 | 0 |
| P8_jitter | coordinated | B original | 0 | 3 | 1 |
| P8_jitter | coordinated | B tuned | 0 | 3 | 1 |
| **all** | coordinated | A overlap-only | 20 | 6 | 4 |
| **all** | coordinated | B original | 3 | 11 | 16 |
| **all** | coordinated | B tuned | 1 | 12 | 17 |
| **all** | organic-only | A overlap-only | 8 | 0 | 5 |
| **all** | organic-only | B original | 5 | 0 | 8 |
| **all** | organic-only | B tuned | 6 | 0 | 7 |

