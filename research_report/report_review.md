# Quality review of the mini research report

Reviewed file: `mini_research_report.md`, on branch `research-evaluation`, November 2026.
This is a self-review against the Phase 3 checklist. It records what was checked, how, and what is still weak.

## 1. Are all numerical claims supported by actual results?

**Yes, and this is checked mechanically.**

- `verify_report_numbers.py` recomputes every number in the report from the committed Phase 2 outputs:
  `summary.csv`, `paired_comparisons.csv`, `raw_results.csv`, `run_info.json` and `tuned_parameters.json`.
- For each number, it checks that the exact text appears in the report.
- It also fails if any two-decimal number in the report is not covered by a check.
- **Current result:** 47 distinct two-decimal values covered, 0 problems.
- **Mutation test:** two values were deliberately altered in a copy of the report (0.78 → 0.79, and 167 → 160 flagged datasets). The verifier reported both, plus the unbacked "0.79", and exited with code 1.
- **Upstream chain:** the release test suite already checks two further links:
  - the committed tables and figures regenerate byte for byte from `raw_results.csv`;
  - re-running two held-out seeds reproduces the committed metric columns.
- **Scope:**
  - Only held-out results (seeds 5000–5029) are cited.
  - Phase 1 development results (seeds 1000–1019) are not used.
  - The tuning score (0.691 vs 0.677) comes from the tuning seeds, and the report says so.

Corrections made while drafting:

- **Runtime.** A sentence said V1's median runtime was "about 160–180 ms" for coordinated datasets. That holds only at the default size; V1's medians range from 22 to 354 ms across configurations. The sentence now gives the default-setting values (176.5 / 3.0 / 0.7 ms) and the full range.
- **Pooled false-positive rates.** An early draft pooled the false-positive counts as rates. The final text reports counts by scenario family (150 plain organic and heavy-user datasets; 240 follower-audience datasets), because a pooled rate depends on the scenario mix.
- **Rule timing.** "A rule fixed before any experiment" became "before the main experiments", because a 3-seed smoke test ran before `RESEARCH_QUESTIONS.md` was written.
- **Wording of untested claims.** "Should not" (for human reactions) became "are not expected to". The explanation of V1's edge at light rotation is now explicitly marked as untested.

## 2. Is the comparison scientifically fair?

It is fair in its stated scope, with known asymmetries that the report names.

**In favour of fairness:**
- tuning and held-out seeds are disjoint, and a code guard enforces it;
- the protocol was written before tuning;
- the tuned baseline was chosen by a declared objective and tie-break;
- V1's decision rule was fixed before the main experiments;
- all methods see identical datasets, and comparisons are paired by seed;
- scenarios that are hard for V1 (random delays, participation, jitter, rotation) are reported as prominently as its strength.

**Against fairness, all stated in Section 6:**
- **Circularity:** the generator and V1 share an author and a model of coordination.
- **Tuning asymmetry:** only B was tuned. Its tuning scenarios share families with the test scenarios, though on different seeds.
- **Objective choice:** the tuning objective is one choice among several.

**Two caveats not stated in the report:**
- Commit history cannot prove that `PHASE2_PROTOCOL.md` was written before tuning, because both were committed together. The claim rests on the author's workflow.
- The default scenario (a group of 40 accounts spread over 120 s) resembles the example V1 was originally built around.

## 3. Are limitations discussed honestly?

Yes. Each of the following is stated in the report:
- the evaluation is synthetic only;
- there is no real-world accuracy estimate;
- an anomaly is not proof of intent or of who controls the accounts;
- jitter does not grow with the time between posts;
- there are no follower graphs or adaptive adversaries;
- one factor is varied at a time, at a single dataset size;
- only B was tuned;
- the paired intervals use a normal approximation (some reach −1.01 in the CSV when outcomes are nearly constant);
- there is no multiple-comparison correction, and some "wins" and "losses" are differences of about 0.01;
- V1's strong tier depends on side signals.

The abstract and conclusion both state that results describe behaviour inside a synthetic world model.

## 4. Are the figures legible?

The Phase 2 figures as rendered had four presentation problems:
- methods overlapped at F1 ≈ 1.0 and hid one another (tuned B was invisible in Fig. 3a);
- tick labels were formatted inconsistently ("1" next to "0.25");
- the leftmost markers covered the "1.00" tick label;
- the captions did not say that the x axes are categorical.

**Fixes (presentation only):** `evaluation/bench/svgplot.py` now offsets methods horizontally by 5 px, adds white marker outlines, uses two-decimal ticks and pads the plot area. The captions now state that the x axis is categorical and that points are offset. All five SVGs in `evaluation/` were regenerated; `git diff` confirms that no CSV or table changed.

