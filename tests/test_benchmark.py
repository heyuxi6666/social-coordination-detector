from __future__ import annotations

import ast
import csv
import json
import math
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evaluation"))

from bench import generator, methods, metrics, runner, svgplot  # noqa: E402
import run_experiments  # noqa: E402
import summarize  # noqa: E402
from coordination_detector import detector as co  # noqa: E402

S = generator.Scenario


class GeneratorTests(unittest.TestCase):
    def test_same_seed_same_data_and_different_seed_differs(self):
        a, _ = generator.generate(S(), 7)
        b, _ = generator.generate(S(), 7)
        c, _ = generator.generate(S(), 8)
        self.assertEqual(a, b)
        self.assertNotEqual(a["posts"][1000]["likers"], c["posts"][1000]["likers"])

    def test_truth_matches_the_parameters(self):
        loaded, truth = generator.generate(S(group_size=25, coord_posts=5), 1)
        self.assertEqual(len(truth.coord_accounts), 25)
        self.assertEqual(len(truth.coord_posts), 5)
        self.assertEqual(len(loaded["posts"]), 30)
        for pid in truth.coord_posts:
            self.assertTrue(truth.coord_accounts <= set(loaded["posts"][pid]["likers"]))

    def test_organic_only_has_no_truth_and_keeps_the_dataset_size(self):
        loaded, truth = generator.generate(S(group_size=0), 1)
        self.assertEqual((truth.coord_posts, truth.coord_accounts), (frozenset(), frozenset()))
        self.assertEqual(len(loaded["posts"]), 30)

    def test_zero_jitter_repeats_each_accounts_delay_exactly(self):
        loaded, truth = generator.generate(S(jitter=0.0), 3)
        first, second = sorted(truth.coord_posts)[:2]
        def created(pid):
            return co.parse_timestamp(loaded["posts"][pid]["created_at"]).timestamp()
        offsets = {loaded["posts"][second]["liked_at"][a] - created(second) - (loaded["posts"][first]["liked_at"][a] - created(first))
                   for a in truth.coord_accounts}
        self.assertTrue(all(abs(x) < 1e-3 for x in offsets))

    def test_participation_scales_the_acting_group(self):
        loaded, truth = generator.generate(S(participation=0.5), 2)
        counts = [len(truth.coord_accounts & set(loaded["posts"][p]["likers"])) for p in truth.coord_posts]
        self.assertTrue(all(10 <= c <= 30 for c in counts), counts)

    def test_rotation_adds_accounts_and_zero_rotation_does_not(self):
        _, still = generator.generate(S(rotation=0.0), 4)
        _, moving = generator.generate(S(rotation=0.5), 4)
        self.assertEqual(len(still.coord_accounts), 40)
        self.assertGreater(len(moving.coord_accounts), 80)

    def test_adjacent_ids_and_repost_signal_are_opt_in(self):
        loaded, truth = generator.generate(S(), 5)
        self.assertNotIn("reposts", loaded["posts"][1000])
        ids = sorted(truth.coord_accounts)
        self.assertGreater(ids[-1] - ids[0], 1000)
        loaded, truth = generator.generate(S(id_adjacent=True, repost_signal=True), 5)
        ids = sorted(truth.coord_accounts)
        self.assertEqual(ids[-1] - ids[0], 39)
        self.assertIn("reposts", loaded["posts"][1000])

    def test_invalid_parameters_are_rejected(self):
        for bad in ({"participation": 0}, {"rotation": 1.5}, {"jitter": -1}, {"coord_posts": 1}, {"n_posts": 8}):
            with self.assertRaises(ValueError, msg=str(bad)):
                S(**bad).validate()


