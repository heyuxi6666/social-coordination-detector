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
