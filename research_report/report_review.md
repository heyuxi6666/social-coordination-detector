# Review of the final academic revision

**Reviewed file:** `mini_research_report.md`, on branch `research-evaluation`, 7 November 2026.

**Scope of the revision:** no experiment was rerun, no detector code was changed, and no number in `raw_results.csv` or `summary.csv` changed.

**What was added:**
- an interval method for the paired comparisons, as extra columns;
- a split scoreboard;
- a bootstrap-interval report figure.

## 1. Corrections made in this revision

| # | Request | What changed | Evidence |
|---|---|---|---|
| 1 | Author name | Placeholder replaced with **Yuxi He**. | Name supplied by the author. No other personal details were added. |
| 2 | Affiliation | "Postgraduate Cyber Security student, The University of Queensland". | No enrolment record was available to support anything more specific, so the requested default is used. |
| 3a | Input features | New Table 1 lists the signals each method uses: liker sets, timestamps, author ids, account-id numbering, like/repost counts. | Checked against `bench/methods.py` and `coordination_detector/detector.py`. |
| 3b | Timing vs metadata vs repost signals | V1's six indicators are now named by kind: three overlap, one timing (fixed-offset cohort), one account-metadata (id adjacency), one count-based (repost-to-like ratio). | See `detector.py`, function `_describe_group`. |
| 3c | Strong-tier diagnostic | The report now explains why *strong* never fires on default data and what the diagnostic scenario plants (see the notes after this table). | Indicator states inspected on seeds 5000/5001; 0/30 and 30/30 from `summary.csv`. |
| 3d | Overloaded notation | The permutation p-value used *m*, which was also B's minimum group size. It is now *p* = (1 + #{*r* : *c_r* ≥ *c*_obs}) / (*R* + 1) with *R* = 500. B's parameters are *w* and *n*_min. | `detector.lockstep`: `(hits + 1) / (perms + 1)`. |
| 3e | Fixed-offset rule | The report now states all four conditions, the tier rules and the single-author exception exactly as coded. | `LOCKSTEP_P`, `MIN_COHORT`, `SESSION_CENTRE`, `MIN_SPAN`, `SPAN_FACTOR` in `detector.py`. |
| 4 | Wins and losses | The previous "7 / 12 / 24" combined F1 comparisons with false-positive comparisons. It is now split (see the notes). Configuration-level verdicts are labelled exploratory. | `paired_comparisons.csv` (`kind`, `metric` columns); `tables.md` scoreboard. |
| 5 | Invalid interval bounds | 4 of 129 paired normal intervals fell outside [−1, 1] (lowest −1.032), and 23 per-configuration F1 intervals (mean ± 1.96 SE) crossed 0 or 1. Corrected as described in the notes. | `IntervalTests` in `tests/test_phase2.py`. |
| 6 | Length | Figure 2 removed, with its key values kept in Table 3. Bullet lists turned into prose, and repeated statements removed. | Figure 1 kept, now with valid intervals. See section 2 below. |
| 7 | Citations | Descriptions of CopyCatch, SynchroTrap and Pacheco et al. checked against the papers' own text. A bootstrap reference was added (Efron 1979, Crossref-verified). | See section 4. |
| 8 | Code availability | Now reads "Evaluation code available on request." Only the published V1 repository is named. | The `research-evaluation` branch is still local. |
| 9 | This document | Rewritten. | – |
| 10 | Verification | Done. | See section 3. |

**Notes on rows 3c, 4 and 5:**

- **3c – strong tier.** By default the generator supplies no repost counts, so the repost indicator cannot be measured. Group accounts get random ids, so the id-adjacency indicator is measured but does not trigger. *Strong* requires every measurable indicator to trigger, so it never fired (0 of 30 datasets). The diagnostic scenario plants consecutive ids and inflated reposts, and *strong* then fired in 30 of 30. The report states that this tests the tier rule, not detection ability.
- **4 – split counts against tuned B.**
  - 30 coordinated configurations, compared on F1: 1 better / 12 worse / 17 no clear difference.
  - 13 organic-only configurations, compared on false positives: 6 fewer / 0 more / 7 no clear difference.
- **5 – interval corrections.**
  - **Paired intervals:** a seeded percentile bootstrap (10,000 resamples) was added. The original columns are kept, so nothing is silently replaced. Only one verdict changed: cohort spread 1,000 s against original B, a mean difference of 0.005 F1. No tuned-B verdict changed.
  - **Report figure:** Figure 1(b) now uses bootstrap intervals computed from the raw results. Figure 1(a) uses Wilson intervals, which are always within [0, 1].
  - **Documentation:** a dated amendment was added to `PHASE2_PROTOCOL.md`.

### Further fixes found during the revision

- **Wording tightened:**
  - "Unreachable by construction" became "never fired (0 of 30)", because the adjacency indicator could trigger by chance.
  - A sentence claiming the differences would not survive multiple-comparison correction was removed; that was never tested.
  - The rotation explanation is labelled as untested.
