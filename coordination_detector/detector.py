"""Offline coordinated-engagement detector (no network, no login, no writes anywhere except its reports).

Reads saved public engagement snapshots (who liked which post, and when) and reports STATISTICAL ANOMALIES
with the numbers behind them.  It never proves a rule violation and never produces a confidence
percentage: every indicator is a raw value next to a baseline taken from the same data.

Input format (JSON, one or more files, merged by post id) - see README.md:

    {"posts": {"<post_id>": {"author_id": 12, "created_at": "2026-01-01T10:00:00Z", "role": "sample",
                             "likers": [{"account_id": 7, "liked_at": "2026-01-01T10:00:05Z"}, ...],
                             "more_pages": false, "likes": 40, "reposts": 3, "views": 300, "body": "..."}},
     "accounts_created": {"<account_id>": "2026-01-01T09:00:00Z"}}

``likers`` may also be a plain list of account ids (no timing).  Every field except ``likers`` is optional.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import random
import re
import statistics
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

LIKER_PAGE_CAP = 100          # a saved liker list of this length is assumed truncated unless more_pages says otherwise
MIN_LIKERS = 10               # smaller liker sets cannot support an overlap statistic
EDGE_MIN_OVERLAP_COEFF = 0.3  # shared / smaller liker set
EDGE_MAX_BONFERRONI_P = 1e-3
ROBUST_Z_FLAG = 3.5
RUN_GAP = 3                   # account ids this close count as "registered together"
RUN_MIN = 3
PERMUTATIONS = 2000
ID_ADJACENCY_P = 0.01
CREATION_WINDOW_MINUTES = 2
MIN_GROUP_POSTS = 2
LOCKSTEP_WINDOW = 20          # seconds: accounts whose like-time difference between two posts stays inside this window
LOCKSTEP_PERMS = 500
LOCKSTEP_P = 0.01
MIN_SHARED_TIMED = 8          # shared timed likers needed before a pair's timing is judged
MIN_COHORT = 10
SESSION_CENTRE = 120          # seconds: a cohort liking both posts within this of each other is one browsing session
SPAN_FACTOR = 5               # the cohort's like times must be spread >= SPAN_FACTOR x its offset jitter ...
MIN_SPAN = 60                 # ... and at least this many seconds, or it is just one burst
SESSION_POSTS, SESSION_SECONDS = 3, 60

TIER_ORDER = ("strong anomaly", "moderate anomaly", "weak / not distinguishable from shared audience",
              "weak / consistent with a shared audience")
DATA_FIELDS = {
    "used": ["likers[].account_id (who liked)", "likers[].liked_at (when; enables timing tests)",
             "author_id", "created_at", "more_pages (truncation)", "likes / reposts / views (counts)", "body (wording)",
             "accounts_created (descriptive only)"],
    "not_used_or_unavailable": ["reposter identities", "follower graphs", "historical engagement snapshots",
                                "device, IP or ownership signals (only the platform holds these)"],
}
NOT_PROOF = ("Statistical anomaly only. Nothing here proves coordinated inauthentic behaviour or a rule violation: "
             "shared audiences, followers and ordinary topical interest can produce the same numbers.")
LIMITATIONS = (
    "Timing is judged only for posts whose saved likers carry `liked_at`; untimed lists support overlap tests only.",
    "Reposter identities, follower graphs and historical snapshots are not part of the input, so reposts are only "
    "counted and follower overlap (the most common innocent explanation) is not tested.",
    f"A liker list of {LIKER_PAGE_CAP} or more entries, or one flagged `more_pages`, is treated as truncated and "
    "under-counts overlap.",
    "The reference population is the set of accounts seen liking the analysed posts. If the posts were chosen "
    "because they were popular, the baseline favours popular posts (this makes p-values conservative, not exact).",
    "Adjacent account ids are suggestive of accounts registered together, not proof of a shared owner.",
    "The comparison posts are only as representative as the sample that was collected.",
)


# ---------------------------------------------------------------- loading

def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def normalized_text(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def _read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_posts(sources: Iterable[Path | str], author_hints: dict[int, int] | None = None) -> dict[str, Any]:
    """Merge saved snapshots into {posts, accounts_created, sources_used, skipped_small}.

    ``author_hints`` fills in authors a snapshot did not record; a post with no known author is never
    treated as a different-author or same-author pair."""
    posts: dict[int, dict[str, Any]] = {}
    created: dict[int, str] = {}
    used: list[str] = []
    for source in map(Path, sources):
        data = _read_json(source)
        if not isinstance(data, dict) or not isinstance(data.get("posts"), dict):
            raise ValueError(f"{source}: expected a JSON object with a 'posts' mapping (see README.md)")
        used.append(source.name)
        for pid, record in data["posts"].items():
            entry = posts.setdefault(int(pid), {"post_id": int(pid)})
            if isinstance(record, list):                                  # untimed: a bare list of liker ids
                entry["likers"] = sorted({int(x) for x in record})
            elif isinstance(record, dict):
                rows = record.get("likers", [])
                if rows and isinstance(rows[0], dict):
                    timed = {int(r["account_id"]): parse_timestamp(r["liked_at"]).timestamp()
                             for r in rows if r.get("liked_at")}
                    entry["likers"] = sorted({int(r["account_id"]) for r in rows})
                    if timed:
                        entry["liked_at"] = timed
                else:
                    entry["likers"] = sorted({int(x) for x in rows})
                for key, target in (("likes", "likes"), ("reposts", "reposts"), ("views", "views")):
                    if _num(record.get(key)) is not None:
                        entry[target] = _num(record.get(key))
                if record.get("more_pages") is not None:
                    entry["more_pages"] = bool(record["more_pages"])
                for key in ("role", "body", "created_at", "global_hot_score", "rank_position"):
                    if record.get(key) is not None:
                        entry[key] = record[key]
                author = _int(record.get("author_id", record.get("author")))
                if author is not None:
                    entry["author"] = author
            else:
                raise ValueError(f"{source}: post {pid} must be an object or a list of liker ids")
            entry["source"] = source.name
        for account_id, moment in (data.get("accounts_created") or {}).items():
            created[int(account_id)] = str(moment)
    for pid, author in (author_hints or {}).items():
        if int(pid) in posts and posts[int(pid)].get("author") is None:
            posts[int(pid)]["author"] = int(author)
    skipped = sorted(pid for pid, p in posts.items() if len(p.get("likers", [])) < MIN_LIKERS)
    return {"posts": posts, "accounts_created": created, "sources_used": used, "skipped_small": skipped}


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- statistics

def hypergeom_sf(shared: int, set_a: int, set_b: int, population: int) -> float:
    """P(overlap >= shared) when two sets of the given sizes are drawn independently from `population`."""
    if shared <= 0:
        return 1.0
    top = min(set_a, set_b)
    if shared > top or set_a > population or set_b > population:
        return 0.0 if shared > top else 1.0
    total = math.comb(population, set_b)
    tail = sum(math.comb(set_a, i) * math.comb(population - set_a, set_b - i)
               for i in range(shared, top + 1) if set_b - i >= 0)
    return min(1.0, tail / total)


def robust_z(value: float, baseline: list[float], floor: float = 0.01) -> float | None:
    """Distance from the median in MAD units (MAD floored so a flat baseline cannot explode the score)."""
    if len(baseline) < 3:
        return None
    median = statistics.median(baseline)
    mad = max(statistics.median(abs(x - median) for x in baseline) * 1.4826, floor)
    return (value - median) / mad


def id_runs(ids: Iterable[int], gap: int = RUN_GAP, minimum: int = RUN_MIN) -> list[list[int]]:
    ordered = sorted(set(ids))
    runs: list[list[int]] = []
    current: list[int] = []
    for value in ordered:
        if current and value - current[-1] > gap:
            runs.append(current)
            current = []
        current.append(value)
    if current:
        runs.append(current)
    return [run for run in runs if len(run) >= minimum]


def run_share(ids: Iterable[int]) -> float:
    ids = list(set(ids))
    return sum(len(run) for run in id_runs(ids)) / len(ids) if ids else 0.0


def adjacency_p_value(core: set[int], population: set[int], draws: int = PERMUTATIONS, seed: int = 0) -> float | None:
    """Empirical P(a random liker subset of the same size is at least as clustered in account-id runs)."""
    pool = sorted(population - core)
    if len(core) < RUN_MIN or len(pool) < len(core):
        return None
    observed = run_share(core)
    rng = random.Random(seed)
    hits = sum(run_share(rng.sample(pool, len(core))) >= observed for _ in range(draws))
    return (hits + 1) / (draws + 1)


def lockstep(times_a: dict[int, float], times_b: dict[int, float], window: int = LOCKSTEP_WINDOW,
             perms: int = LOCKSTEP_PERMS, seed: int = 0) -> dict[str, Any] | None:
    """Do shared likers like the second post a (nearly) constant time after the first?

    Finds the largest cohort whose like-time difference fits in `window` seconds and asks how often a random
    re-pairing of the same accounts does as well.  Kinds:
      same-session      cohort likes both posts within SESSION_CENTRE seconds: ordinary heavy browsers
      fixed-offset      constant offset AND the cohort's own like times are spread out: each account repeats
                        the same delay (offset jitter far smaller than the spread of their own like times)
      co-burst          constant offset but the cohort liked in one short burst on each post (ambiguous)
      unstructured      nothing beyond the overlap itself
    """
    shared = sorted(set(times_a) & set(times_b))
    if len(shared) < MIN_SHARED_TIMED:
        return None
    if statistics.median(times_a[x] for x in shared) > statistics.median(times_b[x] for x in shared):
        times_a, times_b = times_b, times_a
        flipped = True
    else:
        flipped = False
    first = [times_a[x] for x in shared]
    second = [times_b[x] for x in shared]

    def best(second_times: list[float]) -> tuple[int, float, list[int]]:
        ranked = sorted((b - a, i) for i, (a, b) in enumerate(zip(first, second_times)))
        top, left = (0, 0.0, []), 0
        for right in range(len(ranked)):
            while ranked[right][0] - ranked[left][0] > window:
                left += 1
            if right - left + 1 > top[0]:
                top = (right - left + 1, (ranked[right][0] + ranked[left][0]) / 2, [i for _, i in ranked[left:right + 1]])
        return top

    count, centre, members = best(second)
    rng = random.Random(seed)
    shuffled = list(second)
    hits = 0
    for _ in range(perms):
        rng.shuffle(shuffled)
        hits += best(shuffled)[0] >= count
    p_value = (hits + 1) / (perms + 1)
    span = (max(first[i] for i in members) - min(first[i] for i in members)) if members else 0.0
    offsets = [second[i] - first[i] for i in members]
    jitter = (max(offsets) - min(offsets)) if members else 0.0
    if p_value > LOCKSTEP_P or count < 5:
        kind = "unstructured"
    elif abs(centre) < SESSION_CENTRE:
        kind = "same-session"
    elif count >= MIN_COHORT:
        kind = "fixed-offset" if span >= max(MIN_SPAN, SPAN_FACTOR * jitter) else "co-burst"
    else:
        kind = "unstructured"
    return {"shared": len(shared), "cohort": count, "offset_seconds": round(centre), "cohort_span_seconds": round(span),
            "offset_jitter_seconds": round(jitter, 1), "p": p_value, "kind": kind,
            "cohort_accounts": sorted(shared[i] for i in members), "first_post_is_a": not flipped}


def session_regulars(times_by_post: dict[int, dict[int, float]]) -> set[int]:
    """Accounts that like SESSION_POSTS different posts inside SESSION_SECONDS: the normal 'browsing session' audience."""
    per_account: dict[int, list[tuple[float, int]]] = {}
    for pid, times in times_by_post.items():
        for account, moment in times.items():
            per_account.setdefault(account, []).append((moment, pid))
    found = set()
    for account, events in per_account.items():
        events.sort()
        for i in range(len(events)):
            window = {pid for moment, pid in events[i:] if moment - events[i][0] <= SESSION_SECONDS}
            if len(window) >= SESSION_POSTS:
                found.add(account)
                break
    return found


# ---------------------------------------------------------------- analysis

def analyse(loaded: dict[str, Any], exclude_posts: Iterable[int] = (), exclude_accounts: Iterable[int] = (),
            already_reported: Iterable[int] = ()) -> dict[str, Any]:
    drop_posts, drop_accounts = set(exclude_posts), set(exclude_accounts)
    reported = set(already_reported)
    posts = {}
    for pid, post in loaded["posts"].items():
        if pid in drop_posts or post.get("author") in drop_accounts:
            continue
        likers = set(post.get("likers", [])) - drop_accounts
        if len(likers) >= MIN_LIKERS:
            posts[pid] = dict(post, likers=likers)
            if post.get("liked_at"):
                posts[pid]["liked_at"] = {a: t for a, t in post["liked_at"].items() if a in likers}
    if len(posts) < 3:
        return {"posts_analysed": sorted(posts), "groups": [], "limitations": list(LIMITATIONS), "notes": [],
                "verdict": "Insufficient data: fewer than three posts have a usable liker list, so no overlap "
                           "baseline can be built and no conclusion is drawn.", "not_proof": NOT_PROOF}

    population = set().union(*(p["likers"] for p in posts.values()))
    for pid, post in posts.items():
        likes = post.get("likes")
        if post.get("more_pages") is not None:
            post["truncated"] = bool(post["more_pages"])
        else:
            post["truncated"] = len(post["likers"]) >= LIKER_PAGE_CAP or (likes is not None and len(post["likers"]) < 0.95 * likes)
        post["completeness_known"] = likes is not None or post.get("more_pages") is not None
    ids = sorted(posts)
    pairs = []
    for a, b in itertools.combinations(ids, 2):
        la, lb = posts[a]["likers"], posts[b]["likers"]
        shared = len(la & lb)
        p_value = hypergeom_sf(shared, len(la), len(lb), len(population))
        pairs.append({"a": a, "b": b, "shared": shared, "jaccard": shared / len(la | lb),
                      "overlap_coeff": shared / min(len(la), len(lb)), "p": p_value,
                      "same_author": (posts[a]["author"] == posts[b]["author"]
                                      if posts[a].get("author") is not None and posts[b].get("author") is not None else None)})
    tests = len(pairs)
    for pair in pairs:
        pair["p_bonferroni"] = min(1.0, pair["p"] * tests)
    cross = [p["jaccard"] for p in pairs if p["same_author"] is False]
    same = [p["jaccard"] for p in pairs if p["same_author"] is True]
    same_benchmark = max(same) if same else None
    for pair in pairs:
        pair["robust_z"] = robust_z(pair["jaccard"], cross)

    edges = [p for p in pairs if p["overlap_coeff"] >= EDGE_MIN_OVERLAP_COEFF and p["p_bonferroni"] <= EDGE_MAX_BONFERRONI_P]
    components = _components(edges)
    ratios = {pid: p["reposts"] / p["likes"] for pid, p in posts.items() if p.get("likes") and p.get("reposts") is not None}
    flagged = set().union(*components) if components else set()
    timed = {pid: p["liked_at"] for pid, p in posts.items() if p.get("liked_at")}
    regulars = session_regulars(timed)
    timing_cache: dict[tuple[int, int], dict[str, Any] | None] = {}
    for a, b in itertools.combinations(sorted(timed), 2):
        timing_cache[(a, b)] = lockstep(timed[a], timed[b])
    groups = [_describe_group(sorted(comp), posts, pairs, population, flagged, ratios,
                              loaded.get("accounts_created", {}), reported, timing_cache, regulars)
              for comp in components if len(comp) >= MIN_GROUP_POSTS]
    groups.sort(key=lambda g: (TIER_ORDER.index(g["evidence_tier"]), -g["indicators_triggered"], g["weakest_p_bonferroni"]))
    for rank, group in enumerate(groups, 1):
        group["rank"] = rank
        group["linked_posts"] = _linked_posts(group, posts, timed, reported)
    kinds = Counter(t["kind"] for t in timing_cache.values() if t)
    in_group = {(a, b) for g in groups for a, b in itertools.combinations(g["post_ids"], 2)}
    outside = Counter(t["kind"] for key, t in timing_cache.items() if t and key not in in_group)
    sample = Counter(p.get("role") or "unlabelled" for p in posts.values())
    return {
        "timing_summary": {"timed_posts": len(timed), "pairs_with_enough_shared_likers": sum(kinds.values()),
                           "all_pairs": dict(kinds), "pairs_outside_flagged_groups": dict(outside),
                           "session_regulars": len(regulars),
                           "likers_in_timed_posts": len(set().union(*(set(t) for t in timed.values()))) if timed else 0},
        "sample_composition": dict(sample), "data_fields": DATA_FIELDS,
        "posts_analysed": ids, "population_size": len(population), "pairs_tested": tests,
        "baseline": {"cross_author_pair_jaccard_median": round(statistics.median(cross), 4) if cross else None,
                     "cross_author_pair_jaccard_max": round(max(cross), 4) if cross else None,
                     "same_author_pair_jaccard_max": round(same_benchmark, 4) if same_benchmark is not None else None,
                     "same_author_pairs": len(same)},
        "groups": groups, "truncated_posts": sorted(p for p, v in posts.items() if v["truncated"]),
        "skipped_small": loaded.get("skipped_small", []), "limitations": list(LIMITATIONS), "notes": [],
        "not_proof": NOT_PROOF,
        "verdict": ("No liker group stands out from the baseline in this data." if not groups else
                    f"{len(groups)} liker group(s) overlap more than chance allows; see indicators for how much "
                    "extra weight each deserves. None is a proven violation."),
    }


def _components(edges: list[dict[str, Any]]) -> list[set[int]]:
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for edge in edges:
        parent[find(edge["a"])] = find(edge["b"])
    groups: dict[int, set[int]] = {}
    for node in list(parent):
        groups.setdefault(find(node), set()).add(node)
    return list(groups.values())


def _describe_group(ids: list[int], posts: dict[int, dict[str, Any]], pairs: list[dict[str, Any]],
                    population: set[int], flagged: set[int],
                    ratios: dict[int, float], created: dict[int, str], reported: set[int],
                    timing: dict[tuple[int, int], dict[str, Any] | None], regulars: set[int]) -> dict[str, Any]:
    inside = [p for p in pairs if p["a"] in ids and p["b"] in ids]
    core = set.intersection(*(posts[i]["likers"] for i in ids))
    outside = set().union(*(p["likers"] for pid, p in posts.items() if pid not in ids))
    authors = sorted({posts[i].get("author") for i in ids if posts[i].get("author") is not None})
    group_jaccard = min((p["jaccard"] for p in inside), default=0.0)
    indicators: list[dict[str, Any]] = []

    weakest = max(p["p_bonferroni"] for p in inside)
    indicators.append(_ind("overlap_significance", weakest <= EDGE_MAX_BONFERRONI_P, weakest,
                           f"<= {EDGE_MAX_BONFERRONI_P}", "worst Bonferroni p-value among the pairs in the group"))
    others = [p for p in pairs if p["same_author"] is False and not {p["a"], p["b"]} & set(ids)]
    zs = [robust_z(p["jaccard"], [o["jaccard"] for o in others]) for p in inside]
    zs = [z for z in zs if z is not None]
    indicators.append(_ind("overlap_vs_unrelated_pairs", bool(zs) and min(zs) >= ROBUST_Z_FLAG,
                           round(min(zs), 2) if zs else None, f">= {ROBUST_Z_FLAG}",
                           "smallest robust z of the group's pair Jaccard against pairs of different authors outside the group"))
    audience = [p["jaccard"] for p in pairs if p["same_author"] is True and not {p["a"], p["b"]} & flagged]
    if not audience:
        indicators.append(_ind("exceeds_same_author_audience", None, None, "n/a",
                               "no unflagged same-author pairs exist, so there is no clean yardstick for a normal shared audience"))
    else:
        indicators.append(_ind("exceeds_same_author_audience", min(p["jaccard"] for p in inside) > max(audience),
                               round(min(p["jaccard"] for p in inside), 3), f"> {round(max(audience), 3)}",
                               "weakest pair overlap must exceed the largest overlap between one author's own unflagged posts"))
    pool = population - core
    adj_p = adjacency_p_value(core, population)
    indicators.append(_ind("core_account_id_adjacency", None if adj_p is None else adj_p <= ID_ADJACENCY_P,
                           None if adj_p is None else round(adj_p, 4), f"<= {ID_ADJACENCY_P}",
                           f"{round(run_share(core) * 100)}% of the {len(core)} core likers sit in runs of consecutive "
                           f"account ids; permutation test against {len(pool)} other likers"))
    group_ratios = [ratios[i] for i in ids if i in ratios]
    base_ratios = [r for pid, r in ratios.items() if pid not in ids]
    zr = robust_z(statistics.mean(group_ratios), base_ratios, floor=0.05) if group_ratios and base_ratios else None
    indicators.append(_ind("repost_to_like_ratio", None if zr is None else zr >= ROBUST_Z_FLAG,
                           None if zr is None else round(zr, 2), f">= {ROBUST_Z_FLAG}",
                           "group mean reposts/likes against other analysed posts (counts only: reposters unknown)"))
    group_timing = [dict(timing[(a, b)], posts=[a, b]) for a, b in itertools.combinations(ids, 2) if timing.get((a, b))]
    fixed = [t for t in group_timing if t["kind"] == "fixed-offset"]
    if not group_timing:
        indicators.append(_ind("fixed_offset_cohort", None, None, f"cohort >= {MIN_COHORT}, p <= {LOCKSTEP_P}",
                               "no like timestamps for this group's posts, so like timing cannot be judged"))
    else:
        top = max(group_timing, key=lambda t: (t["kind"] == "fixed-offset", t["cohort"]))
        indicators.append(_ind("fixed_offset_cohort", bool(fixed), top["cohort"], f"cohort >= {MIN_COHORT}, p <= {LOCKSTEP_P}",
                               "accounts that like each post a constant time after the other (largest cohort of any pair; "
                               "same-session browsers and single bursts do not count)"))
    counted = [i for i in indicators if i["triggered"] is not None]
    triggered = sum(1 for i in counted if i["triggered"])

    descriptive = {
        "core_likers": len(core),
        "core_liked_nothing_else_analysed": round(len(core - outside) / len(core), 3) if core else None,
        "wording_similarity": _text_similarity(ids, posts),
        "post_time_spread_minutes": _spread(ids, posts),
        "core_accounts_with_known_creation_time": _creation_burst(core, created),
        "core_share_who_are_session_regulars": round(len(core & regulars) / len(core), 3) if core else None,
    }
    truncated = [i for i in ids if posts[i]["truncated"]]
    unknown = [i for i in ids if not posts[i]["completeness_known"]]
    one_author = all(p["same_author"] is True for p in inside)
    yardstick_passed = any(i["name"] == "exceeds_same_author_audience" and i["triggered"] for i in indicators)
    timing_flag = next(i["triggered"] for i in indicators if i["name"] == "fixed_offset_cohort")
    capped = one_author and not (yardstick_passed or timing_flag)  # a loyal audience explains overlap, not repeated fixed delays
    no_timing_support = timing_flag is False                         # timing was measurable and showed nothing beyond overlap
    tier = ("strong anomaly" if triggered >= 3 and triggered == len(counted) and not capped else
            "weak / consistent with a shared audience" if no_timing_support else
            "moderate anomaly" if triggered >= 2 else "weak / not distinguishable from shared audience")
    return {
        "post_ids": ids, "authors": authors, "core_account_ids": sorted(core),
        "already_reported_posts": sorted(set(ids) & reported),
        "pairs": [{k: (round(v, 4) if isinstance(v, float) and k != "p" else v) for k, v in p.items()} for p in inside],
        "group_min_jaccard": round(group_jaccard, 3),
        "indicators": indicators, "indicators_triggered": triggered, "indicators_measurable": len(counted),
        "weakest_p_bonferroni": weakest, "descriptive": descriptive,
        "evidence_tier": tier,
        "caveat": ("All posts share one author, so a loyal audience explains overlap by itself; the tier is capped at "
                   "'moderate' unless the overlap beats a clean same-author yardstick." if capped else None),
        "status": "statistical anomaly, not a proven violation",
        "data_quality": {"truncated_posts": truncated, "completeness_unknown_posts": unknown},
        "timing": [{k: v for k, v in t.items() if k != "cohort_accounts"} for t in group_timing],
        "fixed_offset_cohort_accounts": sorted(set().union(*(set(t["cohort_accounts"]) for t in fixed))) if fixed else [],
        "to_prove_it": ("Would need reposter ids and ownership or control signals (shared devices, operators), which "
                        "public data does not expose; only the platform can establish those."),
    }


def _linked_posts(group: dict[str, Any], posts: dict[int, dict[str, Any]], timed: dict[int, dict[int, float]],
                  reported: set[int]) -> list[dict[str, Any]]:
    """Posts OUTSIDE the group whose likers repeat the group's fixed-offset cohort (same accounts, same delays)."""
    if not group["fixed_offset_cohort_accounts"]:
        return []
    cohort = set(group["fixed_offset_cohort_accounts"])
    anchor = next((i for i in group["post_ids"] if i in timed), None)
    linked = []
    for pid in sorted(timed):
        if pid in group["post_ids"] or anchor is None:
            continue
        result = lockstep({a: t for a, t in timed[anchor].items() if a in cohort},
                          {a: t for a, t in timed[pid].items() if a in cohort})
        if result and result["kind"] == "fixed-offset":
            linked.append({"post_id": pid, "author": posts[pid].get("author"), "cohort": result["cohort"],
                           "offset_seconds": result["offset_seconds"], "p": result["p"], "role": posts[pid].get("role"),
                           "already_reported": pid in reported})
    return linked