class MetricTests(unittest.TestCase):
    def test_counts_and_f1(self):
        self.assertEqual(metrics.prf_counts({1, 2, 3, 9}, {1, 2, 3, 4, 5}), (3, 1, 2))
        self.assertAlmostEqual(metrics.f1_from_counts(3, 1, 2), 6 / 9)
        self.assertEqual(metrics.f1_from_counts(0, 0, 0), 0.0)
        self.assertEqual(metrics.f1_from_counts(0, 0, 5), 0.0)

    def test_group_scoring(self):
        groups = [{"posts": {1, 2, 3, 4}, "accounts": {10, 11}}, {"posts": {8, 9}, "accounts": {50}}]
        row = metrics.score_groups(groups, {1, 2, 3, 4, 5}, {10, 11, 12}, set(range(10, 60)))
        self.assertEqual((row["detected"], row["spurious_groups"], row["tp"], row["fp"], row["fn"]), (1, 1, 2, 1, 1))
        self.assertEqual(row["negatives"], 47)                                  # 50 accounts seen, 3 truly coordinated
        weak = metrics.score_groups([{"posts": {1, 9}, "accounts": set()}], {1, 2, 3, 4}, {10}, {10, 11})
        self.assertEqual((weak["detected"], weak["spurious_groups"]), (0, 1))          # Jaccard 1/5 < 0.5

    def test_organic_only_rows_have_no_detection_label(self):
        row = metrics.score_groups([{"posts": {1, 2}, "accounts": {5, 6}}], set(), set(), {5, 6, 7})
        self.assertEqual((row["detected"], row["fp"], row["any_group"], row["spurious_groups"]), ("", 2, 1, 1))

    def test_wilson_interval_known_values(self):
        lo, hi = metrics.wilson(0, 20)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.1611, places=3)
        lo, hi = metrics.wilson(20, 20)
        self.assertAlmostEqual(lo, 0.8389, places=3)
        self.assertEqual(hi, 1.0)
        self.assertTrue(math.isnan(metrics.wilson(0, 0)[0]))

    def test_mean_and_standard_error(self):
        mean, se = metrics.mean_se([1.0, 2.0, 3.0])
        self.assertAlmostEqual(mean, 2.0)
        self.assertAlmostEqual(se, 1 / math.sqrt(3))
        self.assertEqual(metrics.mean_se([0.5]), (0.5, 0.0))

    def test_summary_pools_counts_across_seeds(self):
        rows = [dict(detected=1, tp=10, fp=0, fn=0, negatives=100, spurious_groups=0, any_group=1, n_groups=1, runtime_s=0.1),
                dict(detected=0, tp=0, fp=0, fn=10, negatives=100, spurious_groups=0, any_group=0, n_groups=0, runtime_s=0.3)]
        out = metrics.summarise(rows)
        self.assertEqual((out["detect_rate"], out["precision"], out["recall"]), (0.5, 1.0, 0.5))
        self.assertAlmostEqual(out["f1_micro"], 2 / 3)
        self.assertEqual(out["runtime_ms_median"], 200.0)


class MethodTests(unittest.TestCase):
    def test_overlap_only_reproduces_v1_group_formation(self):
        for scenario in (S(), S(loyal_followers=35), S(group_size=0, loyal_followers=35)):
            loaded, _ = generator.generate(scenario, 11)
            a = sorted(sorted(g["posts"]) for g in methods.overlap_only(loaded))
            v1 = sorted(sorted(g["post_ids"]) for g in co.analyse(loaded)["groups"])
            self.assertEqual(a, v1)

    def test_all_methods_find_the_default_group_and_score_it(self):
        loaded, truth = generator.generate(S(), 1000)
        for name, groups in (("A", methods.overlap_only(loaded)), ("B", methods.time_bucket(loaded)),
                             ("C", methods.v1_detector(loaded)["C"])):
            row = metrics.score_groups(groups, set(truth.coord_posts), set(truth.coord_accounts), set())
            self.assertEqual(row["detected"], 1, name)
            self.assertGreaterEqual(row["tp"], 35, name)

    def test_organic_only_is_not_flagged_by_any_method(self):
        loaded, _ = generator.generate(S(group_size=0), 1000)
        self.assertEqual(methods.overlap_only(loaded), [])
        self.assertEqual(methods.time_bucket(loaded), [])
        self.assertEqual(methods.v1_detector(loaded)["C"], [])

    def test_loyal_followers_fool_overlap_only_but_not_the_timing_test(self):
        loaded, _ = generator.generate(S(group_size=0, loyal_followers=35), 1000)
        self.assertTrue(methods.overlap_only(loaded))
        self.assertEqual(methods.v1_detector(loaded)["C"], [])

    def test_v1_needs_side_signals_for_its_strong_tier(self):
        plain, _ = generator.generate(S(), 1000)
        signalled, _ = generator.generate(S(id_adjacent=True, repost_signal=True), 1000)
        self.assertEqual(methods.v1_detector(plain)["C_strong"], [])
        self.assertTrue(methods.v1_detector(signalled)["C_strong"])

    def test_small_groups_below_the_minimum_cohort_are_not_reported_by_v1(self):
        loaded, _ = generator.generate(S(group_size=6), 1000)
        self.assertEqual(methods.v1_detector(loaded)["C"], [])


