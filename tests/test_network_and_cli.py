from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from coordination_detector import cli
from coordination_detector import detector as co
from coordination_detector.network import build_network, render_network

EXAMPLE = ROOT / "examples" / "example_engagement.json"


def example():
    return co.load_posts([EXAMPLE])


class ExampleTests(unittest.TestCase):
    def test_example_file_is_reproducible(self):
        with tempfile.TemporaryDirectory() as folder:
            script = ROOT / "examples" / "make_example.py"
            copy = Path(folder) / "make_example.py"
            copy.write_text(script.read_text(encoding="utf-8"), encoding="utf-8")
            subprocess.run([sys.executable, "-I", str(copy)], check=True, capture_output=True)
            self.assertEqual((Path(folder) / "example_engagement.json").read_bytes(), EXAMPLE.read_bytes())

    def test_planted_network_is_strong_and_loyal_audience_is_not(self):
        groups = {tuple(g["post_ids"]): g for g in co.analyse(example())["groups"]}
        self.assertEqual(groups[(3000, 3001, 3002, 3003, 3004)]["evidence_tier"], "strong anomaly")
        self.assertEqual(groups[(2000, 2001, 2002)]["evidence_tier"], "weak / consistent with a shared audience")
        self.assertFalse(any(1000 <= p < 2000 for key in groups for p in key))     # organic posts stay unflagged


class NetworkTests(unittest.TestCase):
    def test_seeds_trace_the_cohort_onto_linked_posts(self):
        net = build_network(example(), seeds=[3000, 3001])
        self.assertTrue(net["ok"])
        self.assertEqual(net["linked"], [3002, 3003, 3004])
        self.assertEqual(net["authors"], [601, 602, 603])
        self.assertEqual(net["pairs_fixed_offset"], net["pairs_judged"])
        self.assertTrue(all(o["spearman"] == 1.0 for o in net["order"]))
        self.assertTrue(set(range(9000, 9040)) <= set(net["cohort"]))
        self.assertLessEqual(net["comparison"]["max_cohort_overlap"], 2)          # chance co-likers only
        self.assertIn("ONE shared network", net["reading"])
        text = render_network(net)
        self.assertIn("Alternative explanations", text)
        self.assertIn("False-positive risks", text)

    def test_loyal_audience_seeds_find_no_network(self):
        net = build_network(example(), seeds=[2000, 2001])
        self.assertTrue(net["ok"])
        self.assertEqual(net["linked"], [])
        self.assertEqual(net["pairs_fixed_offset"], 0)
        self.assertIn("MIXED", net["reading"])

    def test_bad_seeds_explain_themselves(self):
        self.assertFalse(build_network(example(), seeds=[3000])["ok"])
        self.assertIn("missing timing", build_network(example(), seeds=[3000, 99])["reason"])


class CliTests(unittest.TestCase):
    def test_analyze_writes_four_reports_deterministically(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "a", Path(folder) / "b"
            self.assertEqual(cli.main(["analyze", str(EXAMPLE), "--out", str(a)]), 0)
            self.assertEqual(cli.main(["analyze", str(EXAMPLE), "--out", str(b)]), 0)
            names = sorted(p.name for p in a.iterdir())
            self.assertEqual(names, ["detector_report.json", "detector_report.md", "network_report.json", "network_report.md"])
            for name in names:
                self.assertEqual((a / name).read_bytes(), (b / name).read_bytes())
            self.assertTrue(json.loads((a / "network_report.json").read_text(encoding="utf-8"))["ok"])

    def test_bad_input_returns_error_code(self):
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder) / "bad.json"
            bad.write_text("{}", encoding="utf-8")
            self.assertEqual(cli.main(["analyze", str(bad), "--out", str(Path(folder) / "o")]), 2)


if __name__ == "__main__":
    unittest.main()