def _ind(name: str, triggered: bool | None, value: Any, threshold: str, meaning: str) -> dict[str, Any]:
    return {"name": name, "triggered": triggered, "value": value, "threshold": threshold, "meaning": meaning}


def _text_similarity(ids: list[int], posts: dict[int, dict[str, Any]]) -> float | None:
    texts = [normalized_text(posts[i].get("body")) for i in ids if posts[i].get("body")]
    if len(texts) < 2:
        return None
    return round(max(SequenceMatcher(None, a, b).ratio() for a, b in itertools.combinations(texts, 2)), 3)


def _spread(ids: list[int], posts: dict[int, dict[str, Any]]) -> float | None:
    stamps = [parse_timestamp(posts[i]["created_at"]).timestamp() / 60 for i in ids if posts[i].get("created_at")]
    if len(stamps) >= 2:
        return round(max(stamps) - min(stamps), 1)
    ages = [posts[i]["age_m"] for i in ids if posts[i].get("age_m") is not None]    # relative to one scan
    return round(max(ages) - min(ages), 1) if len(ages) >= 2 else None


def _creation_burst(core: set[int], created: dict[int, str]) -> dict[str, Any] | None:
    known = {a: created[a] for a in core if a in created}
    if len(known) < 3:
        return None
    minutes = {a: parse_timestamp(v).timestamp() / 60 for a, v in known.items()}
    close = sum(any(b != a and abs(minutes[a] - minutes[b]) <= CREATION_WINDOW_MINUTES for b in minutes) for a in minutes)
    return {"accounts": len(known), "created_within_2_minutes_of_another": close,
            "note": "descriptive only: no creation times exist for the wider population to compare with"}


