from __future__ import annotations

import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evaluation"))

from bench import generator, methods, metrics, runner  # noqa: E402
import run_experiments  # noqa: E402
import summarize_phase2 as p2  # noqa: E402
import tune_baseline  # noqa: E402

S = generator.Scenario
RESULTS = ROOT / "evaluation" / "results_phase2"
CONFIGS = ROOT / "evaluation" / "configs"


def offsets(mode: str) -> list[float]:
    from coordination_detector import detector as co
    loaded, truth = generator.generate(S(jitter=0.0, delay_mode=mode), 3)
    first, second = sorted(truth.coord_posts)[:2]
    def created(pid):
        return co.parse_timestamp(loaded["posts"][pid]["created_at"]).timestamp()
    return [(loaded["posts"][second]["liked_at"][a] - created(second)) - (loaded["posts"][first]["liked_at"][a] - created(first))
            for a in truth.coord_accounts]


class GeneratorExtensionTests(unittest.TestCase):
    def test_random_delays_have_no_repeated_per_account_offset(self):
        fixed, random_ = offsets("fixed"), offsets("random")
        self.assertLess(max(fixed) - min(fixed), 1e-3)
        self.assertGreater(max(random_) - min(random_), 50)

    def test_default_mode_is_unchanged_and_bad_modes_are_rejected(self):
        self.assertEqual(S().delay_mode, "fixed")
        with self.assertRaises(ValueError):
            S(delay_mode="sometimes").validate()

    def test_wide_spread_makes_the_cohort_window_wide(self):
        loaded, truth = generator.generate(S(cohort_spread=2000, jitter=0.0), 4)
        pid = sorted(truth.coord_posts)[0]
        from coordination_detector import detector as co
        created = co.parse_timestamp(loaded["posts"][pid]["created_at"]).timestamp()
        delays = [loaded["posts"][pid]["liked_at"][a] - created for a in truth.coord_accounts]
        self.assertGreater(max(delays) - min(delays), 1500)


class FragmentMetricTests(unittest.TestCase):
    def test_fragments_are_unmatched_groups_with_true_posts(self):
        truth_posts = {1, 2, 3, 4, 5, 6}
        groups = [{"posts": {1, 2}, "accounts": {10}},          # fragment: 2 true posts, Jaccard 1/3
                  {"posts": {90, 91}, "accounts": {50}},        # spurious: no true posts
                  {"posts": {1, 2, 3, 4, 5}, "accounts": {11}}]  # match
        row = metrics.score_groups(groups, truth_posts, {10, 11}, set(range(1, 100)))
        self.assertEqual((row["detected"], row["spurious_groups"], row["fragment_groups"]), (1, 2, 1))


class TunableBaselineTests(unittest.TestCase):
    def test_defaults_equal_explicit_original_parameters(self):
        loaded, _ = generator.generate(S(), 5000)
        self.assertEqual(methods.time_bucket(loaded), methods.time_bucket(loaded, methods.BUCKET_SECONDS, methods.MIN_GROUP_ACCOUNTS))

    def test_wider_bucket_recovers_a_widely_spread_group(self):
        loaded, truth = generator.generate(S(cohort_spread=2000), 5000)
        def recovered(*args):
            groups = methods.time_bucket(loaded, *args)
            return len(set().union(*(g["accounts"] for g in groups)) & truth.coord_accounts) if groups else 0
        self.assertGreater(recovered(2400, 15), recovered())

    def test_minimum_group_size_filters_small_groups(self):
        loaded, _ = generator.generate(S(group_size=10), 5000)
        self.assertTrue(methods.time_bucket(loaded, 300, 5))
        self.assertEqual(methods.time_bucket(loaded, 300, 20), [])

    def test_runner_adds_the_tuned_method_only_when_given_parameters(self):
        plain = runner.run_dataset(S(), 5000)
        tuned = runner.run_dataset(S(), 5000, tuned={"bucket_seconds": 2400, "min_group_accounts": 15})
        self.assertNotIn("B_tuned", [r["method"] for r in plain])
        self.assertIn("B_tuned", [r["method"] for r in tuned])


class TuningProtocolTests(unittest.TestCase):
    def tiny(self, base_seed=2000):
        return {"base_seed": base_seed, "seeds": 2, "grid": {"bucket_seconds": [300, 2400], "min_group_accounts": [5, 15]},
                "scenarios": [{"label": "c", "params": {}}, {"label": "o", "params": {"group_size": 0}}]}

    def test_tuning_is_deterministic_and_stays_inside_the_grid(self):
        rows1, result1 = tune_baseline.tune(self.tiny())
        rows2, result2 = tune_baseline.tune(self.tiny())
        self.assertEqual(result1, result2)
        self.assertIn(result1["parameters"]["bucket_seconds"], (300, 2400))
        self.assertEqual(len(rows1), 4)

    def test_tuning_refuses_held_out_and_phase1_seeds(self):
        for seed in (5000, 4999, 1005):
            with self.assertRaises(SystemExit):
                tune_baseline.tune(self.tiny(seed))

    def test_committed_splits_are_disjoint(self):
        tuning = json.loads((CONFIGS / "tuning.json").read_text(encoding="utf-8"))
        held = json.loads((CONFIGS / "phase2.json").read_text(encoding="utf-8"))
        tune_seeds = set(range(tuning["base_seed"], tuning["base_seed"] + tuning["seeds"]))
        held_seeds = set(range(held["base_seed"], held["base_seed"] + held["seeds"]))
        self.assertFalse(tune_seeds & held_seeds)
        self.assertFalse(tune_seeds & set(range(1000, 1020)))
        self.assertFalse(held_seeds & set(range(1000, 1020)))
        self.assertGreaterEqual(held["seeds"], 30)


