# coordination-detector

Offline detection of **coordinated-looking engagement** in saved public social-media data: groups of accounts that like the same posts, in the same order, with the same delay each time.

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

## Evaluation (research branch)

`evaluation/` holds a reproducible synthetic benchmark that compares this detector with an overlap-only baseline and a time-bucket co-action baseline under jitter, partial participation, audience noise and account rotation. Questions and hypotheses: [RESEARCH_QUESTIONS.md](RESEARCH_QUESTIONS.md). Method, reproduction steps and limitations: [evaluation/README.md](evaluation/README.md). Results use synthetic data only and say nothing about accuracy on a real platform.

## Layout

```
coordination_detector/  detector.py (groups, indicators, tiers) · network.py (cohort tracing) · cli.py
examples/               make_example.py and the generated example_engagement.json
tests/                  unit and end-to-end tests
tools/check_release.py  pre-publication check
METHODS.md              methods, limitations, false-positive risks
```

## License

MIT - see [LICENSE](LICENSE).