- **Baseline B and SynchroTrap.** The report now states that B uses fixed time buckets, whereas SynchroTrap matches two actions whose timestamps differ by at most T_sim. Fixed buckets can split near-simultaneous likes.
- **Verifier crash.** `verify_report_numbers.py` crashed on a GBK console when printing a failure that contained "−". Its output is now forced to UTF-8, so failures are reported instead of raising an error.

## 2. Length

| Measure | Value |
|---|---|
| Total words, including references | 2,576 |
| Body words, including tables and captions | 2,218 |
| Body words, excluding tables | 1,818 |
| Reference words | 356 |
| A4 preview (11 pt Times, 2 cm margins, tables 8.5 pt) | 4 pages in total. The body ends about a quarter of the way down page 4 (≈3.2 pages), and the references take ≈0.7 pages. |

This meets "approximately 3 A4 pages plus references". Body text is 11 pt. If the PDF template uses larger margins or 12 pt, the body grows to about 3.5 pages; the easiest trim is the related-work paragraph.

## 3. Numerical verification

- **Verifier result:** `python research_report/verify_report_numbers.py` passes: 52 distinct two-decimal values covered, 0 problems. Every two-decimal number in the body is recomputed from the committed results, and the script fails on any number it does not cover.
- **What the verifier also checks:**
  - the split win/loss counts;
  - the 4-of-129 interval violation;
  - the single changed verdict;
  - the "standard errors at most 0.07" statement;
  - the author line;
  - the code-availability sentence;
  - the absence of any reference to Figure 2.
- **Mutation test:** three values were deliberately altered (a Table 3 cell, a false-positive count and a win/loss count). All three were caught, and the verifier exited with code 1.
- **Tests:**
  - **Release suite:** 71 tests OK, 6 of them new. The new tests cover:
    - bootstrap determinism and range;
    - the normal interval exceeding the valid range where the bootstrap does not;
    - the committed CSV bounds and verdicts;
    - the split scoreboard;
    - running the report verifier.
  - **Project suite:** 340 OK, 1 skipped.
  - **Regeneration:** the existing tests that regenerate summaries byte for byte from the raw CSV still pass after regeneration.
- **Privacy:** `tools/check_release.py` passes with the private deny-list. The report uses synthetic data only; it contains no real-platform data.

## 4. Citation check

| Ref | What the report says | Checked against |
|---|---|---|
| [1] CopyCatch | Lockstep Page-Like behaviour on Facebook, from the user–Page graph and like timestamps alone | Paper abstract (author-hosted PDF): "detects lockstep Page Like patterns on Facebook by analyzing only the social graph between users and Pages and the times at which the edges … were created" |
| [2] SynchroTrap | Clusters accounts whose actions on the same object fall within a matching window; Jaccard similarity and connected components; deployed in five applications at Facebook and Instagram | Paper (author-hosted PDF): abstract and §4.2–4.4 ("same constraint object", \|Ti − Tj\| ≤ Tsim, Jaccard, connected components); "deployed our system in five applications at Facebook and Instagram" |
| [5] Pacheco et al. | Builds coordination networks from shared behavioural traces without supervision; Twitter case studies | Crossref abstract: "general, unsupervised network-based methodology … coordination networks based on arbitrary behavioral traces shared among accounts … coordinated Twitter accounts" |
| [12] Efron 1979 | Bootstrap reference | Crossref 10.1214/aos/1176344552 (Annals of Statistics 7(1), 1–26) |
| others | Unchanged from the previous revision | Crossref DOI metadata; TwiBot-22 via the arXiv API, cited as a preprint only |

The ACM Digital Library refused automated access, so the CopyCatch and SynchroTrap texts were read from the authors' own PDFs. These were kept in a temporary folder and not added to the repository.

## 5. Remaining scientific weaknesses

- **No real data.** This is the main gap.
- **Circularity.** The benchmark and the detector share an author and a model of coordination.
- **Tuning asymmetry.** Only baseline B was tuned. B is a simplified SynchroTrap-style baseline, not SynchroTrap itself, and no graph-based or machine-learning baseline is included.
- **Interval method changed after seeing results.** The change is documented as a protocol amendment. Its effect on conclusions is negligible (one verdict, on a 0.005 F1 difference), but it was not pre-registered.
- **Statistics.** There is no multiple-comparison correction. Bootstrap intervals from 30 seeds can under-cover slightly. Many cells sit at a ceiling or floor (1.00 or 0.00).
- **Scale and adversaries.** Only one dataset size was tested; scaling and adaptive adversaries are not evaluated.
- **Unprovable ordering.** Git history cannot prove that the protocol was written before tuning.

## 6. Ready for final PDF production?

Yes, provided you check these points:
1. **Figure files.** Use the PNG figure, which is a 2× render, or the SVG.
2. **Fit and legibility.** Check that Tables 1–3 fit the page width at 9 pt or larger.
3. **Repository link.** Optionally add the public V1 repository URL. The evaluation code stays "available on request" until you publish the branch.
4. **Name and affiliation.** Confirm both before sending.
