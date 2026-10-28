"""Command line: analyse saved public engagement data and write the evidence reports.

    python -m coordination_detector analyze DATA.json [MORE.json ...] --out reports/

Writes detector_report.md / .json and, when a group shows a fixed-offset cohort (or --seed is given),
network_report.md / .json.  Reads only the files named; makes no network calls.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import __version__
from . import detector as co
from .network import build_network, render_network


def run_analysis(loaded: dict[str, Any], out: Path, seeds: list[int] | None = None, exclude_posts=(), exclude_accounts=(),
                 already_reported=()) -> dict[str, Any]:
    """Detector + network evidence on already-loaded data; returns a summary.  Shared by the CLI and wrappers."""
    out.mkdir(parents=True, exist_ok=True)
    result = co.analyse(loaded, exclude_posts, exclude_accounts, already_reported)
    co.write_reports(result, out / "detector_report.md", out / "detector_report.json")
    group = next((g for g in result["groups"] if g.get("fixed_offset_cohort_accounts")), None)
    net = None
    if seeds or group:
        net = build_network(loaded, seeds or (), None if seeds else group, exclude_accounts)
        co.write_text_atomic(out / "network_report.md", render_network(net))
        co.write_text_atomic(out / "network_report.json", json.dumps(net, indent=2, ensure_ascii=False))
    return {"result": result, "network": net, "out": out}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="coordination_detector",
                                     description="Offline coordinated-engagement detector (saved data only)")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="analyse saved engagement JSON and write evidence reports")
    analyze.add_argument("inputs", nargs="+", type=Path, help="engagement JSON files (see README for the format)")
    analyze.add_argument("--out", type=Path, default=Path("reports"), help="output folder (default: reports)")
    analyze.add_argument("--seed", nargs="*", type=int, default=[], metavar="POST",
                         help="seed posts for the network report (default: the strongest fixed-offset group)")
    analyze.add_argument("--exclude-posts", nargs="*", type=int, default=[], metavar="POST")
    analyze.add_argument("--exclude-accounts", nargs="*", type=int, default=[], metavar="ACCOUNT",
                         help="accounts to remove everywhere, e.g. your own")
    analyze.add_argument("--already-reported", nargs="*", type=int, default=[], metavar="POST",
                         help="posts to label as already reported (labelled, not hidden)")
    analyze.add_argument("--author", nargs="*", default=[], metavar="POST=ACCOUNT",
                         help="author of a post the data did not record")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    hints = {int(k): int(v) for k, v in (item.split("=", 1) for item in args.author)}
    try:
        loaded = co.load_posts(args.inputs, hints)
    except (OSError, ValueError, KeyError) as error:
        print(f"error: {error}")
        return 2
    summary = run_analysis(loaded, args.out, args.seed, args.exclude_posts, args.exclude_accounts, args.already_reported)
    result, net = summary["result"], summary["network"]
    print(result["verdict"])
    for group in result["groups"]:
        print(f"#{group['rank']} posts {group['post_ids']}: {group['evidence_tier']} "
              f"({group['indicators_triggered']}/{group['indicators_measurable']} indicators)")
    if net is not None:
        print(f"Network: {net['reading']} ({len(net['authors'])} authors, {len(net['network'])} posts)" if net["ok"]
              else f"Network report not built: {net['reason']}")
    print(f"Reports written to {args.out}")
    return 0
