# coordination-detector

Offline detection of **coordinated-looking engagement** in saved public social-media data: groups of accounts that like the same posts, in the same order, with the same delay each time.

**Research report:** [research_report/Yuxi_He_Research_Report.pdf](research_report/Yuxi_He_Research_Report.pdf) (4 pages): a synthetic-benchmark evaluation of this detector against two baselines. See [Research evaluation](#research-evaluation) below.

It reads JSON files you have already collected and writes evidence reports. It makes no network calls, needs no credentials, and uses only the Python standard library (3.9+).

> **What it is not.** The output is a statistical anomaly report. It does not prove coordinated inauthentic behaviour, shared ownership or a rule violation. Only the platform can establish those, because only the platform holds the account-control signals. See [METHODS.md](METHODS.md) for what each indicator means and where it can mislead.

## Quickstart

```bash
python -m coordination_detector analyze examples/example_engagement.json --out reports/
```

```
2 liker group(s) overlap more than chance allows; see indicators for how much extra weight each deserves. None is a proven violation.
#1 posts [3000, 3001, 3002, 3003, 3004]: strong anomaly (5/5 indicators)
#2 posts [2000, 2001, 2002]: weak / consistent with a shared audience (2/5 indicators)
Network: consistent with ONE shared network: the same accounts repeat fixed delays across all linked posts (3 authors, 5 posts)
Reports written to reports
```

The example is synthetic and seeded (`python examples/make_example.py` regenerates it byte for byte). It contains:

| Posts | What they are | Expected result |
|---|---|---|
| 1000-1013 | organic posts by 14 authors, liked by a shared pool of ordinary users | not flagged |
| 2000-2002 | one author's posts liked by the same 35 loyal followers at random times | flagged for overlap, but **weak / consistent with a shared audience** (false-positive control) |
| 3000-3004 | 40 consecutively registered accounts liking 5 posts by 3 authors, same order, fixed delays | **strong anomaly**; the network report traces all 5 posts |

## Outputs

| File | Contents |
|---|---|
| `detector_report.md` / `.json` | every liker group that overlaps more than chance, with indicator values, thresholds, pairwise timing, data-quality notes and limitations |
| `network_report.md` / `.json` | for the strongest fixed-offset group (or the posts given with `--seed`): the cohort, every other post it likes in lock-step, pairwise delays, reaction order, a comparison with the rest of the sample, alternative explanations and false-positive risks |

## Options

```
python -m coordination_detector analyze INPUT.json [MORE.json ...]
    --out DIR                    output folder (default: reports)
    --seed POST [POST ...]       trace the cohort that liked all of these posts
    --exclude-accounts ID ...    drop accounts everywhere (for example your own)
    --exclude-posts ID ...       drop posts
    --already-reported ID ...    label posts as already reported (labelled, never hidden)
    --author POST=ACCOUNT ...    supply an author the data did not record
```

Exit codes: `0` success, `2` unreadable or wrongly formatted input.

## Input format

One or more JSON files, merged by post id. Only `likers` is required. Timing tests need `liked_at`.

```json
{
  "posts": {
    "3000": {
      "author_id": 601,
      "created_at": "2026-01-10T11:07:01Z",
      "likers": [{"account_id": 9000, "liked_at": "2026-01-10T11:07:03Z"}],
      "more_pages": false,
      "likes": 55, "reposts": 41, "views": 330,
      "body": "post text (optional, used only for a wording-similarity figure)",
      "role": "free-text label for the sample composition"
    },
    "3001": [9000, 9001, 9002]
  },
  "accounts_created": {"9000": "2026-01-05T08:00:00Z"}
}
```

A post may also be a bare list of liker ids (overlap tests only). Set `more_pages: true` when a liker list was cut off; truncated lists are flagged because they under-count overlap.

## Collecting data responsibly

- Collect only what is publicly visible, within the platform's terms and rate limits.
- Keep raw data, credentials and anything identifying real people **out of this repository** (`.gitignore` covers `data/`, `reports/`, logs and credential files).
- Before publishing, run `python tools/check_release.py --deny-file /path/outside/the/repo/denylist.txt`. It fails on credentials, e-mail addresses, home-directory paths, secret-looking file names and any private term you list.
- Treat a strong anomaly as a reason for the platform to look closer, not as a verdict. A report to a platform should describe the observations and their limits, not accuse an author.

## Tests

```bash
python -m unittest discover -s tests
```

The tests cover the statistics, each timing label, tier rules, the false-positive controls, the network tracer, CLI determinism, reproducibility of the example, and the release hygiene check.

## Research evaluation

### Motivation

Synchrony (accounts acting on the same objects at nearly the same time) is a standard signal for coordinated behaviour, but ordinary audiences are synchronised too: followers react to a notification within seconds, and loyal followers like most of an author's posts. This project asks what a detector gains, and loses, by requiring something narrower: that the **same accounts repeat their own fixed delay** from one post to the next. It is an evaluation of that one design, not a new detection principle. The detector uses statistics only (hypergeometric tails, permutation tests, robust z-scores); there is **no machine learning**.

### Methods compared

| | Method | What it uses |
|---|---|---|
| A | Overlap-only | V1's group-forming step alone: pairwise liker overlap with a Bonferroni-corrected hypergeometric test; no timing |
| B | Time-bucket co-action | A simplified SynchroTrap-style baseline (not a reimplementation): accounts that share at least 3 (post, time-bucket) items. Run with the original setting (300 s, groups of 5) and a **tuned** setting (2,400 s, groups of 15) chosen on separate tuning seeds |
| C | V1 detector | Overlap groups plus a seeded permutation test for a repeated per-account fixed delay, with same-session and single-burst guards. See [METHODS.md](METHODS.md) |

### Design

- **Synthetic data only.** A seeded generator builds datasets with known ground truth (group size, jitter, participation, rotation, cohort spread, random delays, audience size, heavy users, loyal audiences, notification bursts). The benchmark code reads no external data.
- **Disjoint seeds.** Tuning seeds 2000-2019 (used only to tune baseline B) and held-out seeds 5000-5029 (30 per configuration, 43 configurations, 1,290 datasets). V1 and baseline A are not tuned.
- **Protocol first.** Questions and hypotheses: [RESEARCH_QUESTIONS.md](RESEARCH_QUESTIONS.md); held-out protocol: [evaluation/PHASE2_PROTOCOL.md](evaluation/PHASE2_PROTOCOL.md).

### Results (held-out seeds, synthetic data)

| Condition | A overlap-only | B tuned | C V1 |
|---|---|---|---|
| Organic-only datasets flagged (of 390) | 242 | 167 | 0 |
| Independent random delays (range 600 s): account F1 | 0.98 | 1.00 | 0.00 |
| Participation 0.4: account F1 | 0.00 | 0.43 | 0.00 |
| Timing jitter sd 40 s: account F1 | 0.98 | 1.00 | 0.42 |
| Account rotation 0.1: account F1 | 0.82 | 0.83 | 0.91 |

V1 flagged none of the 390 organic-only datasets, including audiences that react within seconds of a post, where both time-bucket variants raise false alarms. In exchange it is clearly worse when coordinated accounts randomise their delays, act on only part of the posts, jitter by 40 s or more, or rotate at higher rates, and it is much slower than the tuned baseline (176.5 ms vs 3.0 ms per dataset at default settings, one machine). It is best read as an interpretable, low-false-positive *filter*, not a better detector overall. Full tables with confidence intervals: [evaluation/results_phase2/tables.md](evaluation/results_phase2/tables.md); the earlier development run is in [evaluation/results/](evaluation/results/).

### Research report

[research_report/Yuxi_He_Research_Report.pdf](research_report/Yuxi_He_Research_Report.pdf) is the 4-page report (source: [research_report/mini_research_report.md](research_report/mini_research_report.md)). Every number in it is recomputed from the committed results by `research_report/verify_report_numbers.py`; the review notes are in [research_report/report_review.md](research_report/report_review.md).

### Reproduce

All commands run from the repository root with Python 3.10+ and only the standard library (about 10 minutes for the full held-out run).

```bash
python -m unittest discover -s tests                       # unit tests, including regeneration checks
python evaluation/tune_baseline.py                          # tuning seeds only
python evaluation/run_experiments.py --config evaluation/configs/phase2.json \
       --tuned evaluation/results_phase2/tuned_parameters.json --out evaluation/results_phase2
python evaluation/summarize_phase2.py                       # tables, paired comparisons, figures
python research_report/make_figures.py                      # report Figure 1
python research_report/verify_report_numbers.py             # every number in the report vs the results
python research_report/make_pdf.py                          # rebuild the PDF (needs Microsoft Edge)
```

Metric columns are deterministic; only the runtime columns vary by machine. Details and the Phase 1 commands: [evaluation/README.md](evaluation/README.md).

### Scientific limitations

- **Circularity.** The generator and the detector share an author and a model of coordination, so V1 is tested on the behaviour it was designed for.
- **No real-world estimate.** Nothing here measures precision or recall on a real platform. A flag is a statistical anomaly, not evidence of intent or of who controls the accounts.
- **Simplified world.** No follower graphs, daily cycles or adaptive adversaries; jitter does not grow with the gap between posts; factors were varied one at a time at a single dataset size.
- **Tuning asymmetry.** Only baseline B was tuned, on scenario families shared with the test set (different seeds); a stricter false-positive cap would select other settings.
- **Statistics.** No multiple-comparison correction, so configuration-level wins and losses are exploratory; the paired intervals are seeded bootstrap intervals, adopted after the normal-approximation intervals proved invalid in 4 of 129 comparisons (documented in the protocol amendment).
- **Baselines.** B is SynchroTrap-style, not SynchroTrap; there is no graph-based or machine-learning baseline.

Real-data validation against independently corroborated coordination is the main open question.

## Layout

```
coordination_detector/  detector.py (groups, indicators, tiers) · network.py (cohort tracing) · cli.py
examples/               make_example.py and the generated example_engagement.json
tests/                  unit and end-to-end tests (detector, benchmark, Phase 2, report numbers)
tools/check_release.py  pre-publication check
evaluation/             synthetic benchmark: generator, methods, metrics, configs, results, figures
research_report/        PDF report, Markdown source, figure and PDF scripts, number verifier
RESEARCH_QUESTIONS.md   research questions and hypotheses
METHODS.md              methods, limitations, false-positive risks
```

## License

MIT - see [LICENSE](LICENSE).
