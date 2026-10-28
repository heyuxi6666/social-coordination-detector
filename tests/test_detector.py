from __future__ import annotations

import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from coordination_detector import detector as co


def loaded(posts, created=None):
    return {"posts": {pid: dict(post_id=pid, **p) for pid, p in posts.items()}, "accounts_created": created or {},
            "sources_used": [], "skipped_small": []}


def crowd(start: int, count: int) -> list[int]:
    return list(range(start, start + count * 7, 7))        # spaced ids: no accidental runs


def background(n_posts: int = 8) -> dict:
    return {100 + i: {"author": 50 + i, "likers": crowd(100_000 + i * 997, 30), "likes": 30, "reposts": 6} for i in range(n_posts)}


def planted(authors=(900, 901)):
    posts = background()
    farm = list(range(7000, 7030))                          # consecutive ids: registered together
    posts[900] = {"author": authors[0], "likers": farm + crowd(300_000, 10), "likes": 40, "reposts": 30}
    posts[901] = {"author": authors[1], "likers": farm + crowd(400_000, 10), "likes": 40, "reposts": 30}
    return posts


def timed_post(likers_times: dict, author: int, role: str = "group") -> dict:
    return {"author": author, "likers": sorted(likers_times), "liked_at": dict(likers_times), "role": role,
            "more_pages": False, "likes": len(likers_times)}


def timed_crowd(base: int, count: int, start: float, seed: int) -> dict:
    rng = random.Random(seed)
    return {base + 7 * i: start + rng.uniform(0, 5400) for i in range(count)}


def timed_background() -> dict:
    return {200 + i: timed_post(timed_crowd(100_000 + i * 997, 40, 1_000_000 + i * 50_000, i), 60 + i, "baseline") for i in range(8)}


def timed_farm(offset: float = 1800.0, jitter: float = 3.0, spread: float = 120.0) -> dict:
    rng = random.Random(5)
    ids = list(range(7000, 7030))
    first = {a: 2_000_000 + i * (spread / 30) for i, a in enumerate(ids)}
    second = {a: t + offset + rng.uniform(0, jitter) for a, t in first.items()}
    noise_a, noise_b = timed_crowd(300_000, 10, 2_000_000, 71), timed_crowd(400_000, 10, 2_000_000, 72)
    return {900: timed_post({**first, **noise_a}, 900), 901: timed_post({**second, **noise_b}, 901)}


class StatisticsTests(unittest.TestCase):
    def test_hypergeometric_known_values(self):
        self.assertAlmostEqual(co.hypergeom_sf(5, 5, 5, 10), 1 / 252)
        self.assertEqual(co.hypergeom_sf(0, 5, 5, 10), 1.0)
        self.assertEqual(co.hypergeom_sf(6, 5, 5, 10), 0.0)

    def test_robust_z_needs_a_baseline_and_ignores_flat_noise(self):
        self.assertIsNone(co.robust_z(0.5, [0.0, 0.0]))
        self.assertGreater(co.robust_z(0.5, [0.0] * 10), 10)

    def test_id_runs_and_adjacency(self):
        self.assertEqual(co.id_runs([1, 2, 3, 50, 90, 91, 92, 93]), [[1, 2, 3], [90, 91, 92, 93]])
        population = set(crowd(1000, 200))
        clustered = set(range(5000, 5030))
        self.assertLess(co.adjacency_p_value(clustered, population | clustered), 0.01)
        self.assertGreater(co.adjacency_p_value(set(crowd(1000, 200)[::5]), population), 0.2)


