"""Generates examples/example_engagement.json: fully synthetic, seeded, no real accounts or posts.

Contents:
* 14 organic posts by different authors, liked by a shared pool of ordinary accounts at random delays;
* a loyal audience: one author's 3 posts liked by the same 35 followers at random delays (a false-positive control);
* a planted network: 40 consecutively registered accounts that like 5 posts by 3 authors in the same order,
  each with its own fixed delay after the post appears, and one repost per cohort account.

    python examples/make_example.py            (rewrites the file; the output is identical every time)
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).with_name("example_engagement.json")
T0 = datetime(2026, 1, 10, 8, 0, tzinfo=timezone.utc)


def iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def main() -> int:
    rng = random.Random(2026)
    pool = sorted(rng.sample(range(20_000, 80_000), 2500))
    regulars = pool[:300]                                     # ordinary heavy users: they appear on many posts
    posts: dict[str, dict] = {}
    created: dict[str, str] = {}

    def add(pid: int, author: int, when: datetime, likers: dict[int, datetime], role: str, reposts: int | None = None) -> None:
        posts[str(pid)] = {"author_id": author, "created_at": iso(when), "role": role, "more_pages": False,
                           "likes": len(likers), "reposts": rng.randint(0, len(likers) // 5) if reposts is None else reposts,
                           "views": len(likers) * rng.randint(4, 9), "body": f"Synthetic example post {pid}.",
                           "likers": [{"account_id": a, "liked_at": iso(t)} for a, t in sorted(likers.items(), key=lambda x: x[1])]}

    for i in range(14):                                       # organic posts
        when = T0 + timedelta(minutes=rng.uniform(0, 2880))
        chosen = set(rng.sample(regulars, rng.randint(8, 18))) | set(rng.sample(pool, rng.randint(30, 50)))
        add(1000 + i, 500 + i, when, {a: when + timedelta(seconds=rng.expovariate(1 / 2400)) for a in chosen}, "organic")

    followers = rng.sample(pool[300:], 35)                    # loyal audience of one author
    for i in range(3):
        when = T0 + timedelta(hours=6 + 9 * i)
        chosen = set(followers) | set(rng.sample(pool, 15))
        add(2000 + i, 777, when, {a: when + timedelta(seconds=rng.expovariate(1 / 1800)) for a in chosen}, "loyal-audience")

    farm = list(range(9000, 9040))                            # planted network: registered together, fixed order and delays
    for i, account in enumerate(farm):
        created[str(account)] = iso(T0 - timedelta(days=5) + timedelta(seconds=4 * i))
    for i, (author, hours) in enumerate([(601, 3), (602, 5), (601, 20), (603, 31), (602, 44)]):
        when = T0 + timedelta(hours=hours, minutes=rng.uniform(0, 30))
        likers = {a: when + timedelta(seconds=1 + 3.0 * k + rng.uniform(0, 1.5)) for k, a in enumerate(farm)}
        likers.update({a: when + timedelta(seconds=rng.expovariate(1 / 2400)) for a in rng.sample(pool, 15)})
        add(3000 + i, author, when, likers, "planted", reposts=len(farm) + rng.randint(0, 3))

    OUT.write_bytes(json.dumps({"posts": posts, "accounts_created": created}, indent=1).encode("utf-8"))   # LF on every OS
    print(f"wrote {OUT.name}: {len(posts)} posts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
