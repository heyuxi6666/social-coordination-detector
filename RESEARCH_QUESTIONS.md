# Research questions

This document fixes the questions, hypotheses, methods and decision rules of the evaluation in `evaluation/`. It was written after a 3-seed smoke test of five configurations (to check that the code runs) and **before** the full 20-seed grid was run or read. Results are in `evaluation/results/`; they are reported as measured, including where they contradict the hypotheses below.

The detector under test is V1 as released (`main`, commit `4273f73`). The evaluation changes none of its code.

## Scope and honest framing

- All data are synthetic. The generator is written by the same author as the detector, so the results show how the detectors behave **inside this world model**, not how they would perform on a real platform. There is no real-world ground truth here, and no accuracy claim about real platforms is made or supported.
- No machine learning is used. The three methods are statistical or rule-based.
- Thresholds of all three methods are fixed defaults; none was tuned on the benchmark.

## RQ1 - Does timing-based coordination detection outperform overlap-only detection?

Methods: **A** engagement-overlap-only (V1's own group-forming step, without timing or indicators), **B** time-bucket co-action baseline (SynchroTrap-style), **C** the V1 detector.

Hypotheses (stated in advance):

- H1a. On a plain coordinated group at default settings, all three methods detect the group (the planted group is large and overlaps heavily), so the methods will **not** differ in recall there.
- H1b. The methods differ in **false positives** on ordinary shared audiences: A flags loyal followers and notification-burst audiences; B flags notification bursts (it sees only co-timing); C flags neither because it requires a repeated per-account delay.
- H1c. C's top tier ("strong anomaly") needs side signals (adjacent account ids, repost inflation) in addition to timing, so without them C reports at most "moderate".

Measured: account-level precision, recall and F1; group detection rate; false-positive rate on organic-only data; runtime. Scenarios: coordinated; coordinated with the example's side signals; organic-only; organic with loyal followers; organic with a notification burst; coordinated plus loyal followers.

## RQ2 - How robust is detection under timing jitter, partial participation and organic audience noise?

Sweeps, one parameter at a time from the defaults: timing jitter, participation rate, organic audience size, heavy-user activity, coordinated group size.

Hypotheses:

- H2a. C's recall falls once per-like jitter makes a cohort's delay difference exceed its 20 s window (Gaussian sd of roughly 7 s or more per like); B is less sensitive to jitter because its 300 s bucket is much wider.
- H2b. Low participation and small groups hurt every overlap-based method (A and C share the same group-forming step); B depends on repeated co-action and should also degrade.
- H2c. Groups smaller than C's minimum cohort (10 accounts) are never reported by C.
- H2d. Heavy-user activity raises false-positive pressure for A; C's timing test should hold it down.

## RQ3 - How does account rotation affect detection and network tracking?

Sweep: before each coordinated post after the first, each group slot is replaced by a brand-new account with the given probability (the new account keeps the slot's delay). Rotated-in accounts count as coordinated.

Measured additionally for C: whether V1's network tracer (started from V1's first fixed-offset group, as the CLI does) can be built, and what share of the coordinated posts it recovers.

Hypotheses:

- H3a. Rotation lowers C's account recall, because its cohort consists of accounts that repeat across posts.
- H3b. The tracer's cohort is "accounts that liked every seed post", so it collapses quickly under rotation.
- H3c. A (post-level overlap) and B (per-bucket co-action) degrade more slowly in group detection, but not in account recall.

## Metric definitions

- **Account level.** Predicted accounts = union over a method's flagged groups. Precision, recall and F1 are pooled over seeds (counts summed); the per-seed mean F1 and its standard error are also given. A method that flags nothing scores F1 = 0 on a coordinated dataset.
- **Group level.** A coordinated dataset is *detected* when some flagged group's post set has Jaccard >= 0.5 with the true coordinated posts. Any flagged group that does not match is *spurious*.
- **False-positive rate.** (i) share of organic-only datasets with at least one flagged group; (ii) flagged non-coordinated accounts as a share of all non-coordinated accounts seen.
- **Runtime.** Median wall-clock seconds for one dataset of 30 posts on the machine that ran the benchmark; not comparable across machines.
- **Decision rule for C.** Flagged groups are those of tier "strong anomaly" or "moderate anomaly" (the tiers the project already routes to human review). The strong-only variant is reported as a sensitivity row.
- **Seeds.** 20 independent seeds per configuration (1000-1019).

## Known biases this design cannot remove

See `evaluation/README.md` for the full list. In short: the generator shares its author with the detector; timing noise is independent of the gap between posts (real cross-day jitter grew with the gap); the account-delay model is the one the detector is built to find; organic behaviour is simple; one sweep at a time ignores interactions.
