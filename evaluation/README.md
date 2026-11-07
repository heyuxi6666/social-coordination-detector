# Evaluation

A reproducible, fully synthetic benchmark that compares three coordination detectors on datasets with known ground truth. The questions, hypotheses and metric definitions are fixed in [../RESEARCH_QUESTIONS.md](../RESEARCH_QUESTIONS.md) (written before the full grid was run).

| Method | What it is |
|---|---|
| **A** overlap-only | V1's group-forming step alone: pairwise liker overlap, hypergeometric tail, Bonferroni; no timing |
| **B** time-bucket | SynchroTrap-style co-action: accounts linked when they like the same posts inside the same 300 s bucket at least 3 times (item Jaccard >= 0.5) |
| **C** V1 detector | `coordination_detector.detector.analyse`; flagged = tier strong or moderate (`C_v1_strong`: strong only) |

No machine learning is involved. Standard library only.

## Reproduce

From the repository root (Python 3.10+ for the test that checks imports; the benchmark itself runs on 3.9+):

```bash
python evaluation/run_experiments.py     # about 3 minutes; writes evaluation/results/raw_results.csv and run_info.json
python evaluation/summarize.py           # writes summary.csv, tables.md and figures/*.svg
python -m unittest discover -s tests     # unit tests, including the benchmark and metrics
```

Quick check: `python evaluation/run_experiments.py --seeds 3 --only E1_jitter --out /tmp/quick`.

Everything is seeded (seeds 1000-1019). Re-running reproduces every metric column byte for byte; only `runtime_s` and `trace_runtime_s` (wall-clock) change.

## Layout

```
configs/experiments.json   scenarios and sweeps (E0 headline, E1 jitter, E2 participation, E3 audience size,
                           E4 heavy users, E5 group size, E6 rotation); 20 seeds each
bench/generator.py         the synthetic world: Scenario parameters, ground truth
bench/methods.py           methods A, B, C and V1's network tracer
bench/metrics.py           account- and group-level scoring, Wilson intervals, aggregation
bench/runner.py            experiment expansion and per-dataset evaluation
bench/svgplot.py           dependency-free SVG charts
run_experiments.py         raw per-dataset CSV
summarize.py               summary.csv, tables.md, figures
results/                   outputs of the last full run
```

## Generator parameters

Number of accounts (`n_accounts`) and posts (`n_posts`), coordinated group size (`group_size`), coordinated posts and authors, timing jitter (`jitter`, Gaussian sd per like, seconds), `participation`, account `rotation`, organic audience size, heavy-user share and weight, loyal followers (with `loyal_delay_mean` small, a notification burst), cohort spread, and the seed. `id_adjacent` and `repost_signal` reproduce the two side signals the V1 example plants and are off by default.

## Limitations and potential biases