class RunnerAndOutputTests(unittest.TestCase):
    CONFIG = {"id": "T", "rq": "RQ2", "sweep": {"jitter": [1, 30]}, "trace": True, "title": "t"}

    def test_expand_validates_and_labels_configurations(self):
        entries = runner.expand({"id": "X", "sweep": {"rotation": [0, 0.5]}, "null_too": True})
        self.assertEqual([e["label"] for e in entries],
                         ["rotation=0", "rotation=0 (organic-only)", "rotation=0.5", "rotation=0.5 (organic-only)"])
        self.assertEqual(entries[1]["params"]["group_size"], 0)
        with self.assertRaises(TypeError):
            runner.expand({"id": "X", "sweep": {"not_a_parameter": [1]}})

    def test_every_method_gets_one_row_per_dataset(self):
        rows = runner.run_dataset(S(), 1000, trace=True)
        self.assertEqual([r["method"] for r in rows], list(methods.METHODS))
        self.assertTrue(all(set(r) <= set(runner.ROW_COLUMNS) for r in rows))
        traced = next(r for r in rows if r["method"] == "C_v1")
        self.assertEqual(traced["trace_built"], 1)
        self.assertGreater(traced["trace_post_recall"], 0.5)

    def test_run_writes_reproducible_metrics_and_valid_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            config = folder / "cfg.json"
            config.write_text('{"seeds": 2, "base_seed": 5, "defaults": {}, "experiments": [' + json.dumps(self.CONFIG) + "]}")
            for name in ("a", "b"):
                self.assertEqual(run_experiments.main(["--config", str(config), "--out", str(folder / name)]), 0)
            def metric_columns(name):
                with (folder / name / "raw_results.csv").open(newline="", encoding="utf-8") as handle:
                    return [{k: v for k, v in row.items() if "runtime" not in k} for row in csv.DictReader(handle)]
            first = metric_columns("a")
            self.assertEqual(first, metric_columns("b"))
            self.assertEqual(len(first), 2 * 2 * len(methods.METHODS))
            self.assertEqual(summarize.main(["--results", str(folder / "a"), "--config", str(config)]), 0)
            figures = sorted((folder / "a" / "figures").glob("*.svg"))
            self.assertEqual(len(figures), 2)
            for figure in figures:
                self.assertEqual(ET.parse(figure).getroot().tag.split("}")[-1], "svg")
            self.assertIn("Benchmark summary tables", (folder / "a" / "tables.md").read_text(encoding="utf-8"))
            self.assertGreater(len((folder / "a" / "summary.csv").read_text(encoding="utf-8").splitlines()), 4)

    def test_svg_chart_handles_missing_points(self):
        panel = {"title": "t", "xlabel": "x", "ylabel": "y", "x_labels": ["1", "2", "3"],
                 "series": {"C_v1": [(0.5, 0.4, 0.6), None, (1.0, 1.0, 1.0)]}}
        ET.fromstring(svgplot.two_panel_chart([panel], {"C_v1": "C"}, "caption"))


class HygieneTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(sys, "stdlib_module_names"), "needs Python 3.10+")
    def test_evaluation_code_is_standard_library_only(self):
        allowed = set(getattr(sys, "stdlib_module_names", ())) | {"bench", "coordination_detector", "run_experiments", "summarize"}
        for path in (ROOT / "evaluation").rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) and not node.level else []
                for name in names:
                    self.assertIn(name.split(".")[0], allowed, f"{path.name} imports {name}")


if __name__ == "__main__":
    unittest.main()
