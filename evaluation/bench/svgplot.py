"""Minimal dependency-free SVG line charts with error bars (two panels side by side)."""

from __future__ import annotations

import math
from xml.sax.saxutils import escape

COLORS = {"A_overlap_only": "#E69F00", "B_time_bucket": "#009E73", "B_tuned": "#CC79A7", "C_v1": "#0072B2"}     # colour-blind-safe
MARKERS = {"A_overlap_only": "square", "B_time_bucket": "triangle", "B_tuned": "diamond", "C_v1": "circle"}
DASH = {"A_overlap_only": "6 3", "B_time_bucket": "2 3", "B_tuned": "8 3 2 3", "C_v1": ""}
PANEL_W, PANEL_H, MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 380, 260, 58, 16, 44, 56


def _marker(kind: str, x: float, y: float, color: str) -> str:
    if kind == "square":
        return f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" fill="{color}"/>'
    if kind == "diamond":
        return f'<polygon points="{x:.1f},{y - 5:.1f} {x + 5:.1f},{y:.1f} {x:.1f},{y + 5:.1f} {x - 5:.1f},{y:.1f}" fill="{color}"/>'
    if kind == "triangle":
        return f'<polygon points="{x:.1f},{y - 5:.1f} {x - 5:.1f},{y + 4:.1f} {x + 5:.1f},{y + 4:.1f}" fill="{color}"/>'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>'


def _panel(panel: dict, left: float) -> list[str]:
    plot_w, plot_h = PANEL_W - MARGIN_L - MARGIN_R, PANEL_H - MARGIN_T - MARGIN_B
    labels = panel["x_labels"]
    step = plot_w / max(1, len(labels) - 1) if len(labels) > 1 else 0
    px = lambda i: left + MARGIN_L + (i * step if len(labels) > 1 else plot_w / 2)
    py = lambda v: MARGIN_T + plot_h * (1 - min(max(v, 0.0), 1.0))
    out = [f'<text x="{left + MARGIN_L:.0f}" y="20" class="title">{escape(panel["title"])}</text>']
    for tick in (0, 0.25, 0.5, 0.75, 1.0):
        y = py(tick)
        out.append(f'<line x1="{left + MARGIN_L}" x2="{left + MARGIN_L + plot_w}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>')
        out.append(f'<text x="{left + MARGIN_L - 6}" y="{y + 4:.1f}" class="tick" text-anchor="end">{tick:g}</text>')
    for i, label in enumerate(labels):
        out.append(f'<text x="{px(i):.1f}" y="{MARGIN_T + plot_h + 16}" class="tick" text-anchor="middle">{escape(str(label))}</text>')
    out.append(f'<text x="{left + MARGIN_L + plot_w / 2:.0f}" y="{PANEL_H - 10}" class="axis" text-anchor="middle">{escape(panel["xlabel"])}</text>')
    out.append(f'<text transform="translate({left + 14:.0f},{MARGIN_T + plot_h / 2:.0f}) rotate(-90)" class="axis" text-anchor="middle">{escape(panel["ylabel"])}</text>')
    for name, points in panel["series"].items():
        color = COLORS.get(name, "#555555")
        valid = [(i, p) for i, p in enumerate(points) if p is not None and not math.isnan(p[0])]
        path = " ".join(f'{"M" if k == 0 else "L"}{px(i):.1f},{py(p[0]):.1f}' for k, (i, p) in enumerate(valid))
        dash = f' stroke-dasharray="{DASH.get(name, "")}"' if DASH.get(name) else ""
        out.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2"{dash}/>')
        for i, (value, lo, hi) in valid:
            out.append(f'<line x1="{px(i):.1f}" x2="{px(i):.1f}" y1="{py(lo):.1f}" y2="{py(hi):.1f}" stroke="{color}" stroke-width="1.2"/>')
            out.append(_marker(MARKERS.get(name, "circle"), px(i), py(value), color))
    return out


def two_panel_chart(panels: list[dict], legend: dict[str, str], caption: str) -> str:
    width, height = PANEL_W * len(panels), PANEL_H + 46
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" font-family="Helvetica, Arial, sans-serif">',
            "<style>.title{font-size:13px;font-weight:bold;fill:#222}.axis{font-size:12px;fill:#333}.tick{font-size:11px;fill:#444}.grid{stroke:#ddd;stroke-width:1}.leg{font-size:12px;fill:#222}.cap{font-size:11px;fill:#555}</style>",
            f'<rect width="{width}" height="{height}" fill="#ffffff"/>']
    for k, panel in enumerate(panels):
        body += _panel(panel, k * PANEL_W)
    x = MARGIN_L
    for name, text in legend.items():
        body.append(_marker(MARKERS.get(name, "circle"), x, PANEL_H + 10, COLORS.get(name, "#555555")))
        body.append(f'<text x="{x + 10}" y="{PANEL_H + 14}" class="leg">{escape(text)}</text>')
        x += 24 + 7 * len(text)
    body.append(f'<text x="{MARGIN_L}" y="{PANEL_H + 36}" class="cap">{escape(caption)}</text>')
    body.append("</svg>")
    return "\n".join(body) + "\n"
