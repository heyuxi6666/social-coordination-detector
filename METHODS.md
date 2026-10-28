# Methods, limitations and false-positive risks

Every number in the reports is a raw value next to a baseline drawn from the same data. No probability of wrongdoing or confidence percentage is calculated, because the data cannot support one.

## 1. Pipeline

1. **Load.** Posts with at least 10 saved likers are analysed. Excluded accounts are removed everywhere.
2. **Pairwise overlap.** For every pair of posts, the detector computes:
   - shared likers and Jaccard overlap;
   - the overlap coefficient (shared / smaller set);
   - a hypergeometric tail probability against the population of all accounts seen liking any analysed post, with a Bonferroni correction across all pairs.
3. **Groups.** Pairs with an overlap coefficient of at least 0.3 and a corrected p ≤ 0.001 are joined into connected groups.
4. **Indicators per group.** Five indicators are scored. Each is either triggered, not triggered, or not measurable (section 2).
5. **Tier.** A group's tier is derived from its indicators (section 3).
6. **Network tracing.** The detector starts from the strongest fixed-offset group, or from `--seed` posts.
   - The cohort is the set of accounts that liked every seed post.
   - Every other timed post is tested for the cohort's lock-step pattern.
   - The report covers pairwise delays, the reaction order (Spearman rho against an anchor post), membership drift, cross-likes between authors, and the same timing tests run on the posts outside the network.

## 2. Indicators

| Indicator | Triggered when | Why it matters | How it misleads |
|---|---|---|---|
| `overlap_significance` | worst corrected pair p ≤ 0.001 | the overlap is not chance | large shared audiences pass easily; this alone means little |
| `overlap_vs_unrelated_pairs` | smallest robust z (median/MAD) of the group's Jaccard vs unrelated different-author pairs ≥ 3.5 | the overlap is far above what unrelated posts show | a small or homogeneous sample makes the baseline narrow |
| `exceeds_same_author_audience` | weakest pair overlap > the largest overlap among one author's own unflagged posts | beats the loyal-audience yardstick | not measurable when no clean same-author pairs exist |
| `core_account_id_adjacency` | permutation p ≤ 0.01 (2000 draws, seed 0) that the core likers sit in runs of consecutive ids | accounts registered together | ids may be assigned in batches for innocent reasons |
| `repost_to_like_ratio` | group mean reposts/likes robust z ≥ 3.5 | amplification out of proportion to likes | reposter identities are unknown; counts only |
| `fixed_offset_cohort` | a pair has a cohort ≥ 10 with the label `fixed-offset` | the timing pattern that audience size cannot explain | see section 4 |

## 3. Tiers

- **strong anomaly:**
  - at least 3 indicators are measurable, and all of them are triggered;
  - the group is not a single-author group that lacks both the same-author yardstick and timing support.
- **weak / consistent with a shared audience:**
  - timing was measurable and showed no fixed-offset cohort.
  - This overrides other indicators, because overlap without timing is what ordinary audiences produce.
- **moderate anomaly:** at least 2 indicators are triggered.
- **weak / not distinguishable from a shared audience:** everything else.

Tiers are counts of triggered indicators, not probabilities.

## 4. The lock-step (timing) test

For two posts A and B, the test runs on the accounts that liked both, and needs at least 8 of them:

1. Compute each account's delay, `liked_at(B) − liked_at(A)`.
2. Find the largest **cohort** whose delays fit inside a 20-second window.
3. **Permutation test:** shuffle which account gets which B time (500 shuffles, seed 0). The p-value is the share of shuffles that match the cohort size, with p = 1/501 ≈ 0.002 as the floor.
4. **Labels:**
   - `unstructured`: p > 0.01, or a cohort under 5 accounts.
   - `same-session`: the cohort's typical delay is under 120 s. These are ordinary people liking several posts in one sitting.
   - `fixed-offset`:
     - the cohort has at least 10 accounts;
     - its own like times on A are spread out, by at least 60 s and at least 5 × the delay jitter.
     - Each account therefore repeats its own delay, even though the accounts acted at different moments.
   - `co-burst`: a cohort of at least 10 that liked both posts in one short burst each. This is ambiguous.

## 5. Limitations

- **Timing coverage:** timing is judged only where `liked_at` exists.
- **Missing data:**
  - Reposter identities, follower graphs and historical snapshots are not used.
  - So reposts are only counted, and follower overlap (the most common innocent explanation) is not tested.
- **Population:** the reference population is the accounts seen in the sample. A sample of popular posts biases the baseline. This makes p-values conservative rather than exact.
- **Truncation:** truncated liker lists under-count overlap. They are flagged in the report, not silently dropped.
- **Snapshots:** each liker list is a single snapshot, so likes that arrive later are missing.
- **Cohort size across long gaps:**
  - Across long gaps (for example, days), delay jitter grows towards the 20 s window.
  - The measured cohort size then becomes sensitive to that window. The network report warns when this happens.
- **Thresholds:** the thresholds (0.3, 0.001, 3.5, 20 s, 10 accounts) are fixed by design choice, not fitted. They are constants at the top of `detector.py`.

## 6. False-positive risks and how the reports address them

| Innocent pattern | What it looks like | Guard |
|---|---|---|
| Heavy browsers liking many posts in one sitting | overlap and tiny delays | `same-session` label; session regulars counted separately |
| Loyal followers of one author | very high overlap among that author's posts | single-author cap; same-author yardstick; downgrade when timing shows nothing |
| Popular posts sharing a big audience | significant overlap across authors | robust z against unrelated pairs; timing test |
| One notification wave | everyone likes both posts in one burst | `co-burst` is kept separate from `fixed-offset` |
| Platform-run or simulated audience accounts | can produce genuine fixed-offset patterns | **not separable from public data**; always listed as an alternative explanation |
| An author liked by a network they do not control | the author appears in a strong group | reports describe engagement on posts, never intent; "may be a beneficiary or bystander" is stated |

## 7. Using results

A strong anomaly is a reason for the platform to look closer. A responsible report:

- states the observations (accounts, order, delays, comparison);
- states their limits;
- leaves the verdict to the platform.