class PairedComparisonTests(unittest.TestCase):
    def row(self, method, seed, tp, fp, fn, detected=1):
        return {"experiment": "X", "config_id": "X|c", "label": "c", "method": method, "seed": seed, "tp": tp, "fp": fp, "fn": fn,
                "detected": detected, "any_group": 1 if (tp + fp) else 0}

    def test_verdict_direction(self):
        self.assertEqual(p2.verdict(0.1, 0.3, True), "C better")
        self.assertEqual(p2.verdict(-0.3, -0.1, True), "C worse")
        self.assertEqual(p2.verdict(-0.1, 0.1, True), "no clear difference")
        self.assertEqual(p2.verdict(0.1, 0.3, False), "C worse")        # more false positives is worse
        self.assertEqual(p2.verdict(-0.3, -0.1, False), "C better")

    def test_paired_difference_uses_matching_seeds(self):
        rows = []
        for seed in range(10):
            rows.append(self.row("C_v1", seed, 40, 0, 0))
            rows.append(self.row("B_tuned", seed, 20 + seed % 2, 0, 20 - seed % 2))
            rows.append(self.row("A_overlap_only", seed, 40, 0, 0))
            rows.append(self.row("B_time_bucket", seed, 0, 0, 40))
        out = {r["baseline"]: r for r in p2.paired(rows)}
        self.assertEqual(out["A_overlap_only"]["verdict"], "no clear difference")
        self.assertEqual(out["B_time_bucket"]["verdict"], "C better")
        self.assertEqual(out["B_tuned"]["verdict"], "C better")
        self.assertAlmostEqual(out["B_time_bucket"]["mean_difference"], 1.0)


class ReportedResultsComeFromExecutedExperiments(unittest.TestCase):
    """The committed tables, summaries and figures must be reproducible from the committed raw CSV, and the raw CSV
    from re-running the experiments."""

    def test_summaries_regenerate_byte_for_byte_from_raw_results(self):
        with tempfile.TemporaryDirectory() as folder:
            copy_dir = Path(folder)
            for name in ("raw_results.csv", "run_info.json", "tuned_parameters.json"):
                (copy_dir / name).write_bytes((RESULTS / name).read_bytes())
            self.assertEqual(p2.main(["--results", str(copy_dir)]), 0)
            names = ["summary.csv", "paired_comparisons.csv", "tables.md"] + [f"figures/{p.name}" for p in (RESULTS / "figures").glob("*.svg")]
            self.assertEqual(len(names), 6)
            for name in names:
                self.assertEqual((copy_dir / name).read_bytes(), (RESULTS / name).read_bytes(), name)

    def test_held_out_run_used_the_committed_tuned_parameters(self):
        tuned = json.loads((RESULTS / "tuned_parameters.json").read_text(encoding="utf-8"))
        info = json.loads((RESULTS / "run_info.json").read_text(encoding="utf-8"))
        self.assertEqual(info["tuned_baseline"], tuned["parameters"])
        self.assertEqual(info["seeds"][0], 5000)
        self.assertEqual(len(info["seeds"]), 30)
        self.assertGreater(tuned["tuning_seeds"][1], 1999)
        self.assertLess(tuned["tuning_seeds"][1], 5000)

    def test_rerunning_two_held_out_seeds_reproduces_the_committed_metrics(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            self.assertEqual(run_experiments.main(["--config", str(CONFIGS / "phase2.json"), "--tuned", str(RESULTS / "tuned_parameters.json"),
                                                   "--out", str(out), "--seeds", "2", "--only", "P1_headline", "P3_random_delays"]), 0)
            def load(path):
                with path.open(newline="", encoding="utf-8") as handle:
                    return {(r["config_id"], r["seed"], r["method"]): {k: v for k, v in r.items() if "runtime" not in k} for r in csv.DictReader(handle)}
            fresh, committed = load(out / "raw_results.csv"), load(RESULTS / "raw_results.csv")
            self.assertEqual(len(fresh), 2 * (6 + 3) * 5)
            for key, row in fresh.items():
                self.assertEqual(row, committed[key], key)

    def test_every_experiment_has_at_least_30_seeds_and_all_methods(self):
        with (RESULTS / "raw_results.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        seeds, methods_ = {}, {}
        for r in rows:
            seeds.setdefault(r["config_id"], set()).add(r["seed"])
            methods_.setdefault(r["config_id"], set()).add(r["method"])
        self.assertEqual(len(seeds), 43)
        self.assertTrue(all(len(s) == 30 for s in seeds.values()))
        self.assertTrue(all(m == {"A_overlap_only", "B_time_bucket", "B_tuned", "C_v1", "C_v1_strong"} for m in methods_.values()))


if __name__ == "__main__":
    unittest.main()