# ---------------------------------------------------------------- report

def render_markdown(result: dict[str, Any]) -> str:
    lines = ["# Coordinated engagement detector - evidence report", "", f"**{result['not_proof']}**", "",
             f"Verdict: {result['verdict']}", ""]
    if "population_size" in result:
        base = result["baseline"]
        lines += [f"Posts analysed: {len(result['posts_analysed'])} | accounts seen liking them: {result['population_size']} "
                  f"| pairs tested: {result['pairs_tested']}",
                  f"Baseline Jaccard overlap, different authors: median {base['cross_author_pair_jaccard_median']}, "
                  f"max {base['cross_author_pair_jaccard_max']}. Same author's own posts, max: "
                  f"{base['same_author_pair_jaccard_max']} ({base['same_author_pairs']} pairs, themselves possibly anomalous).", ""]
    if result.get("timing_summary"):
        ts = result["timing_summary"]
        lines += ["## Normal shared audience vs unusual engagement",
                  f"Like timestamps exist for {ts['timed_posts']} posts ({ts['likers_in_timed_posts']} accounts). "
                  f"{ts['pairs_with_enough_shared_likers']} post pairs share enough timed likers to judge: {ts['all_pairs']}.",
                  f"Pairs outside the flagged groups (the comparison baseline): {ts['pairs_outside_flagged_groups']}.",
                  f"{ts['session_regulars']} accounts liked {SESSION_POSTS} or more different posts within "
                  f"{SESSION_SECONDS} seconds: ordinary heavy browsers who explain much of the 'shared audience' overlap.",
                  "- same-session: overlap made of people who like several posts in one sitting. Normal.",
                  "- unstructured: overlap with no timing pattern. Consistent with a shared audience.",
                  "- co-burst: one short burst on each post. Ambiguous.",
                  "- fixed-offset: the same accounts like post after post with the same delay and the same order. "
                  "This is the unusual pattern, and the only one that audience size cannot explain.", ""]
        lines += ["Sample composition: " + ", ".join(f"{k}: {v}" for k, v in sorted(result["sample_composition"].items())), ""]
    for group in result["groups"]:
        lines += [f"## #{group['rank']} posts {', '.join(map(str, group['post_ids']))} - {group['evidence_tier']}",
                  f"Authors: {', '.join(map(str, group['authors'])) or 'not recorded'} | indicators triggered: "
                  f"{group['indicators_triggered']} of {group['indicators_measurable']} measurable | status: {group['status']}"]
        if group["already_reported_posts"]:
            lines.append(f"Already reported: posts {', '.join(map(str, group['already_reported_posts']))}")
        lines += ["", "| Indicator | Value | Threshold | Triggered | Meaning |", "|---|---|---|---|---|"]
        for ind in group["indicators"]:
            flag = "not measurable" if ind["triggered"] is None else ("yes" if ind["triggered"] else "no")
            value = _fmt_p(ind["value"]) if ind["name"] == "overlap_significance" else ind["value"]
            lines.append(f"| {ind['name']} | {value} | {ind['threshold']} | {flag} | {ind['meaning']} |")
        lines += ["", "Pairs: " + "; ".join(f"{p['a']}-{p['b']} shared {p['shared']}, Jaccard {p['jaccard']}, "
                                            f"p(Bonferroni) {_fmt_p(p['p_bonferroni'])}" for p in group["pairs"])]
        desc = group["descriptive"]
        if group["timing"]:
            lines.append("Timing: " + "; ".join(
                f"{t['posts'][0]}->{t['posts'][1]} {t['kind']} (cohort {t['cohort']} of {t['shared']} shared, "
                f"offset {t['offset_seconds']}s, jitter {t['offset_jitter_seconds']}s, p {_fmt_p(t['p'])})" for t in group["timing"]))
        if group["linked_posts"]:
            lines.append("Other posts the same cohort liked in lock-step: " + ", ".join(
                f"{l['post_id']} (author {l['author']})" for l in group["linked_posts"]))
        if group["caveat"]:
            lines.append(f"Caveat: {group['caveat']}")
        lines += [f"Core likers (liked every post in the group): {desc['core_likers']} -> {group['core_account_ids']}",
                  f"Descriptive only: wording similarity {desc['wording_similarity']}, post time spread "
                  f"{desc['post_time_spread_minutes']} min, core accounts that liked no other analysed post "
                  f"{desc['core_liked_nothing_else_analysed']}, account creation {desc['core_accounts_with_known_creation_time']}"]
        quality = group["data_quality"]
        if quality["truncated_posts"] or quality["completeness_unknown_posts"]:
            lines.append(f"Data quality: truncated liker lists {quality['truncated_posts']}; completeness unknown "
                         f"{quality['completeness_unknown_posts']}")
        lines += [f"To prove it: {group['to_prove_it']}", ""]
    if result.get("truncated_posts"):
        lines.append(f"Truncated liker lists (overlap under-counted): {result['truncated_posts']}")
    if result.get("skipped_small"):
        lines.append(f"Skipped, fewer than {MIN_LIKERS} likers saved: {len(result['skipped_small'])} posts")
    if result.get("data_fields"):
        lines += ["", "## Data fields", "Used: " + "; ".join(result["data_fields"]["used"]),
                  "Not used or unavailable: " + "; ".join(result["data_fields"]["not_used_or_unavailable"])]
    lines += ["", "## Limitations", *[f"- {item}" for item in result["limitations"]], "",
              "Evidence tiers follow a fixed rule: strong = at least 3 indicators measurable, all triggered, and not a "
              "single-author group without a clean yardstick; moderate = at least 2 triggered; otherwise weak. They are "
              "counts of triggered indicators, not probabilities. No confidence percentage is calculated because the "
              "data cannot support one.", ""]
    return "\n".join(lines)


def _fmt_p(value: float) -> str:
    return "<1e-300" if value < 1e-300 else f"{value:.2e}"


def write_text_atomic(path: Path, text: str) -> None:
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(text.encode("utf-8"))                 # LF on every OS, so reports compare byte for byte
    os.replace(temp, path)


def write_reports(result: dict[str, Any], md_path: Path, json_path: Path) -> None:
    write_text_atomic(md_path, render_markdown(result))
    write_text_atomic(json_path, json.dumps(result, indent=2, default=sorted, ensure_ascii=False))