1. **Same author, same assumptions.** The generator and the detector share an author and a concept of coordination (accounts repeating a personal fixed delay). Method C is therefore tested on the behaviour it was designed for. Results show behaviour inside this world model, **not** performance on a real platform.
2. **No real ground truth.** No labelled real platform data are used or available. Nothing here supports a claim of real-world precision or recall.
3. **Jitter does not grow with time.** Noise is the same for every post pair. In the one real case study the cross-day jitter grew with the gap between posts; the benchmark does not model that.
4. **Simple organic behaviour.** Exponential like delays, a weighted random audience and an optional heavy-user class. Real audiences have follower graphs, topical interest, diurnal cycles and bursts; none is modelled. Heavy users here do not like in sessions.
5. **Adversary model.** Evasion is limited to jitter, partial participation and rotation (the new account keeps the replaced account's delay). Randomising per-account delays across posts, mimicking organic timing, or splitting the group is not tested.
6. **One factor at a time.** Sweeps vary one parameter from the defaults; interactions are not explored.
7. **Fixed, untuned thresholds.** All three methods use defaults. Method B in particular might improve with tuning (bucket width, item threshold), and so might A's account rule. A tuned B was not tried.
8. **Account rule for A and B is a design choice.** A flags accounts that liked at least half of a group's posts; B flags a connected component. Other rules give other precision/recall numbers.
9. **Only 20 seeds** per configuration and a single dataset size (30 posts, 2000 accounts). Intervals are reported, but small differences should not be over-read. The sweeps use one sample of seeds each, with no correction for multiple comparisons across the many configurations.
10. **Group-level matching** uses Jaccard >= 0.5 on post sets; other thresholds change the detection rates.
11. **Defaults mirror the V1 example** (group of 40, 120 s spread), which favours detection of large, well-spread groups.
12. **Runtime** is wall-clock on one machine and includes interpreter overhead; it is only indicative of relative cost.
13. **Dataset truncation.** The platform returns at most 100 likers per post; the generator does not cap lists, so at high organic audience plus a large group a post can exceed 100 likers.

## Privacy

Only synthetic data are used. The folder contains no real accounts, posts, credentials or platform logs; `python tools/check_release.py` checks the tree before publication.

## Phase 2: tuned baseline on held-out seeds

Protocol (fixed before tuning and before the held-out run): [PHASE2_PROTOCOL.md](PHASE2_PROTOCOL.md). Results: `results_phase2/` (Phase 1 results in `results/` are kept unchanged).

| Split | Seeds | Purpose |
|---|---|---|
| Tuning | 2000-2019 | choose the time-bucket baseline's bucket width and minimum group size (42-cell grid, 11 scenarios) |
| Held-out | 5000-5029 (30 seeds) | every reported Phase 2 number |

```bash
python evaluation/tune_baseline.py                  # tuning seeds only -> results_phase2/tuning_grid.csv, tuned_parameters.json
python evaluation/run_experiments.py --config evaluation/configs/phase2.json \
       --tuned evaluation/results_phase2/tuned_parameters.json --out evaluation/results_phase2    # about 10 minutes
python evaluation/summarize_phase2.py               # summary.csv, paired_comparisons.csv, tables.md, figures/fig3-5
python -m unittest discover -s tests                # includes checks that every committed table regenerates from the raw CSV
```

Selected parameters (tuning seeds only): bucket 2400 s, minimum group 15 accounts. Tuning score 0.691 against 0.677 for the original 300 s / 5, so tuning changed little overall, but it changed behaviour a lot in specific scenarios (wide spread, random delays). V1 and the overlap baseline were not tuned, and V1's code is unmodified.

New generator options: `delay_mode` ("fixed" or "random": independently redrawn delay per account and post) and `cohort_spread` up to 2000 s. New metric: fragment groups (unmatched groups containing at least two true coordinated posts), reported next to spurious groups.

### Additional limitations (Phase 2)

14. **Tuning and test families overlap.** The 11 tuning scenarios come from the same families as the held-out experiments (different seeds, some different parameter values). Held-out seeds were never used to choose anything, but the baseline was tuned on the kinds of scenarios it is then tested on. V1 got no such tuning.
15. **The objective is a choice.** F1 minus false-positive rate, weighted equally across scenarios, accepted a baseline that still flags every notification-burst dataset because the F1 gains elsewhere outweighed one of four negative scenarios. A different objective (for example, a hard cap on false positives) would select different parameters and could change the comparison.
16. **Random-delay scenarios are blind to V1 by construction.** V1 tests for a repeated per-account offset; with `delay_mode: random` no such offset exists, so its failure there is expected. The result shows what V1 cannot see; it does not show that the groups are undetectable.
17. **Tiny differences are labelled.** "Better"/"worse" in the paired tables only means the 95% interval of the mean per-seed difference excludes zero. Some flagged differences are about 0.01 F1 and not practically meaningful. There is no multiple-comparison correction across the 43 configurations.
18. **Zero-variance cells.** Many cells have identical outcomes on all 30 seeds (for example 1.00 detection); intervals there are Wilson bounds, not evidence of exactly 100%.
19. **Rotation and group size interact with the group-match rule.** Under rotation V1 often returns fragments; whether that counts as detection depends on the Jaccard 0.5 rule.
20. **Unmeasured dimensions.** Scale beyond 30 posts, adversaries that adapt to the detector, real follower graphs, and tuned versions of V1 or the overlap baseline were not evaluated.

### Interval amendment (7 November 2026)

Paired comparisons now also carry seeded percentile-bootstrap intervals. The originally specified normal-approximation intervals exceeded [−1, 1] in 4 of 129 comparisons. See the amendment in [PHASE2_PROTOCOL.md](PHASE2_PROTOCOL.md).

The per-configuration F1 error bars in `results*/figures/` are still mean ± 1.96 SE, clipped to [0, 1]. The report's Figure 1(b) instead uses bootstrap intervals computed from the raw results (`research_report/make_figures.py`).
