"""Network evidence: follow one liker cohort across every saved post it reacts to in lock-step.

Starts from seed posts (or the strongest detector group), defines the cohort as the accounts that liked every
seed post, finds other posts the same cohort likes with a repeating delay, and compares all of them with the
rest of the sample.  Saved data only; deterministic (every permutation test is seeded).
"""

from __future__ import annotations

import itertools
import statistics
from datetime import datetime, timezone
from typing import Any, Iterable

from . import detector as co

MIN_NETWORK_COHORT = co.MIN_COHORT
JITTER_WARNING = 0.75          # median cross-post jitter above this share of the lockstep window is measured loosely


def _stamp(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def spearman(order_a: list[int], order_b: list[int]) -> float:
    rank_b = {a: i for i, a in enumerate(order_b)}
    n = len(order_a)
    return 1 - 6 * sum((i - rank_b[a]) ** 2 for i, a in enumerate(order_a)) / (n * (n * n - 1)) if n > 1 else 1.0


def build_network(loaded: dict[str, Any], seeds: Iterable[int] = (), group: dict[str, Any] | None = None,
                  exclude_accounts: Iterable[int] = ()) -> dict[str, Any]:
    drop = set(exclude_accounts)
    posts = loaded["posts"]
    timed = {pid: {a: t for a, t in p["liked_at"].items() if a not in drop}
             for pid, p in posts.items() if p.get("liked_at")}
    seeds = [int(s) for s in seeds] or (list(group["post_ids"]) if group else [])
    missing = [s for s in seeds if s not in timed]
    if len(seeds) < 2 or missing:
        return {"ok": False, "reason": f"need at least two seed posts with like timestamps (missing timing: {missing})"}
    cohort = set.intersection(*(set(timed[s]) for s in seeds))
    if len(cohort) < MIN_NETWORK_COHORT:
        return {"ok": False, "reason": f"only {len(cohort)} accounts liked every seed post (need {MIN_NETWORK_COHORT})"}

    anchor = min(seeds, key=lambda s: statistics.median(timed[s][a] for a in cohort))
    linked = []
    for pid in sorted(timed):
        if pid in seeds or len(cohort & set(timed[pid])) < co.MIN_SHARED_TIMED:
            continue
        r = co.lockstep({a: t for a, t in timed[anchor].items() if a in cohort},
                        {a: t for a, t in timed[pid].items() if a in cohort})
        if r and r["kind"] == "fixed-offset":
            linked.append(pid)
    network = sorted(seeds + linked, key=lambda p: min(timed[p][a] for a in cohort if a in timed[p]))

    rows = []
    for pid in network:
        mine = [timed[pid][a] for a in cohort if a in timed[pid]]
        created = posts[pid].get("created_at")
        lag = (min(mine) - co.parse_timestamp(created).timestamp()) if created else None
        rows.append({"post_id": pid, "author": posts[pid].get("author"), "seed": pid in seeds, "created_at": created,
                     "likers": len(timed[pid]), "complete": posts[pid].get("more_pages") is False,
                     "cohort_present": len(mine), "first_cohort_like_after_post_s": None if lag is None else round(lag, 1),
                     "cohort_window_s": round(max(mine) - min(mine), 1), "first_cohort_like": _stamp(min(mine))})

    pairs = []
    for a, b in itertools.combinations(network, 2):
        r = co.lockstep(timed[a], timed[b])
        if r:
            first, second = (a, b) if r["first_post_is_a"] else (b, a)
            pairs.append({"earlier": first, "later": second, **{k: v for k, v in r.items() if k not in ("cohort_accounts", "first_post_is_a")}})
        else:
            pairs.append({"earlier": a, "later": b, "kind": "not judged", "shared": len(set(timed[a]) & set(timed[b]))})
    judged = [p for p in pairs if p["kind"] != "not judged"]
    fixed = [p for p in judged if p["kind"] == "fixed-offset"]

    order = []
    for pid in network:
        common = [a for a in cohort if a in timed[pid] and a in timed[anchor]]
        base = sorted(common, key=lambda a: timed[anchor][a])
        mine = sorted(common, key=lambda a: timed[pid][a])
        deltas = [timed[pid][a] - timed[anchor][a] for a in common]
        med = statistics.median(deltas) if deltas else 0.0
        order.append({"post_id": pid, "compared": len(common), "spearman": round(spearman(base, mine), 4),
                      "median_delay_h": round(med / 3600, 2),
                      "max_deviation_s": round(max(abs(d - med) for d in deltas), 1) if deltas else None})

    on_all = cohort & set.intersection(*(set(timed[p]) for p in network))
    later = [p for p in network if p not in seeds]
    absent = sorted(a for a in cohort if later and not any(a in timed[p] for p in later))
    joined = sorted(set.intersection(*(set(timed[p]) for p in later)) - cohort) if later else []
    authors = sorted({posts[p].get("author") for p in network if posts[p].get("author") is not None})
    cross_likes = [{"author": a, "liked_post": p} for a in authors for p in network
                   if a in timed[p] and posts[p].get("author") != a]

    rest = sorted(p for p in timed if p not in network)
    overlap = {p: len(cohort & set(timed[p])) for p in rest}
    kinds: dict[str, int] = {}
    top = None
    for a, b in itertools.combinations(rest, 2):
        r = co.lockstep(timed[a], timed[b])
        if r:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
            if top is None or (r["cohort"], -r["p"]) > (top["cohort"], -top["p"]):
                top = {"posts": [a, b], "cohort": r["cohort"], "p": r["p"], "kind": r["kind"]}

    jitters = [p["offset_jitter_seconds"] for p in fixed]
    one_network = bool(judged) and len(fixed) / len(judged) >= 0.8 and len(authors) >= 2
    reading = ("consistent with ONE shared network: the same accounts repeat fixed delays across all linked posts"
               if one_network else
               "MIXED: not every linked pair repeats a fixed delay, so this may be several overlapping patterns")
    return {
        "ok": True, "seeds": seeds, "anchor": anchor, "cohort": sorted(cohort), "linked": linked, "network": network,
        "authors": authors, "posts": rows, "pairs": pairs, "pairs_judged": len(judged), "pairs_fixed_offset": len(fixed),
        "median_fixed_jitter_s": round(statistics.median(jitters), 1) if jitters else None,
        "loose_timing_warning": bool(jitters) and statistics.median(jitters) > JITTER_WARNING * co.LOCKSTEP_WINDOW,
        "order": order, "accounts_on_every_post": sorted(on_all), "cohort_absent_from_linked": absent,
        "joined_on_every_linked_post": joined, "author_cross_likes": cross_likes,
        "comparison": {"posts": len(rest), "cohort_overlap": overlap,
                       "max_cohort_overlap": max(overlap.values()) if overlap else None,
                       "pair_kinds": kinds, "largest_cohort": top},
        "reading": reading, "not_proof": co.NOT_PROOF,
    }


ALTERNATIVES = (
    "Platform-run or simulated audience accounts acting on a fixed internal schedule; public data cannot separate "
    "these from a third-party operation.",
    "An automated follow/notification chain that delivers posts to the same followers in a fixed order, with "
    "clients that act on notifications automatically (follower graphs are not part of the input).",
    "The authors may be beneficiaries or bystanders: being liked by a cohort says nothing about who controls it.",
)
FALSE_POSITIVE_RISKS = (
    "Heavy browsers who like many posts in one sitting create overlap; the `same-session` label and the comparison "
    "pairs exist to show that ordinary pattern.",
    "Loyal followers of one author overlap heavily; single-author groups are capped unless timing also repeats.",
    "Cross-day delays are measured less tightly: jitter grows with the gap, and a jitter close to the "
    f"{co.LOCKSTEP_WINDOW} s window means the cohort size is sensitive to that window.",
    "p = 1/(permutations+1) is the floor of the permutation test, not an exact probability.",
)


def render_network(net: dict[str, Any]) -> str:
    if not net.get("ok"):
        return f"# Network evidence\n\nNot built: {net.get('reason')}\n"
    L = ["# Network evidence - one liker cohort across posts", "", f"**{net['not_proof']}**", "",
         f"Seeds: {', '.join(map(str, net['seeds']))} (anchor {net['anchor']}). Cohort: {len(net['cohort'])} accounts that "
         f"liked every seed post. Linked posts found: {len(net['linked'])}.", "",
         f"**{len(net['authors'])} authors, {len(net['network'])} posts**: authors {', '.join(map(str, net['authors']))}. "
         f"{len(net['accounts_on_every_post'])} cohort accounts liked every post.", "",
         "## 1. Posts", "",
         "| Post | Author | Seed | Posted | Likers | List complete | Cohort present | First cohort like after posting | Cohort window |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in net["posts"]:
        lag = "-" if r["first_cohort_like_after_post_s"] is None else f"{r['first_cohort_like_after_post_s']:.0f} s"
        L.append(f"| {r['post_id']} | {r['author']} | {'yes' if r['seed'] else 'linked'} | {r['created_at'] or 'not saved'} | "
                 f"{r['likers']} | {'yes' if r['complete'] else 'unknown'} | {r['cohort_present']} of {len(net['cohort'])} | "
                 f"{lag} | {r['cohort_window_s']:.0f} s |")
    L += ["", f"Cohort members absent from every linked post ({len(net['cohort_absent_from_linked'])}): "
          f"{net['cohort_absent_from_linked']}.",
          f"Non-cohort accounts on every linked post ({len(net['joined_on_every_linked_post'])}): {net['joined_on_every_linked_post']}.",
          "Authors who liked another network post: " + (", ".join(f"{x['author']} -> {x['liked_post']}" for x in net["author_cross_likes"]) or "none") + ".",
          "", "## 2. Pairwise timing", "",
          "| Earlier | Later | Shared | Cohort | Offset | Jitter | p | Label |", "|---|---|---|---|---|---|---|---|"]
    for p in net["pairs"]:
        if p["kind"] == "not judged":
            L.append(f"| {p['earlier']} | {p['later']} | {p['shared']} | - | - | - | - | not judged |")
        else:
            L.append(f"| {p['earlier']} | {p['later']} | {p['shared']} | {p['cohort']} | {p['offset_seconds']} s "
                     f"({p['offset_seconds'] / 3600:.2f} h) | {p['offset_jitter_seconds']} s | {p['p']:.3f} | {p['kind']} |")
    L += ["", f"Fixed-offset pairs: {net['pairs_fixed_offset']} of {net['pairs_judged']} judged. Median jitter of those: "
          f"{net['median_fixed_jitter_s']} s."]
    if net["loose_timing_warning"]:
        L.append(f"Warning: median jitter is close to the {co.LOCKSTEP_WINDOW} s window, so cohort sizes are sensitive to it.")
    L += ["", "## 3. Reaction order (Spearman rho of cohort order vs the anchor; 1.0 = identical)", "",
          "| Post | Compared | rho | Median delay vs anchor | Largest deviation |", "|---|---|---|---|---|"]
    for o in net["order"]:
        L.append(f"| {o['post_id']} | {o['compared']} | {o['spearman']:.4f} | {o['median_delay_h']:+.2f} h | {o['max_deviation_s']} s |")
    c = net["comparison"]
    L += ["", "## 4. Comparison with the rest of the sample", "",
          f"- Other timed posts: {c['posts']}. Cohort members among their likers: max {c['max_cohort_overlap']}.",
          f"- Their pairs with enough shared likers: {sum(c['pair_kinds'].values())}, labelled {c['pair_kinds']}.",
          "- Largest timing cohort among them: " + (
              f"{c['largest_cohort']['cohort']} (posts {c['largest_cohort']['posts'][0]}/{c['largest_cohort']['posts'][1]}, "
              f"p {c['largest_cohort']['p']:.3f}, {c['largest_cohort']['kind']})." if c["largest_cohort"] else "none judged."), "",
          "## 5. Reading", "", f"**{net['reading']}.**", "",
          "Coordinated-looking (measured above): the same accounts, the same order, a repeating delay. Not shown: who "
          "operates the accounts, whether any author arranged the likes, and whether any platform rule was broken.", "",
          "**Alternative explanations:**", *[f"- {x}" for x in ALTERNATIVES], "",
          "**False-positive risks:**", *[f"- {x}" for x in FALSE_POSITIVE_RISKS], ""]
    return "\n".join(L)
