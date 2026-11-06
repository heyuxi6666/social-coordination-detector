"""The three compared detectors, behind one interface.

Each takes a dataset in the detector's loaded format and returns predicted groups, each a dict
{"posts": set[int], "accounts": set[int]}.  Account-level scoring uses the union of the accounts of all
predicted groups; group-level scoring compares post sets (see metrics.py).

A  overlap-only   V1's own group-formation step (pairwise liker overlap, hypergeometric tail, Bonferroni) with
                  no timing test and no indicators.  Accounts: those liking at least half of a group's posts.
B  time-bucket    a SynchroTrap-style co-action baseline: two accounts are linked when they like the same posts
                  inside the same fixed time bucket often enough; linked accounts form groups.
C  V1 detector    coordination_detector.detector.analyse.  Flagged groups: tier "strong" or "moderate" (the tiers
                  the project treats as worth human review; chosen before any result was seen); "C_strong"
                  keeps strong only.  Accounts: the group's fixed-offset cohort.

All thresholds are fixed defaults, not tuned on the benchmark.
"""

from __future__ import annotations

import itertools
import math
import time
from collections import defaultdict
from typing import Any, Callable

from coordination_detector import detector as co
from coordination_detector.network import build_network

BUCKET_SECONDS = 300
MIN_SHARED_ITEMS = 3
MIN_ITEM_JACCARD = 0.5
MIN_GROUP_ACCOUNTS = 5
MEMBER_POST_SHARE = 0.5
REVIEW_TIERS = ("strong anomaly", "moderate anomaly")

Group = dict[str, set]


def _components(edges: list[tuple[Any, Any]]) -> list[set]:
    parent: dict[Any, Any] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        parent[find(a)] = find(b)
    found: dict[Any, set] = defaultdict(set)
    for node in list(parent):
        found[find(node)].add(node)
    return list(found.values())


def overlap_only(loaded: dict[str, Any]) -> list[Group]:
    posts = {pid: set(p["likers"]) for pid, p in loaded["posts"].items() if len(p.get("likers", [])) >= co.MIN_LIKERS}
    if len(posts) < 3:
        return []
    population = len(set().union(*posts.values()))
    ids = sorted(posts)
    tests = len(ids) * (len(ids) - 1) // 2
    edges = []
    for a, b in itertools.combinations(ids, 2):
        shared = len(posts[a] & posts[b])
        coeff = shared / min(len(posts[a]), len(posts[b]))
        if coeff >= co.EDGE_MIN_OVERLAP_COEFF:
            p = min(1.0, co.hypergeom_sf(shared, len(posts[a]), len(posts[b]), population) * tests)
            if p <= co.EDGE_MAX_BONFERRONI_P:
                edges.append((a, b))
    groups = []
    for comp in _components(edges):
        if len(comp) < co.MIN_GROUP_POSTS:
            continue
        need = max(2, math.ceil(MEMBER_POST_SHARE * len(comp)))
        counts: dict[int, int] = defaultdict(int)
        for pid in comp:
            for account in posts[pid]:
                counts[account] += 1
        groups.append({"posts": set(comp), "accounts": {a for a, c in counts.items() if c >= need}})
    return groups


def time_bucket(loaded: dict[str, Any]) -> list[Group]:
    items: dict[tuple[int, int], list[int]] = defaultdict(list)
    per_account: dict[int, set] = defaultdict(set)
    for pid, post in loaded["posts"].items():
        for account, moment in (post.get("liked_at") or {}).items():
            item = (pid, int(moment // BUCKET_SECONDS))
            items[item].append(account)
            per_account[account].add(item)
    shared: dict[tuple[int, int], int] = defaultdict(int)
    for members in items.values():
        for a, b in itertools.combinations(sorted(members), 2):
            shared[(a, b)] += 1
    edges = [(a, b) for (a, b), n in shared.items()
             if n >= MIN_SHARED_ITEMS and n / (len(per_account[a]) + len(per_account[b]) - n) >= MIN_ITEM_JACCARD]
    groups = []
    for comp in _components(edges):
        if len(comp) < MIN_GROUP_ACCOUNTS:
            continue
        liked: dict[int, int] = defaultdict(int)
        for account in comp:
            for pid in {pid for pid, _ in per_account[account]}:
                liked[pid] += 1
        member_posts = {pid for pid, n in liked.items() if n >= MEMBER_POST_SHARE * len(comp)}
        if len(member_posts) >= co.MIN_GROUP_POSTS:
            groups.append({"posts": member_posts, "accounts": set(comp)})
    return groups


def v1_detector(loaded: dict[str, Any]) -> dict[str, Any]:
    """Run V1 once; return the raw result and the review-level and strong-only readouts."""
    result = co.analyse(loaded)

    def readout(tiers: tuple[str, ...]) -> list[Group]:
        return [{"posts": set(g["post_ids"]), "accounts": set(g["fixed_offset_cohort_accounts"])}
                for g in result["groups"] if g["evidence_tier"] in tiers]

    return {"result": result, "C": readout(REVIEW_TIERS), "C_strong": readout(("strong anomaly",))}


def trace(loaded: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
    """V1's network tracer, started from the first group with a fixed-offset cohort (as the CLI does)."""
    group = next((g for g in result["groups"] if g.get("fixed_offset_cohort_accounts")), None)
    if group is None:
        return None
    return build_network(loaded, (), group)


def timed(function: Callable[..., Any], *args: Any) -> tuple[Any, float]:
    start = time.perf_counter()
    value = function(*args)
    return value, time.perf_counter() - start


METHODS = ("A_overlap_only", "B_time_bucket", "C_v1", "C_v1_strong")