**Report figures:**
- `figures/figure1_false_positives_vs_participation`: the false-positive behaviour (V1's strength) next to partial participation (a weakness).
- `figures/figure2_failure_modes`: random delays and jitter.
- Each is provided as an SVG and as a 2× PNG for Word/PDF conversion.
- They were rendered with headless Edge and inspected visually after the fixes.
- Rotation results are given in Table 2 rather than a third figure, to save space.

## 5. Are all references real and accurately cited?

Every reference was checked against **Crossref DOI metadata** (api.crossref.org); TwiBot-22 was checked against the **arXiv API**. Titles, authors, venues, years and page ranges in the report match the returned metadata.

| # | Work | DOI / identifier | Verified |
|---|---|---|---|
| 1 | Beutel et al., CopyCatch, WWW 2013, pp. 119–130 | 10.1145/2488388.2488400 | Crossref |
| 2 | Cao et al., SynchroTrap ("Uncovering large groups of active malicious accounts…"), CCS 2014, pp. 477–488 | 10.1145/2660267.2660269 | Crossref |
| 3 | Jiang et al., CatchSync, KDD 2014, pp. 941–950 | 10.1145/2623330.2623632 | Crossref |
| 4 | Hooi et al., FRAUDAR, KDD 2016, pp. 895–904 | 10.1145/2939672.2939747 | Crossref |
| 5 | Pacheco et al., ICWSM 15(1), 2021, pp. 455–466 | 10.1609/icwsm.v15i1.18075 | Crossref |
| 6 | Giglietto et al., Information, Communication & Society 23(6), 2020, pp. 867–891 | 10.1080/1369118X.2020.1739732 | Crossref |
| 7 | Cresci et al., WWW Companion 2017, pp. 963–972 | 10.1145/3041021.3055135 | Crossref |
| 8 | Ferrara et al., CACM 59(7), 2016, pp. 96–104 | 10.1145/2818717 | Crossref |
| 9 | Feng et al., TwiBot-22 | arXiv:2206.04564 | arXiv |
| 10 | Phipson & Smyth, SAGMB 9(1), 2010 | 10.2202/1544-6115.1585 | Crossref |
| 11 | Wilson, JASA 22(158), 1927, pp. 209–212 | 10.1080/01621459.1927.10502953 | Crossref |
| 12 | Benjamini & Hochberg, JRSS-B 57(1), 1995, pp. 289–300 | 10.1111/j.2517-6161.1995.tb02031.x | Crossref |

**Caveats:**
- TwiBot-22 is cited only as an arXiv preprint. Its peer-reviewed venue was not verified here, so none is claimed.
- The one-line summaries of each work in Related Work are general and drawn from their titles and abstracts. Before sending, skim [1], [2] and [5] to confirm the summaries match your own reading.
- The report says SynchroTrap operated "at the scale of large social networks" and avoids naming specific deployments.

## 6. Does the report clearly identify the actual contribution?

Yes. The introduction says the contribution is an evaluation, not a new principle, and notes that lockstep and synchronised-action detection are established [1–3]. It lists three concrete contributions:
1. an open fixed-offset test with false-positive controls;
2. a reproducible benchmark with disjoint seed splits;
3. a map of where the design succeeds and fails.

The conclusion positions V1 as "an interpretable low-false-positive filter, not a better detector overall". The report says V1 is not machine learning, and it presents flags as statistical anomalies, not evidence of malice.

## 7. Is it suitable to send to an academic supervisor?

**Almost. Do these first:**
1. **Author line.** Replace `[Author name]` and confirm the degree and university line.
2. **Code availability.** The header cites the `research-evaluation` branch, which is not pushed yet. A professor who follows the link will see only V1 on `main`. Either push the branch (after your own review) or change the line to "evaluation code available on request".
3. **Length.** Previewed at A4, 11 pt, 2 cm margins and single column, the body is about 3.5 pages plus about 0.8 pages of references. That is slightly over the 2–3 page target. Options:
   - drop Figure 2 (its key numbers are already in Table 2), which brings the body to about 3 pages;
   - or use a two-column or 10 pt template.
4. **PDF.** Convert to PDF with the PNG figures, and check that table widths fit.
5. **No competition material.** Keep the report free of competition material, as it is now. It mentions no platform, accounts, reports or private data. If a professor asks how the project started, answer accurately: the report itself does not need those details, but they should not be misrepresented.
6. **Tailoring.** For a specific lab (for example, graph-based bot detection), add one sentence linking the future-work items to that lab's methods. Do not claim familiarity you do not have.

## Remaining weaknesses that a reviewer may raise

- **No real data.** This is the largest gap; the report states it directly.
- **Circularity.** The benchmark is designed by the same author as the detector. The independently randomised delays only partly counter this, by testing a behaviour V1 cannot see.
- **Baselines.** B is a simplified SynchroTrap-style baseline, not SynchroTrap itself, and no machine-learning or graph-based baseline is included.
- **Statistics.** There is no multiple-comparison correction, the paired intervals use a normal approximation, and many cells reach their ceiling or floor (1.00 or 0.00) on every seed.
- **Scale.** Only one dataset size (30 posts) was tested. V1's runtime (about 177 ms against 3 ms) would matter at scale, and its scaling is unmeasured.
- **Ordering of documents.** The protocol-before-tuning order is documented but cannot be proven from commit history.