class TimingTests(unittest.TestCase):
    def test_fixed_offset_cohort_is_detected(self):
        posts = timed_farm()
        result = co.lockstep(posts[900]["liked_at"], posts[901]["liked_at"])
        self.assertEqual(result["kind"], "fixed-offset")
        self.assertGreaterEqual(result["cohort"], 30)
        self.assertLessEqual(result["p"], 0.01)

    def test_ordinary_patterns_are_not_fixed_offset(self):
        a, b = timed_crowd(1000, 40, 0, 1), {k: v + 4000 for k, v in timed_crowd(1000, 40, 0, 2).items()}
        self.assertEqual(co.lockstep(a, b)["kind"], "unstructured")
        self.assertEqual(co.lockstep({i: 1000.0 + i * 3 for i in range(20)}, {i: 1012.0 + i * 3 for i in range(20)})["kind"], "same-session")
        self.assertEqual(co.lockstep({i: 1000.0 + i for i in range(20)}, {i: 5000.0 + i for i in range(20)})["kind"], "co-burst")
        self.assertIsNone(co.lockstep({1: 0.0, 2: 1.0}, {1: 5.0, 2: 6.0}))


class DetectionTests(unittest.TestCase):
    def test_planted_group_is_strong_but_never_proven(self):
        group = co.analyse(loaded(planted()))["groups"][0]
        self.assertEqual(group["post_ids"], [900, 901])
        self.assertEqual(group["evidence_tier"], "strong anomaly")
        self.assertIn("not a proven violation", group["status"])

    def test_independent_posts_produce_no_group(self):
        self.assertEqual(co.analyse(loaded(background(10)))["groups"], [])

    def test_single_author_overlap_is_capped(self):
        group = co.analyse(loaded(planted(authors=(900, 900))))["groups"][0]
        self.assertEqual(group["evidence_tier"], "moderate anomaly")

    def test_overlap_without_timing_is_downgraded(self):
        posts = timed_background()
        rng = random.Random(9)
        for pid in (900, 901):
            times = {a: 2_000_000 + rng.uniform(0, 9000) for a in range(7000, 7030)}
            posts[pid] = timed_post({**times, **timed_crowd(300_000 + pid, 10, 2_000_000, pid)}, pid)
        self.assertEqual(co.analyse(loaded(posts))["groups"][0]["evidence_tier"], "weak / consistent with a shared audience")

    def test_exclusions_and_reported_labels(self):
        self.assertEqual(co.analyse(loaded(planted()), exclude_posts=[901])["groups"], [])
        self.assertEqual(co.analyse(loaded(planted()), exclude_accounts=[900])["groups"], [])
        self.assertEqual(co.analyse(loaded(planted()), already_reported=[900])["groups"][0]["already_reported_posts"], [900])

    def test_too_little_data_is_a_limitation_not_a_score(self):
        result = co.analyse(loaded({1: {"author": 1, "likers": crowd(1, 20)}, 2: {"author": 2, "likers": crowd(5, 20)}}))
        self.assertIn("Insufficient data", result["verdict"])

    def test_report_states_limits_and_makes_no_probability_claim(self):
        text = co.render_markdown(co.analyse(loaded({**timed_background(), **timed_farm()})))
        for phrase in ("Statistical anomaly only", "## Limitations", "No confidence percentage", "fixed-offset"):
            self.assertIn(phrase, text)


class LoadingTests(unittest.TestCase):
    def test_documented_format_loads_timed_and_untimed_posts(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            rows = [{"account_id": i, "liked_at": f"2026-01-01T10:00:{i:02d}Z"} for i in range(12)]
            path.write_text(json.dumps({"posts": {"5": {"author_id": 9, "likers": rows, "more_pages": True, "body": "x",
                                                         "created_at": "2026-01-01T09:00:00Z", "likes": 12},
                                                   "6": list(range(20)), "7": {"likers": [1, 2]}},
                                        "accounts_created": {"3": "2026-01-01T08:00:00Z"}}), encoding="utf-8")
            data = co.load_posts([path], {6: 44})
            self.assertEqual(data["posts"][5]["author"], 9)
            self.assertEqual(len(data["posts"][5]["liked_at"]), 12)
            self.assertTrue(data["posts"][5]["more_pages"])
            self.assertEqual(data["posts"][5]["body"], "x")
            self.assertEqual(data["posts"][6]["author"], 44)
            self.assertEqual(data["skipped_small"], [7])
            self.assertEqual(data["accounts_created"], {3: "2026-01-01T08:00:00Z"})

    def test_wrong_format_is_rejected_clearly(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "'posts' mapping"):
                co.load_posts([path])


if __name__ == "__main__":
    unittest.main()
