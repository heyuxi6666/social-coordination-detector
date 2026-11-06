"""Synthetic benchmark generator: seeded, fully synthetic, with known ground truth.

One call builds one dataset in the detector's own loaded format (posts with likers and like times) together with
the truth: which posts and which accounts were coordinated.  Every knob below is a field of `Scenario`.

World model (deliberately simple, stated so that its biases can be judged):
* organic posts: each has its own author; likers come from a population of `n_accounts` accounts, a fraction
  `heavy_frac` of which are heavy users `heavy_weight` times as likely to be picked; each liker acts after an
  exponential delay (mean `organic_delay_mean` seconds);
* coordinated posts: `coord_posts` posts by `coord_authors` authors, liked by a group of `group_size` accounts that
  each act a personal fixed delay after the post (uniform over `cohort_spread` seconds) plus Gaussian noise of
  `jitter` seconds, plus an ordinary organic audience;
* `participation`: each group account skips a coordinated post with probability 1 - participation;
* `rotation`: before each coordinated post after the first, every group slot is taken over by a brand-new account
  with probability `rotation` (the new account keeps the slot's personal delay);
* `loyal_followers`: one author's `loyal_posts` posts are liked by the same followers; with a short
  `loyal_delay_mean` this is a notification burst.  Both are ordinary behaviour, so they are negatives;
* `delay_mode`: "fixed" (default) gives each group slot one personal delay reused on every coordinated post;
  "random" draws every delay independently per account and post (uniform over `cohort_spread`), so there is no
  repeated per-account offset for a fixed-delay test to find;
* `id_adjacent` / `repost_signal`: give the group consecutive account ids and inflated repost counts, the two
  side signals the V1 example plants.  Off by default so the main results do not lean on them.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from typing import Any

T0 = datetime(2026, 1, 10, 8, 0, tzinfo=timezone.utc).timestamp()
POPULATION_IDS = range(10_000, 90_000)
RESERVE_IDS = range(100_000, 400_000)
ADJACENT_START = 95_000
MIN_AUDIENCE = 10
DELAY_MODES = ("fixed", "random")


@dataclass(frozen=True)
class Scenario:
    n_accounts: int = 2000
    n_posts: int = 30
    group_size: int = 40
    coord_posts: int = 6
    coord_authors: int = 3
    jitter: float = 2.0
    participation: float = 1.0
    rotation: float = 0.0
    organic_audience: int = 40
    heavy_frac: float = 0.1
    heavy_weight: float = 5.0
    loyal_followers: int = 0
    loyal_posts: int = 3
    loyal_delay_mean: float = 1800.0
    cohort_spread: float = 120.0
    organic_delay_mean: float = 2400.0
    id_adjacent: bool = False
    repost_signal: bool = False
    hours: float = 48.0
    delay_mode: str = "fixed"

    def validate(self) -> None:
        if not 0 < self.participation <= 1 or not 0 <= self.rotation <= 1:
            raise ValueError("participation must be in (0, 1] and rotation in [0, 1]")
        if min(self.jitter, self.group_size, self.loyal_followers, self.heavy_frac) < 0 or self.heavy_weight <= 0:
            raise ValueError("jitter, group_size, loyal_followers and heavy_frac must be non-negative; heavy_weight positive")
        if self.delay_mode not in DELAY_MODES:
            raise ValueError(f"delay_mode must be one of {DELAY_MODES}")
        if self.group_size and self.coord_posts < 2:
            raise ValueError("a coordinated group needs at least two coordinated posts")
        if self.n_organic < 3:
            raise ValueError("n_posts is too small: at least three organic posts are needed for a baseline")
        if self.n_accounts > len(POPULATION_IDS) or self.organic_audience < MIN_AUDIENCE:
            raise ValueError("n_accounts or organic_audience out of range")

    @property
    def n_coordinated(self) -> int:
        return self.coord_posts if self.group_size else 0

    @property
    def n_loyal(self) -> int:
        return self.loyal_posts if self.loyal_followers else 0

    @property
    def n_organic(self) -> int:
        return self.n_posts - self.n_coordinated - self.n_loyal


PARAMETER_NAMES = tuple(f.name for f in fields(Scenario))


@dataclass(frozen=True)
class Truth:
    coord_posts: frozenset
    coord_accounts: frozenset
    loyal_posts: frozenset
    loyal_accounts: frozenset


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _weighted_sample(rng: random.Random, ids: list[int], weights: list[float], k: int) -> list[int]:
    """Efraimidis-Spirakis: k distinct ids, each draw proportional to its weight."""
    keyed = sorted(((rng.random() ** (1.0 / w), a) for a, w in zip(ids, weights)), reverse=True)
    return [a for _, a in keyed[:k]]


def generate(scenario: Scenario, seed: int) -> tuple[dict[str, Any], Truth]:
    scenario.validate()
    s = scenario
    rng = random.Random(seed)
    population = sorted(rng.sample(POPULATION_IDS, s.n_accounts))
    heavy = set(rng.sample(population, round(s.heavy_frac * s.n_accounts)))
    weights = [s.heavy_weight if a in heavy else 1.0 for a in population]
    reserve = [] if s.id_adjacent else rng.sample(RESERVE_IDS, s.group_size * max(s.coord_posts, 1) + 1)
    fresh = iter(range(ADJACENT_START, ADJACENT_START + 10_000) if s.id_adjacent else reserve)

    specs = ([("organic", 500 + i, rng.uniform(0, s.hours * 3600)) for i in range(s.n_organic)]
             + [("coordinated", 600 + j % s.coord_authors, rng.uniform(0, s.hours * 3600)) for j in range(s.n_coordinated)]
             + [("loyal", 777, rng.uniform(0, s.hours * 3600)) for _ in range(s.n_loyal)])
    specs.sort(key=lambda spec: spec[2])

    slots = [{"account": next(fresh), "base": rng.uniform(1.0, max(s.cohort_spread, 1.0))} for _ in range(s.group_size)]
    followers = rng.sample(population, s.loyal_followers) if s.loyal_followers else []
    coord_accounts: set[int] = set()
    posts: dict[str, dict[str, Any]] = {}
    coordinated_seen = 0

    for index, (kind, author, offset) in enumerate(specs):
        when = T0 + offset
        size = max(MIN_AUDIENCE, round(s.organic_audience * rng.uniform(0.7, 1.3) * (0.4 if kind == "loyal" else 1.0)))
        times: dict[int, float] = {}
        if kind == "loyal":
            for a in followers:
                times[a] = when + rng.expovariate(1 / s.loyal_delay_mean)
        for a in _weighted_sample(rng, population, weights, size):
            times.setdefault(a, when + rng.expovariate(1 / s.organic_delay_mean))
        acting = 0
        if kind == "coordinated":
            if coordinated_seen and s.rotation:
                for slot in slots:
                    if rng.random() < s.rotation:
                        slot["account"] = next(fresh)
            for slot in slots:
                if rng.random() < s.participation:
                    delay = slot["base"] if s.delay_mode == "fixed" else rng.uniform(1.0, max(s.cohort_spread, 1.0))
                    times[slot["account"]] = when + max(0.5, delay + rng.gauss(0.0, s.jitter))
                    coord_accounts.add(slot["account"])
                    acting += 1
            coordinated_seen += 1
        pid = 1000 + index
        record = {"post_id": pid, "author": author, "created_at": _iso(when), "role": kind, "more_pages": False,
                  "likers": sorted(times), "liked_at": times}
        if s.repost_signal:
            record.update(likes=len(times), views=len(times) * 6,
                          reposts=acting + rng.randint(0, 3) if kind == "coordinated" else rng.randint(0, len(times) // 5))
        posts[str(pid)] = record

    loaded = {"posts": {int(k): v for k, v in posts.items()}, "accounts_created": {}, "sources_used": [], "skipped_small": []}
    truth = Truth(
        coord_posts=frozenset(p["post_id"] for p in posts.values() if p["role"] == "coordinated"),
        coord_accounts=frozenset(coord_accounts),
        loyal_posts=frozenset(p["post_id"] for p in posts.values() if p["role"] == "loyal"),
        loyal_accounts=frozenset(followers))
    return loaded, truth
