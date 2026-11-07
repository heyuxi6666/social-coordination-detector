"""Build Yuxi_He_Research_Report.pdf from mini_research_report.md (A4, 11 pt, via headless Microsoft Edge).

    python research_report/make_pdf.py

Standard library only plus an installed Microsoft Edge (Windows).  The Markdown file is the single source of truth: this
script only converts the subset of Markdown the report uses (headings, paragraphs, bullet lists, pipe tables, one figure,
bold/italic/code) and prints it.  It never changes the report text or any result.
"""

from __future__ import annotations

import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "mini_research_report.md"
OUTPUT = HERE / "Yuxi_He_Research_Report.pdf"
EDGE_CANDIDATES = (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")

CSS = """
@page { size: A4; margin: 17mm 18mm 17mm 18mm; }
html { font-family: 'Times New Roman', Times, serif; font-size: 11pt; line-height: 1.26; color: #111; font-variant-ligatures: none; }
body { margin: 0; }
h1 { font-size: 15.5pt; line-height: 1.2; margin: 0 0 5pt 0; text-align: left; }
.author { margin: 0 0 8pt 0; font-size: 10.5pt; line-height: 1.3; }
.author b { font-size: 11.5pt; }
h2 { font-size: 12pt; margin: 9pt 0 3pt 0; break-after: avoid; }
p { margin: 3pt 0; text-align: justify; hyphens: auto; }
ul { margin: 3pt 0 3pt 16pt; padding: 0; }
li { margin: 1pt 0; text-align: justify; }
table { border-collapse: collapse; width: 100%; margin: 3pt 0 5pt 0; font-size: 9pt; line-height: 1.2; break-inside: avoid; }
th, td { border: 0.6pt solid #888; padding: 1.5pt 3pt; text-align: left; vertical-align: top; }
th { background: #eceff3; }
td.num, th.num { text-align: center; white-space: nowrap; }
.caption { font-size: 10pt; line-height: 1.22; margin: 2pt 0 6pt 0; break-inside: avoid; }
.table-caption { margin-bottom: 2pt; break-after: avoid; }
figure { margin: 4pt 0 0 0; break-inside: avoid; }
figure img { width: 100%; display: block; }
.refs p { text-align: left; font-size: 9.5pt; line-height: 1.2; margin: 1.5pt 0; padding-left: 18pt; text-indent: -18pt; hyphens: none; word-break: break-word; }
sub { font-size: 70%; line-height: 0; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 9.5pt; }
a { color: #111; text-decoration: none; }
"""


def inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = re.sub(r"`(.+?)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"\*(.+?)\*", r"<i>\1</i>", out)
    out = re.sub(r"(https?://[^\s<)]+[^\s<).,;])", r"<a href='\1'>\1</a>", out)
    out = re.sub(r"(?<=[A-Za-z>])_(min|obs|i|r)\b", r"<sub>\1</sub>", out)         # n_min, c_obs, d_i, c_r -> subscripts
    out = re.sub(r"(?<=\d) / (?=\d)", "&nbsp;/&nbsp;", out)                           # keep "20 / 6 / 4" on one line
    return out


def table_html(rows: list[list[str]]) -> str:
    def cell(tag: str, text: str, numeric: bool) -> str:
        return f"<{tag}{' class=num' if numeric else ''}>{inline(text)}</{tag}>"
    body = []
    for k, row in enumerate(rows):
        numeric = [c != row[0] and bool(re.match(r"^[+−\-–✓\d]", c.strip())) for c in row]
        body.append("<tr>" + "".join(cell("th" if k == 0 else "td", c, n and k > 0 or (k == 0 and i > 0)) for i, (c, n) in enumerate(zip(row, numeric))) + "</tr>")
    return "<table>" + "".join(body) + "</table>"


def convert(markdown: str) -> str:
    lines, out, i = markdown.splitlines(), [], 0
    refs = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
            i += 1
            block = []
            while i < len(lines) and lines[i].strip():            # author block: consecutive lines until the next blank line
                block.append(lines[i])
                i += 1
            out.append("<div class=author>" + "<br>".join(inline(b) for b in block) + "</div>")
            continue
        if line.startswith("## "):
            refs = line[3:].strip() == "References"
            out.append(f"<h2>{inline(line[3:])}</h2>" + ("<div class=refs>" if refs else ""))
        elif line.startswith("!["):
            name = re.match(r"!\[.*?\]\((.+?)\)", line).group(1)
            caption = lines[i + 1] if i + 1 < len(lines) and lines[i + 1].startswith("**Figure") else ""
            out.append(f"<figure><img src='{(HERE / name).as_uri()}'><div class=caption>{inline(caption)}</div></figure>")
            i += 2 if caption else 1
            continue
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[-| :]+\|$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append(table_html(rows))
            continue
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(inline(lines[i][2:]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>")
            continue
        elif line.strip():
            css = " class='caption table-caption'" if line.startswith("**Table") else ""
            out.append(f"<p{css}>{inline(line)}</p>")
        i += 1
    if refs:
        out.append("</div>")
    return "".join(out)


def main() -> int:
    edge = next((p for p in EDGE_CANDIDATES if Path(p).exists()), None)
    if edge is None:
        print("Microsoft Edge not found; cannot print to PDF")
        return 2
    document = f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Evaluating Temporal Coordination Detection: False-Positive Control and Robustness under Synthetic Engagement Behaviour</title><style>{CSS}</style></head><body>{convert(SOURCE.read_text(encoding='utf-8'))}</body></html>"
    with tempfile.TemporaryDirectory() as folder:
        page = Path(folder) / "report.html"
        page.write_text(document, encoding="utf-8")
        profile = Path(folder) / "profile"
        subprocess.run([edge, "--headless", "--disable-gpu", "--no-first-run", f"--user-data-dir={profile}", "--no-pdf-header-footer",
                        f"--print-to-pdf={OUTPUT}", page.as_uri()], check=True, capture_output=True, timeout=120)
    print(f"wrote {OUTPUT.name} ({OUTPUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
